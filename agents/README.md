# Humanmark examiners (the swarm)

Five examiner programs examine one case on the Humanmark contract
(humanmark.bindingvow1106.testnet, NEAR testnet) and vote commit-reveal
with the list of evidence items each of them verified. A case is a
final image plus an evidence bundle folder. An evidence item counts
onchain only if at least 3 of 5 examiners verify it.

Points menu. Human axis: passkey_attestation 5, aged_social_account 2,
live_challenge 3. Process axis: continuous_timelapse 4,
layered_source_file 2, live_redraw 3, progress_sketches 1.

Wording rule used everywhere: a work is certified at a level based on
this evidence. Nothing here guarantees an origin, and pixel scores are
advisory, never the verdict.

## How to run

Use the project venv python for everything (torch and transformers are
installed there, and the scanner models are loaded from local pinned
dirs only, with HF_HUB_OFFLINE=1):

    ~/workspace/human-cert/venv/bin/python orchestrator.py --case CASE_ID --bundle /path/to/bundle

The orchestrator runs the 5 examiners sequentially, then calls
finalize signed as bindingvow1106.testnet, then prints get_case.

Run one examiner on its own:

    ~/workspace/human-cert/venv/bin/python examiner1_scanner_a.py --case CASE_ID --bundle /path/to/bundle

Add --dry-run to any examiner or to the orchestrator to analyze and
write reports locally with no chain writes (no commit, no reveal, no
finalize). Dry run synthesizes the case from the bundle manifest when
the case is not onchain yet.

Each examiner writes its report to
reports/<case_id>-<examiner_short>.json, where examiner_short is one
of scanner_a, scanner_b, scanner_c, provenance, process. It then
commits and reveals its vote signed as its own exam account and prints
the transaction ids. Keys stay in the near CLI legacy keychain; no
private key is read by this code.

Chain reads use the FastNEAR mirror at https://rpc.testnet.fastnear.com
because rpc.testnet.near.org is unreachable from this VM. Signed calls
use the official near CLI at
~/tools/near-bin/near-cli-rs-x86_64-unknown-linux-gnu/near.

## Commitment formula

report_hash is the sha256 hex of the examiner report JSON file bytes
exactly as written to disk. The commitment sent to commit_vote is the
sha256 hex of:

    sorted verified_items joined with "," + "|" + report_hash + "|" + salt

The salt is a random 16 hex character string generated per vote.
reveal_vote then sends case_id, verified_items, report_hash and salt,
and the contract recomputes the commitment to check the reveal.

## Bundle schema

The bundle is a folder with a manifest.json. bundle_hash onchain is
the sha256 of the manifest.json bytes, and image_hash onchain is the
sha256 of the image file bytes.

    {
      "artist": "bindingvow1106.testnet",
      "image_file": "image.png",
      "claimed_items": ["passkey_attestation", "layered_source_file", "progress_sketches", "live_redraw"],
      "challenge_code": "HM-2026-1107-POSTER",
      "attestation": {"account_id": "...", "public_key": "ed25519:...", "message": "...", "signature_b64": "..."},
      "files": [
        {"path": "image.png", "sha256": "<hex>", "role": "image"},
        {"path": "source/gen-poster2.py", "sha256": "<hex>", "item": "layered_source_file", "created_at": "2026-11-04T13:06:00+07:00"},
        {"path": "source/render.png", "sha256": "<hex>", "item": "layered_source_file", "role": "layered_export", "created_at": "..."},
        {"path": "progress/step1.png", "sha256": "<hex>", "item": "progress_sketches", "step": 1, "created_at": "..."},
        {"path": "attestation.json", "sha256": "<hex>", "item": "passkey_attestation"},
        {"path": "redraw/HM-2026-1107-POSTER-detail.png", "sha256": "<hex>", "item": "live_redraw", "region": [0.0, 0.0, 0.5, 0.5]}
      ]
    }

## Integrity precheck (all 5 examiners)

Every examiner first checks that the image file sha256 equals the
onchain image_hash, the manifest.json sha256 equals the onchain
bundle_hash, and every files[] entry hash matches the file on disk.
If integrity fails, the examiner verifies nothing and says why in its
report.

Perceptual similarity, used by several examiners, is computed with PIL
grayscale 64x64 thumbnails: sim = 1 - mean_abs_diff / 255.

## The 5 examiners and their published rules

1. Scanner A, exam1.bindingvow1106.testnet, model
   yaya36095/ai-source-detector from ~/workspace/human-cert/models/yaya.
2. Scanner B, exam2.bindingvow1106.testnet, model
   umm-maybe/AI-image-detector from ~/workspace/human-cert/models/umm.
   License CC BY 4.0 (commercial use with attribution). Scanner B was
   originally hungnh1201/ai-image-detector; it was replaced on
   2026-11-07 because hung is CC BY-NC 3.0 (non-commercial). The swap
   changed only the model, not the method: same Swin family, same
   label names (artificial, human), same rules and thresholds. The
   original demo cases (case-0, case-1) were judged by the old panel;
   case-2 and case-3 were judged by the current panel.
