# 开发路线图

## 时间线总览

```
2026-06-01 ──────────────────────────── 2026-06-30
│                                          │
├── Week 1 (6/1-6/7) ──── 合约 + 骨架 ────┤
├── Week 2 (6/8-6/14) ─── 代理核心 ───────┤
├── Week 3 (6/15-6/21) ── 前端 + 集成 ────┤
├── Week 4 (6/22-6/30) ── 测试 + 提交 ────┤
│                                          │
▼ 资格赛截止                                ▼
```

## MVP 范围（资格赛）

### P0 — 必须完成

| 模块 | 功能 | 验收标准 |
|------|------|----------|
| 合约 | YieldPool：存入/取出/查询 APY | 部署到测试网，可生成交易 |
| 合约 | YieldPool：rebalance 函数 | 授权代理可调用，资金跨池迁移 |
| 合约 | RwaOracle：submit_data | 代理可提交数据到链上 |
| 合约 | AgentRegistry：register_agent | 代理可注册身份 |
| 代理 | MCP Client：读取链上状态 | 成功查询池子 APY 和余额 |
| 代理 | 决策引擎：LLM 推理 | 输入数据 → 输出结构化决策 |
| 代理 | 决策引擎：规则预检 | 硬性约束正确过滤 |
| 代理 | 执行引擎：提交交易 | rebalance 交易成功上链 |
| 前端 | 仪表盘首页 | 显示池子状态和代理日志 |

### P1 — 应该完成

| 模块 | 功能 | 验收标准 |
|------|------|----------|
| 合约 | RwaOracle：get_valid_data + 有效期 | 过期数据返回 None |
| 合约 | RwaOracle：verify_data + 信誉更新 | 验证准确后信誉分提升 |
| 合约 | AgentRegistry：record_operation | 操作记录写入链上 |
| 合约 | AgentRegistry：get_leaderboard | 按信誉排序返回代理列表 |
| 代理 | x402 数据获取 | 成功付费获取链下数据 |
| 代理 | 风险评估器 | 5 项检查正确执行 |
| 代理 | Oracle 数据提交 | x402 数据 → 链上 Oracle |
| 前端 | 收益池详情页 | 图表 + 操作历史 |
| 前端 | Oracle 数据页 | 数据流展示 |

### P2 — 可以完成

| 模块 | 功能 | 验收标准 |
|------|------|----------|
| 合约 | AgentRegistry：follow_agent | 用户可跟投代理 |
| 代理 | WebSocket 日志推送 | 前端实时显示决策日志 |
| 代理 | 缓存机制 | x402 数据 5 分钟 TTL |
| 前端 | 代理排行榜 | 按信誉排序展示 |
| 前端 | 代理详情页 | 完整决策历史 |

## 里程碑

### Milestone 1: 合约就绪（Week 1）

**目标**：三个合约部署到测试网，基本函数可调用。

```
交付物:
  ✓ contracts/yield_pool/ — 编译通过，部署成功
  ✓ contracts/rwa_oracle/ — 编译通过，部署成功
  ✓ contracts/agent_registry/ — 编译通过，部署成功
  ✓ scripts/deploy_contracts.sh — 一键部署脚本
  ✓ 测试交易：deposit, withdraw, submit_data, register_agent

验证:
  $ make contracts
  $ make deploy-contracts
  $ casper-client query-state --key $YIELD_POOL_HASH
```

### Milestone 2: 代理可运行（Week 2）

**目标**：代理能读取链上状态、做出决策、提交交易。

```
交付物:
  ✓ agent/blockchain/mcp_client.py — MCP 查询和交易提交
  ✓ agent/core/decision_engine.py — LLM 推理 + 规则预检
  ✓ agent/core/risk_assessor.py — 5 项风险检查
  ✓ agent/core/executor.py — 交易构建和提交
  ✓ agent/main.py — 主循环运行

验证:
  $ make agent-run
  # 日志显示: Cycle 0, Reading on-chain state..., Decision: HOLD/REBALANCE
  # 交易 hash 出现在测试网浏览器
```

### Milestone 3: 前端可视（Week 3）

**目标**：前端仪表盘可展示系统状态。

