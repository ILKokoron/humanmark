//! Humanmark: human-made art certification on NEAR (testnet).
//!
//! An artist submits an image hash plus an evidence bundle hash plus a
//! list of claimed evidence items, and locks an examination fee. A fixed
//! set of 5 examiner agents votes commit-reveal on which claimed items
//! each examiner verified. An item counts only if at least 3 of the 5
//! examiners verify it. Verified items sum to points on two axes:
//!
//! - Human axis: passkey_attestation 5, aged_social_account 2,
//!   live_challenge 3.
//! - Process axis: continuous_timelapse 4, layered_source_file 2,
//!   live_redraw 3, progress_sketches 1.
//!
//! Pass means Human axis >= 5 AND Process axis >= 5. On pass the
//! contract mints a soulbound certificate NFT to the artist. The fee
//! splits equally among the examiners who revealed, pass or fail. If
//! no examiner revealed at all, the case fails and the full fee is
//! refunded to the artist.

use near_sdk::borsh::{self, BorshDeserialize, BorshSerialize};
use near_sdk::json_types::U128;
use near_sdk::serde::{Deserialize, Serialize};
use near_sdk::store::IterableMap;
use near_sdk::{env, near, AccountId, NearToken, PanicOnDefault, Promise};
use schemars::JsonSchema;

pub const REQUIRED_EXAMINERS: usize = 5;
pub const ITEM_VERIFY_THRESHOLD: usize = 3;
pub const AXIS_PASS_POINTS: u32 = 5;

// Fixed evidence points. Do not change without a spec change.
pub fn human_points_for(item: &str) -> u32 {
    match item {
        "passkey_attestation" => 5,
        "aged_social_account" => 2,
        "live_challenge" => 3,
        _ => 0,
    }
}

pub fn process_points_for(item: &str) -> u32 {
    match item {
        "continuous_timelapse" => 4,
        "layered_source_file" => 2,
        "live_redraw" => 3,
        "progress_sketches" => 1,
        _ => 0,
    }
}

pub fn is_known_item(item: &str) -> bool {
    human_points_for(item) > 0 || process_points_for(item) > 0
}

#[derive(BorshSerialize, BorshDeserialize, Clone, Copy, PartialEq, Debug)]
pub enum Status {
    Open,
    Passed,
    Failed,
}

pub fn status_str(s: Status) -> &'static str {
    match s {
        Status::Open => "open",
        Status::Passed => "passed",
        Status::Failed => "failed",
    }
}

#[derive(BorshSerialize, BorshDeserialize, Clone)]
pub struct Reveal {
    pub examiner: AccountId,
    pub verified_items: Vec<String>,
    pub report_hash: String,
}

#[derive(BorshSerialize, BorshDeserialize)]
pub struct Case {
    pub numeric_id: u64,
    pub artist: AccountId,
    pub image_hash: String,
    pub bundle_hash: String,
    pub fee: u128,
    pub claimed_items: Vec<String>,
    pub status: Status,
    pub commits: Vec<(AccountId, String)>,
    pub reveals: Vec<Reveal>,
    pub human_points: u32,
    pub process_points: u32,
    pub level: Option<u32>,
    pub cert_token_id: Option<String>,
    pub fee_settled: bool,
    pub created_ns: u64,
    pub judging_window_secs: u64,
}

#[derive(BorshSerialize, BorshDeserialize, Clone)]
pub struct Cert {
    pub owner: AccountId,
    pub case_id: String,
    pub level: u32,
    pub human_points: u32,
    pub process_points: u32,
    pub image_hash: String,
    pub bundle_hash: String,
    pub report_hashes: Vec<String>,
    pub issued_ns: u64,
}

#[derive(Serialize, Deserialize, JsonSchema)]
#[serde(crate = "near_sdk::serde")]
pub struct RevealView {
    pub examiner: String,
    pub verified_items: Vec<String>,
    pub report_hash: String,
}

