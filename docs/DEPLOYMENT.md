# 部署指南

## 前置条件

| 工具 | 版本 | 用途 |
|------|------|------|
| Rust | 1.75+ | 编译 Odra 合约 |
| Python | 3.11+ | 运行 AI 代理 |
| Node.js | 20+ | 运行前端 |
| Docker | 24+ | 容器化部署 |
| Casper CLI | 3.0+ | 合约部署 |
| Odra CLI | 最新 | 合约编译 |

## 环境配置

### 1. 克隆项目

```bash
git clone https://github.com/your-org/yield-agent.git
cd yield-agent
```

### 2. 创建环境配置

```bash
cp .env.example .env
```

编辑 `.env`：

```env
# ─── Casper 网络 ───
CASPER_NETWORK=testnet
CASPER_NODE_URL=https://rpc.testnet.casper.casperlabs.io
CASPER_CHAIN_NAME=casper-testnet

# ─── 代理密钥 ───
AGENT_SECRET_KEY=./keys/agent.pem

# ─── LLM ───
LLM_MODEL=claude-sonnet-4-6
LLM_API_KEY=sk-ant-...

# ─── CSPR.cloud ───
CSPR_CLOUD_API=https://api.cspr.cloud
CSPR_API_KEY=your_api_key

# ─── 前端 ───
NEXT_PUBLIC_AGENT_WS=ws://localhost:8080/ws
NEXT_PUBLIC_CSPR_EXPLORER=https://testnet.cspr.live
```

### 3. 生成代理密钥

```bash
# 使用 Casper CLI 生成密钥对
casper-client keygen ./keys

# 或使用已有的 PEM 文件
# 将 agent.pem 放到 ./keys/ 目录
```

## 智能合约部署

### Step 1: 编译合约

```bash
cd contracts

# 安装 Odra CLI
cargo install odra-cli

# 编译所有合约
cargo odra build

# 编译产物在 target/wasm32-unknown-unknown/release/
```

### Step 2: 部署到测试网

```bash
# 设置环境变量
export NODE_URL=https://rpc.testnet.casper.casperlabs.io
export CHAIN_NAME=casper-testnet
export SECRET_KEY=./keys/agent.pem

# 部署 AgentRegistry
casper-client put-deploy \
  --node-address $NODE_URL \
  --chain-name $CHAIN_NAME \
  --secret-key $SECRET_KEY \
  --session-path target/wasm32-unknown-unknown/release/agent_registry.wasm \
  --payment-amount 5000000000

# 记录返回的 deploy hash，等待确认后获取合约 hash
# 部署 RwaOracle
casper-client put-deploy \
  --node-address $NODE_URL \
  --chain-name $CHAIN_NAME \
  --secret-key $SECRET_KEY \
  --session-path target/wasm32-unknown-unknown/release/rwa_oracle.wasm \
  --payment-amount 5000000000

# 部署 YieldPool
casper-client put-deploy \
  --node-address $NODE_URL \
  --chain-name $CHAIN_NAME \
  --secret-key $SECRET_KEY \
  --session-path target/wasm32-unknown-unknown/release/yield_pool.wasm \
  --payment-amount 5000000000
```

### Step 3: 初始化合约

```bash
# 更新 .env 中的合约 hash
# REGISTRY_HASH=<agent_registry_hash>
# ORACLE_HASH=<rwa_oracle_hash>
# YIELD_POOL_HASH=<yield_pool_hash>

# 授权代理提交 Oracle 数据
casper-client put-deploy \
  --node-address $NODE_URL \
  --chain-name $CHAIN_NAME \
  --secret-key $SECRET_KEY \
  --session-hash $ORACLE_HASH \
  --session-entry-point "authorize_submitter" \
  --session-arg "agent:account_hash='<AGENT_ADDRESS>'" \
  --payment-amount 1000000000

# 创建收益池
# Pool 0: Stable (3% APY)
casper-client put-deploy \
  --session-hash $YIELD_POOL_HASH \
  --session-entry-point "create_pool" \
  --session-arg "apy_basis_points:u64='300'" \
  --payment-amount 1000000000

# Pool 1: Growth (6% APY)
casper-client put-deploy \
  --session-hash $YIELD_POOL_HASH \
  --session-entry-point "create_pool" \
  --session-arg "apy_basis_points:u64='600'" \
  --payment-amount 1000000000

# Pool 2: High Yield (9% APY)
casper-client put-deploy \
  --session-hash $YIELD_POOL_HASH \
  --session-entry-point "create_pool" \
  --session-arg "apy_basis_points:u64='900'" \
  --payment-amount 1000000000

# 授权代理执行 rebalance
casper-client put-deploy \
  --session-hash $YIELD_POOL_HASH \
  --session-entry-point "authorize_agent" \
  --session-arg "agent:account_hash='<AGENT_ADDRESS>'" \
  --payment-amount 1000000000
```

