"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  ArrowUpRight,
  ArrowDownRight,
  Bot,
  Target,
  TrendingUp,
  Activity,
} from "lucide-react";

interface AgentProfile {
  name: string;
  strategy: string;
  reputation: number;
  winRate: number;
  totalRebalances: number;
  totalYield: number;
  status: string;
  createdAt: string;
}

interface DecisionRecord {
  id: number;
  timestamp: string;
  action: string;
  fromPool: number | null;
  toPool: number | null;
  amount: number | null;
  confidence: number;
  reasoning: string;
  outcome: string;
  riskScore: number;
}

// Mock data
const MOCK_AGENT: AgentProfile = {
  name: "YieldOptimizer-v1",
  strategy:
    "Autonomous yield rebalancing across RWA-backed pools. Optimizes for risk-adjusted returns using real-time treasury yield data.",
  reputation: 6200,
  winRate: 7500,
  totalRebalances: 80,
  totalYield: 1250_000_000_000,
  status: "active",
  createdAt: "2026-06-20",
};

const MOCK_DECISIONS: DecisionRecord[] = [
  {
    id: 42,
    timestamp: "10:30:00",
    action: "rebalance",
    fromPool: 0,
    toPool: 1,
    amount: 15_000_000_000_000,
    confidence: 85,
    reasoning:
      "Pool 1 APY (6%) significantly higher than Pool 0 (3%). Oracle data shows stable treasury yields, supporting growth allocation.",
    outcome: "profitable",
    riskScore: 15,
  },
  {
    id: 41,
    timestamp: "10:29:00",
    action: "hold",
    fromPool: null,
    toPool: null,
    amount: null,
    confidence: 90,
    reasoning:
      "APY spread 80bps < 100bps threshold. No rebalance warranted — transaction costs would exceed benefit.",
    outcome: "neutral",
    riskScore: 0,
  },
  {
    id: 40,
    timestamp: "10:15:00",
    action: "rebalance",
    fromPool: 1,
    toPool: 2,
    amount: 8_000_000_000_000,
    confidence: 72,
    reasoning:
      "High Yield Pool offers 9% APY. Risk assessment passed but volatility is elevated — smaller position size.",
    outcome: "profitable",
    riskScore: 25,
  },
  {
    id: 39,
    timestamp: "10:00:00",
    action: "hold",
    fromPool: null,
    toPool: null,
    amount: null,
    confidence: 80,
    reasoning:
      "Market volatility 6% exceeds 2% threshold. Holding stable positions until conditions improve.",
    outcome: "neutral",
    riskScore: 0,
  },
  {
    id: 38,
    timestamp: "09:45:00",
    action: "rebalance",
    fromPool: 2,
    toPool: 0,
    amount: 12_000_000_000_000,
    confidence: 78,
    reasoning:
      "De-risking: moving funds from High Yield to Stable Pool. Treasury data suggests rate stability.",
    outcome: "loss",
    riskScore: 20,
  },
];

export default function AgentPage() {
  const [agent] = useState<AgentProfile>(MOCK_AGENT);
  const [decisions] = useState<DecisionRecord[]>(MOCK_DECISIONS);

  const getOutcomeBadge = (outcome: string) => {
    switch (outcome) {
      case "profitable":
        return <Badge variant="default">Profitable</Badge>;
      case "loss":
        return <Badge variant="destructive">Loss</Badge>;
      default:
        return <Badge variant="secondary">Neutral</Badge>;
    }
  };

  const getActionBadge = (action: string) => {
    switch (action) {
      case "rebalance":
        return <Badge variant="default">REBALANCE</Badge>;
      case "hold":
        return <Badge variant="outline">HOLD</Badge>;
      default:
        return <Badge variant="secondary">{action.toUpperCase()}</Badge>;
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Agent: {agent.name}</h1>
        <Badge variant={agent.status === "active" ? "default" : "secondary"}>
          {agent.status}
        </Badge>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KPI
          title="Reputation"
          value={(agent.reputation / 100).toFixed(0) + "%"}
          icon={<Target className="h-4 w-4" />}
        />
        <KPI
          title="Win Rate"
          value={(agent.winRate / 100).toFixed(1) + "%"}
          icon={<TrendingUp className="h-4 w-4" />}
          trend={agent.winRate > 6000 ? "up" : "down"}
        />
        <KPI
          title="Total Rebalances"
          value={agent.totalRebalances.toString()}
          icon={<Activity className="h-4 w-4" />}
        />
        <KPI
          title="Yield Generated"
          value={`${(agent.totalYield / 1e9).toFixed(0)} CSPR`}
          icon={<Bot className="h-4 w-4" />}
        />
      </div>

      {/* Strategy */}
      <Card>
        <CardHeader>
          <CardTitle>Strategy</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">{agent.strategy}</p>
        </CardContent>
      </Card>

      {/* Decision History */}
      <Card>
        <CardHeader>
          <CardTitle>Decision History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {decisions.map((d) => (
              <div key={d.id} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground w-16">
                      #{d.id} {d.timestamp}
                    </span>
                    {getActionBadge(d.action)}
                    {getOutcomeBadge(d.outcome)}
                  </div>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <span>Confidence: {d.confidence}%</span>
                    <span>Risk: {d.riskScore}/100</span>
                  </div>
                </div>

                {d.action === "rebalance" && d.fromPool !== null && (
                  <div className="text-sm mb-2">
                    <span className="font-medium">
                      Pool {d.fromPool} → Pool {d.toPool}
                    </span>
                    <span className="text-muted-foreground ml-2">
                      {d.amount ? `${(d.amount / 1e9).toFixed(0)} CSPR` : ""}
                    </span>
                  </div>
                )}

                <p className="text-sm text-muted-foreground">{d.reasoning}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function KPI({
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