#[derive(Serialize, Deserialize, JsonSchema)]
#[serde(crate = "near_sdk::serde")]
pub struct CaseView {
    pub case_id: String,
    pub artist: String,
    pub image_hash: String,
    pub bundle_hash: String,
    pub fee: String,
    pub claimed_items: Vec<String>,
    pub status: String,
    pub commits_count: u64,
    pub reveals: Vec<RevealView>,
    pub human_points: u32,
    pub process_points: u32,
    pub level: Option<u32>,
    pub cert_token_id: Option<String>,
    pub fee_settled: bool,
    pub created_ns: u64,
    pub judging_window_secs: u64,
}

#[derive(Serialize, Deserialize, JsonSchema)]
#[serde(crate = "near_sdk::serde")]
pub struct TokenMetadataView {
    pub title: Option<String>,
    pub description: Option<String>,
    pub issued_at: Option<String>,
    pub extra: Option<String>,
}

#[derive(Serialize, Deserialize, JsonSchema)]
#[serde(crate = "near_sdk::serde")]
pub struct JsonToken {
    pub token_id: String,
    pub owner_id: String,
    pub metadata: TokenMetadataView,
}

#[derive(Serialize, Deserialize, JsonSchema)]
#[serde(crate = "near_sdk::serde")]
pub struct NftMetadataView {
    pub spec: String,
    pub name: String,
    pub symbol: String,
    pub icon: Option<String>,
    pub base_uri: Option<String>,
    pub reference: Option<String>,
    pub reference_hash: Option<String>,
}

/// Commitment for a reveal: sha256 hex of the string built from the
/// sorted verified_items joined with ",", then "|", then report_hash,
/// then "|", then salt. Sorting happens here so ordering never matters.
pub fn compute_commitment(verified_items: Vec<String>, report_hash: &str, salt: &str) -> String {
    let mut sorted = verified_items;
    sorted.sort();
    let raw = format!("{}|{}|{}", sorted.join(","), report_hash, salt);
    let hash = env::sha256(raw.as_bytes());
    let mut out = String::with_capacity(hash.len() * 2);
    for b in hash.iter() {
        out.push_str(&format!("{:02x}", b));
    }
    out
}

#[near(contract_state)]
#[derive(PanicOnDefault)]
pub struct Contract {
    pub owner: AccountId,
    pub examiners: Vec<AccountId>,
    pub min_fee: u128,
    pub cases: IterableMap<String, Case>,
    pub certs: IterableMap<String, Cert>,
    pub next_id: u64,
    pub live_supply: u64,
}

#[near]
impl Contract {
    #[init]
    pub fn new(owner: AccountId, examiners: Vec<AccountId>, min_fee: U128) -> Self {
        assert!(
            examiners.len() == REQUIRED_EXAMINERS,
            "exactly 5 examiners are required"
        );
        Self {
            owner,
            examiners,
            min_fee: min_fee.into(),
            cases: IterableMap::new(b"c"),
            certs: IterableMap::new(b"t"),
            next_id: 0,
            live_supply: 0,
        }
    }

    pub fn examiners(&self) -> Vec<String> {
        self.examiners.iter().map(|e| e.to_string()).collect()
    }

    pub fn min_fee(&self) -> String {
        self.min_fee.to_string()
    }

    // ---------------- case lifecycle ----------------

    #[payable]
    pub fn submit_case(
        &mut self,
        image_hash: String,
        bundle_hash: String,
        claimed_items: Vec<String>,
        judging_window_secs: u64,
    ) -> String {
        assert!(judging_window_secs > 0, "judging window must be positive");
        assert!(!claimed_items.is_empty(), "claimed_items must not be empty");
        for item in claimed_items.iter() {
            assert!(is_known_item(item), "unknown evidence item: {}", item);
        }
        let fee = env::attached_deposit().as_yoctonear();
        assert!(fee >= self.min_fee, "attached deposit below min_fee");
        let case_id = format!("case-{}", self.next_id);
        let numeric_id = self.next_id;
        self.next_id += 1;
        let case = Case {
            numeric_id,
            artist: env::predecessor_account_id(),
            image_hash,
            bundle_hash,
            fee,
            claimed_items,
            status: Status::Open,
            commits: Vec::new(),
            reveals: Vec::new(),
            human_points: 0,
            process_points: 0,
            level: None,
            cert_token_id: None,
            fee_settled: false,
            created_ns: env::block_timestamp(),
            judging_window_secs,
        };
        env::log_str(&format!("CASE_SUBMITTED {} by {}", case_id, case.artist));
        self.cases.insert(case_id.clone(), case);
        case_id
    }