3. Scanner C, exam3.bindingvow1106.testnet, model
   king1oo1/deepfake-model from ~/workspace/human-cert/models/king.

   Each scanner loads only its own model, reports per class scores and
   P(AI) for the final image, and states its calibration context (see
   below). Published rule: pixels judge consistency of artifacts,
   process evidence judges origin, so P(AI) never gates item
   verification. A scanner verifies passkey_attestation if integrity
   holds and the attestation signature verifies with the key owned by
   the artist onchain; layered_source_file if a layered_export file
   has sim at least 0.85 to the final image; progress_sketches if the
   highest step sketch has sim at least 0.80 to the final; live_redraw
   if the redraw file has sim at least 0.85 to the final image cropped
   to its region; continuous_timelapse if a video file entry exists
   (metadata only, noted as such).

4. Provenance, exam4.bindingvow1106.testnet, no ML. It checks PNG and
   JPEG metadata with PIL (format, size, info dict, EXIF), scans raw
   bytes and PNG text chunks for AI generator signatures (parameters,
   stable diffusion, midjourney, dall-e, openai, c2pa, content
   credentials) and records hits by name, checks dimension and format
   consistency between the final image and any layered_export,
   verifies the attestation signature plus onchain key ownership, and
   checks that the live_redraw file name contains the challenge_code.
   It verifies an item only if integrity holds and none of its
   forensic checks for that item failed. An AI signature hit inside a
   process artifact fails that item. A signature hit in the final
   image is reported, but the item verdict follows the artifact
   checks, since the case is decided by evidence.

5. Process auditor, exam5.bindingvow1106.testnet, the devil's
   advocate. Its job is to try to prove fabrication, and it publishes
   every failed check by name. It checks the hash chain from manifest
   to files, created_at ordering (process files not after the final
   image's declared creation, steps ascending), sketch progression
   (sim of each step to the final strictly increasing with step), the
   layered source (a .py source is copied alone into a temp dir and
   run with the venv python with a 120 second timeout, its produced
   PNG is compared to the final image with sim at least 0.98 expected
   for deterministic renders and the actual sim recorded, and lines
   calling draw primitives are counted as a layer proxy), and
   live_redraw with a stricter published threshold of 0.90. It
   verifies an item only if all of its checks for that item pass.

Attestation verification (shared, in common.py): the ed25519
signature must verify over attestation.message with the base58 decoded
public key from attestation.public_key, and that public key must
belong to the artist account onchain (checked with
view_access_key_list). Verification uses PyNaCl, installed into the
venv, with a vendored pure python Ed25519 verifier as fallback.

## Calibration numbers (quoted honestly)

On a 20 image calibration set (10 human, 10 AI), the original scanner
models scored 0.50 (yaya36095/ai-source-detector), 0.75
(hungnh1201/ai-image-detector) and 0.70 (king1oo1/deepfake-model)
individually at a 0.5 threshold, and 0.85 as an ensemble. The set is
small, one model flags almost everything as AI, and a code drawn human
poster was called AI by all three scanners at 0.86 to 0.94. That is
exactly why pixel scores are advisory in this system and the process
evidence carries the verdict. Full record:
~/workspace/human-cert/calibration/results/GATE-DECISION.md.

Candidate replacement test (2026-11-07, same 20 images): three
license-clean candidates were measured as Scanner B replacements.
umm-maybe/AI-image-detector (CC BY 4.0) scored 0.75 alone with zero
false positives on the human works, and the new ensemble
{yaya, umm, king} scored 0.85, identical to the old panel, with
ensemble false positives down from 2 to 1. Ateeqq scored 0.65 and
abacusai/Smaug scored 0.75 alone but dropped its panel to 0.75 and
flagged all three Squeek design files, so both were rejected. Honest
note: no license-clean panel beats 0.85 on this set; every panel
above 0.85 (0.90, 0.95) includes the NC-licensed hung. Full record:
~/workspace/human-cert/calibration/results/candidates/RESULTS.md.
Every error from both studies is catalogued in
~/workspace/human-cert/calibration/results/FAILURE-CATALOG.md.

## Files

- near.py: FastNEAR RPC views (get_case, view_access_key,
  view_access_key_list) and signed calls through the near CLI.
- common.py: bundle loading, sha256 helpers, the commitment formula,
  integrity verification, perceptual similarity, base58 decode, and
  ed25519 attestation verification.
- examiner_base.py: shared runner (arguments, case loading, report
  writing, commit and reveal) plus the shared scanner method.
- examiner1_scanner_a.py to examiner5_process.py: the 5 examiners,
  each with its published method and rule in its header comment.
- orchestrator.py: runs all 5 examiners, then finalize, then get_case.
- fixtures/: a tiny self test bundle built from the Squeek Arena
  headline poster v2 and its real source. Its attestation is a dummy
  that fails signature verification on purpose, and the reports show
  that failure in every examiner. Its source script reads a data file
  that lives outside the bundle and writes to absolute output paths,
  so the Process auditor records a failed isolation check, measures
  the regenerated output at sim 0.9783 against the 0.98 threshold
  before restoring the originals, and does not verify
  layered_source_file for the fixture. The scanners and Provenance do
  verify it, which is the intended diversity of the panel.
- reports/: examiner reports, one JSON per examiner per case.

## Report format

Each report JSON has: examiner (account id), role, case_id, tool
(model id or tool description), timestamp (ISO), checks (a list of
name, result and detail entries, with failed checks named), raw_scores
and p_ai where relevant, threshold, verified_items, and notes.
Reports are honest by construction: failed checks and dissenting pixel
scores are recorded, never hidden.
