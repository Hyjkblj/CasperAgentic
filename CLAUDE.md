# CasperAgentic — YieldAgent 项目

## 项目概述

Casper Agentic Buildathon 2026 参赛项目。自主 AI 代理，监控 RWA 收益率，自动在 Casper DeFi 池之间 rebalance。

## 关键约束

- 截止日期: 2026-06-30
- 部署目标: Casper 测试网
- 必须有: 链上组件 + 生成交易
- 工具: Odra, MCP Server, x402, Agent Skills, CSPR.cloud

## 文档位置

所有设计文档在 `docs/` 目录，README.md 有完整索引。实现前先读相关文档。

## 开发优先级

1. P0: 合约 (YieldPool + RwaOracle + AgentRegistry) + 代理决策循环 + 前端首页
2. P1: x402 数据获取 + 风险评估器 + Oracle 数据页
3. P2: 代理排行榜 + 跟投机制 + WebSocket 实时推送

## 代码风格

- 合约: Rust + Odra，注释用英文
- 代理: Python，type hints，docstrings
- 前端: TypeScript，shadcn/ui 组件
