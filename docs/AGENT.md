# AI 代理设计

## 代理架构

```
┌─────────────────────────────────────────────────────────┐
│                    代理进程 (Python asyncio)              │
│                                                         │
│  ┌─────────────┐                                        │
│  │ Scheduler   │  每 60 秒触发一次决策循环               │
│  │ (定时器)     │                                        │
│  └──────┬──────┘                                        │
│         │                                               │
│  ┌──────▼──────┐     ┌──────────────┐                   │
│  │ Data        │────▶│ Decision     │                   │
│  │ Collector   │     │ Engine       │                   │
│  │             │     │              │                   │
│  │ - MCP 读取  │     │ ┌──────────┐ │                   │
│  │ - x402 获取 │     │ │ 规则预检 │ │                   │
│  │ - 缓存管理  │     │ ├──────────┤ │                   │
│  └─────────────┘     │ │ LLM 推理 │ │                   │
│                      │ ├──────────┤ │                   │
│                      │ │ 风险校验 │ │                   │
│                      │ └──────────┘ │                   │
│                      └──────┬───────┘                   │
│                             │                           │
│                      ┌──────▼───────┐                   │
│                      │ Executor     │                   │
│                      │              │                   │
│                      │ - 交易构建   │                   │
│                      │ - 签名广播   │                   │
│                      │ - 结果记录   │                   │
│                      │ - 日志推送   │                   │
│                      └──────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

## 决策引擎详细设计

### 三层决策模型

```
输入数据
    │
    ▼
┌──────────────────────────────────────┐
│  Layer 1: 规则预检 (Rule Precheck)   │
│                                      │
│  硬性约束，不满足则直接 HOLD         │
│                                      │
│  ✓ 余额 >= min_gas_reserve (5 CSPR) │
│  ✓ APY 差异 >= 100 bps (1%)         │
│  ✓ 距上次 rebalance >= 300 秒       │
│  ✓ 所有目标池 is_active == true     │
│                                      │
│  不通过 → 返回 HOLD + 原因           │
└──────────────┬───────────────────────┘
               │ 通过
               ▼
┌──────────────────────────────────────┐
│  Layer 2: LLM 分析 (LLM Analysis)   │
│                                      │
│  将市场数据送入 LLM，获取策略建议    │
│                                      │
│  输入:                               │
│    - 各池 APY、TVL、占比             │
│    - Oracle 数据 (收益率、置信度)    │
│    - 市场波动率                      │
│    - 代理配置 (风险偏好、阈值)       │
│                                      │
│  输出:                               │
│    - 操作类型 (hold/rebalance)       │
│    - from_pool, to_pool, amount     │
│    - confidence (0-100)              │
│    - reasoning (解释)                │
│    - expected_apy_gain (预期增益)    │
│                                      │
│  解析失败 → 返回 HOLD               │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  Layer 3: 风险校验 (Risk Validation) │
│                                      │
│  对 LLM 建议进行多维评估             │
│                                      │
│  检查项:                             │
│    - 金额占比 <= 30%                 │
│    - 目标池分配 <= max_allocation    │
│    - Gas 成本 < 年化收益的 1%        │
│    - 市场波动率 < 阈值               │
│    - LLM 置信度 >= 60%              │
│                                      │
│  风险总分 < 50 → 通过               │
│  风险总分 >= 50 → 拒绝, 返回 HOLD   │
└──────────────┬───────────────────────┘
               │ 通过
               ▼
         执行 REBALANCE
```

### LLM Prompt 设计

#### System Prompt

```
You are a yield optimization agent for Casper Network DeFi pools.

Your job: analyze pool states, RWA oracle data, and market conditions
to decide whether to rebalance funds between pools.

Rules:
- Only suggest rebalance when the APY gain exceeds 0.5% (50 bps)
  after accounting for gas costs
- Never allocate more than the configured max_allocation_pct to any
  single pool
- Prefer stability over maximum yield in high-volatility conditions
- Always explain your reasoning clearly
- Consider RWA oracle confidence: low confidence data should reduce
  your conviction

Output JSON only:
{
    "action": "hold|rebalance",
    "from_pool": null | int,
    "to_pool": null | int,
    "amount": null | int,
    "confidence": 0-100,
    "reasoning": "string",
    "expected_apy_gain": int
}
```

#### User Prompt 模板

```
Current market snapshot:
- Timestamp: {timestamp}
- CSPR price: ${cspr_price}
- Market volatility index: {volatility}%

Pool states:
  Pool 0 (Stable Pool): APY=3.00%, TVL=50000 CSPR, allocation=50%
  Pool 1 (Growth Pool): APY=6.00%, TVL=30000 CSPR, allocation=30%
  Pool 2 (High Yield Pool): APY=9.00%, TVL=20000 CSPR, allocation=20%

RWA Oracle data:
  us_treasury_10y: 4.25% (confidence: 95%, age: 45s, source: federal_res)
  t_bill_3m: 5.20% (confidence: 88%, age: 120s, source: treasury_api)

Agent config:
- Max single rebalance: 30% of pool
- Min rebalance interval: 300s
- Risk tolerance: moderate