    pub fn commit_vote(&mut self, case_id: String, commitment: String) {
        let caller = env::predecessor_account_id();
        assert!(self.examiners.contains(&caller), "only examiners may vote");
        let case = self.cases.get_mut(&case_id).expect("case not found");
        assert!(matches!(case.status, Status::Open), "case is not open");
        assert!(
            !case.commits.iter().any(|(e, _)| *e == caller),
            "already committed"
        );
        case.commits.push((caller, commitment));
    }

    pub fn reveal_vote(
        &mut self,
        case_id: String,
        verified_items: Vec<String>,
        report_hash: String,
        salt: String,
    ) {
        let caller = env::predecessor_account_id();
        assert!(self.examiners.contains(&caller), "only examiners may vote");
        let case = self.cases.get_mut(&case_id).expect("case not found");
        assert!(matches!(case.status, Status::Open), "case is not open");
        for item in verified_items.iter() {
            assert!(
                case.claimed_items.contains(item),
                "verified item not in claimed_items: {}",
                item
            );
        }
        let (_, commitment) = case
            .commits
            .iter()
            .find(|(e, _)| *e == caller)
            .expect("no commitment found for this examiner")
            .clone();
        assert_eq!(
            commitment,
            compute_commitment(verified_items.clone(), &report_hash, &salt),
            "reveal does not match commitment"
        );
        assert!(
            !case.reveals.iter().any(|r| r.examiner == caller),
            "already revealed"
        );
        case.reveals.push(Reveal {
            examiner: caller,
            verified_items,
            report_hash,
        });
    }

    pub fn finalize(&mut self, case_id: String) {
        let (status, payouts, refund, new_cert) = {
            let case = self.cases.get_mut(&case_id).expect("case not found");
            assert!(matches!(case.status, Status::Open), "case is not open");
            let all_revealed = case.reveals.len() >= self.examiners.len();
            let window_over = env::block_timestamp()
                > case.created_ns + case.judging_window_secs * 1_000_000_000;
            assert!(
                all_revealed || window_over,
                "judging is still in progress"
            );
            if case.reveals.is_empty() {
                // No examiner did any work: verdict fails, fee goes back.
                case.status = Status::Failed;
                case.fee_settled = true;
                (
                    Status::Failed,
                    Vec::new(),
                    Some((case.artist.clone(), case.fee)),
                    None,
                )
            } else {
                let mut human_points: u32 = 0;
                let mut process_points: u32 = 0;
                for item in case.claimed_items.iter() {
                    let count = case
                        .reveals
                        .iter()
                        .filter(|r| r.verified_items.contains(item))
                        .count();
                    if count >= ITEM_VERIFY_THRESHOLD {
                        human_points += human_points_for(item);
                        process_points += process_points_for(item);
                    }
                }
                let passed =
                    human_points >= AXIS_PASS_POINTS && process_points >= AXIS_PASS_POINTS;
                case.human_points = human_points;
                case.process_points = process_points;
                let share = case.fee / case.reveals.len() as u128;
                let mut payouts: Vec<(AccountId, u128)> = case
                    .reveals
                    .iter()
                    .map(|r| (r.examiner.clone(), share))
                    .collect();
                let remainder = case.fee - share * case.reveals.len() as u128;
                if remainder > 0 {
                    payouts[0].1 += remainder;
                }
                case.fee_settled = true;
                if passed {
                    let total = human_points + process_points;
                    let level = ((10 * total + 10) / 20).clamp(1, 10);
                    let cert_token_id = format!("cert-{}", case.numeric_id);
                    case.level = Some(level);
                    case.cert_token_id = Some(cert_token_id.clone());
                    case.status = Status::Passed;
                    let cert = Cert {
                        owner: case.artist.clone(),
                        case_id: case_id.clone(),
                        level,
                        human_points,
                        process_points,
                        image_hash: case.image_hash.clone(),
                        bundle_hash: case.bundle_hash.clone(),
                        report_hashes: case
                            .reveals
                            .iter()
                            .map(|r| r.report_hash.clone())
                            .collect(),
                        issued_ns: env::block_timestamp(),
                    };
                    (Status::Passed, payouts, None, Some((cert_token_id, cert)))
                } else {
                    case.status = Status::Failed;
                    (Status::Failed, payouts, None, None)
                }
            }
        };
        if let Some((cert_token_id, cert)) = new_cert {
            self.certs.insert(cert_token_id, cert);
            self.live_supply += 1;
        }
        for (examiner, amount) in payouts {
            if amount > 0 {
                Promise::new(examiner).transfer(NearToken::from_yoctonear(amount));
            }
        }
        if let Some((artist, amount)) = refund {
            if amount > 0 {
                Promise::new(artist).transfer(NearToken::from_yoctonear(amount));
            }
        }
        env::log_str(&format!(
            "CASE_FINALIZED {} -> {}",
            case_id,
            status_str(status)
        ));
    }

