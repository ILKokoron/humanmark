# Humanmark (working name): swarm certificate for human-made art

Start: 2026-11-07 10:40 WIB, kokoron gave the go after the calibration gate passed.
Design brief: ~/workspace/goals/near-hackathon-entry/files/BRIEF-SWARM-HUMAN-MADE.md
Gate record: ~/workspace/human-cert/calibration/results/GATE-DECISION.md
Deadline: Sat 2026-11-14 23:59 UTC. This is kokoron's SECOND hackathon project
(max 2 per person, each README must disclose the other project, Binding Vow).
Tracks: AI Swarms (primary), NFTs That Do Something (primary), AI Security (optional third).

## Design locks from the gate (do not relitigate)

- Process-evidence-first: the scanner ensemble is ONE signal, never the verdict.
- Two axes, item-based points from the brief's menu. An evidence item counts
  only if at least 3 of 5 examiners verify it (commit-reveal votes carry the
  verified item id list). Axis points = sum of verified item points.
  Pass = Human axis >= 5 AND Process axis >= 5.
- Level = clamp(round(10 * total verified points / 20), 1, 10) on a pass.
- Fee escrow: artist locks the examination fee up front (min package 0.05
  NEAR testnet). Fee splits equally among examiners who revealed a report,
  pass or fail. No reveal, no pay. Pay is for examining, never for passing.
- Certificate NFT: minted by the contract to the artist on a pass only.
  Soulbound (transfer panics, same pattern as Binding Vow). Metadata carries
  image hash, evidence bundle hash, level, both axis points, and the report
  hashes, so anyone can re-audit the verdict.
- Wording everywhere: "certified at level N based on this evidence". Never
  "guaranteed 100 percent original", never any value promise for the NFT.

## Evidence menu (fixed points, from the brief)

Human axis: passkey_attestation 5; aged_social_account 2; live_challenge 3.
Process axis: continuous_timelapse 4; layered_source_file 2; live_redraw 3;
progress_sketches 1.

For the hackathon build, evidence items are verified from a bundle: a folder
(or zip) with a manifest.json listing claimed items and files, file hashes
checked against the manifest. Live challenge items are verified by the
Process auditor from a recorded challenge response file in the bundle
(same-day code word visible in the timelapse or redraw file name plus a
signed message). Keep verification rule-based and published; no LLM judges.

## Examiners (5 accounts, 5 genuinely different methods, open JSON reports)

1. Scanner A: yaya36095/ai-source-detector (local pinned model in
   ~/workspace/human-cert/models/yaya). Reports per-class scores.
2. Scanner B: hungnh1201/ai-image-detector (~/workspace/human-cert/models/hung).
3. Scanner C: king1oo1/deepfake-model (~/workspace/human-cert/models/king).
   Scanners vote on items only where pixels are relevant evidence: they can
   veto nothing alone; their ensemble P(AI) is reported and they verify an
   item only when the bundle's claimed item is consistent with their reading
   (published rule in their code). Scanner reports must include the ensemble
   context from the calibration: these models alone capped at 0.85.
4. Provenance: no ML. EXIF and metadata scan, PNG text chunks, C2PA string
   scan, file hash vs manifest, image dimensions and format consistency,
   known-AI-generator metadata signatures (e.g. png "parameters" chunks).
