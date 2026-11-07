#!/usr/bin/env python3
# Examiner 2, Scanner B, account exam2.bindingvow1106.testnet.
# Method: pixel classification with the pinned local model
# umm-maybe/AI-image-detector, loaded only from
# ~/workspace/human-cert/models/umm with HF_HUB_OFFLINE=1. It reports
# per class scores and P(AI) for the final image.
# License: CC BY 4.0, commercial use allowed with attribution to the
# model authors (umm-maybe). This examiner replaced
# hungnh1201/ai-image-detector on 2026-11-07 because that model is
# CC BY-NC 3.0 (non-commercial) and cannot sit in a panel that may be
# used commercially. The swap changes only the model, not the method:
# same Swin family, same label names (artificial, human), same
# verification rules and thresholds as the previous Scanner B.
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
# Calibration note: on the 20 image calibration set this model scored
# 0.75 alone, with zero false positives on the human works (its errors
# are missed AI images, never false accusations), and the ensemble
# {yaya, umm, king} scored 0.85, identical to the previous panel.
# Pixel scores are advisory, never the verdict, and a dissenting
# pixel score is recorded, not hidden. Full record:
# calibration/results/candidates/RESULTS.md.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("HF_HUB_OFFLINE", "1")

from examiner_base import CALIBRATION_NOTE, run_examiner, scanner_analyze

EXAMINER = "exam2.bindingvow1106.testnet"
MODEL_ID = "umm-maybe/AI-image-detector"
LOCAL_DIR = os.path.expanduser("~/workspace/human-cert/models/umm")


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
            f"This examiner (Scanner B, {MODEL_ID}) reported P(AI) {p_ai} for this image. "
            "That score is advisory and did not gate any item verification.",
            "Rule: pixels judge consistency of artifacts, process evidence judges origin.",
        ],
    }


if __name__ == "__main__":
    run_examiner(
        examiner=EXAMINER,
        role="Scanner B",
        short="scanner_b",
        tool=f"{MODEL_ID} (local pinned model at {LOCAL_DIR}, transformers image-classification pipeline)",
        analyze_fn=analyze,
    )