    // ---------------- views ----------------

    fn case_view(&self, case_id: &String, c: &Case) -> CaseView {
        CaseView {
            case_id: case_id.clone(),
            artist: c.artist.to_string(),
            image_hash: c.image_hash.clone(),
            bundle_hash: c.bundle_hash.clone(),
            fee: c.fee.to_string(),
            claimed_items: c.claimed_items.clone(),
            status: status_str(c.status).to_string(),
            commits_count: c.commits.len() as u64,
            reveals: c
                .reveals
                .iter()
                .map(|r| RevealView {
                    examiner: r.examiner.to_string(),
                    verified_items: r.verified_items.clone(),
                    report_hash: r.report_hash.clone(),
                })
                .collect(),
            human_points: c.human_points,
            process_points: c.process_points,
            level: c.level,
            cert_token_id: c.cert_token_id.clone(),
            fee_settled: c.fee_settled,
            created_ns: c.created_ns,
            judging_window_secs: c.judging_window_secs,
        }
    }

    pub fn get_case(&self, case_id: String) -> Option<CaseView> {
        self.cases.get(&case_id).map(|c| self.case_view(&case_id, c))
    }

    pub fn get_cases(
        &self,
        from_index: Option<u64>,
        limit: Option<u64>,
    ) -> Vec<CaseView> {
        let start: u64 = from_index.unwrap_or(0);
        let limit: u64 = limit.unwrap_or(50);
        self.cases
            .iter()
            .skip(start as usize)
            .take(limit as usize)
            .map(|(id, c)| self.case_view(id, c))
            .collect()
    }

    pub fn nft_metadata(&self) -> NftMetadataView {
        NftMetadataView {
            spec: "nft-1.0.0".to_string(),
            name: "Humanmark Certificate".to_string(),
            symbol: "HMARK".to_string(),
            icon: None,
            base_uri: None,
            reference: None,
            reference_hash: None,
        }
    }

    fn token_view(&self, token_id: &String, cert: &Cert) -> JsonToken {
        let extra = near_sdk::serde_json::json!({
            "case_id": cert.case_id,
            "image_hash": cert.image_hash,
            "bundle_hash": cert.bundle_hash,
            "human_points": cert.human_points,
            "process_points": cert.process_points,
            "level": cert.level,
            "report_hashes": cert.report_hashes,
        })
        .to_string();
        JsonToken {
            token_id: token_id.clone(),
            owner_id: cert.owner.to_string(),
            metadata: TokenMetadataView {
                title: Some(format!("Humanmark Certificate {}", token_id)),
                description: Some(format!(
                    "Certified at level {} based on this evidence",
                    cert.level
                )),
                issued_at: Some(cert.issued_ns.to_string()),
                extra: Some(extra),
            },
        }
    }