### 使用部署脚本（推荐）

```bash
# 一键部署所有合约
chmod +x scripts/*.sh

./scripts/deploy_contracts.sh
./scripts/init_pools.sh
./scripts/register_agent.sh
```

## 代理部署

### 本地运行

```bash
cd agent

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 运行代理
python main.py
```

### Docker 运行

```bash
cd agent

# 构建镜像
docker build -t yield-agent .

# 运行
docker run -d \
  --name yield-agent \
  --env-file ../.env \
  -v ../keys:/app/keys:ro \
  yield-agent
```

### requirements.txt

```
anthropic>=0.40.0
httpx>=0.27.0
pydantic>=2.0
python-dotenv>=1.0
websockets>=12.0
```

### Dockerfile

```dockerfile
# agent/Dockerfile

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

## 前端部署

### 本地运行

```bash
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev
# 访问 http://localhost:3000
```

### Docker 运行

```bash
cd frontend

# 构建
docker build -t yield-frontend .

# 运行
docker run -d \
  --name yield-frontend \
  -p 3000:3000 \
  --env-file ../.env \
  yield-frontend
```

### Vercel 部署（推荐）

```bash
# 安装 Vercel CLI
npm i -g vercel

# 部署
cd frontend
vercel --prod
```

## Docker Compose 全栈部署

```yaml
# docker-compose.yml

version: "3.8"

services:
  # 模拟 x402 数据源
  mock-data:
    build: ./mock_x402_server
    ports:
      - "8000:8000"
    restart: unless-stopped

  # AI 代理
  agent:
    build: ./agent
    env_file: .env
    environment:
      - X402_BASE_URL=http://mock-data:8000
    volumes:
      - ./keys:/app/keys:ro
    depends_on:
      - mock-data
    restart: unless-stopped

  # WebSocket 代理（转发代理日志到前端）
  ws-proxy:
    build: ./ws_proxy
    ports:
      - "8080:8080"
    depends_on:
      - agent
    restart: unless-stopped

  # 前端
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    env_file: .env
    environment:
      - NEXT_PUBLIC_AGENT_WS=ws://ws-proxy:8080/ws
    depends_on:
      - ws-proxy
    restart: unless-stopped

volumes:
  redis_data:
```

启动：

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f agent

# 停止
docker-compose down
```

## 验证部署

### 1. 验证合约

```bash
# 查询池子数量
casper-client query-state \
  --node-address $NODE_URL \
  --state-root-hash $(casper-client get-state-root-hash --node-address $NODE_URL | jq -r '.state_root_hash') \
  --key $YIELD_POOL_HASH

# 查询代理注册状态
casper-client query-state \
  --key $REGISTRY_HASH
```

### 2. 验证代理

```bash
# 查看代理日志
docker-compose logs -f agent

# 预期输出:
# [INFO] Yield Optimization Agent Starting
# [INFO] Network: testnet
# [INFO] Agent registered on-chain
# [INFO] ─── Cycle 0 ───
# [INFO] [1/5] Reading on-chain state...
# ...
```

### 3. 验证前端

```bash
# 访问 http://localhost:3000
# 应看到仪表盘，显示池子状态和代理日志

# 检查 API
curl http://localhost:3000/api/dashboard
# 应返回 JSON 数据
```

## 测试网水龙头

部署合约和运行代理需要测试网 CSPR：

- Casper Testnet Faucet: https://testnet.cspr.cloud/tools/faucet
- 每次请求可获得 1000 CSPR

## 常见问题

### 合约部署失败

```
错误: "Insufficient gas"
解决: 增加 --payment-amount，建议 5000000000 (5 CSPR)
```

### 代理连接 MCP 失败

```
错误: "Connection refused"
解决: 确认 MCP Server 已启动，检查端口配置
```

### x402 支付失败

```
错误: "Payment rejected"
解决: 检查代理余额，确认 x402 服务端地址正确
```

### 前端无法获取数据

```
错误: API 返回 500
解决: 检查 .env 中合约 hash 是否正确，CSPR API Key 是否有效
```
