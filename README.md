# Humanmark

**A swarm of five examiners certifies human-made art, and gets paid for examining, never for passing.**

An artist submits a finished image plus an evidence bundle they chose themselves, and locks an examination fee in escrow. Five examiner agents with genuinely different methods examine the bundle independently and vote commit-reveal on which evidence items they verified. If the verified evidence clears both axes, Human at least 5 points and Process at least 5 points, the contract mints a soulbound certificate NFT to the artist. The certificate carries the image hash, the bundle hash, the level, both axis scores, and the hash of every examiner report, so anyone can re-audit the verdict. If the evidence falls short, no NFT is minted, nothing is published or shamed, and the fee still pays the examiners, because the examination really happened.

Free detector websites guess from pixels. Humanmark certifies from evidence, with a panel, a published calibration, and a permanent record.

## Live

- App: frontend source in `frontend/` (planned URL https://humanmark-ilkokorons-projects.vercel.app; deployment status and the one blocker are recorded honestly in `docs/BUILD-RESULT.md`)
- Contract: `humanmark.bindingvow1106.testnet` on NEAR testnet
- Examiners: `exam1` to `exam5` under `bindingvow1106.testnet` (accounts listed onchain by the `examiners()` view)

## The two axes

One design decision runs the whole system: proving the human and proving the work are two different questions, and both must be answered.

**Human axis (need 5).** Is a real, living person behind this?
- `passkey_attestation` 5: a biometric passkey assertion. The fingerprint never leaves the artist's phone; it only unlocks a passkey locally, and what reaches the system is a cryptographic attestation. In this testnet demo the attestation is an ed25519 signature by the artist account over the case challenge code, verified by the examiners against the account's keys onchain; the frontend includes real WebAuthn enrolment, and wiring the assertion into the bundle is roadmap work.
- `aged_social_account` 2: an old account with a posting history that predates AI image generators. Hard to fake because what is faked is time.
- `live_challenge` 3: appear live, sign with the wallet, draw.

**Process axis (need 5).** Did this person's hands actually make this image?
- `continuous_timelapse` 4: the work drawn from blank to final, hands visible.
- `layered_source_file` 2: the original layered source, or for code-drawn work the generator source that re-renders it.
- `live_redraw` 3: redraw one detail of the work on challenge, in your own hand.
- `progress_sketches` 1: progress steps alone. Weak on purpose: AI can generate fake progress steps backwards from a final image.

An evidence item counts only if at least 3 of the 5 examiners verify it in their revealed votes. Level on a pass: `clamp(round(10 * total verified points / 20), 1, 10)`. The official wording everywhere is "certified at level N based on this evidence". Never "guaranteed 100 percent original", and the NFT carries no value promise.

## The five examiners (methods genuinely differ, reports are open)

1. **Scanner A** (`exam1`): yaya36095/ai-source-detector, a 5-class source classifier (Stable Diffusion, Midjourney, DALL-E, real, other AI).
2. **Scanner B** (`exam2`): umm-maybe/AI-image-detector, a Swin-based AI image detector. Scanner B originally ran hungnh1201/ai-image-detector; it was replaced on 2026-11-07 because hung is licensed CC BY-NC 3.0 (non-commercial). The replacement is the parent model family hung was fine-tuned from, with the same label names and the same verification method; only the model changed. See Credits and Licenses.
3. **Scanner C** (`exam3`): king1oo1/deepfake-model, a SigLIP2 real-vs-fake model trained for photo fakery.
4. **Provenance** (`exam4`): no machine learning. EXIF and metadata scan, PNG text chunk scan, C2PA string scan, hash and dimension consistency, known AI generator metadata signatures.
5. **Process auditor** (`exam5`): the devil's advocate. Its job is to try to prove the work is AI or the bundle fabricated: hash chain audit, timestamp ordering, sketch progression measurement, re-running generator source, strict redraw similarity.

Scanners report their pixel scores openly, including when they dissent, but pixel scores never decide a case alone: scanners verify an evidence item when the bundle artifact for it is present, intact, and perceptually consistent with the final image under their published rule. Every examiner report is a public JSON file naming its model or tool, version, raw scores or check results, verified items, and threshold. The SHA-256 of each report goes onchain in the reveal.

## Calibration (our own numbers, not the model pages)

Before any threshold was set, the three scanners were run over a 20 image set with certain ground truth (pre-1900 classics, human design files, categorized and self-generated AI images, including trap categories). Measured on that set: Scanner A scored 0.50 accuracy (it calls everything AI; its "real" class means real photograph, so human paintings fail it), Scanner B 0.75, Scanner C 0.70, and the ensemble 0.85, beating every single model. Pairwise agreement was only 0.30 to 0.65, which is why the ensemble works at all: the models are wrong in different places. Full record: `calibration/results/GATE-DECISION.md`. The honest conclusion built into the design: pixel-only judgment caps out around 0.85 and fails hardest on exactly the work digital artists submit, so the process evidence axis is the primary axis and the scanners are one signal among five. A full 100 image calibration set is required before any public accuracy claim; the 20 image spike only gated the build decision.

**Candidate replacement test (2026-11-07, same 20 images).** Three license-clean candidates were measured as Scanner B replacements. umm-maybe/AI-image-detector (CC BY 4.0) scored 0.75 alone with zero false positives on the human works, and the new ensemble {Scanner A, umm, Scanner C} scored 0.85, identical to the original panel, with ensemble false positives down from 2 to 1. Ateeqq/ai-vs-human-image-detector scored 0.65, and abacusai/Smaug-AI-Image-Detector scored 0.75 alone but dropped its panel to 0.75 and flagged all three Squeek Arena design files, so both were rejected. The honest note, recorded rather than hidden: no license-clean panel beats 0.85 on this set; every panel measured above 0.85 (0.90 and 0.95) includes the non-commercial hung model. Full record: `calibration/results/candidates/RESULTS.md`. Every error from both studies, named image by image and grouped by failure pattern, is catalogued in `calibration/results/FAILURE-CATALOG.md`.

## Credits and licenses

The scanners are borrowed models, credited here as their licenses require. Humanmark's own contribution is the rule set, the escrow, the orchestration, and the calibration; the models belong to their authors.

- **yaya36095/ai-source-detector** (Scanner A): Apache-2.0.
- **umm-maybe/AI-image-detector** (Scanner B, current): CC BY 4.0, used with attribution to the umm-maybe authors.
- **king1oo1/deepfake-model** (Scanner C): Apache-2.0.
- **hungnh1201/ai-image-detector** (Scanner B, original panel only): CC BY-NC 3.0. It judged demo case-0 and case-1 during the initial build and was then replaced by umm-maybe, because a non-commercial model cannot sit in a panel that may be used commercially. Its scores remain in the calibration record as history.
- **Ateeqq/ai-vs-human-image-detector** and **abacusai/Smaug-AI-Image-Detector**: Apache-2.0, tested as candidates, not used in the panel.
- The calibration set is not redistributed in this repo; only its manifest, raw scores, analyses, and this failure literature are published.

## Demo cases (live on testnet, both directions)

case-0 and case-1 were judged by the original panel (with hung as Scanner B). case-2 and case-3 are the same two demonstrations re-run on 2026-11-07 with the current license-clean panel (umm-maybe as Scanner B), so the live demo matches the code in this repo. All four verdicts were read back from chain state.

**case-0, PASS (original panel).** Kokoron's headline poster v2 for Squeek Arena, a code-drawn work that all three scanners call AI (pixel scores 0.84 to 0.94 AI in calibration, and AI-leaning again in their case reports, recorded, not hidden). Submitted with a real process bundle: the actual generator scripts (`gen-poster.py`, `gen-poster2.py`), the recovered sprite grid, a fresh re-render, a signed attestation, and a challenge detail redraw. Four examiners verified all three claimed items; the Process auditor verified none and published why: two bundle files are honestly dated after the final image (the sprite grid was recovered and the export re-rendered during bundle preparation), and its generator re-run measured 0.8705 against its 0.98 threshold. Every item still reached 4 of 5 votes. Verdict onchain: Human 5, Process 5, **certified at level 5 based on this evidence**, certificate `cert-0` minted to the artist.
- Submit tx: `4vt7JToCCfQTgNUewMAfJubxBS7E9qLjPLdZYHRDNyKQ`
- Finalize tx: `4n3Ys47vfU7D92rsr95MiY1mQDpRCU4HVkdn3JujX4Qx`

**case-1, FAIL (original panel).** A self-generated AI image (fantasy floating islands, from the calibration set) submitted claiming evidence it did not provide: no attestation, no timelapse, no source files. All five examiners examined it, reported, and verified nothing. Axes stayed at 0. No NFT was minted. The fee still split five ways to the examiners: pay is for examining, never for passing.
- Submit tx: `HFn1QSj5BwqpGw2FRZ79Zu4pNBPy14kZgowyYBjukaLY`
- Finalize tx: `6ztPGioNcv3gqcU71MoGk4HKwR6xMsAKJn8sppUknxZG`

**case-2, PASS (current panel).** The same headline poster v2 and the same process bundle as case-0, judged by the panel with umm-maybe as Scanner B. Scanner pixel scores this time: Scanner A 0.7617 AI, Scanner B (umm) 0.0505 AI (it did not accuse the poster, consistent with its zero false positives in calibration), Scanner C 0.9435 AI. Four examiners verified all three items; the Process auditor again verified none, for the same published reasons as case-0. Verdict onchain: Human 5, Process 5, **certified at level 5 based on this evidence**, certificate `cert-2` minted to the artist. Total supply after this case: 2.
- Submit tx: `3EAiSPEJ8LEhMEU173EAfredi41pcoC1BC2Kj5fND55E`
- Finalize tx: `5fuCn6hvuznxyzxL5abTVEEL5BwMdvmpogm6Um7r24y2`

**case-3, FAIL (current panel).** The same AI image and empty-evidence claim as case-1. All five examiners verified nothing; axes 0 and 0; no NFT minted (total supply stayed 2). The fee still split five ways: each examiner's balance rose by about 0.0095 NEAR across the case (the 0.01 share minus their own commit and reveal gas), read back from chain before and after.
- Submit tx: `7gcKinuqgUwfhkbjigQk9xYYnUN2RisVNEp4cTh8y9D`
- Finalize tx: `4GCm3RrSXtemxM4p17xj4pABhbZahC4PMsxVsA8Eg9rR`

## Anti-gadungan rules

- Pay never equals pass. Failure is a real, demonstrated, onchain outcome (case-1).
- The swarm is not one script pretending to be five agents: five accounts, five different published methods, five open reports per case.
- The certificate embeds its evidence trail (hashes of image, bundle, and every report), so it can be re-audited instead of merely believed.
- Claims never exceed the calibration: detectors are fallible in both directions, and the wording is always "certified at a level based on this evidence".

## Contract design

One contract holds escrow, voting, registry, and minting. `submit_case` locks a fee at or above the onchain minimum package (0.05 NEAR on testnet). Examiners `commit_vote` a sha256 commitment of (sorted verified items, report hash, salt), then `reveal_vote`. `finalize` is permissionless once all five revealed or the judging window closed; it counts items at 3 of 5 verifications, sums the axes, splits the fee equally among the examiners who revealed (if nobody revealed, the fee refunds to the artist and the case fails), and mints the certificate on a pass. Certificates are soulbound: `nft_transfer` always refuses. The judges list is fixed at init; swapping examiner accounts means a new deployment, while the methods behind the accounts can evolve freely.

## Repository layout

- `contract/` - the Rust contract (near-sdk 5), 10 unit tests covering fee floor, unknown items, pass and fail flows, the 3-of-5 item rule, reveal integrity, and soulbound transfer.
- `agents/` - the five examiners and the orchestrator in Python; each examiner file header publishes its method and rule.
- `frontend/` - the static 4-screen app (submit with in-browser SHA-256 and evidence checklist, cases, case detail with examiner reports, certificate view) with NEAR Wallet Selector connect and a WebAuthn passkey enrolment panel.
- `calibration/` - the 20 image calibration spike (set manifest, raw scores, analysis, gate decision), the candidate replacement study under `calibration/results/candidates/`, and the failure catalog at `calibration/results/FAILURE-CATALOG.md`.
- `demo/` - the demo evidence bundles and the orchestrator logs for all four cases.
- `docs/` - the build result record with every transaction link.

## Run it yourself

Contract: `cd contract && cargo test`; build with `cargo build --target wasm32-unknown-unknown --release`.
Examiners: use the project venv (torch and transformers for the scanners, models pinned under `models/`, loaded locally only): `cd agents && ../venv/bin/python orchestrator.py --case <case-id> --bundle <bundle-dir>`. Examiner signing keys must be in the local near CLI keychain.
Frontend: serve `frontend/` statically; it reads the live contract through the FastNEAR mirror RPC and needs no backend.

## Honest limitations

- Testnet only, and this build runs a **reference swarm**: one operator runs all five examiner programs to prove the design end to end. It is not a decentralized examiner network. The contract accepts votes only from the five registered examiner accounts, every commit and reveal is signed by that examiner's own account, and finalize is permissionless; a production swarm adds open examiner registration, staking, and reputation.
- The demo attestation is an account-key signature stand-in for a WebAuthn assertion (documented in the bundle). The frontend enrols a real passkey; binding the assertion to a case bundle is roadmap work.
- One person can still hold many passkeys and many wallets: the Human axis proves a living person holding a device, not global uniqueness.
- Process evidence can be fabricated with effort, and detectors err in both directions; the layered design reduces this, it does not erase it. The Process auditor's case-0 dissent is part of the public record, not an embarrassment to hide.
- Examiner independence in this build is methodological (different models, different checks, different thresholds), not organizational.

## Roadmap

Full 100 image calibration with modern digital art as the human class; real WebAuthn assertions bound into bundles; reverse-image provenance search as a sixth sense for the Provenance examiner; examiner staking, slashing, and reputation; a minimum reveal quorum for fee settlement.

## Disclosure

Humanmark and Binding Vow are two independent entries by the same author in this hackathon (the rules allow up to two projects per person, each disclosing the other). Binding Vow is a self-commitment protocol with the same escrow and commit-reveal DNA pointed at the future; its repo is https://github.com/ILKokoron/binding-vow and its contract is `bindingvow.bindingvow1106.testnet`.

## Tracks

Built for NEAR Hackathon "Build Beyond Boundaries": **AI Swarms** (five examiners with different methods doing paid verification work) and **NFTs That Do Something** (the certificate NFT is the verdict, carrying its full evidence trail), with **AI Security** as a supporting tag (forensic defense against AI content fraud).
