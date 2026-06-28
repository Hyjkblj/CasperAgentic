use odra::casper_types::U512;
use odra::prelude::*;

/// Agent profile stored on-chain.
#[odra::odra_type]
pub struct AgentProfile {
    pub owner: Address,
    pub name: String,
    pub strategy: String,
    pub total_rebalances: u32,
    pub total_yield_generated: U512,
    pub win_rate: u64,
    pub reputation: u64,
    pub created_at: u64,
    pub is_active: bool,
}

/// Outcome of a rebalance operation.
#[odra::odra_type]
pub enum OperationOutcome {
    Pending,
    Profitable,
    Neutral,
    Loss,
}

/// A recorded rebalance operation.
#[odra::odra_type]
pub struct OperationRecord {
    pub agent: Address,
    pub from_pool: u8,
    pub to_pool: u8,
    pub amount: U512,
    pub from_apy: u64,
    pub to_apy: u64,
    pub timestamp: u64,
    pub outcome: OperationOutcome,
}

/// A user follow relationship.
#[odra::odra_type]
pub struct FollowRelation {
    pub user: Address,
    pub agent: Address,
    pub pool_id: u8,
    pub amount: U512,
    pub followed_at: u64,
}

#[odra::event]
pub struct AgentRegistered {
    pub agent: Address,
    pub name: String,
    pub timestamp: u64,
}

#[odra::event]
pub struct OperationRecorded {
    pub op_id: u64,
    pub agent: Address,
    pub from_pool: u8,
    pub to_pool: u8,
    pub amount: U512,
}

#[odra::event]
pub struct FollowCreated {
    pub user: Address,
    pub agent: Address,
    pub pool_id: u8,
    pub amount: U512,
}

#[odra::module]
pub struct AgentRegistry {
    agents: Mapping<Address, AgentProfile>,
    operations: Mapping<u64, OperationRecord>,
    operation_count: Var<u64>,
    follows: Mapping<(Address, Address), FollowRelation>,
    user_follows: Mapping<Address, Vec<Address>>,
}

#[odra::module]
impl AgentRegistry {
    #[odra(init)]
    pub fn init(&mut self) {
        self.operation_count.set(0);
    }

    // ─── Agent Management ───

    pub fn register_agent(&mut self, name: String, strategy: String) {
        let caller = self.env().caller();
        assert!(self.agents.get(&caller).is_none(), "Already registered");
        assert!(!name.is_empty(), "Name required");

        self.agents.set(
            &caller,
            AgentProfile {
                owner: caller,
                name: name.clone(),
                strategy,
                total_rebalances: 0,
                total_yield_generated: U512::zero(),
                win_rate: 5000,
                reputation: 5000,
                created_at: self.env().get_block_time(),
                is_active: true,
            },
        );

        self.env().emit_event(AgentRegistered {
            agent: caller,
            name,
            timestamp: self.env().get_block_time(),
        });
    }

    pub fn deactivate_agent(&mut self) {
        let caller = self.env().caller();
        let mut agent = self.agents.get(&caller).expect("Not registered");
        agent.is_active = false;
        self.agents.set(&caller, agent);
    }

    pub fn update_strategy(&mut self, strategy: String) {
        let caller = self.env().caller();
        let mut agent = self.agents.get(&caller).expect("Not registered");
        agent.strategy = strategy;
        self.agents.set(&caller, agent);
    }

    // ─── Operation Recording ───

    pub fn record_operation(
        &mut self,
        from_pool: u8,
        to_pool: u8,
        amount: U512,
        from_apy: u64,
        to_apy: u64,
    ) -> u64 {
        let caller = self.env().caller();
        let mut agent = self.agents.get(&caller).expect("Not registered");
        assert!(agent.is_active, "Agent not active");

        let op_id = self.operation_count.get_or_default();
        let outcome = if to_apy > from_apy {
            OperationOutcome::Profitable
        } else if to_apy == from_apy {
            OperationOutcome::Neutral
        } else {
            OperationOutcome::Loss
        };

        self.operations.set(
            &op_id,
            OperationRecord {
                agent: caller,
                from_pool,
                to_pool,
                amount,
                from_apy,
                to_apy,
                timestamp: self.env().get_block_time(),
                outcome,
            },
        );

        agent.total_rebalances += 1;
        self.agents.set(&caller, agent);
        self.operation_count.set(op_id + 1);

        self.env().emit_event(OperationRecorded {
            op_id,
            agent: caller,
            from_pool,
            to_pool,
            amount,
        });

        op_id
    }

    pub fn resolve_operation(&mut self, op_id: u64, outcome: OperationOutcome) {
        let mut op = self.operations.get(&op_id).expect("Op not found");
        let agent_addr = op.agent;
        op.outcome = outcome;
        self.operations.set(&op_id, op);

        let mut agent = self.agents.get(&agent_addr).unwrap();
        agent.reputation = self.calculate_reputation(&agent);
        self.agents.set(&agent_addr, agent);
    }

    // ─── Follow ───

    pub fn follow_agent(&mut self, agent: Address, pool_id: u8) {
        let caller = self.env().caller();
        assert!(self.agents.get(&agent).is_some(), "Agent not found");
        assert!(self.follows.get(&(caller, agent)).is_none(), "Already following");

        let amount = self.env().attached_value();
        assert!(amount > U512::zero(), "Must attach tokens");

        self.follows.set(
            &(caller, agent),
            FollowRelation {
                user: caller,
                agent,
                pool_id,
                amount,
                followed_at: self.env().get_block_time(),
            },
        );

        let mut list = self.user_follows.get(&caller).unwrap_or_default();
        list.push(agent);
        self.user_follows.set(&caller, list);

        self.env().emit_event(FollowCreated {
            user: caller,
            agent,
            pool_id,
            amount,
        });
    }

    pub fn unfollow_agent(&mut self, agent: Address) {
        let caller = self.env().caller();
        assert!(self.follows.get(&(caller, agent)).is_some(), "Not following");
        self.follows.set(&(caller, agent), FollowRelation {
            user: caller,
            agent,
            pool_id: 0,
            amount: U512::zero(),
            followed_at: 0,
        });
    }

    // ─── Queries ───

    pub fn get_agent(&self, agent: Address) -> Option<AgentProfile> {
        self.agents.get(&agent)
    }

    pub fn get_operation(&self, op_id: u64) -> Option<OperationRecord> {
        self.operations.get(&op_id)
    }

    pub fn get_operation_count(&self) -> u64 {
        self.operation_count.get_or_default()
    }

    pub fn get_follow(&self, user: Address, agent: Address) -> Option<FollowRelation> {
        self.follows.get(&(user, agent))
    }

    pub fn get_user_follows(&self, user: Address) -> Vec<Address> {
        self.user_follows.get(&user).unwrap_or_default()
    }

    // ─── Internal ───

    fn calculate_reputation(&self, agent: &AgentProfile) -> u64 {
        if agent.total_rebalances == 0 {
            return 5000;
        }
        let win_weight = agent.win_rate * 60 / 100;
        let volume_weight = core::cmp::min(agent.total_rebalances as u64 * 100, 4000);
        win_weight + volume_weight
    }
}
