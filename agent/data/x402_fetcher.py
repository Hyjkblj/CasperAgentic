"""x402 protocol data fetcher for off-chain RWA data."""

import asyncio
import base64
import json
import time
from typing import Optional

import httpx

from config import X402Config
from data.models import FetchedData


class X402Fetcher:
    """Fetches off-chain data using the x402 payment protocol.

    Flow:
    1. Send GET request to data source
    2. Receive 402 Payment Required with price info
    3. Generate cryptographic payment proof
    4. Retry request with payment proof in X-Payment header
    5. Receive data

    Includes caching (5 min TTL) and budget tracking.
    """

    def __init__(self, config: X402Config, wallet_key: str = ""):
        self.config = config
        self.wallet_key = wallet_key
        self.http = httpx.AsyncClient(timeout=15.0)
        self.cache: dict[str, FetchedData] = {}
        self.cache_ttl = 300  # 5 minutes
        self.total_spent = 0
        self.budget_limit = 1_000_000  # 1 CSPR in motes

    async def fetch(self, data_type: str) -> Optional[FetchedData]:
        """Fetch a single data type, using cache if fresh."""
        # Check cache
        if data_type in self.cache:
            cached = self.cache[data_type]
            if cached.timestamp + self.cache_ttl > int(time.time()):
                return cached

        source = self.config.data_sources.get(data_type)
        if not source:
            raise ValueError(f"Unknown data type: {data_type}")

        # Check budget
        if self.total_spent + source["expected_cost"] > self.budget_limit:
            raise RuntimeError(
                f"Budget exhausted: {self.total_spent}/{self.budget_limit}"
            )

        url = source["url"]

        # Initial request
        response = await self.http.get(url)

        # Handle 402
        if response.status_code == 402:
            payment_info = response.json()
            amount = int(payment_info.get("amount", 0))

            if amount > self.config.max_payment_per_request:
                raise RuntimeError(
                    f"Cost {amount} > max {self.config.max_payment_per_request}"
                )

            # Generate payment proof
            proof = self._create_payment_proof(payment_info)

            # Retry with payment
            response = await self.http.get(
                url,
                headers={"X-Payment": proof, "X-Payment-Type": "x402"},
            )
            self.total_spent += amount

        if response.status_code != 200:
            raise RuntimeError(f"Fetch {data_type} failed: {response.status_code}")

        data = response.json()
        result = FetchedData(
            data_type=data_type,
            value=int(data["value"]),
            source=data.get("source", url),
            confidence=int(data.get("confidence", 80)),
            cost_paid=source["expected_cost"],
            timestamp=int(data.get("timestamp", time.time())),
        )

        self.cache[data_type] = result
        return result

    async def fetch_all(self) -> dict[str, FetchedData]:
        """Fetch all configured data sources."""
        results = {}
        for data_type in self.config.data_sources:
            try:
                data = await self.fetch(data_type)
                if data:
                    results[data_type] = data
            except Exception as e:
                print(f"[x402] Warning: Failed to fetch {data_type}: {e}")
        return results

    def _create_payment_proof(self, payment_info: dict) -> str:
        """Generate x402 payment proof (base64 encoded)."""
        payload = {
            "x402Version": 1,
            "scheme": "exact",
            "network": "casper-testnet",
            "amount": str(payment_info.get("amount", 0)),
            "payto": payment_info.get("payTo", ""),
            "resource": payment_info.get("resource", ""),
            "timestamp": int(time.time()),
        }
        # In production: sign with Casper SDK
        # signature = casper_sdk.sign(self.wallet_key, json.dumps(payload))
        # payload["signature"] = signature
        return base64.b64encode(json.dumps(payload).encode()).decode()

    async def close(self):
        """Close the HTTP client."""
        await self.http.aclose()
