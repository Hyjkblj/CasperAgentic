"""Multi-dimensional risk assessment for rebalance decisions."""

from dataclasses import dataclass
from typing import Any

from config import RiskConfig
from data.models import PoolState, MarketSnapshot


@dataclass
class RiskAssessment:
    """Result of a risk evaluation."""

    approved: bool
    score: int  # 0-100, higher = riskier
    reason: str
    checks: dict[str, bool]


class RiskAssessor:
    """Evaluates rebalance actions against multiple risk dimensions.

    Checks:
    1. Amount limit — single rebalance <= 30% of pool
    2. Allocation cap — target pool <= max_allocation_pct
    3. Gas efficiency — gas cost < 1% of annual gain
    4. Volatility — market volatility < threshold
    5. Confidence — LLM confidence >= 60%
    """

    def __init__(self, config: RiskConfig):
        self.config = config

    def assess(
        self,
        action: Any,
        pools: list[PoolState],
        agent_balance: int,
        market: MarketSnapshot,
    ) -> RiskAssessment:
        """Run all risk checks on a proposed action."""
        checks: dict[str, bool] = {}
        reasons: list[str] = []
        total_score = 0

        # Check 1: Amount limit
        if action.from_pool is not None and action.amount is not None:
            from_pool = pools[action.from_pool]
            max_amount = from_pool.total_deposited * self.config.max_single_rebalance_pct // 100
            checks["amount_limit"] = action.amount <= max_amount
            if not checks["amount_limit"]:
                reasons.append(
                    f"Amount exceeds {self.config.max_single_rebalance_pct}% limit"
                )
                total_score += 30

        # Check 2: Target allocation cap
        if action.to_pool is not None and action.amount is not None:
            total_tvl = sum(p.total_deposited for p in pools)
            if total_tvl > 0:
                new_target_tvl = pools[action.to_pool].total_deposited + action.amount
                new_pct = new_target_tvl * 100 // total_tvl
                max_pct = 50  # default max
                checks["allocation_limit"] = new_pct <= max_pct
                if not checks["allocation_limit"]:
                    reasons.append(
                        f"Target pool allocation {new_pct}% exceeds max {max_pct}%"
                    )
                    total_score += 25

        # Check 3: Gas efficiency
        estimated_gas_motes = 12_000_000  # ~0.012 CSPR
        if action.expected_apy_gain > 0 and action.amount:
            annual_gain = action.amount * action.expected_apy_gain // 10000
            if annual_gain > 0:
                gas_ratio = estimated_gas_motes * 10000 // annual_gain
                checks["gas_efficiency"] = gas_ratio < 100  # gas < 1% of gain
                if not checks["gas_efficiency"]:
                    reasons.append("Gas cost exceeds benefit threshold")
                    total_score += 20

        # Check 4: Market volatility
        checks["volatility"] = market.volatility_bps < self.config.volatility_threshold
        if not checks["volatility"]:
            reasons.append(
                f"Volatility {market.volatility_bps/100:.1f}% exceeds threshold"
            )
            total_score += 15

        # Check 5: Confidence
        checks["confidence"] = action.confidence >= 60
        if not checks["confidence"]:
            reasons.append(f"Low confidence: {action.confidence}%")
            total_score += 10

        approved = total_score < 50
        reason = "; ".join(reasons) if reasons else "All checks passed"

        return RiskAssessment(
            approved=approved,
            score=total_score,
            reason=reason,
            checks=checks,
        )
