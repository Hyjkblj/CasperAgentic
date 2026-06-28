"""MCP Server client for Casper blockchain interaction."""

from dataclasses import dataclass
from typing import Any, Optional

import httpx

from config import AgentConfig


@dataclass
class McpResponse:
    """Response from an MCP tool call."""

    success: bool
    data: Any
    error: Optional[str] = None


class McpClient:
    """Client for interacting with Casper MCP Server.

    Provides standardized JSON-RPC calls for querying chain state
    and submitting transactions.
    """

    def __init__(self, config: AgentConfig):
        self.base_url = config.mcp_server_url
        self.config = config
        self.http = httpx.AsyncClient(timeout=30.0)

    async def call_tool(self, tool_name: str, arguments: dict) -> McpResponse:
        """Call an MCP tool via JSON-RPC."""
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
            "id": 1,
        }
        try:
            resp = await self.http.post(
                f"{self.base_url}/mcp",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            result = resp.json()
            if "error" in result:
                return McpResponse(False, None, result["error"]["message"])
            return McpResponse(True, result.get("result"))
        except Exception as e:
            return McpResponse(False, None, str(e))

    # ─── Queries ───

    async def get_pool_state(self, contract_hash: str, pool_id: int) -> dict:
        """Query a single pool's state."""
        resp = await self.call_tool("query_contract_state", {
            "contract_hash": contract_hash,
            "entry_point": "get_pool",
            "args": {"pool_id": pool_id},
        })
        if not resp.success:
            raise RuntimeError(f"get_pool failed: {resp.error}")
        return resp.data

    async def get_all_pools(self, contract_hash: str) -> list[dict]:
        """Query all pool APYs."""
        resp = await self.call_tool("query_contract_state", {
            "contract_hash": contract_hash,
            "entry_point": "get_all_pool_apys",
            "args": {},
        })
        if not resp.success:
            raise RuntimeError(f"get_all_pool_apys failed: {resp.error}")
        return resp.data

    async def get_account_balance(self, address: str) -> int:
        """Query account balance in motes."""
        resp = await self.call_tool("get_account_balance", {"address": address})
        if not resp.success:
            raise RuntimeError(f"get_account_balance failed: {resp.error}")
        return int(resp.data)

    async def get_oracle_data(self, contract_hash: str, data_type: str) -> Optional[dict]:
        """Query valid oracle data."""
        resp = await self.call_tool("query_contract_state", {
            "contract_hash": contract_hash,
            "entry_point": "get_valid_data",
            "args": {"data_type": data_type},
        })
        return resp.data if resp.success else None

    # ─── Transactions ───

    async def submit_rebalance(
        self,
        contract_hash: str,
        from_pool: int,
        to_pool: int,
        amount: int,
        key_path: str,
    ) -> McpResponse:
        """Submit a rebalance transaction."""
        return await self.call_tool("deploy_contract_call", {
            "contract_hash": contract_hash,
            "entry_point": "rebalance",
            "args": {
                "from_pool": from_pool,
                "to_pool": to_pool,
                "amount": amount,
            },
            "payment_amount": 10_000_000,
            "secret_key_path": key_path,
        })

    async def submit_oracle_data(
        self,
        contract_hash: str,
        data_type: str,
        value: int,
        source: str,
        confidence: int,
        key_path: str,
    ) -> McpResponse:
        """Submit oracle data to chain."""
        return await self.call_tool("deploy_contract_call", {
            "contract_hash": contract_hash,
            "entry_point": "submit_data",
            "args": {
                "data_type": data_type,
                "value": value,
                "source": source,
                "confidence": confidence,
            },
            "payment_amount": 5_000_000,
            "secret_key_path": key_path,
        })

    async def register_agent(
        self,
        contract_hash: str,
        name: str,
        strategy: str,
        key_path: str,
    ) -> McpResponse:
        """Register this agent on-chain."""
        return await self.call_tool("deploy_contract_call", {
            "contract_hash": contract_hash,
            "entry_point": "register_agent",
            "args": {"name": name, "strategy": strategy},
            "payment_amount": 5_000_000,
            "secret_key_path": key_path,
        })

    async def record_operation(
        self,
        contract_hash: str,
        from_pool: int,
        to_pool: int,
        amount: int,
        from_apy: int,
        to_apy: int,
        key_path: str,
    ) -> McpResponse:
        """Record an operation in AgentRegistry."""
        return await self.call_tool("deploy_contract_call", {
            "contract_hash": contract_hash,
            "entry_point": "record_operation",
            "args": {
                "from_pool": from_pool,
                "to_pool": to_pool,
                "amount": amount,
                "from_apy": from_apy,
                "to_apy": to_apy,
            },
            "payment_amount": 5_000_000,
            "secret_key_path": key_path,
        })

    async def close(self):
        """Close the HTTP client."""
        await self.http.aclose()
