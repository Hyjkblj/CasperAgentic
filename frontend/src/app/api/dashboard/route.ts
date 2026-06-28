import { NextResponse } from "next/server";

// Mock data — in production, fetch from CSPR.cloud or MCP Server
const MOCK_DATA = {
  pools: [
    { id: 0, name: "Stable Pool", apy: 300, tvl: 50_000_000_000_000, allocation: 50 },
    { id: 1, name: "Growth Pool", apy: 600, tvl: 30_000_000_000_000, allocation: 30 },
    { id: 2, name: "High Yield Pool", apy: 900, tvl: 20_000_000_000_000, allocation: 20 },
  ],
  agent: {
    status: "active",
    totalRebalances: 42,
    winRate: 7500,
    reputation: 6200,
    lastAction: "REBALANCE Pool 0 -> Pool 1",
    lastActionTime: "2 minutes ago",
  },
  oracle: [
    { type: "us_treasury_10y", value: 425, confidence: 95, source: "federal_res", age: 45 },
    { type: "t_bill_3m", value: 520, confidence: 88, source: "treasury_api", age: 120 },
    { type: "t_bill_6m", value: 505, confidence: 91, source: "treasury_api", age: 200 },
  ],
  logs: [
    { type: "rebalance", timestamp: Date.now() / 1000 - 120, message: "REBALANCE P0->P1 15000 CSPR" },
    { type: "oracle", timestamp: Date.now() / 1000 - 180, message: "Oracle: t_bill_3m = 5.20%" },
    { type: "hold", timestamp: Date.now() / 1000 - 240, message: "HOLD: APY spread < 1%" },
  ],
};

export async function GET() {
  // In production: fetch from CSPR.cloud API
  // const pools = await fetch(`${process.env.CSPR_CLOUD_API}/contracts/${YIELD_POOL_HASH}/state`);
  // const agent = await fetch(`${process.env.CSPR_CLOUD_API}/contracts/${REGISTRY_HASH}/state`);
  // const oracle = await fetch(`${process.env.CSPR_CLOUD_API}/contracts/${ORACLE_HASH}/state`);

  return NextResponse.json(MOCK_DATA);
}
