"""Data models for the YieldAgent."""

from dataclasses import dataclass


@dataclass
class PoolState:
    """State of a single yield pool."""

    pool_id: int
    name: str
    total_deposited: int  # motes
    apy_basis_points: int  # e.g. 500 = 5%
    allocation_pct: int  # 0-100


@dataclass
class OracleData:
    """A single oracle data point."""

    data_type: str  # e.g. "us_treasury_10y"
    value: int  # basis points
    source: str
    confidence: int  # 0-100
    age_seconds: int


@dataclass
class MarketSnapshot:
    """Aggregated market state for decision-making."""

    timestamp: int
    cspr_price: float  # USD
    volatility_bps: int  # basis points


@dataclass
class AgentState:
    """On-chain agent profile."""

    address: str
    balance: int  # motes
    reputation: int  # 0-10000
    total_rebalances: int
    total_yield_generated: int


@dataclass
class FetchedData:
    """Raw data fetched via x402."""

    data_type: str
    value: int
    source: str
    confidence: int
    cost_paid: int  # motes
    timestamp: int