Should we rebalance? Analyze the data and provide your recommendation.
```

### 风险评估器

#### 检查项权重

| 检查项 | 权重 | 触发条件 | 拒绝分 |
|--------|------|----------|--------|
| 金额占比 | 30 | amount > pool × 30% | +30 |
| 分配上限 | 25 | target_pool_pct > max_pct | +25 |
| Gas 效益 | 20 | gas > annual_gain × 1% | +20 |
| 波动性 | 15 | volatility > threshold | +15 |
| 置信度 | 10 | confidence < 60% | +10 |

总分 >= 50 → 拒绝操作

#### 波动性估算

```
volatility_bps = max(pool_apys) - min(pool_apys)

示例:
  Pool 0: 3% APY
  Pool 1: 6% APY
  Pool 2: 9% APY

  volatility = 900 - 300 = 600 bps (6%)
  阈值: 200 bps (2%)
  结论: 600 > 200 → 高波动，倾向于 HOLD
```

### 决策示例

#### 场景 1: 正常 rebalance

```
输入:
  Pool 0: APY 3%, TVL 50000, allocation 50%
  Pool 1: APY 7%, TVL 30000, allocation 30%
  Pool 2: APY 5%, TVL 20000, allocation 20%
  Oracle: t_bill_3m = 5.5%, confidence 95%
  波动率: 400 bps

规则预检: ✓ APY 差异 400bps > 100bps
LLM 分析: 建议从 Pool 0 迁移 15000 到 Pool 1
  理由: Pool 1 APY 最高，且 Oracle 数据支持收益率上行
  置信度: 85%
  预期增益: 400 bps

风险校验:
  金额占比: 15000/50000 = 30% ✓ (刚好等于上限)
  分配上限: (30000+15000)/100000 = 45% ✓ (假设 max=50%)
  Gas 效益: 0.012 CSPR < 15000 × 4% / 10000 × 365 = 6 CSPR ✓
  波动率: 400 bps > 200 bps → +15 分
  置信度: 85% > 60% ✓
  总分: 15 < 50 → 通过

结果: 执行 REBALANCE Pool 0 → Pool 1, amount=15000
```

#### 场景 2: 波动性过高

```
输入:
  Pool 0: APY 2%, Pool 1: APY 8%, Pool 2: APY 12%
  Oracle: 置信度 60%
  波动率: 1000 bps

规则预检: ✓
LLM 分析: 建议 rebalance 到 Pool 2
  理由: Pool 2 收益最高
  置信度: 55%

风险校验:
  波动率: 1000 bps > 200 bps → +15 分
  置信度: 55% < 60% → +10 分
  总分: 25 < 50 → 勉强通过

结果: 执行 REBALANCE（但风险提示较高）
```

#### 场景 3: 被拒绝

```
输入:
  Pool 0: APY 3%, Pool 1: APY 4%, Pool 2: APY 3.5%
  余额: 3 CSPR

规则预检:
  余额: 3 CSPR < 5 CSPR (min_gas_reserve) → 不通过

结果: HOLD — "Insufficient balance for gas fees"
```

## 代理生命周期管理

### 启动流程

```
1. 加载配置 (config.py)
2. 验证密钥文件存在
3. 连接 MCP Server (health check)
4. 连接 x402 数据源 (test request)
5. 在 AgentRegistry 注册身份
6. 启动定时调度器
7. 进入主循环
```

### 异常处理

| 异常 | 处理策略 |
|------|----------|
| MCP Server 不可达 | 重试 3 次，间隔 10 秒，然后等待下一轮 |
| x402 支付失败 | 跳过该数据源，使用缓存数据 |
| LLM 超时 | 使用规则引擎的保守策略 (HOLD) |
| LLM 输出非法 JSON | 返回 HOLD，记录错误 |
| 交易提交失败 | 记录错误，等待下一轮 |
| 余额不足 | 停止 rebalance，只做数据采集 |

### 日志格式

```
[2026-06-24 10:30:00] [INFO] ─── Cycle 42 ───
[2026-06-24 10:30:01] [INFO] [1/5] Reading on-chain state...
[2026-06-24 10:30:02] [INFO] [2/5] Fetching off-chain data via x402...
[2026-06-24 10:30:03] [INFO] [3/5] Building market snapshot...
[2026-06-24 10:30:03] [INFO] [4/5] Running decision engine...
[2026-06-24 10:30:05] [INFO] Decision: rebalance | Confidence: 85% | Reasoning: Pool 1 APY superior
[2026-06-24 10:30:05] [INFO] [5/5] Executing...
[2026-06-24 10:30:06] [INFO] Rebalancing: Pool 0 → Pool 1, Amount: 15000
[2026-06-24 10:30:08] [INFO] Rebalance tx submitted: 0xabc123...
[2026-06-24 10:30:08] [INFO] Cycle 42 completed in 8.2s
```

## 配置参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `poll_interval_sec` | 60 | 决策循环间隔（秒） |
| `risk.max_single_rebalance_pct` | 30 | 单次最大迁移比例（%） |
| `risk.min_rebalance_interval_sec` | 300 | 最小 rebalance 间隔（秒） |
| `risk.max_slippage_bps` | 100 | 最大滑点（万分比） |
| `risk.min_gas_reserve` | 5.0 | 最低保留 CSPR |
| `risk.volatility_threshold` | 200 | 波动率阈值（万分比） |
| `x402.max_payment_per_request` | 10000 | 单次最大支付 (motes) |
| `llm_model` | claude-sonnet-4-6 | 决策用 LLM 模型 |
