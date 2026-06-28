# x402 协议集成

## 什么是 x402

x402 是基于 HTTP 402 状态码的原生支付协议，允许客户端按请求付费获取资源。核心特点：

- **无需预授权**：每次请求独立支付
- **无需订阅**：按需使用，按量计费
- **加密证明**：支付证明基于密码学签名
- **机器原生**：专为 AI 代理设计的支付流程

## 在本项目中的角色

x402 是获取链下 RWA 数据的通道：

```
AI 代理 ──x402──▶ 国债收益率 API ──▶ 链下数据 ──▶ RwaOracle 合约 ──▶ 链上可信数据
```

**差异化价值**：大多数参赛者会硬编码模拟数据，我们通过 x402 展示了真实的「代理自主付费获取外部数据」能力。

## 协议流程

### 标准 x402 流程

```
客户端                              服务端
  │                                   │
  │  GET /api/data                    │
  │ ────────────────────────────────▶ │
  │                                   │
  │  HTTP 402 Payment Required        │
  │  Content-Type: application/json   │
  │  {                                │
  │    "x402Version": 1,              │
  │    "accepts": [{                  │
  │      "scheme": "exact",           │
  │      "network": "casper-testnet", │
  │      "maxAmountRequired": "500",  │
  │      "resource": "/api/data",     │
  │      "description": "...",        │
  │      "payTo": "01abc...",         │
  │      "asset": "CSPR"              │
  │    }]                             │
  │  }                                │
  │ ◀──────────────────────────────── │
  │                                   │
  │  [客户端生成支付证明]              │
  │  1. 构造支付 payload              │
  │  2. 用私钥签名                    │
  │  3. 编码为 base64                 │
  │                                   │
  │  GET /api/data                    │
  │  X-Payment: <base64_proof>        │
  │ ────────────────────────────────▶ │
  │                                   │
  │  [服务端验证支付]                  │
  │  1. 解码 base64                   │
  │  2. 验证签名                      │
  │  3. 验证金额                      │
  │  4. 记录支付                      │
  │                                   │
  │  HTTP 200 OK                      │
  │  { "value": 425, ... }           │
  │ ◀──────────────────────────────── │
```

## 数据源设计

### 数据源清单

| 数据源 | data_type | URL | 预估成本 | 更新频率 |
|--------|-----------|-----|----------|----------|
| 美国 10 年期国债 | `us_treasury_10y` | `/api/treasury/10y` | 500 motes | 每日 |
| 3 个月国库券 | `t_bill_3m` | `/api/tbill/3m` | 300 motes | 每日 |
| 6 个月国库券 | `t_bill_6m` | `/api/tbill/6m` | 300 motes | 每日 |
| AAA 企业债 | `corp_bond_aaa` | `/api/bond/aaa` | 400 motes | 每周 |
| 房地产指数 | `real_estate_idx` | `/api/realestate/idx` | 600 motes | 每月 |

### 数据源响应格式

#### 402 响应

```json
{
  "x402Version": 1,
  "accepts": [
    {
      "scheme": "exact",
      "network": "casper-testnet",
      "maxAmountRequired": "500",
      "resource": "/api/treasury/10y",
      "description": "US 10-Year Treasury Yield",
      "payTo": "01a1b2c3d4e5f6...",
      "asset": "CSPR"
    }
  ]
}
```

#### 200 成功响应

```json
{
  "data_type": "us_treasury_10y",
  "value": 425,
  "unit": "basis_points",
  "source": "federal_reserve",
  "confidence": 95,
  "timestamp": 1719225600,
  "metadata": {
    "previous_value": 420,
    "change": 5,
    "change_pct": "1.19%"
  }
}
```

## 代理端实现

### X402Fetcher 类