```
交付物:
  ✓ frontend/app/page.tsx — 仪表盘首页
  ✓ frontend/components/PoolChart.tsx — 池子图表
  ✓ frontend/components/AgentLog.tsx — 决策日志
  ✓ frontend/components/OracleFeed.tsx — Oracle 数据
  ✓ frontend/api/dashboard/route.ts — API 聚合

验证:
  $ make frontend-dev
  # 浏览器打开 http://localhost:3000
  # 显示池子 APY、TVL、代理决策日志
```

### Milestone 4: 提交就绪（Week 4）

**目标**：全栈集成，录制演示视频，提交到 DoraHacks。

```
交付物:
  ✓ docker-compose.yml — 一键启动全栈
  ✓ 完整 README.md — 架构、部署、使用说明
  ✓ 演示视频 — 3-5 分钟，展示完整流程
  ✓ DoraHacks 提交 — GitHub 链接 + 视频链接

验证:
  $ docker-compose up -d
  # 所有服务正常运行
  # 代理持续做出决策并执行
  # 前端实时更新
```

## 演示视频脚本

### 结构（3-5 分钟）

```
[0:00-0:30] 开场
  "这是 YieldAgent，一个运行在 Casper 上的自主收益优化代理。
   它能自动监控 RWA 收益率变化，在 DeFi 池之间重新平衡资金。"

[0:30-1:30] 架构介绍
  "系统由三层组成：
   链上层：三个 Odra 智能合约 — 收益池、Oracle、代理注册
   代理层：AI 决策引擎，每 60 秒自主运行一次决策循环
   数据层：通过 x402 协议按请求付费获取链下 RWA 数据"

[1:30-2:30] 演示：代理决策循环
  "现在让我们看代理运行：
   1. 它读取链上三个池子的状态 — APY 分别是 3%, 6%, 9%
   2. 通过 x402 获取最新国债收益率 — 4.25%
   3. LLM 分析：Pool 1 的 APY 最高且 RWA 数据支持
   4. 风险校验通过：金额占比 30%，Gas 效益合理
   5. 执行 rebalance：从 Pool 0 迁移 15000 CSPR 到 Pool 1
   6. 交易确认，结果记录到链上"

[2:30-3:30] 演示：前端仪表盘
  "仪表盘实时展示：
   - 各池 APY 和资金分布
   - 代理决策日志和置信度
   - Oracle 数据流和源信誉
   - 收益曲线变化"

[3:30-4:30] 差异化亮点
  "与其他方案不同：
   1. 我们不是简单的单次交易 — 而是自主循环决策
   2. 我们通过 x402 真正付费获取数据 — 不是硬编码
   3. 每次决策都记录在链上 — 代理信誉可验证
   4. 用户可以跟投表现最好的代理"

[4:30-5:00] 结尾
  "YieldAgent 展示了 Casper 上 AI + DeFi + RWA 的可能性。
   代理可以 24/7 自主运行，将被动持仓变成主动管理。
   谢谢！"
```

## 长期计划（决赛及以后）

### Phase 1: 真实数据接入（决赛阶段）

| 目标 | 说明 |
|------|------|
| 接入真实 Casper DeFi 协议 | 替换模拟池为真实的流动性池 |
| 真实 RWA 数据源 | 接入国债收益率 API |
| 多代理策略 | 支持不同风险偏好的代理 |
| 用户跟投 UI | 用户可选择代理并委托资金 |

### Phase 2: 生态扩展

| 目标 | 说明 |
|------|------|
| 跨链 RWA | 聚合多条链的 RWA 数据 |
| DAO 治理 | 代理参数由 DAO 投票决定 |
| 策略市场 | 开发者可发布策略，用户可选择 |
| 移动端 | 移动端监控和跟投 |

### Phase 3: 商业化

| 目标 | 说明 |
|------|------|
| 管理费模型 | 代理收取收益的 N% 作为管理费 |
| 机构接入 | 为机构提供定制化代理服务 |
| 合规框架 | 集成 KYC/AML 合规模块 |

## 风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 合约 Bug | 中 | 高 | 充分测试，限制单次操作金额 |
| LLM 决策失误 | 中 | 中 | 规则引擎兜底，风险评估器拒绝高风险操作 |
| MCP Server 不可用 | 低 | 高 | 重试机制，缓存上次数据 |
| x402 数据源不可用 | 中 | 中 | 降级使用缓存数据，多数据源冗余 |
| Gas 费超预算 | 低 | 低 | 预算管理器，每日限额 |
| 测试网不稳定 | 中 | 中 | 本地测试环境，合约状态快照 |
