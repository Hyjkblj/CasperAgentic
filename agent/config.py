"""Agent configuration."""

import os
from dataclasses import dataclass, field


@dataclass
class PoolConfig:
    """Configuration for a single yield pool."""

    pool_id: int
    name: str
    min_apy_threshold: int  # bps, trigger rebalance below this
    max_allocation_pct: int  # max % of total funds


@dataclass
class RiskConfig:
    """Risk management parameters."""

    max_single_rebalance_pct: int = 30
    min_rebalance_interval_sec: int = 300
    max_slippage_bps: int = 100
    min_gas_reserve: float = 5.0  # CSPR
    volatility_threshold: int = 200  # bps


@dataclass
class X402Config:
    """x402 data source configuration."""

    payment_address: str = ""
    max_payment_per_request: int = 10000  # motes
    data_sources: dict = field(default_factory=lambda: {
        "us_treasury_10y": {
            "url": "http://localhost:8000/api/us_treasury_10y",
            "expected_cost": 500,
        },
        "t_bill_3m": {
            "url": "http://localhost:8000/api/t_bill_3m",
            "expected_cost": 300,
        },
    })


@dataclass
class AgentConfig:
    """Top-level agent configuration."""

    # Casper network
    network: str = "testnet"
    node_url: str = "https://rpc.testnet.casper.casperlabs.io"
    mcp_server_url: str = "http://localhost:3001"

    # Agent key
    secret_key_path: str = os.getenv("AGENT_SECRET_KEY", "./keys/agent.pem")

    # Contract hashes (filled after deploy)
    yield_pool_hash: str = os.getenv("YIELD_POOL_HASH", "")
    oracle_hash: str = os.getenv("ORACLE_HASH", "")
    registry_hash: str = os.getenv("REGISTRY_HASH", "")

    # Runtime
    poll_interval_sec: int = int(os.getenv("POLL_INTERVAL_SEC", "60"))
    llm_model: str = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")

    # Pools
    pools: list = field(default_factory=lambda: [
        PoolConfig(pool_id=0, name="Stable Pool", min_apy_threshold=300, max_allocation_pct=50),
        PoolConfig(pool_id=1, name="Growth Pool", min_apy_threshold=500, max_allocation_pct=40),
        PoolConfig(pool_id=2, name="High Yield Pool", min_apy_threshold=800, max_allocation_pct=30),
    ])

    risk: RiskConfig = field(default_factory=RiskConfig)
    x402: X402Config = field(default_factory=X402Config)