    pub fn nft_token(&self, token_id: String) -> Option<JsonToken> {
        self.certs
            .get(&token_id)
            .map(|cert| self.token_view(&token_id, cert))
    }

    pub fn nft_total_supply(&self) -> U128 {
        U128(self.live_supply as u128)
    }

    pub fn nft_supply_for_owner(&self, account_id: AccountId) -> U128 {
        let count = self
            .certs
            .iter()
            .filter(|(_, cert)| cert.owner == account_id)
            .count();
        U128(count as u128)
    }

    pub fn nft_tokens_for_owner(
        &self,
        account_id: AccountId,
        from_index: Option<U128>,
        limit: Option<u64>,
    ) -> Vec<JsonToken> {
        let start: u128 = from_index.map(|i| i.into()).unwrap_or(0);
        let limit: u64 = limit.unwrap_or(50);
        self.certs
            .iter()
            .filter(|(_, cert)| cert.owner == account_id)
            .skip(start as usize)
            .take(limit as usize)
            .map(|(id, cert)| self.token_view(id, cert))
            .collect()
    }

    // ---------------- soulbound ----------------

    #[payable]
    pub fn nft_transfer(
        &mut self,
        receiver_id: AccountId,
        token_id: String,
        approval_id: Option<u64>,
        memo: Option<String>,
    ) {
        let _ = (receiver_id, token_id, approval_id, memo);
        assert_eq!(
            env::attached_deposit().as_yoctonear(),
            1,
            "Requires attached deposit of exactly 1 yoctoNEAR"
        );
        env::panic_str("Humanmark certificates are non-transferable");
    }

