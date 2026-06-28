# 前端设计

## 技术选型

| 维度 | 选择 | 理由 |
|------|------|------|
| 框架 | Next.js 14 (App Router) | SSR + API Routes 一体，部署简单 |
| 样式 | TailwindCSS + shadcn/ui | 快速开发，组件质量高，可定制 |
| 图表 | Recharts | React 原生，轻量，文档完善 |
| 状态 | Zustand | 简单轻量，适合中等复杂度 |
| 实时 | WebSocket | 代理决策日志实时推送 |
| 表格 | TanStack Table | 排序、筛选、分页一体化 |

## 页面结构

```
app/
├── layout.tsx                  # 全局布局：侧边栏 + 顶栏
├── page.tsx                    # 首页：概览仪表盘
├── pools/
│   └── page.tsx                # 收益池详情页
├── agent/
│   ├── page.tsx                # 代理状态 + 决策日志
│   └── [address]/
│       └── page.tsx            # 单个代理详情
├── oracle/
│   └── page.tsx                # Oracle 数据流
├── leaderboard/
│   └── page.tsx                # 代理排行榜
└── api/
    ├── dashboard/route.ts      # 仪表盘聚合数据
    ├── pools/route.ts          # 池子数据
    ├── agent/route.ts          # 代理状态
    └── oracle/route.ts         # Oracle 数据
```

## 页面设计

### 1. 首页 — 概览仪表盘

**目标**：一屏展示系统全貌，让用户 3 秒内理解当前状态。

```
┌─────────────────────────────────────────────────────────────┐
│  YieldAgent Dashboard                          [Connect]    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Best APY  │  │ Total TVL│  │ Win Rate │  │Rebalances│  │
│  │   9.00%   │  │ 100,000  │  │  75.0%   │  │    42    │  │
│  │   ↑ 0.5%  │  │  CSPR    │  │  ↑ 2.1%  │  │  today:3 │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                             │
│  ┌─────────────────────────────┐  ┌──────────────────────┐ │
│  │  Pool Allocation & APY      │  │  Agent Decision Log  │ │
│  │                             │  │                      │ │
│  │  ████████░░░░  Pool 0  3%   │  │  10:30 REBALANCE    │ │
│  │  █████░░░░░░░  Pool 1  6%   │  │  P0→P1 15000 CSPR   │ │
│  │  ███░░░░░░░░░  Pool 2  9%   │  │                      │ │
│  │                             │  │  10:29 Oracle        │ │
│  │  [Bar Chart]                │  │  t_bill_3m: 5.25%    │ │
│  │                             │  │                      │ │
│  │                             │  │  10:28 HOLD          │ │
│  │                             │  │  APY spread < 1%     │ │
│  └─────────────────────────────┘  └──────────────────────┘ │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  RWA Oracle Feed                                        ││
│  │                                                         ││
│  │  us_treasury_10y  │  4.25%  │  95% conf  │  45s ago    ││
│  │  t_bill_3m        │  5.20%  │  88% conf  │  120s ago   ││
│  │  t_bill_6m        │  5.05%  │  91% conf  │  200s ago   ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 2. 收益池详情页

```
┌─────────────────────────────────────────────────────────────┐
│  Yield Pools                                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Pool Performance (7d)                                  ││
│  │                                                         ││
│  │  APY%                                                   ││
│  │  10│                    ╱───── Pool 2 (High Yield)      ││
│  │   8│              ╱────╱                                ││
│  │   6│        ╱────╱──────── Pool 1 (Growth)              ││
│  │   4│  ╱────╱                                            ││
│  │   2│──────────────────── Pool 0 (Stable)                ││
│  │   0└──────────────────────────────▶ time                ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐              │
│  │ Pool 0    │  │ Pool 1    │  │ Pool 2    │              │
│  │ Stable    │  │ Growth    │  │ High Yield│              │
│  │           │  │           │  │           │              │
│  │ APY: 3%   │  │ APY: 6%   │  │ APY: 9%   │              │
│  │ TVL: 50K  │  │ TVL: 30K  │  │ TVL: 20K  │              │
│  │ Alloc: 50%│  │ Alloc: 30%│  │ Alloc: 20%│              │
│  │           │  │           │  │           │              │
│  │ [Deposit] │  │ [Deposit] │  │ [Deposit] │              │
│  │ [Withdraw]│  │ [Withdraw]│  │ [Withdraw]│              │
│  └───────────┘  └───────────┘  └───────────┘              │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Rebalance History                                      ││
│  │                                                         ││
│  │  Time    │ From → To │ Amount   │ APY Gain │ Tx Hash   ││
│  │  10:30   │ P0 → P1   │ 15,000   │ +3.00%   │ 0xabc... ││
│  │  09:15   │ P1 → P2   │ 8,000    │ +3.00%   │ 0xdef... ││
│  │  08:00   │ P2 → P0   │ 12,000   │ -6.00%   │ 0xghi... ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 3. 代理详情页

