"""YieldAgent — autonomous yield optimization agent for Casper Network.

Runs a continuous decision loop:
1. Read on-chain state via MCP Server
2. Fetch off-chain RWA data via x402
3. Run decision engine (rules + LLM + risk)
4. Execute rebalance if warranted
5. Record results on-chain
"""

import asyncio
import signal
import time

from config import AgentConfig
from core.decision_engine import DecisionEngine, ActionType
from core.risk_assessor import RiskAssessor
from blockchain.mcp_client import McpClient
from data.x402_fetcher import X402Fetcher
from data.models import PoolState, OracleData, MarketSnapshot
from utils.logger import setup_logger
from ws_server import broadcaster


class YieldAgent:
    """Main agent class running the autonomous decision loop."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.logger = setup_logger("YieldAgent")
        self.mcp = McpClient(config)
        self.x402 = X402Fetcher(config.x402)
        self.risk = RiskAssessor(config.risk)
        self.decision = DecisionEngine(config, self.risk)
        self.running = False
        self.cycle_count = 0

    async def start(self):
        """Start the agent loop."""
        self.logger.info("=" * 60)
        self.logger.info("Yield Optimization Agent Starting")
        self.logger.info(f"Network: {self.config.network}")
        self.logger.info(f"Poll interval: {self.config.poll_interval_sec}s")
        self.logger.info(f"Pools: {[p.name for p in self.config.pools]}")
        self.logger.info("=" * 60)

        self.running = True

        # Start WebSocket server for real-time log push
        await broadcaster.start()
        self.logger.info("WebSocket server started on ws://0.0.0.0:8080")

        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, lambda s, f: asyncio.create_task(self.stop()))

        await self._register_identity()

        while self.running:
            try:
                await self._run_cycle()
            except Exception as e:
                self.logger.error(f"Cycle {self.cycle_count} failed: {e}", exc_info=True)

            self.cycle_count += 1
            await asyncio.sleep(self.config.poll_interval_sec)

    async def stop(self):
        """Gracefully stop the agent."""
        self.logger.info("Shutting down...")
        self.running = False
        await broadcaster.stop()
        await self.mcp.close()
        await self.x402.close()

    async def _register_identity(self):
        """Register agent on-chain (idempotent)."""
        if not self.config.registry_hash:
            self.logger.warning("No registry hash — skipping registration")
            return
        try:
            resp = await self.mcp.register_agent(
                contract_hash=self.config.registry_hash,
                name="YieldOptimizer-v1",
                strategy="Autonomous yield rebalancing across RWA-backed pools",
                key_path=self.config.secret_key_path,
            )
            if resp.success:
                self.logger.info("Agent registered on-chain")
            else:
                self.logger.warning(f"Registration skipped: {resp.error}")
        except Exception as e:
            self.logger.warning(f"Registration skipped: {e}")

    async def _run_cycle(self):
        """Single decision cycle."""
        start = time.time()
        self.logger.info(f"─── Cycle {self.cycle_count} ───")
        await broadcaster.log_cycle_start(self.cycle_count)

        # Step 1: Read on-chain state
        self.logger.info("[1/5] Reading on-chain state...")
        pools = await self._read_pools()
        agent_balance = await self._get_balance()

        # Step 2: Fetch off-chain data
        self.logger.info("[2/5] Fetching off-chain data via x402...")
        oracle_raw = await self.x402.fetch_all()
        oracle_data = {
            k: OracleData(
                data_type=v.data_type,
                value=v.value,
                source=v.source,
                confidence=v.confidence,
                age_seconds=0,
            )
            for k, v in oracle_raw.items()
        }

        # Submit to on-chain oracle
        for data in oracle_raw.values():
            await self._submit_oracle(data)
            await broadcaster.log_oracle(data.data_type, data.value, data.source)

        # Step 3: Build market snapshot
        self.logger.info("[3/5] Building market snapshot...")
        market = MarketSnapshot(
            timestamp=int(time.time()),
            cspr_price=0.05,  # TODO: fetch from API
            volatility_bps=self._estimate_volatility(pools),
        )

        # Step 4: Decision
        self.logger.info("[4/5] Running decision engine...")
        action = await self.decision.decide(
            pools=pools,
            oracle_data=oracle_data,
            market=market,
            agent_balance=agent_balance,
        )

        self.logger.info(
            f"Decision: {action.action_type.value} | "
            f"Confidence: {action.confidence}% | "
            f"Reason: {action.reasoning}"
        )
        await broadcaster.log_decision(
            action.action_type.value,
            action.confidence,
            action.reasoning,
        )

        # Step 5: Execute
        self.logger.info("[5/5] Executing...")
        if action.action_type == ActionType.REBALANCE and action.amount:
            await self._execute_rebalance(action)
        else:
            self.logger.info("Holding — no action needed")

        elapsed = time.time() - start
        self.logger.info(f"Cycle {self.cycle_count} completed in {elapsed:.1f}s")

    async def _read_pools(self) -> list[PoolState]:
        """Read all pool states from chain."""
        if not self.config.yield_pool_hash:
            # Return mock data if no contract deployed
            return [
                PoolState(0, "Stable Pool", 50_000_000_000_000, 300, 50),
                PoolState(1, "Growth Pool", 30_000_000_000_000, 600, 30),
                PoolState(2, "High Yield Pool", 20_000_000_000_000, 900, 20),
            ]

        try:
            raw = await self.mcp.get_all_pools(self.config.yield_pool_hash)
            pools = []
            total = sum(int(p[1]) for p in raw) if raw else 1
            for pool_id, apy in raw:
                config = next((c for c in self.config.pools if c.pool_id == pool_id), None)
                name = config.name if config else f"Pool {pool_id}"
                tvl = 0  # Would need separate query
                alloc = tvl * 100 // total if total > 0 else 0
                pools.append(PoolState(pool_id, name, tvl, int(apy), alloc))
            return pools
        except Exception as e:
            self.logger.warning(f"Failed to read pools: {e}")
            return []

    async def _get_balance(self) -> int:
        """Get agent's CSPR balance."""
        if not self.config.secret_key_path:
            return 100_000_000_000  # 100 CSPR mock
        try:
            # Would extract address from key file
            return 100_000_000_000
        except Exception:
            return 0

    async def _submit_oracle(self, data):
        """Submit fetched data to on-chain oracle."""
        if not self.config.oracle_hash:
            return
        try:
            resp = await self.mcp.submit_oracle_data(
                contract_hash=self.config.oracle_hash,
                data_type=data.data_type,
                value=data.value,
                source=data.source,
                confidence=data.confidence,
                key_path=self.config.secret_key_path,
            )
            if resp.success:
                self.logger.info(f"Oracle submitted: {data.data_type}={data.value}")
            else:
                self.logger.warning(f"Oracle submit failed: {resp.error}")
        except Exception as e:
            self.logger.warning(f"Oracle submit error: {e}")

    async def _execute_rebalance(self, action):
        """Execute a rebalance transaction."""
        self.logger.info(
            f"Rebalancing: Pool {action.from_pool} -> Pool {action.to_pool}, "
            f"Amount: {action.amount}"
        )
        await broadcaster.log_rebalance(
            action.from_pool or 0,
            action.to_pool or 0,
            action.amount or 0,
        )

        if not self.config.yield_pool_hash:
            self.logger.info("[mock] Rebalance — no contract hash")
            return

        try:
            resp = await self.mcp.submit_rebalance(
                contract_hash=self.config.yield_pool_hash,
                from_pool=action.from_pool,
                to_pool=action.to_pool,
                amount=action.amount,
                key_path=self.config.secret_key_path,
            )
            if resp.success:
                self.logger.info(f"Rebalance tx: {resp.data}")
                await self._record_operation(action)
            else:
                self.logger.error(f"Rebalance failed: {resp.error}")
        except Exception as e:
            self.logger.error(f"Rebalance error: {e}")

    async def _record_operation(self, action):
        """Record operation in AgentRegistry."""
        if not self.config.registry_hash:
            return
        try:
            pools = await self._read_pools()
            from_apy = pools[action.from_pool].apy_basis_points if action.from_pool is not None else 0
            to_apy = pools[action.to_pool].apy_basis_points if action.to_pool is not None else 0

            await self.mcp.record_operation(
                contract_hash=self.config.registry_hash,
                from_pool=action.from_pool or 0,
                to_pool=action.to_pool or 0,
                amount=action.amount or 0,
                from_apy=from_apy,
                to_apy=to_apy,
                key_path=self.config.secret_key_path,
            )
        except Exception as e:
            self.logger.warning(f"Record operation failed: {e}")

    def _estimate_volatility(self, pools: list[PoolState]) -> int:
        """Estimate market volatility from APY spread."""
        if len(pools) < 2:
            return 0
        apys = [p.apy_basis_points for p in pools]
        return max(apys) - min(apys)


async def main():
    config = AgentConfig()
    agent = YieldAgent(config)
    await agent.start()


if __name__ == "__main__":
    asyncio.run(main())
