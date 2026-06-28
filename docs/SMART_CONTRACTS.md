# 智能合约设计

## 概述

本项目包含三个 Odra 智能合约，部署在 Casper 测试网上：

| 合约 | 职责 | 核心操作 |
|------|------|----------|
| **YieldPool** | 收益池管理 | 存入/取出/查询/rebalance |
| **RwaOracle** | 链下数据上链 | 提交/验证/查询 |
| **AgentRegistry** | 代理身份与信誉 | 注册/记录/查询/排行 |

## 一、YieldPool 合约

### 状态模型

```
PoolState {
    total_deposited: U256       // 池中总资金 (motes)
    apy_basis_points: u64       // 当前 APY (万分比, 500 = 5%)
    last_rebalance: u64         // 上次 rebalance 时间戳
    is_active: bool             // 池是否活跃
}

UserPosition {
    deposited: U256             // 用户存入金额
    entry_apy: u64              // 存入时的 APY
    entry_time: u64             // 存入时间
    accumulated_yield: U256     // 累计收益
}
```

### 接口定义

#### 管理函数

```rust
/// 创建新的收益池
/// 权限: admin
/// 参数:
///   - apy_basis_points: 初始 APY (万分比, 1-5000)
/// 返回: pool_id
fn create_pool(apy_basis_points: u64) -> u8;

/// 更新池子 APY
/// 权限: admin 或已授权代理
/// 参数:
///   - pool_id: 池子 ID
///   - new_apy: 新的 APY (万分比)
fn update_pool_apy(pool_id: u8, new_apy: u64);

/// 授权代理执行 rebalance
/// 权限: admin
/// 参数:
///   - agent: 代理地址
fn authorize_agent(agent: Address);

/// 暂停/激活池子
/// 权限: admin
fn set_pool_active(pool_id: u8, active: bool);
```

#### 用户函数

```rust
/// 存入资金到指定池
/// 需要附带 CSPR 代币
/// 参数:
///   - pool_id: 目标池子 ID
/// 附带: 存入金额 (通过 transaction amount)
fn deposit(pool_id: u8);

/// 取出资金
/// 参数:
///   - pool_id: 池子 ID
///   - amount: 取出金额 (motes)
fn withdraw(pool_id: u8, amount: U256);

/// 取出全部收益
/// 参数:
///   - pool_id: 池子 ID
fn claim_yield(pool_id: u8);
```

#### 代理函数

```rust
/// 将资金从一个池迁移到另一个池
/// 权限: 已授权代理
/// 参数:
///   - from_pool: 源池 ID
///   - to_pool: 目标池 ID
///   - amount: 迁移金额 (motes)
/// 事件: RebalanceEvent
fn rebalance(from_pool: u8, to_pool: u8, amount: U256);
```

#### 查询函数

```rust
/// 查询池状态
fn get_pool(pool_id: u8) -> PoolState;

/// 查询用户仓位
fn get_position(pool_id: u8, user: Address) -> UserPosition;

/// 查询所有池的 APY
fn get_all_pool_apys() -> Vec<(u8, u64)>;

/// 查询池子数量
fn get_pool_count() -> u8;
```

### 收益计算模型

```
yield = deposited × apy × elapsed_seconds / (365 × 24 × 3600 × 10000)

示例:
  存入: 1,000,000,000 motes (1000 CSPR)
  APY: 800 (8%)
  时间: 30 天 (2,592,000 秒)

  yield = 1,000,000,000 × 800 × 2,592,000 / (31,536,000 × 10,000)
        = 6,531,506 motes (~6.5 CSPR)
```

### Rebalance 安全约束

| 约束 | 检查点 |
|------|--------|
| 权限 | 调用者必须是 `authorized_agents` 中的地址 |
| 源池余额 | `from_pool.total_deposited >= amount` |
| 目标池状态 | `to_pool.is_active == true` |
| 金额上限 | `amount <= from_pool.total_deposited × 30%` （在代理层校验） |
| 时间间隔 | 距上次 rebalance >= 300 秒 （在代理层校验） |

### 事件定义

```rust
#[odra::event]
struct RebalanceEvent {
    from_pool: u8,          // 源池 ID
    to_pool: u8,            // 目标池 ID
    amount: U256,           // 迁移金额
    agent: Address,         // 执行代理
    timestamp: u64,         // 时间戳
}

#[odra::event]
struct DepositEvent {
    pool_id: u8,
    user: Address,
    amount: U256,
    new_total: U256,
}

#[odra::event]
struct WithdrawEvent {
    pool_id: u8,
    user: Address,
    amount: U256,
    yield_claimed: U256,
}
```

---

## 二、RwaOracle 合约

### 状态模型

