# YieldAgent — Casper 上的自主收益优化代理

> Casper Agentic Buildathon 2026 参赛项目

## 一句话描述

一个自主 AI 代理，监控链下 RWA 资产收益率变化，通过 MCP Server 读取 Casper DeFi 协议状态，自动在收益池之间重新平衡资金，并使用 x402 协议按需付费获取链下数据源——将被动持仓变成主动管理的收益引擎。

## 解决的问题

DeFi 用户面临的核心痛点：

- **收益被动**：存入资金池后无法及时跟踪 APY 变化，错过更高收益机会
- **操作门槛高**：手动 rebalance 需要持续监控多个池子、计算 gas 成本、评估风险
- **数据断层**：链下 RWA 数据（国债收益率、票据价格）无法可信地传递到链上
- **信任缺失**：无法验证代理决策的质量和历史表现

## 核心特性

| 特性 | 说明 |
|------|------|
| **自主决策循环** | 代理每 60 秒读取链上状态 + 链下数据，自主判断是否 rebalance |
| **x402 数据获取** | 通过 x402 协议按请求付费获取 RWA 收益率数据，无需预授权 |
| **链上信誉系统** | 每次决策和收益记录在链上，用户可基于历史数据选择跟投 |
| **多维风险控制** | LLM 推理 + 规则引擎双重校验，防止单一模型失误导致资金损失 |
| **实时仪表盘** | WebSocket 推送代理决策日志，资产分布和收益曲线实时可视化 |

## 技术栈

| 层 | 技术 |
|----|------|
| 智能合约 | Rust + Odra 框架 |
| AI 代理 | Python + asyncio + Anthropic SDK |
| 链上交互 | Casper MCP Server + CSPR.cloud API |
| 交易签名 | CSPR.click AI Agent Skills |
| 链下数据 | x402 协议 |
| 前端 | Next.js 14 + TailwindCSS + shadcn/ui + Recharts |
| 部署 | Docker Compose + Railway/Vercel |

## 架构概览

```
┌─────────────────────────────────────────────┐
│            用户界面 (Next.js)                │
│   仪表盘：资产分布、收益曲线、代理决策日志    │
└────────────────┬────────────────────────────┘
                 │ WebSocket / REST
┌────────────────▼────────────────────────────┐
│            AI 代理核心 (Python)              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │ 决策引擎 │ │ 风险评估 │ │ 执行引擎 │    │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘    │
│       └────────────┼────────────┘           │
│              MCP Client Layer               │
└───────┬──────────┬──────────┬───────────────┘
        │          │          │
┌───────▼───┐ ┌────▼────┐ ┌──▼──────────────┐
│ Casper    │ │ CSPR    │ │ RWA 数据源      │
│ MCP Server│ │ .cloud  │ │ (x402 付费获取) │
└───────────┘ └─────────┘ └─────────────────┘
        │
┌───────▼─────────────────────────────────────┐
│           Casper 测试网 (链上)               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │ 收益池   │ │ Oracle   │ │ 代理注册 │    │
│  │ 合约     │ │ 合约     │ │ 合约     │    │
│  └──────────┘ └──────────┘ └──────────┘    │
└─────────────────────────────────────────────┘
```

## 快速开始

### 前置条件

- Python 3.11+
- Node.js 20+
- Rust (编译合约用)

### 本地演示

```bash
# 1. 克隆仓库
git clone https://github.com/your-org/yield-agent.git
cd yield-agent

# 2. 一键启动（Windows）
scripts\demo.bat

# 或 Linux/Mac
bash scripts/demo.sh
```

启动后访问 http://localhost:3000 查看仪表盘。

### 部署到测试网

```bash
# 1. 安装 casper-client
cargo install casper-client

# 2. 生成密钥
casper-client keygen ./keys

# 3. 编译合约
make contracts

# 4. 部署合约
python scripts/deploy_contracts.py

# 5. 初始化池子和代理权限
bash scripts/init_pools.sh
bash scripts/register_agent.sh

# 6. 配置 .env 中的合约 hash
# 7. 启动代理和前端
make agent-run
make frontend-dev
```

详细部署说明见 [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)。

## 项目结构

```
yield-agent/
├── contracts/                  # Odra 智能合约
│   ├── yield_pool/             # 收益池合约
│   ├── rwa_oracle/             # RWA Oracle 合约
│   ├── agent_registry/         # 代理注册与信誉合约
│   └── Cargo.toml
├── agent/                      # AI 代理核心
│   ├── main.py                 # 入口，启动决策循环
│   ├── config.py               # 配置管理
│   ├── core/                   # 决策引擎、风险评估、执行器
│   ├── blockchain/             # MCP 客户端、交易构建
│   ├── data/                   # x402 数据获取、缓存
│   └── utils/                  # 日志、指标
├── frontend/                   # Next.js 仪表盘
│   ├── app/                    # 页面路由
│   ├── components/             # UI 组件
│   └── package.json
├── scripts/                    # 部署脚本
├── docs/                       # 详细文档
├── docker-compose.yml
├── Makefile
└── README.md
```

## 文档索引

| 文档 | 内容 |
|------|------|
| [架构设计](docs/ARCHITECTURE.md) | 系统架构、数据流、组件交互 |
| [智能合约](docs/SMART_CONTRACTS.md) | 三个合约的接口设计、状态模型、安全考量 |
| [AI 代理](docs/AGENT.md) | 决策引擎、风险模型、LLM 集成 |
| [x402 集成](docs/X402_INTEGRATION.md) | x402 协议流程、数据源对接 |
| [前端设计](docs/FRONTEND.md) | 页面结构、组件设计、实时通信 |
| [部署指南](docs/DEPLOYMENT.md) | 环境配置、合约部署、服务启动 |
| [开发路线图](docs/ROADMAP.md) | MVP 范围、里程碑、长期计划 |

## Casper Buildathon 评分对应

| 评分维度 | 本项目对应 |
|----------|-----------|
| 技术执行 | Odra 合约 + Python 代理 + Next.js 前端，完整全栈 |
| 创新与原创性 | x402 原生集成 + 链上代理信誉 + 自主循环决策 |
| AI/智能体应用 | LLM 驱动的决策引擎，非简单聊天机器人 |
| 实际应用性 | RWA 收益优化是真实 DeFi 需求 |
| 用户体验 | 实时仪表盘 + 代理决策可视化 |
| 智能合约运作 | 三个 Odra 合约部署到测试网，可生成交易 |
| 长期发射计划 | 可接入真实 RWA 数据源，支持多代理竞争 |
| 长期影响潜力 | 为 Casper 生态提供 DeFi + AI 基础设施 |

## 许可证

MIT License