5. Process auditor (devil's advocate): its job is to try to prove the work
   is AI or the bundle is fabricated. Checks hash chain manifest to files,
   timestamp ordering of process files, perceptual distance progression of
   sketches toward the final (PIL, grayscale thumbnails), layered file layer
   count where parseable (ORA zip listing, PSD header), timelapse presence
   and duration metadata. Publishes every failed check by name.

Each examiner report JSON: examiner id, case id, model or tool + version,
raw scores or check results, verified item ids, threshold used, timestamp.
Reports are public files; their SHA-256 goes onchain in the reveal.

## Contract (adapt Binding Vow patterns, do not start from zero)

Base patterns: ~/workspace/binding-vow/contract-vow/src/lib.rs (escrow split,
soulbound NEP-171 minimal, commit-reveal with hash of vote plus salt,
finalize by majority, permissionless finalize after window). AGENTS.md has
binding NEAR lessons (borsh and unit-testing dev-deps, view structs expose
amounts as String, verify state after deploy, method param names are JSON
field names, never delete credentials before verifying account operations).

Contract state per case: artist, image_hash, bundle_hash, fee locked,
claimed items, status (Open, Judging, Passed, Failed), commits, reveals
(verified items + report hash per examiner), axis points after finalize,
certificate token id when minted.

Methods: new (examiners list, min_fee), submit_case (payable, >= min_fee),
commit_vote(case_id, hash), reveal_vote(case_id, verified_items, report_hash,
salt), finalize(case_id) permissionless after all reveals or judging window
closed, plus views. Judging window: configurable seconds (demo uses minutes).

Accounts: create subaccounts under bindingvow1106.testnet following the
Binding Vow record in ~/workspace/binding-vow/docs/CONTRACT-RESULT.md:
contract humanmark.bindingvow1106.testnet, examiners exam1 to exam5 under
the same parent. Fund from the parent like the judges were funded. Verify
state after every deploy by reading a known record back.

## Swarm runner

Python, venv at ~/workspace/human-cert/venv (torch and transformers already
installed). Reuse calibration code in ~/workspace/human-cert/calibration/
(run_scanners.py patterns, analyze.py label mapping). One runner process
per examiner identity or one orchestrator that signs per examiner account
with each examiner's own key file, like the Binding Vow swarm did (see
~/workspace/binding-vow/agents and docs/SWARM-RESULT.md). Agents read chain
state via FastNEAR mirror rpc.testnet.fastnear.com. Deterministic rules,
published in each examiner's source file header.

## Demo evidence (both directions, real onchain)

1. PASS case: kokoron's headline poster v2 (the h10 image all three
   scanners called AI at 0.86 to 0.94) submitted WITH a process bundle
   (source design files from ~/workspace/squeek-arena/design/, manifest
   with hashes and timestamps, progress files). Scanners report AI-leaning
   scores honestly in their reports; provenance and process verification
   carry the Process axis over 5 and the Human axis is covered by a
   passkey-style signed attestation file from the artist account for the
   demo (documented as the demo stand-in for WebAuthn, real WebAuthn is
   frontend scope below). Certificate minted, level computed by the rule.
2. FAIL case: one self-generated AI image from the calibration set (a04 or
   a07) submitted with NO evidence bundle beyond the image. Axes stay under
   threshold, no NFT, fee still splits to examiners who reported.

## Frontend

Static site mirroring Binding Vow frontend structure
(~/workspace/binding-vow/frontend): screens for Submit (image file, SHA-256
computed in browser, evidence checklist with points shown, fee), Cases,
Case detail (examiner reports, axis bars, verdict), Certificate view.
NEAR Wallet Selector connect like the updated Binding Vow frontend.
Browser WebAuthn passkey enrolment as the passkey_attestation evidence
(credential id plus signed assertion stored in the bundle manifest) -
implement if time allows after the onchain demo works; the demo stand-in
must not block it. Deploy to Vercel like Binding Vow. Click-verify the
read path in a real browser before reporting it works; wallet-signed write
path may stay human-unverified, say so plainly if it does.

## Repo and disclosure

New public repo under ILKokoron (github connector available), name
humanmark. README: what it is, the anti-gadungan rules, calibration summary
with the real numbers from the gate record (never the model pages' claims),
how to run the examiners, contract address, demo case ids and tx links,
known limits (no minimum quorum issue does not apply here since items need
3 of 5; sybil passkeys; detectors are fallible both ways), roadmap (full
100-image calibration, real WebAuthn, quorum and staking).
Cross-disclosure: add one line to this README naming Binding Vow as the
same author's other entry, and add the matching line to Binding Vow's
README (local repo at ~/workspace/binding-vow, push if credentials allow;
if push fails, leave the local edit and report it).

## Out of scope

No token, no staking or slashing, no mainnet, no training models, no
marketplace. Do not touch Binding Vow's contract or live state beyond the
README line. Do not delete anything in ~/workspace/human-cert/calibration.
