"""WebSocket server for real-time agent log push.

Run alongside the agent to broadcast decision logs to connected frontends.
"""

import asyncio
import json
import time
from typing import Set

import websockets
from websockets.server import WebSocketServerProtocol


class LogBroadcaster:
    """Manages WebSocket connections and broadcasts log messages."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self.server = None

    async def handler(self, websocket: WebSocketServerProtocol):
        """Handle a new WebSocket connection."""
        self.clients.add(websocket)
        print(f"[WS] Client connected ({len(self.clients)} total)")
        try:
            async for _ in websocket:
                # Clients don't send messages; just keep connection alive
                pass
        finally:
            self.clients.discard(websocket)
            print(f"[WS] Client disconnected ({len(self.clients)} total)")

    async def broadcast(self, message: dict):
        """Send a message to all connected clients."""
        if not self.clients:
            return

        payload = json.dumps(message)
        disconnected = set()

        for client in self.clients:
            try:
                await client.send(payload)
            except websockets.ConnectionClosed:
                disconnected.add(client)

        self.clients -= disconnected

    def log_cycle_start(self, cycle: int):
        """Log a cycle start event."""
        return self.broadcast({
            "type": "cycle_start",
            "timestamp": time.time(),
            "message": f"─── Cycle {cycle} ───",
            "data": {"cycle": cycle},
        })

    def log_decision(self, action: str, confidence: int, reasoning: str, details: dict = None):
        """Log a decision event."""
        return self.broadcast({
            "type": "decision",
            "timestamp": time.time(),
            "message": f"Decision: {action} | Confidence: {confidence}% | {reasoning}",
            "data": {
                "action": action,
                "confidence": confidence,
                "reasoning": reasoning,
                **(details or {}),
            },
        })

    def log_oracle(self, data_type: str, value: int, source: str):
        """Log an oracle data submission."""
        return self.broadcast({
            "type": "oracle",
            "timestamp": time.time(),
            "message": f"Oracle: {data_type} = {value/100:.2f}% ({source})",
            "data": {"data_type": data_type, "value": value, "source": source},
        })

    def log_rebalance(self, from_pool: int, to_pool: int, amount: int):
        """Log a rebalance execution."""
        return self.broadcast({
            "type": "rebalance",
            "timestamp": time.time(),
            "message": f"REBALANCE P{from_pool}->P{to_pool} {amount/1e9:.0f} CSPR",
            "data": {"from_pool": from_pool, "to_pool": to_pool, "amount": amount},
        })

    def log_error(self, error: str):
        """Log an error event."""
        return self.broadcast({
            "type": "error",
            "timestamp": time.time(),
            "message": f"ERROR: {error}",
            "data": {"error": error},
        })

    async def start(self):
        """Start the WebSocket server."""
        self.server = await websockets.serve(self.handler, self.host, self.port)
        print(f"[WS] Server running on ws://{self.host}:{self.port}")

    async def stop(self):
        """Stop the WebSocket server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()


# Singleton instance
broadcaster = LogBroadcaster()


async def main():
    """Run standalone for testing."""
    await broadcaster.start()
    print("[WS] Waiting for connections...")

    # Simulate some log messages
    cycle = 0
    while True:
        await asyncio.sleep(5)
        cycle += 1
        await broadcaster.log_cycle_start(cycle)
        await asyncio.sleep(1)
        await broadcaster.log_decision(
            "hold" if cycle % 2 == 0 else "rebalance",
            85,
            "APY spread too narrow" if cycle % 2 == 0 else "Pool 1 APY superior",
        )


if __name__ == "__main__":
    asyncio.run(main())
