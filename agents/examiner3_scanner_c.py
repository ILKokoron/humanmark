#!/usr/bin/env python3
# Examiner 3, Scanner C, account exam3.bindingvow1106.testnet.
# Method: pixel classification with the pinned local model
# king1oo1/deepfake-model, loaded only from
# ~/workspace/human-cert/models/king with HF_HUB_OFFLINE=1. It reports
# per class scores and P(AI) for the final image.
# Published verification rule: pixels judge consistency of artifacts,
# process evidence judges origin, so P(AI) is advisory and never gates
# item verification. This examiner verifies an item only when the
# shared integrity precheck passes (image hash, bundle hash and every
# manifest file hash match the chain and the disk) AND the item rule
# holds: passkey_attestation when the attestation signature verifies
# and the key belongs to the artist onchain; layered_source_file when
# a layered_export file has perceptual sim at least 0.85 to the final
# image; progress_sketches when the highest step sketch has sim at
# least 0.80 to the final; live_redraw when the redraw file has sim at
# least 0.85 to the final image cropped to its region;
# continuous_timelapse when a video file entry exists (metadata only).
# Calibration note: on a 20 image set this model scored 0.70 alone and
# the three scanner ensemble scored 0.85. Pixel scores are advisory,
# never the verdict, and a dissenting pixel score is recorded, not hidden.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("HF_HUB_OFFLINE", "1")

from examiner_base import CALIBRATION_NOTE, run_examiner, scanner_analyze

EXAMINER = "exam3.bindingvow1106.testnet"
MODEL_ID = "king1oo1/deepfake-model"
LOCAL_DIR = os.path.expanduser("~/workspace/human-cert/models/king")


def analyze(bundle_dir, manifest, case, integrity_ok, integrity_checks, attestation_cache):
    checks, verified, raw_scores, p_ai, thresholds = scanner_analyze(
        MODEL_ID, LOCAL_DIR, bundle_dir, manifest, case, integrity_ok, attestation_cache
    )
    return {
        "checks": checks,
        "verified_items": verified,
        "raw_scores": raw_scores,
        "p_ai": p_ai,
        "threshold": thresholds,
        "notes": [
            CALIBRATION_NOTE,
            f"This examiner (Scanner C, {MODEL_ID}) reported P(AI) {p_ai} for this image. "
            "That score is advisory and did not gate any item verification.",
            "Rule: pixels judge consistency of artifacts, process evidence judges origin.",
        ],
    }


if __name__ == "__main__":
    run_examiner(
        examiner=EXAMINER,
        role="Scanner C",
        short="scanner_c",
        tool=f"{MODEL_ID} (local pinned model at {LOCAL_DIR}, transformers image-classification pipeline)",
        analyze_fn=analyze,
    )