```
┌─────────────────────────────────────────────────────────────┐
│  Agent: YieldOptimizer-v1                      [Follow]     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │Reputation│  │Win Rate  │  │Total Ops │  │Yield Gen │  │
│  │  6,200   │  │  75.0%   │  │    80    │  │ 1,250 CSPR│ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Strategy                                               ││
│  │  "Autonomous yield rebalancing across RWA-backed pools. ││
│  │   Optimizes for risk-adjusted returns using real-time   ││
│  │   treasury yield data."                                 ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Decision History                                       ││
│  │                                                         ││
│  │  ┌─────────────────────────────────────────────────┐   ││
│  │  │ #42  10:30  REBALANCE  P0→P1  15000  ✓ Profit  │   ││
│  │  │       Reasoning: Pool 1 APY superior, oracle     │   ││
│  │  │       data supports upward rate trend.           │   ││
│  │  │       Confidence: 85%  │  Risk: 15/100          │   ││
│  │  └─────────────────────────────────────────────────┘   ││
│  │  ┌─────────────────────────────────────────────────┐   ││
│  │  │ #41  10:29  HOLD                                │   ││
│  │  │       Reasoning: APY spread 80bps < 100bps      │   ││
│  │  │       threshold. No rebalance warranted.        │   ││
│  │  │       Confidence: 90%  │  Risk: 0/100           │   ││
│  │  └─────────────────────────────────────────────────┘   ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 4. Oracle 数据页

```
┌─────────────────────────────────────────────────────────────┐
│  RWA Oracle Feed                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Yield Curve                                            ││
│  │                                                         ││
│  │  Yield%                                                 ││
│  │   6│        ╱────── 3m T-Bill                           ││
│  │   5│  ╱────╱                                            ││
│  │   4│──────╱────────── 10y Treasury                      ││
│  │   3│                                                    ││
│  │   2│                                                    ││
│  │   0└────────────────────────────────▶ maturity          ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Source Reputation                                      ││
│  │                                                         ││
│  │  Source           │ Submissions │ Accuracy │ Score      ││
│  │  federal_reserve  │    120      │  96.7%   │  9,670     ││
│  │  treasury_api     │     85      │  92.9%   │  9,294     ││
│  │  mock_source      │     50      │  88.0%   │  8,800     ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## 核心组件

### 数据获取 Hook

```typescript
// hooks/useDashboard.ts

import { useEffect, useState, useCallback } from "react"

interface DashboardData {
  pools: PoolData[]
  agent: AgentData
  oracle: OracleData[]
}

export function useDashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch("/api/dashboard")
      if (!res.ok) throw new Error("Failed to fetch")
      setData(await res.json())
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000) // 30 秒轮询
    return () => clearInterval(interval)
  }, [fetchData])

  return { data, loading, error, refetch: fetchData }
}
```

### WebSocket Hook

```typescript
// hooks/useAgentSocket.ts

import { useEffect, useRef, useState, useCallback } from "react"

interface AgentMessage {
  type: "cycle_start" | "decision" | "cycle_complete" | "error"
  timestamp: number
  message: string
  data?: any
}

export function useAgentSocket() {
  const [messages, setMessages] = useState<AgentMessage[]>([])
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const ws = new WebSocket(process.env.NEXT_PUBLIC_AGENT_WS!)
    wsRef.current = ws

    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data) as AgentMessage
      setMessages((prev) => [...prev.slice(-100), msg]) // 保留最近 100 条
    }

    return () => ws.close()
  }, [])

  const clearMessages = useCallback(() => setMessages([]), [])

  return { messages, connected, clearMessages }
}
```

### 池子分配图表

```tsx
// components/PoolChart.tsx

"use client"

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell,
} from "recharts"

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444"]

interface PoolChartProps {
  pools: Array<{
    name: string
    apy: number
    tvl: number
    allocation: number
  }>
}

export function PoolChart({ pools }: PoolChartProps) {
  const data = pools.map((p) => ({
    name: p.name,
    apy: p.apy / 100,
    tvl: p.tvl / 1e9,
    allocation: p.allocation,
  }))

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
            label={{ value: "TVL (CSPR)", angle: 90, position: "insideRight" }}
          />
          <Tooltip />
          <Bar yAxisId="left" dataKey="apy" name="APY %" radius={[4, 4, 0, 0]}>
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
  )
}
```

### 决策日志组件