```python
class X402Fetcher:
    """
    x402 协议数据获取器。

    关键设计:
    1. 支付金额上限检查 — 防止恶意服务端要求过高支付
    2. 缓存机制 — 相同数据类型在 TTL 内不重复请求
    3. 降级策略 — x402 失败时使用缓存数据
    4. 成本追踪 — 记录总支出用于预算控制
    """

    def __init__(self, config: X402Config, wallet_key: str):
        self.config = config
        self.wallet_key = wallet_key
        self.cache: dict[str, FetchedData] = {}
        self.total_spent: int = 0
        self.budget_limit: int = 1_000_000  # 1 CSPR 总预算

    async def fetch(self, data_type: str) -> Optional[FetchedData]:
        """获取指定类型的数据"""

        # 1. 检查缓存
        if data_type in self.cache:
            cached = self.cache[data_type]
            if cached.timestamp + 300 > time.time():  # 5 分钟 TTL
                return cached

        # 2. 检查预算
        source = self.config.data_sources.get(data_type)
        if not source:
            raise ValueError(f"Unknown data type: {data_type}")

        if self.total_spent + source["expected_cost"] > self.budget_limit:
            raise BudgetExhaustedError(
                f"Budget exhausted: {self.total_spent}/{self.budget_limit}"
            )

        # 3. 发起请求
        response = await httpx.AsyncClient().get(source["url"])

        # 4. 处理 402
        if response.status_code == 402:
            payment_info = response.json()

            # 4a. 检查金额上限
            amount = int(payment_info["accepts"][0]["maxAmountRequired"])
            if amount > self.config.max_payment_per_request:
                raise PaymentTooHighError(
                    f"Requested {amount} > max {self.config.max_payment_per_request}"
                )

            # 4b. 生成支付证明
            proof = self._sign_payment(payment_info)

            # 4c. 带支付证明重试
            response = await httpx.AsyncClient().get(
                source["url"],
                headers={"X-Payment": proof},
            )

            # 4d. 记录支出
            self.total_spent += amount

        # 5. 解析响应
        if response.status_code == 200:
            data = self._parse_response(response.json(), data_type)
            self.cache[data_type] = data
            return data

        return None

    def _sign_payment(self, payment_info: dict) -> str:
        """生成 x402 支付证明"""
        import base64
        import json

        payload = {
            "x402Version": 1,
            "scheme": "exact",
            "network": "casper-testnet",
            "amount": payment_info["accepts"][0]["maxAmountRequired"],
            "payTo": payment_info["accepts"][0]["payTo"],
            "resource": payment_info["accepts"][0]["resource"],
            "timestamp": int(time.time()),
        }

        # 用 Casper SDK 签名
        # signature = casper_sdk.sign(self.wallet_key, json.dumps(payload))
        # payload["signature"] = signature

        return base64.b64encode(json.dumps(payload).encode()).decode()
```

### 成本控制策略

```python
class BudgetManager:
    """预算管理器 — 控制 x402 总支出"""

    def __init__(self, daily_limit: int = 10_000_000):  # 10 CSPR/天
        self.daily_limit = daily_limit
        self.daily_spent: int = 0
        self.last_reset: int = 0

    def can_afford(self, cost: int) -> bool:
        """检查是否在预算内"""
        self._maybe_reset_day()
        return self.daily_spent + cost <= self.daily_limit

    def record_cost(self, cost: int):
        """记录支出"""
        self.daily_spent += cost

    def get_remaining(self) -> int:
        """获取剩余预算"""
        self._maybe_reset_day()
        return self.daily_limit - self.daily_spent

    def _maybe_reset_day(self):
        """每日重置"""
        now = int(time.time())
        if now - self.last_reset > 86400:
            self.daily_spent = 0
            self.last_reset = now
```

## 模拟数据源（Buildathon 用途）

对于 Buildathon 演示，我们提供一个模拟 x402 数据源服务：

```python
# mock_x402_server.py

from fastapi import FastAPI, Response
import random
import time

app = FastAPI()

# 模拟数据
MOCK_DATA = {
    "us_treasury_10y": {"base": 425, "volatility": 10},
    "t_bill_3m": {"base": 520, "volatility": 15},
    "t_bill_6m": {"base": 505, "volatility": 12},
}

PAYMENT_COSTS = {
    "us_treasury_10y": 500,
    "t_bill_3m": 300,
    "t_bill_6m": 300,
}

@app.get("/api/{data_type}")
async def get_data(data_type: str, x_payment: str = None):
    if data_type not in MOCK_DATA:
        return Response(status_code=404)

    # 检查支付
    if not x_payment:
        return Response(
            status_code=402,
            content=json.dumps({
                "x402Version": 1,
                "accepts": [{
                    "scheme": "exact",
                    "network": "casper-testnet",
                    "maxAmountRequired": str(PAYMENT_COSTS[data_type]),
                    "resource": f"/api/{data_type}",
                    "description": f"Mock {data_type} data",
                    "payTo": "01a1b2c3d4e5f6...",
                    "asset": "CSPR",
                }],
            }),
            media_type="application/json",
        )

    # 验证支付（模拟）
    # 实际应验证签名和金额

    # 返回模拟数据
    config = MOCK_DATA[data_type]
    value = config["base"] + random.randint(-config["volatility"], config["volatility"])

    return {
        "data_type": data_type,
        "value": value,
        "unit": "basis_points",
        "source": "mock_source",
        "confidence": random.randint(80, 99),
        "timestamp": int(time.time()),
    }
```

## 安全考量

| 风险 | 缓解措施 |
|------|----------|
| 恶意服务端要求过高支付 | `max_payment_per_request` 硬限制 |
| 支付证明重放 | 包含 timestamp，服务端验证时效性 |
| 预算耗尽 | `BudgetManager` 每日限额 |
| 数据篡改 | 多数据源交叉验证（未来） |
| 中间人攻击 | HTTPS + 签名验证 |