    #[payable]
    pub fn nft_transfer_call(
        &mut self,
        receiver_id: AccountId,
        token_id: String,
        approval_id: Option<u64>,
        memo: Option<String>,
        msg: String,
    ) {
        let _ = (receiver_id, token_id, approval_id, memo, msg);
        assert_eq!(
            env::attached_deposit().as_yoctonear(),
            1,
            "Requires attached deposit of exactly 1 yoctoNEAR"
        );
        env::panic_str("Humanmark certificates are non-transferable");
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use near_sdk::test_utils::{accounts, VMContextBuilder};
    use near_sdk::testing_env;

    const NEAR: u128 = 1_000_000_000_000_000_000_000_000;
    const MIN_FEE: u128 = 50_000_000_000_000_000_000_000; // 0.05 NEAR
    const SEC: u64 = 1_000_000_000;

    fn ctx(account: AccountId, deposit: u128, ts: u64) -> VMContextBuilder {
        let mut builder = VMContextBuilder::new();
        builder
            .current_account_id(accounts(0))
            .signer_account_id(account.clone())
            .predecessor_account_id(account)
            .attached_deposit(NearToken::from_yoctonear(deposit))
            .block_timestamp(ts);
        builder
    }

    // near_sdk test_utils accounts() only provides 6 accounts (indices
    // 0 to 5), so examiners 3 to 5, the artist and outsiders use
    // explicit test account ids instead of accounts(6) and beyond.
    fn acct(name: &str) -> AccountId {
        name.parse().unwrap()
    }

    fn examiners() -> Vec<AccountId> {
        vec![
            acct("examiner1.test"),
            acct("examiner2.test"),
            acct("examiner3.test"),
            acct("examiner4.test"),
            acct("examiner5.test"),
        ]
    }

    fn setup() -> Contract {
        testing_env!(ctx(accounts(0), 0, SEC).build());
        Contract::new(accounts(0), examiners(), U128(MIN_FEE))
    }

    fn artist() -> AccountId {
        acct("artist.test")
    }

    fn pass_items() -> Vec<String> {
        vec![
            "passkey_attestation".to_string(),
            "layered_source_file".to_string(),
            "live_redraw".to_string(),
        ]
    }

    fn submit(c: &mut Contract, claimed_items: Vec<String>) -> String {
        testing_env!(ctx(artist(), MIN_FEE, SEC).build());
        c.submit_case(
            "imagehash123".to_string(),
            "bundlehash456".to_string(),
            claimed_items,
            100,
        )
    }

    fn examiner_vote(
        c: &mut Contract,
        case_id: &String,
        examiner: AccountId,
        verified_items: Vec<String>,
    ) {
        let salt = format!("salt-{}", examiner);
        let report_hash = format!("report-{}", examiner);
        testing_env!(ctx(examiner.clone(), 0, 2 * SEC).build());
        c.commit_vote(
            case_id.clone(),
            compute_commitment(verified_items.clone(), &report_hash, &salt),
        );
        c.reveal_vote(case_id.clone(), verified_items, report_hash, salt);
    }

    fn all_verify(c: &mut Contract, case_id: &String, items_for: Vec<Vec<String>>) {
        assert_eq!(items_for.len(), 5);
        for (examiner, items) in examiners().into_iter().zip(items_for.into_iter()) {
            examiner_vote(c, case_id, examiner, items);
        }
    }

    #[test]
    #[should_panic(expected = "attached deposit below min_fee")]
    fn submit_below_min_fee_panics() {
        let mut c = setup();
        testing_env!(ctx(artist(), MIN_FEE - 1, SEC).build());
        c.submit_case(
            "img".to_string(),
            "bundle".to_string(),
            pass_items(),
            100,
        );
    }

    #[test]
    #[should_panic(expected = "unknown evidence item")]
    fn unknown_claimed_item_panics() {
        let mut c = setup();
        testing_env!(ctx(artist(), MIN_FEE, SEC).build());
        c.submit_case(
            "img".to_string(),
            "bundle".to_string(),
            vec!["passkey_attestation".to_string(), "made_up_item".to_string()],
            100,
        );
    }

    #[test]
    fn pass_flow_mints_cert() {
        let mut c = setup();
        let case_id = submit(&mut c, pass_items());
        assert_eq!(case_id, "case-0");
        let items = pass_items();
        all_verify(
            &mut c,
            &case_id,
            vec![
                items.clone(),
                items.clone(),
                items.clone(),
                Vec::new(),
                Vec::new(),
            ],
        );
        testing_env!(ctx(artist(), 0, 3 * SEC).build());
        c.finalize(case_id.clone());
        let v = c.get_case(case_id.clone()).expect("case view");
        assert_eq!(v.status, "passed");
        assert_eq!(v.human_points, 5);
        assert_eq!(v.process_points, 5);
        assert_eq!(v.level, Some(5));
        assert_eq!(v.cert_token_id, Some("cert-0".to_string()));
        assert!(v.fee_settled);
        assert_eq!(v.commits_count, 5);
        assert_eq!(v.reveals.len(), 5);
        let token = c.nft_token("cert-0".to_string()).expect("cert must exist");
        assert_eq!(token.owner_id, artist().to_string());
        assert_eq!(
            token.metadata.title,
            Some("Humanmark Certificate cert-0".to_string())
        );
        assert_eq!(
            token.metadata.description,
            Some("Certified at level 5 based on this evidence".to_string())
        );
        assert_eq!(c.nft_total_supply(), U128(1));
        assert_eq!(c.nft_supply_for_owner(artist()), U128(1));
        let owned = c.nft_tokens_for_owner(artist(), None, None);
        assert_eq!(owned.len(), 1);
        assert_eq!(owned[0].token_id, "cert-0");
        // A case id is not a cert token.
        assert!(c.nft_token(case_id).is_none());
        let _ = NEAR;
    }

    #[test]
    fn item_with_only_two_verifications_does_not_count() {
        let mut c = setup();
        let case_id = submit(&mut c, pass_items());
        let items = pass_items();
        all_verify(
            &mut c,
            &case_id,
            vec![
                items.clone(),
                items.clone(),
                Vec::new(),
                Vec::new(),
                Vec::new(),
            ],
        );
        testing_env!(ctx(artist(), 0, 3 * SEC).build());
        c.finalize(case_id.clone());
        let v = c.get_case(case_id).expect("case view");
        assert_eq!(v.status, "failed");
        assert_eq!(v.human_points, 0);
        assert_eq!(v.process_points, 0);
        assert_eq!(v.cert_token_id, None);
        assert!(c.nft_token("cert-0".to_string()).is_none());
        assert_eq!(c.nft_total_supply(), U128(0));
    }

    #[test]
    fn fail_flow_no_nft_fee_settled() {
        let mut c = setup();
        let case_id = submit(&mut c, pass_items());
        all_verify(
            &mut c,
            &case_id,
            vec![Vec::new(), Vec::new(), Vec::new(), Vec::new(), Vec::new()],
        );
        testing_env!(ctx(acct("examiner1.test"), 0, 3 * SEC).build());
        c.finalize(case_id.clone());
        let v = c.get_case(case_id).expect("case view");
        assert_eq!(v.status, "failed");
        assert!(v.fee_settled);
        assert_eq!(v.level, None);
        assert_eq!(c.nft_total_supply(), U128(0));
        assert_eq!(c.nft_supply_for_owner(artist()), U128(0));
    }

    #[test]
    #[should_panic(expected = "reveal does not match commitment")]
    fn reveal_wrong_salt_panics() {
        let mut c = setup();
        let case_id = submit(&mut c, pass_items());
        let examiner = acct("examiner1.test");
        testing_env!(ctx(examiner.clone(), 0, 2 * SEC).build());
        c.commit_vote(
            case_id.clone(),
            compute_commitment(pass_items(), "report-hash", "real-salt"),
        );
        c.reveal_vote(
            case_id,
            pass_items(),
            "report-hash".to_string(),
            "wrong-salt".to_string(),
        );
    }

    #[test]
    #[should_panic(expected = "only examiners may vote")]
    fn non_examiner_commit_panics() {
        let mut c = setup();
        let case_id = submit(&mut c, pass_items());
        testing_env!(ctx(acct("outsider.test"), 0, 2 * SEC).build());
        c.commit_vote(case_id, "whatever".to_string());
    }

    #[test]
    #[should_panic(expected = "judging is still in progress")]
    fn finalize_too_early_panics() {
        let mut c = setup();
        let case_id = submit(&mut c, pass_items());
        examiner_vote(&mut c, &case_id, acct("examiner1.test"), pass_items());
        testing_env!(ctx(artist(), 0, 3 * SEC).build());
        c.finalize(case_id);
    }

    #[test]
    #[should_panic(expected = "Humanmark certificates are non-transferable")]
    fn cert_transfer_panics() {
        let mut c = setup();
        let case_id = submit(&mut c, pass_items());
        let items = pass_items();
        all_verify(
            &mut c,
            &case_id,
            vec![
                items.clone(),
                items.clone(),
                items.clone(),
                Vec::new(),
                Vec::new(),
            ],
        );
        testing_env!(ctx(artist(), 0, 3 * SEC).build());
        c.finalize(case_id);
        assert!(c.nft_token("cert-0".to_string()).is_some());
        testing_env!(ctx(artist(), 1, 4 * SEC).build());
        c.nft_transfer(acct("examiner1.test"), "cert-0".to_string(), None, None);
    }

    #[test]
    fn zero_reveals_after_window_fails_and_refunds() {
        let mut c = setup();
        let case_id = submit(&mut c, pass_items());
        // Judging window is 100 secs from created at 1 sec: jump past it.
        testing_env!(ctx(acct("examiner2.test"), 0, 200 * SEC).build());
        c.finalize(case_id.clone());
        let v = c.get_case(case_id).expect("case view");
        assert_eq!(v.status, "failed");
        assert!(v.fee_settled);
        assert_eq!(v.human_points, 0);
        assert_eq!(v.process_points, 0);
        assert_eq!(c.nft_total_supply(), U128(0));
    }
}
