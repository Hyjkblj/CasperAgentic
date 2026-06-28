"""Decision engine combining LLM reasoning with rule-based constraints."""

import json
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import anthropic

from config import AgentConfig
from data.models import PoolState, OracleData, MarketSnapshot
from core.risk_assessor import RiskAssessor


class ActionType(Enum):
    HOLD = "hold"
    REBALANCE = "rebalance"


@dataclass
class RebalanceAction:
    """A decision output from the engine."""

    action_type: ActionType
    from_pool: Optional[int] = None
    to_pool: Optional[int] = None
    amount: Optional[int] = None
    confidence: int = 0  # 0-100
    reasoning: str = ""
    risk_score: int = 0  # 0-100
    expected_apy_gain: int = 0  # basis points


SYSTEM_PROMPT = """You are a yield optimization agent for Casper Network DeFi pools.

Your job: analyze pool states, RWA oracle data, and market conditions to decide
whether to rebalance funds between pools.

Rules:
- Only suggest rebalance when the APY gain exceeds 0.5% (50 bps) after gas costs
- Never allocate more than the configured max_allocation_pct to any single pool
- Prefer stability over maximum yield in high-volatility conditions
- Consider RWA oracle confidence: low confidence reduces conviction
- Always explain your reasoning clearly

Output JSON only:
{
    "action": "hold|rebalance",
    "from_pool": null | int,
    "to_pool": null | int,
    "amount": null | int,
    "confidence": 0-100,
    "reasoning": "string",
    "expected_apy_gain": int
}"""


class DecisionEngine:
    """Three-layer decision engine: rules -> LLM -> risk check.

    Layer 1 (Rule Precheck): Hard constraints filter impossible actions.
    Layer 2 (LLM Analysis): Claude analyzes market data for strategy.
    Layer 3 (Risk Validation): Multi-dimensional risk scoring.
    """

    def __init__(self, config: AgentConfig, risk_assessor: RiskAssessor):
        self.config = config
        self.risk = risk_assessor
        self.client = anthropic.Anthropic(api_key=config.llm_api_key)

    async def decide(
        self,
        pools: list[PoolState],
        oracle_data: dict[str, OracleData],
        market: MarketSnapshot,
        agent_balance: int,
    ) -> RebalanceAction:
        """Main decision entry point."""

        # Layer 1: Rule precheck
        rule_result = self._rule_precheck(pools, agent_balance)
        if rule_result:
            return rule_result

        # Layer 2: LLM analysis
        llm_suggestion = self._llm_analyze(pools, oracle_data, market)

        # Layer 3: Risk validation
        risk_result = self.risk.assess(
            action=llm_suggestion,
            pools=pools,
            agent_balance=agent_balance,
            market=market,
        )

        if not risk_result.approved:
            return RebalanceAction(
                action_type=ActionType.HOLD,
                confidence=80,
                reasoning=(
                    f"LLM suggested {llm_suggestion.action_type.value} "
                    f"but rejected by risk: {risk_result.reason}"
                ),
                risk_score=risk_result.score,
            )

        llm_suggestion.risk_score = risk_result.score
        return llm_suggestion

    def _rule_precheck(
        self, pools: list[PoolState], agent_balance: int
    ) -> Optional[RebalanceAction]:
        """Hard constraint checks — return HOLD if any fail."""

        min_gas = int(self.config.risk.min_gas_reserve * 1e9)
        if agent_balance < min_gas:
            return RebalanceAction(
                action_type=ActionType.HOLD,
                confidence=100,
                reasoning="Insufficient balance for gas fees",
            )

        apys = [p.apy_basis_points for p in pools]
        if apys and (max(apys) - min(apys)) < 100:
            return RebalanceAction(
                action_type=ActionType.HOLD,
                confidence=90,
                reasoning="APY spread too narrow for rebalance (< 1%)",
            )

        return None

    def _llm_analyze(
        self,
        pools: list[PoolState],
        oracle_data: dict[str, OracleData],
        market: MarketSnapshot,
    ) -> RebalanceAction:
        """Call Claude for strategy analysis."""

        prompt = self._build_prompt(pools, oracle_data, market)

        try:
            message = self.client.messages.create(
                model=self.config.llm_model,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            return self._parse_response(message.content[0].text)
        except Exception as e:
            return RebalanceAction(
                action_type=ActionType.HOLD,
                confidence=0,
                reasoning=f"LLM call failed: {e}",
            )

    def _build_prompt(
        self,
        pools: list[PoolState],
        oracle_data: dict[str, OracleData],
        market: MarketSnapshot,
    ) -> str:
        pools_str = "\n".join(
            f"  Pool {p.pool_id} ({p.name}): "
            f"APY={p.apy_basis_points/100:.2f}%, "
            f"TVL={p.total_deposited/1e9:.0f} CSPR, "
            f"allocation={p.allocation_pct}%"
            for p in pools
        )

        oracle_str = "\n".join(
            f"  {k}: {v.value/100:.2f}% (confidence: {v.confidence}%, "
            f"age: {v.age_seconds}s, source: {v.source})"
            for k, v in oracle_data.items()
        ) or "  (no oracle data available)"

        return f"""Current market snapshot:
- Timestamp: {market.timestamp}
- CSPR price: ${market.cspr_price:.4f}
- Market volatility: {market.volatility_bps/100:.2f}%

Pool states:
{pools_str}

RWA Oracle data:
{oracle_str}

Agent config:
- Max single rebalance: {self.config.risk.max_single_rebalance_pct}% of pool
- Risk tolerance: moderate

Should we rebalance? Analyze and provide your recommendation as JSON."""

    def _parse_response(self, response: str) -> RebalanceAction:
        """Parse LLM JSON output into a RebalanceAction."""
        try:
            # Strip markdown fences if present
            text = response.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]

            data = json.loads(text)
            action_type = ActionType(data.get("action", "hold"))

            if action_type == ActionType.HOLD:
                return RebalanceAction(
                    action_type=ActionType.HOLD,
                    confidence=data.get("confidence", 50),
                    reasoning=data.get("reasoning", ""),
                    expected_apy_gain=data.get("expected_apy_gain", 0),
                )

            return RebalanceAction(
                action_type=action_type,
                from_pool=data.get("from_pool"),
                to_pool=data.get("to_pool"),
                amount=data.get("amount"),
                confidence=data.get("confidence", 50),
                reasoning=data.get("reasoning", ""),
                expected_apy_gain=data.get("expected_apy_gain", 0),
            )
        except (json.JSONDecodeError, ValueError) as e:
            return RebalanceAction(
                action_type=ActionType.HOLD,
                confidence=0,
                reasoning=f"Failed to parse LLM response: {e}",
            )
