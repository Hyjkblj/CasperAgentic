use odra::prelude::*;

/// A single oracle data record.
#[odra::odra_type]
pub struct OracleRecord {
    pub data_type: String,
    pub value: u64,
    pub source: String,
    pub submitter: Address,
    pub timestamp: u64,
    pub confidence: u8,
}

/// Reputation tracked per data source.
#[odra::odra_type]
pub struct SourceReputation {
    pub total_submissions: u32,
    pub accurate_submissions: u32,
    pub reputation_score: u64,
    pub last_submission: u64,
}

#[odra::event]
pub struct DataSubmitted {
    pub data_type: String,
    pub value: u64,
    pub source: String,
    pub submitter: Address,
    pub timestamp: u64,
    pub confidence: u8,
}

#[odra::event]
pub struct DataVerified {
    pub data_type: String,
    pub timestamp: u64,
    pub is_accurate: bool,
    pub verifier: Address,
}

#[odra::module]
pub struct RwaOracle {
    latest_data: Mapping<String, OracleRecord>,
    history: Mapping<(String, u64), OracleRecord>,
    source_reputation: Mapping<String, SourceReputation>,
    authorized_submitters: Mapping<Address, bool>,
    admin: Var<Address>,
    validity_window: Var<u64>,
}

#[odra::module]
impl RwaOracle {
    #[odra(init)]
    pub fn init(&mut self) {
        self.admin.set(self.env().caller());
        self.validity_window.set(3600);
    }

    // ─── Admin ───

    pub fn authorize_submitter(&mut self, agent: Address) {
        self.assert_admin();
        self.authorized_submitters.set(&agent, true);
    }

    pub fn set_validity_window(&mut self, seconds: u64) {
        self.assert_admin();
        self.validity_window.set(seconds);
    }

    // ─── Data Operations ───

    pub fn submit_data(
        &mut self,
        data_type: String,
        value: u64,
        source: String,
        confidence: u8,
    ) {
        let caller = self.env().caller();
        assert!(
            self.authorized_submitters.get(&caller).unwrap_or(false),
            "Unauthorized"
        );
        assert!(confidence <= 100, "Invalid confidence");
        assert!(value > 0, "Invalid value");

        let timestamp = self.env().get_block_time();
        let record = OracleRecord {
            data_type: data_type.clone(),
            value,
            source: source.clone(),
            submitter: caller,
            timestamp,
            confidence,
        };

        self.latest_data.set(&data_type, record.clone());
        self.history.set(&(data_type.clone(), timestamp), record.clone());

        // Update source reputation
        let mut rep = self.source_reputation.get(&source).unwrap_or(SourceReputation {
            total_submissions: 0,
            accurate_submissions: 0,
            reputation_score: 5000,
            last_submission: 0,
        });
        rep.total_submissions += 1;
        rep.last_submission = timestamp;
        self.source_reputation.set(&source, rep);

        self.env().emit_event(DataSubmitted {
            data_type,
            value,
            source,
            submitter: caller,
            timestamp,
            confidence,
        });
    }

    pub fn verify_data(
        &mut self,
        data_type: String,
        timestamp: u64,
        actual_value: u64,
        tolerance_basis_points: u64,
    ) {
        let record = self.history.get(&(data_type.clone(), timestamp)).expect("Record not found");

        let diff = if record.value > actual_value {
            record.value - actual_value
        } else {
            actual_value - record.value
        };
        let tolerance = record.value * tolerance_basis_points / 10000;
        let is_accurate = diff <= tolerance;

        if is_accurate {
            let mut rep = self.source_reputation.get(&record.source).unwrap();
            rep.accurate_submissions += 1;
            rep.reputation_score =
                (rep.accurate_submissions as u64 * 10000) / rep.total_submissions as u64;
            self.source_reputation.set(&record.source, rep);
        }

        self.env().emit_event(DataVerified {
            data_type,
            timestamp,
            is_accurate,
            verifier: self.env().caller(),
        });
    }

    // ─── Queries ───

    pub fn get_latest(&self, data_type: String) -> Option<OracleRecord> {
        self.latest_data.get(&data_type)
    }

    pub fn get_valid_data(&self, data_type: String) -> Option<OracleRecord> {
        self.latest_data.get(&data_type).and_then(|record| {
            let now = self.env().get_block_time();
            if now - record.timestamp <= self.validity_window.get_or_default() {
                Some(record)
            } else {
                None
            }
        })
    }

    pub fn get_source_reputation(&self, source: String) -> Option<SourceReputation> {
        self.source_reputation.get(&source)
    }

    pub fn get_history(&self, data_type: String, timestamp: u64) -> Option<OracleRecord> {
        self.history.get(&(data_type, timestamp))
    }

    fn assert_admin(&self) {
        assert!(self.env().caller() == self.admin.get().expect("Admin not set"), "Admin only");
    }
}
