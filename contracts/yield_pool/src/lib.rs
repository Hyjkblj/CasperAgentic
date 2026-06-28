use odra::casper_types::U512;
use odra::prelude::*;

/// Pool state stored on-chain.
#[odra::odra_type]
pub struct PoolState {
    pub total_deposited: U512,
    pub apy_basis_points: u64,
    pub last_rebalance: u64,
    pub is_active: bool,
}

/// Per-user position in a pool.
#[odra::odra_type]
pub struct UserPosition {
    pub deposited: U512,
    pub entry_apy: u64,
    pub entry_time: u64,
    pub accumulated_yield: U512,
}

/// Emitted when funds move between pools.
#[odra::event]
pub struct RebalanceEvent {
    pub from_pool: u8,
    pub to_pool: u8,
    pub amount: U512,
    pub agent: Address,
    pub timestamp: u64,
}

/// Emitted on user deposit.
#[odra::event]
pub struct DepositEvent {
    pub pool_id: u8,
    pub user: Address,
    pub amount: U512,
}

/// Emitted on user withdrawal.
#[odra::event]
pub struct WithdrawEvent {
    pub pool_id: u8,
    pub user: Address,
    pub amount: U512,
    pub yield_claimed: U512,
}

#[odra::module]
pub struct YieldPool {
    pools: Mapping<u8, PoolState>,
    positions: Mapping<(u8, Address), UserPosition>,
    pool_count: Var<u8>,
    admin: Var<Address>,
    authorized_agents: Mapping<Address, bool>,
}

#[odra::module]
impl YieldPool {
    #[odra(init)]
    pub fn init(&mut self) {
        self.admin.set(self.env().caller());
        self.pool_count.set(0);
    }

    // ─── Admin ───

    pub fn create_pool(&mut self, apy_basis_points: u64) -> u8 {
        self.assert_admin();
        assert!(apy_basis_points > 0 && apy_basis_points <= 5000, "APY 1-5000 bps");
        let id = self.pool_count.get_or_default();
        self.pools.set(
            &id,
            PoolState {
                total_deposited: U512::zero(),
                apy_basis_points,
                last_rebalance: self.env().get_block_time(),
                is_active: true,
            },
        );
        self.pool_count.set(id + 1);
        id
    }

    pub fn update_pool_apy(&mut self, pool_id: u8, new_apy: u64) {
        self.assert_admin();
        assert!(new_apy > 0 && new_apy <= 5000, "APY 1-5000 bps");
        let mut pool = self.pools.get(&pool_id).expect("Pool not found");
        assert!(pool.is_active, "Pool not active");
        pool.apy_basis_points = new_apy;
        self.pools.set(&pool_id, pool);
    }

    pub fn authorize_agent(&mut self, agent: Address) {
        self.assert_admin();
        self.authorized_agents.set(&agent, true);
    }

    pub fn set_pool_active(&mut self, pool_id: u8, active: bool) {
        self.assert_admin();
        let mut pool = self.pools.get(&pool_id).expect("Pool not found");
        pool.is_active = active;
        self.pools.set(&pool_id, pool);
    }

    // ─── User ───

    pub fn deposit(&mut self, pool_id: u8) {
        let amount = self.env().attached_value();
        assert!(amount > U512::zero(), "Must attach tokens");
        let pool = self.pools.get(&pool_id).expect("Pool not found");
        assert!(pool.is_active, "Pool not active");

        let caller = self.env().caller();
        let mut pos = self.positions.get(&(pool_id, caller)).unwrap_or(UserPosition {
            deposited: U512::zero(),
            entry_apy: pool.apy_basis_points,
            entry_time: self.env().get_block_time(),
            accumulated_yield: U512::zero(),
        });
        self.settle_yield(&mut pos, pool.apy_basis_points);
        pos.deposited += amount;
        pos.entry_apy = pool.apy_basis_points;
        self.positions.set(&(pool_id, caller), pos);

        let mut pool = self.pools.get(&pool_id).expect("Pool not found");
        pool.total_deposited += amount;
        self.pools.set(&pool_id, pool);

        self.env().emit_event(DepositEvent { pool_id, user: caller, amount });
    }

