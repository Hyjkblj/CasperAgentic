"""MCP Server client for Casper blockchain interaction."""

import ipaddress
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import urlparse

import httpx

from config import AgentConfig


# Private/internal networks that should never be reached via MCP_SERVER_URL
_PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def _validate_mcp_url(url: str) -> str:
    """Validate that the MCP server URL is not a private/internal address."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"MCP_SERVER_URL must use http/https scheme, got: {parsed.scheme}")
    hostname = parsed.hostname
    if not hostname:
        raise ValueError(f"MCP_SERVER_URL has no hostname: {url}")
    try:
        resolved = ipaddress.ip_address(hostname)
    except ValueError:
        # It's a domain name — resolve it and check the result
        import socket
        try:
            addr_infos = socket.getaddrinfo(hostname, parsed.port or 80)
        except socket.gaierror:
            raise ValueError(f"Cannot resolve MCP_SERVER_URL hostname: {hostname}")
        for family, _type, _proto, _canon, sockaddr in addr_infos:
            resolved = ipaddress.ip_address(sockaddr[0])
            for net in _PRIVATE_NETWORKS:
                if resolved in net:
                    raise ValueError(
                        f"MCP_SERVER_URL resolves to private address {resolved}, "
                        f"which is blocked to prevent SSRF"
                    )
        return url
    for net in _PRIVATE_NETWORKS:
        if resolved in net:
            raise ValueError(
                f"MCP_SERVER_URL points to private address {resolved}, "
                f"which is blocked to prevent SSRF"
            )
    return url


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
        self.base_url = _validate_mcp_url(config.mcp_server_url)
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