```
OracleRecord {
    data_type: String           // "us_treasury_10y", "t_bill_3m"
    value: u64                  // 值 (万分比, 425 = 4.25%)
    source: String              // 数据来源标识
    submitter: Address          // 提交者（代理地址）
    timestamp: u64              // 提交时间
    confidence: u8              // 置信度 0-100
}

SourceReputation {
    total_submissions: u32      // 总提交次数
    accurate_submissions: u32   // 被验证为准确的次数
    reputation_score: u64       // 信誉分 0-10000
    last_submission: u64        // 最后提交时间
}
```

### 接口定义

#### 管理函数

```rust
/// 授权代理提交数据
/// 权限: admin
fn authorize_submitter(agent: Address);

/// 设置数据有效期窗口（秒）
/// 权限: admin
fn set_validity_window(seconds: u64);
```

#### 数据操作

```rust
/// 提交链下数据到链上
/// 权限: 已授权提交者
/// 参数:
///   - data_type: 数据类型 ("us_treasury_10y")
///   - value: 值 (万分比)
///   - source: 数据源标识 ("federal_reserve")
///   - confidence: 置信度 0-100
/// 事件: DataSubmitted
fn submit_data(data_type: String, value: u64, source: String, confidence: u8);

/// 验证之前提交的数据准确性（事后验证）
/// 权限: 任何已授权提交者
/// 参数:
///   - data_type: 数据类型
///   - timestamp: 原始提交时间戳
///   - actual_value: 实际值
///   - tolerance_basis_points: 容差 (万分比, 100 = 1%)
/// 事件: DataVerified
fn verify_data(
    data_type: String,
    timestamp: u64,
    actual_value: u64,
    tolerance_basis_points: u64,
);
```

#### 查询函数

```rust
/// 获取最新数据
fn get_latest(data_type: String) -> Option<OracleRecord>;

/// 获取数据（带有效性检查）
/// 返回 None 如果数据已过期
fn get_valid_data(data_type: String) -> Option<OracleRecord>;

/// 获取源信誉
fn get_source_reputation(source: String) -> Option<SourceReputation>;

/// 获取历史数据
fn get_history(data_type: String, timestamp: u64) -> Option<OracleRecord>;
```

### 数据类型定义

| data_type | 含义 | 单位 | 示例值 |
|-----------|------|------|--------|
| `us_treasury_10y` | 美国 10 年期国债收益率 | 万分比 | 425 (4.25%) |
| `t_bill_3m` | 3 个月国库券收益率 | 万分比 | 520 (5.20%) |
| `t_bill_6m` | 6 个月国库券收益率 | 万分比 | 505 (5.05%) |
| `corp_bond_aaa` | AAA 级企业债收益率 | 万分比 | 480 (4.80%) |
| `real_estate_idx` | 房地产指数 | 万分比 | 10200 (102.00) |

### 信誉计算模型

```
reputation_score = (accurate_submissions / total_submissions) × 10000

示例:
  总提交: 100 次
  准确提交: 92 次
  信誉分: 9200 (92%)

权重:
  - 新代理初始信誉: 5000 (50%)
  - 每次准确提交: +权重
  - 每次不准确提交: -权重
  - 信誉分用于决策引擎评估数据可信度
```

### 事件定义

```rust
#[odra::event]
struct DataSubmitted {
    data_type: String,
    value: u64,
    source: String,
    submitter: Address,
    timestamp: u64,
    confidence: u8,
}

#[odra::event]
struct DataVerified {
    data_type: String,
    timestamp: u64,
    is_accurate: bool,
    verifier: Address,
}
```

---

## 三、AgentRegistry 合约

### 状态模型

```
AgentProfile {
    owner: Address              // 创建者
    name: String                // 代理名称
    strategy: String            // 策略描述
    total_rebalances: u32       // 总 rebalance 次数
    total_yield_generated: U256 // 总生成收益
    win_rate: u64               // 胜率 (万分比)
    reputation: u64             // 综合信誉分 0-10000
    created_at: u64             // 创建时间
    is_active: bool             // 是否活跃
}

OperationRecord {
    agent: Address              // 执行代理
    from_pool: u8               // 源池
    to_pool: u8                 // 目标池
    amount: U256                // 金额
    from_apy: u64               // 操作前源池 APY
    to_apy: u64                 // 操作前目标池 APY
    timestamp: u64              // 时间戳
    outcome: OperationOutcome   // 结果
}

OperationOutcome {
    Pending,                    // 待评估
    Profitable,                 // 收益更高
    Neutral,                    // 收益持平
    Loss,                       // 收益更低
}

FollowRelation {
    user: Address               // 跟投用户
    agent: Address              // 跟投代理
    pool_id: u8                 // 跟投池子
    amount: U256                // 跟投金额
    followed_at: u64            // 跟投时间
}
```

### 接口定义

#### 代理管理

```rust
/// 注册新代理
/// 参数:
///   - name: 代理名称 (非空)
///   - strategy: 策略描述
fn register_agent(name: String, strategy: String);

/// 停用代理
fn deactivate_agent();

/// 更新策略描述
fn update_strategy(strategy: String);
```