```tsx
// components/AgentLog.tsx

"use client"

import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import type { AgentMessage } from "@/hooks/useAgentSocket"

interface AgentLogProps {
  messages: AgentMessage[]
}

export function AgentLog({ messages }: AgentLogProps) {
  return (
    <ScrollArea className="h-80">
      <div className="space-y-2">
        {messages.map((msg, i) => (
          <LogEntry key={i} message={msg} />
        ))}
        {messages.length === 0 && (
          <p className="text-muted-foreground text-sm">
            Waiting for agent activity...
          </p>
        )}
      </div>
    </ScrollArea>
  )
}

function LogEntry({ message }: { message: AgentMessage }) {
  const getBadge = () => {
    switch (message.type) {
      case "decision":
        if (message.data?.action === "rebalance")
          return <Badge variant="default">REBALANCE</Badge>
        return <Badge variant="secondary">HOLD</Badge>
      case "cycle_start":
        return <Badge variant="outline">CYCLE</Badge>
      case "cycle_complete":
        return <Badge variant="outline">DONE</Badge>
      case "error":
        return <Badge variant="destructive">ERROR</Badge>
      default:
        return null
    }
  }

  const time = new Date(message.timestamp * 1000).toLocaleTimeString()

  return (
    <div className="flex items-start gap-2 text-sm">
      <span className="text-muted-foreground text-xs w-14 shrink-0">
        {time}
      </span>
      {getBadge()}
      <span className="text-muted-foreground font-mono text-xs">
        {message.message}
      </span>
    </div>
  )
}
```

### Oracle 数据表格

```tsx
// components/OracleFeed.tsx

"use client"

import {
  Table, TableBody, TableCell, TableHead,
  TableHeader, TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

interface OracleFeedProps {
  data: Array<{
    type: string
    value: number
    confidence: number
    age: number
    source: string
  }>
}

export function OracleFeed({ data }: OracleFeedProps) {
  const formatAge = (seconds: number) => {
    if (seconds < 60) return `${seconds}s ago`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
    return `${Math.floor(seconds / 3600)}h ago`
  }

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 90) return <Badge variant="default">High</Badge>
    if (confidence >= 70) return <Badge variant="secondary">Medium</Badge>
    return <Badge variant="destructive">Low</Badge>
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Data Type</TableHead>
          <TableHead>Value</TableHead>
          <TableHead>Confidence</TableHead>
          <TableHead>Source</TableHead>
          <TableHead>Age</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((row) => (
          <TableRow key={row.type}>
            <TableCell className="font-mono">{row.type}</TableCell>
            <TableCell className="font-bold">
              {(row.value / 100).toFixed(2)}%
            </TableCell>
            <TableCell>{getConfidenceBadge(row.confidence)}</TableCell>
            <TableCell className="text-muted-foreground">{row.source}</TableCell>
            <TableCell className="text-muted-foreground">
              {formatAge(row.age)}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
```

## API Routes

```typescript
// app/api/dashboard/route.ts

import { NextResponse } from "next/server"

export async function GET() {
  const [pools, agent, oracle] = await Promise.all([
    fetchPools(),
    fetchAgent(),
    fetchOracle(),
  ])

  return NextResponse.json({ pools, agent, oracle })
}

async function fetchPools() {
  // 通过 CSPR.cloud 查询链上数据
  const res = await fetch(
    `${process.env.CSPR_CLOUD_API}/contracts/${process.env.YIELD_POOL_HASH}/state`,
    { headers: { Authorization: `Bearer ${process.env.CSPR_API_KEY}` } }
  )
  const data = await res.json()
  return data.pools.map((p: any) => ({
    id: p.pool_id,
    name: p.name,
    apy: p.apy_basis_points,
    tvl: p.total_deposited,
    allocation: p.allocation_pct,
  }))
}

async function fetchAgent() {
  const res = await fetch(
    `${process.env.CSPR_CLOUD_API}/contracts/${process.env.REGISTRY_HASH}/state`,
    { headers: { Authorization: `Bearer ${process.env.CSPR_API_KEY}` } }
  )
  return res.json()
}

async function fetchOracle() {
  const res = await fetch(
    `${process.env.CSPR_CLOUD_API}/contracts/${process.env.ORACLE_HASH}/state`,
    { headers: { Authorization: `Bearer ${process.env.CSPR_API_KEY}` } }
  )
  return res.json()
}
```

## 环境变量

```env
# 前端环境变量

NEXT_PUBLIC_AGENT_WS=ws://localhost:8080/ws
NEXT_PUBLIC_CSPR_EXPLORER=https://testnet.cspr.live
NEXT_PUBLIC_NETWORK=casper-testnet

# API Routes (服务端)
CSPR_CLOUD_API=https://api.cspr.cloud
CSPR_API_KEY=
YIELD_POOL_HASH=
ORACLE_HASH=
REGISTRY_HASH=
```