    pub fn withdraw(&mut self, pool_id: u8, amount: U512) {
        let caller = self.env().caller();
        let mut pos = self.positions.get(&(pool_id, caller)).expect("No position");
        assert!(pos.deposited >= amount, "Insufficient balance");

        let pool = self.pools.get(&pool_id).expect("Pool not found");
        self.settle_yield(&mut pos, pool.apy_basis_points);
        pos.deposited -= amount;
        let yield_amount = pos.accumulated_yield;
        pos.accumulated_yield = U512::zero();
        self.positions.set(&(pool_id, caller), pos);

        let mut pool = self.pools.get(&pool_id).expect("Pool not found");
        pool.total_deposited -= amount;
        self.pools.set(&pool_id, pool);

        self.env().transfer_tokens(&caller, &(amount + yield_amount));
        self.env().emit_event(WithdrawEvent {
            pool_id,
            user: caller,
            amount,
            yield_claimed: yield_amount,
        });
    }

    pub fn claim_yield(&mut self, pool_id: u8) {
        let caller = self.env().caller();
        let mut pos = self.positions.get(&(pool_id, caller)).expect("No position");
        let pool = self.pools.get(&pool_id).expect("Pool not found");
        self.settle_yield(&mut pos, pool.apy_basis_points);

        let yield_amount = pos.accumulated_yield;
        assert!(yield_amount > U512::zero(), "No yield to claim");
        pos.accumulated_yield = U512::zero();
        self.positions.set(&(pool_id, caller), pos);

        self.env().transfer_tokens(&caller, &yield_amount);
    }

    // ─── Agent ───

    pub fn rebalance(&mut self, from_pool: u8, to_pool: u8, amount: U512) {
        assert!(
            self.authorized_agents.get(&self.env().caller()).unwrap_or(false),
            "Unauthorized"
        );
        let from = self.pools.get(&from_pool).expect("From pool not found");
        let to = self.pools.get(&to_pool).expect("To pool not found");
        assert!(from.is_active && to.is_active, "Pool not active");
        assert!(from.total_deposited >= amount, "Insufficient pool balance");

        let mut from_state = from;
        let mut to_state = to;
        from_state.total_deposited -= amount;
        to_state.total_deposited += amount;
        let now = self.env().get_block_time();
        from_state.last_rebalance = now;
        to_state.last_rebalance = now;
        self.pools.set(&from_pool, from_state);
        self.pools.set(&to_pool, to_state);

        self.env().emit_event(RebalanceEvent {
            from_pool,
            to_pool,
            amount,
            agent: self.env().caller(),
            timestamp: now,
        });
    }

    // ─── Queries ───

    pub fn get_pool(&self, pool_id: u8) -> Option<PoolState> {
        self.pools.get(&pool_id)
    }

    pub fn get_position(&self, pool_id: u8, user: Address) -> UserPosition {
        self.positions.get(&(pool_id, user)).unwrap_or(UserPosition {
            deposited: U512::zero(),
            entry_apy: 0,
            entry_time: 0,
            accumulated_yield: U512::zero(),
        })
    }

    pub fn get_pool_count(&self) -> u8 {
        self.pool_count.get_or_default()
    }

    pub fn get_all_pool_apys(&self) -> Vec<(u8, u64)> {
        let count = self.pool_count.get_or_default();
        let mut result = Vec::new();
        for i in 0..count {
            if let Some(pool) = self.pools.get(&i) {
                if pool.is_active {
                    result.push((i, pool.apy_basis_points));
                }
            }
        }
        result
    }

    // ─── Internal ───

    fn settle_yield(&self, pos: &mut UserPosition, current_apy: u64) {
        let elapsed = self.env().get_block_time() - pos.entry_time;
        if elapsed > 0 && pos.deposited > U512::zero() {
            let seconds_in_year = U512::from(365u64 * 24 * 3600);
            let yield_amount = pos.deposited
                * U512::from(current_apy)
                * U512::from(elapsed)
                / (seconds_in_year * U512::from(10_000u64));
            pos.accumulated_yield += yield_amount;
            pos.entry_time = self.env().get_block_time();
        }
    }

    fn assert_admin(&self) {
        assert!(self.env().caller() == self.admin.get().expect("Admin not set"), "Admin only");
    }
}
