"use client";

import { useEffect, useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ArrowUpRight,
  ArrowDownRight,
  Bot,
  Database,
  TrendingUp,
} from "lucide-react";
import { PoolChart } from "@/components/PoolChart";
import { AgentLog } from "@/components/AgentLog";
import { OracleFeed } from "@/components/OracleFeed";

interface DashboardData {
  pools: Array<{
    id: number;
    name: string;
    apy: number;
    tvl: number;
    allocation: number;
  }>;
  agent: {
    status: string;
    totalRebalances: number;
    winRate: number;
    reputation: number;
    lastAction: string;
    lastActionTime: string;
  };
  oracle: Array<{
    type: string;
    value: number;
    confidence: number;
    source: string;
    age: number;
  }>;
  logs: Array<{
    type: string;
    timestamp: number;
    message: string;
  }>;
}

// Mock data for demo
const MOCK_DATA: DashboardData = {
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
    { type: "rebalance", timestamp: Date.now() / 1000 - 120, message: "REBALANCE P0->P1 15000 CSPR, confidence: 85%" },
    { type: "oracle", timestamp: Date.now() / 1000 - 180, message: "Oracle: t_bill_3m = 5.20%" },
    { type: "hold", timestamp: Date.now() / 1000 - 240, message: "HOLD: APY spread < 1%" },
    { type: "oracle", timestamp: Date.now() / 1000 - 300, message: "Oracle: us_treasury_10y = 4.25%" },
    { type: "rebalance", timestamp: Date.now() / 1000 - 600, message: "REBALANCE P1->P2 8000 CSPR, confidence: 72%" },
  ],
};

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch("/api/dashboard");
      if (res.ok) {
        setData(await res.json());
      } else {
        setData(MOCK_DATA);
      }
    } catch {
      setData(MOCK_DATA);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  if (!data) {
    return <div className="p-6">Loading...</div>;
  }

  const bestApy = Math.max(...data.pools.map((p) => p.apy / 100));
  const totalTvl = data.pools.reduce((s, p) => s + p.tvl, 0) / 1e9;

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">YieldAgent Dashboard</h1>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KPICard
          title="Best APY"
          value={`${bestApy.toFixed(2)}%`}
          icon={<TrendingUp className="h-4 w-4" />}
          trend="up"
        />
        <KPICard
          title="Total TVL"
          value={`${totalTvl.toFixed(0)} CSPR`}
          icon={<Database className="h-4 w-4" />}
        />
        <KPICard
          title="Win Rate"
          value={`${(data.agent.winRate / 100).toFixed(1)}%`}
          icon={<Bot className="h-4 w-4" />}
          trend={data.agent.winRate > 6000 ? "up" : "down"}
        />
        <KPICard
          title="Rebalances"
          value={data.agent.totalRebalances.toString()}
          icon={<ArrowUpRight className="h-4 w-4" />}
        />
      </div>

      {/* Charts + Log */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Pool Allocation & APY</CardTitle>
          </CardHeader>
          <CardContent>
            <PoolChart pools={data.pools} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Agent Decision Log</CardTitle>
          </CardHeader>
          <CardContent>
            <AgentLog messages={data.logs} />
          </CardContent>
        </Card>
      </div>

      {/* Oracle Data */}
      <Card>
        <CardHeader>
          <CardTitle>RWA Oracle Feed</CardTitle>
        </CardHeader>
        <CardContent>
          <OracleFeed data={data.oracle} />
        </CardContent>
      </Card>
    </div>
  );
}

function KPICard({
  title,
  value,
  icon,
  trend,
}: {
  title: string;
  value: string;
  icon: React.ReactNode;
  trend?: "up" | "down";
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">{title}</span>
          {icon}
        </div>
        <div className="text-2xl font-bold mt-1">{value}</div>
        {trend && (
          <div
            className={`flex items-center text-sm ${
              trend === "up" ? "text-green-500" : "text-red-500"
            }`}
          >
            {trend === "up" ? (
              <ArrowUpRight className="h-3 w-3" />
            ) : (
              <ArrowDownRight className="h-3 w-3" />
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