#### 操作记录

```rust
/// 记录一次 rebalance 操作
/// 权限: 已注册代理
/// 参数:
///   - from_pool: 源池 ID
///   - to_pool: 目标池 ID
///   - amount: 金额
///   - from_apy: 操作前源池 APY
///   - to_apy: 操作前目标池 APY
/// 返回: operation_id
/// 事件: OperationRecorded
fn record_operation(
    from_pool: u8,
    to_pool: u8,
    amount: U256,
    from_apy: u64,
    to_apy: u64,
) -> u64;

/// 更新操作结果（事后评估）
/// 参数:
///   - op_id: 操作 ID
///   - outcome: 结果 (Profitable/Neutral/Loss)
fn resolve_operation(op_id: u64, outcome: OperationOutcome);
```

#### 跟投机制

```rust
/// 跟投代理
/// 需要附带 CSPR 代币
/// 参数:
///   - agent: 代理地址
///   - pool_id: 跟投池子
fn follow_agent(agent: Address, pool_id: u8);

/// 取消跟投
fn unfollow_agent(agent: Address);
```

#### 查询函数

```rust
/// 查询代理档案
fn get_agent(agent: Address) -> Option<AgentProfile>;

/// 查询操作记录
fn get_operation(op_id: u64) -> Option<OperationRecord>;

/// 获取代理排行榜（按信誉排序）
fn get_leaderboard(top_n: u32) -> Vec<(Address, AgentProfile)>;

/// 查询用户的跟投列表
fn get_user_follows(user: Address) -> Vec<Address>;
```

### 信誉计算模型

```
reputation = win_rate_weight × 60% + volume_weight × 40%

win_rate_weight = (profitable_ops / total_ops) × 10000
volume_weight = min(total_ops × 100, 4000)

示例:
  代理 A: 80 次操作, 60 次 Profitable
  win_rate = 60/80 = 7500 (75%)
  volume = min(80 × 100, 4000) = 4000
  reputation = 7500 × 0.6 + 4000 × 0.4 = 4500 + 1600 = 6100

  代理 B: 20 次操作, 18 次 Profitable
  win_rate = 18/20 = 9000 (90%)
  volume = min(20 × 100, 4000) = 2000
  reputation = 9000 × 0.6 + 2000 × 0.4 = 5400 + 800 = 6200
```

### 事件定义

```rust
#[odra::event]
struct AgentRegistered {
    agent: Address,
    name: String,
    strategy: String,
    timestamp: u64,
}

#[odra::event]
struct OperationRecorded {
    op_id: u64,
    agent: Address,
    from_pool: u8,
    to_pool: u8,
    amount: U256,
    timestamp: u64,
}

#[odra::event]
struct FollowCreated {
    user: Address,
    agent: Address,
    pool_id: u8,
    amount: U256,
}
```

---

## 四、合约间交互

```
用户 deposit/withdraw ──▶ YieldPool
                              │
代理调用 rebalance ─────────▶ YieldPool
                              │
                              ▼
                         RebalanceEvent
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
              AgentRegistry         RwaOracle
              record_operation()    submit_data()
                    │                   │
                    ▼                   ▼
              OperationRecorded     DataSubmitted
```

## 五、部署顺序

```
1. 部署 AgentRegistry
   └─ 返回 registry_hash

2. 部署 RwaOracle
   └─ 返回 oracle_hash
   └─ 调用 authorize_submitter(registry_hash) 授权代理

3. 部署 YieldPool
   └─ 返回 yield_pool_hash
   └─ 调用 create_pool(300)  // Stable Pool, 3% APY
   └─ 调用 create_pool(600)  // Growth Pool, 6% APY
   └─ 调用 create_pool(900)  // High Yield Pool, 9% APY
   └─ 调用 authorize_agent(agent_address) 授权代理

4. 注册代理身份
   └─ 调用 AgentRegistry.register_agent("YieldOptimizer-v1", "...")
```

## 六、Gas 估算

| 操作 | 预估 Gas | 预估费用 (CSPR) |
|------|----------|-----------------|
| create_pool | 50,000 | 0.005 |
| deposit | 80,000 | 0.008 |
| withdraw | 90,000 | 0.009 |
| rebalance | 120,000 | 0.012 |
| submit_data | 60,000 | 0.006 |
| register_agent | 70,000 | 0.007 |
| record_operation | 50,000 | 0.005 |
| verify_data | 40,000 | 0.004 |

代理每轮决策周期预估 gas 消耗：

```
读取 (query): 免费
提交 Oracle 数据: 0.006 CSPR
执行 rebalance: 0.012 CSPR
记录操作: 0.005 CSPR
─────────────────────
总计: ~0.023 CSPR / 轮 (约 $0.001)
```
