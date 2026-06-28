"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444"];

interface PoolData {
  name: string;
  apy: number;
  tvl: number;
  allocation: number;
}

interface PoolChartProps {
  pools: PoolData[];
}

export function PoolChart({ pools }: PoolChartProps) {
  const data = pools.map((p) => ({
    name: p.name,
    apy: p.apy / 100,
    tvl: p.tvl / 1e9,
    allocation: p.allocation,
  }));

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis
            yAxisId="left"
            orientation="left"
            label={{ value: "APY %", angle: -90, position: "insideLeft" }}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            label={{
              value: "TVL (CSPR)",
              angle: 90,
              position: "insideRight",
            }}
          />
          <Tooltip />
          <Bar
            yAxisId="left"
            dataKey="apy"
            name="APY %"
            radius={[4, 4, 0, 0]}
          >
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Bar>
          <Bar
            yAxisId="right"
            dataKey="tvl"
            name="TVL (CSPR)"
            fill="#6366f1"
            opacity={0.3}
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
