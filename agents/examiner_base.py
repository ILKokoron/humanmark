"""Shared runner for the Humanmark examiners.

Each examiner script supplies its own analyze function and identity;
this module handles argument parsing, chain case loading, the shared
integrity precheck, report writing, and the commit-reveal vote with
the contract commitment formula:
sha256 hex of sorted verified_items joined with "," + "|" + report_hash
+ "|" + salt, where report_hash is the sha256 hex of the report JSON
file bytes exactly as written to disk.
No em dashes are used in any string produced here.
"""
import argparse
import json
import os
import secrets
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import common
import near

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
CALIBRATION_NOTE = (
    "Calibration on a 20 image set: the three scanner models scored 0.50, "
    "0.75 and 0.70 individually and 0.85 as an ensemble. Pixel scores are "
    "advisory, never the verdict."
)

AI_WORDS = ("ai", "artificial", "fake", "generated", "synthetic", "stable",
            "midjourney", "dalle", "dall", "sdxl", "diffusion", "other_ai", "label_1")
HUMAN_WORDS = ("real", "human", "natural", "authentic", "label_0")


def p_ai_from_scores(scores):
    """Map raw label scores to P(AI), reusing the calibration analyze.py mapping."""
    total_ai = 0.0
    for entry in scores:
        lab = entry["label"].lower().replace(" ", "_").replace("-", "_")
        if any(w in lab for w in HUMAN_WORDS) and "fake" not in lab:
            continue
        if any(w in lab for w in AI_WORDS):
            total_ai += float(entry["score"])
    return round(total_ai, 4)


def run_scanner_model(local_dir, image_path):
    """Load one pinned local model and return (raw_scores, p_ai). Local files only."""
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    from PIL import Image
    from transformers import pipeline

    clf = pipeline("image-classification", model=local_dir, device=-1)
    img = Image.open(image_path).convert("RGB")
    out = clf(img, top_k=None)
    raw = [{"label": str(o["label"]), "score": round(float(o["score"]), 4)} for o in out]
    return raw, p_ai_from_scores(raw)


def case_id_value(case_id):
    """Pass numeric case ids as ints and other ids as strings to the contract."""
    return int(case_id) if str(case_id).isdigit() else case_id


def load_case(case_id, bundle_dir, dry_run):
    """Load the case from chain, or synthesize one from the bundle in dry run mode."""
    if not dry_run:
        case = near.view("get_case", {"case_id": case_id_value(case_id)})
        if not case:
            raise RuntimeError(f"case {case_id} not found onchain")
        return case
    try:
        case = near.view("get_case", {"case_id": case_id_value(case_id)})
        if case:
            return case
    except Exception:
        pass
    manifest, manifest_bytes = common.load_bundle(bundle_dir)
    image_path = common.bundle_file(bundle_dir, manifest.get("image_file", "image.png"))
    return {
        "case_id": case_id,
        "artist": manifest.get("artist", ""),
        "image_hash": common.sha256_file(image_path) if os.path.exists(image_path) else None,
        "bundle_hash": common.sha256_bytes(manifest_bytes),
        "claimed_items": manifest.get("claimed_items", []),
        "status": "dry_run_synthetic",
    }


def scanner_analyze(model_id, local_dir, bundle_dir, manifest, case, integrity_ok, attestation_cache):
    """Shared Scanner A, B and C method. See each scanner script header for the rule."""
    checks = []
    verified = []
    raw_scores = None
    p_ai = None
    thresholds = {
        "layered_source_file_sim_min": 0.85,
        "progress_sketches_sim_min": 0.80,
        "live_redraw_sim_min": 0.85,
        "p_ai": "advisory only, does not gate item verification",
    }
    image_path = common.bundle_file(bundle_dir, manifest.get("image_file", "image.png"))

    if os.path.exists(image_path):
        try:
            raw_scores, p_ai = run_scanner_model(local_dir, image_path)
            checks.append({
                "name": "scanner_pixel_score",
                "result": True,
                "detail": f"model {model_id} P(AI) {p_ai} (advisory only)",
            })
        except Exception as exc:
            checks.append({
                "name": "scanner_pixel_score",
                "result": False,
                "detail": f"model {model_id} failed to run: {exc}",
            })
    else:
        checks.append({
            "name": "scanner_pixel_score",
            "result": False,
            "detail": "final image missing on disk, pixel score not computed",
        })

    if not integrity_ok:
        return checks, verified, raw_scores, p_ai, thresholds

    claimed = case.get("claimed_items") or manifest.get("claimed_items", [])

    if "passkey_attestation" in claimed:
        ok, att_checks = attestation_cache()
        checks.extend(att_checks)
        checks.append({
            "name": "verify:passkey_attestation",
            "result": bool(ok),
            "detail": "attestation signature and onchain key ownership verified"
            if ok else "attestation verification failed, see attestation checks above",
        })
        if ok:
            verified.append("passkey_attestation")

    if "layered_source_file" in claimed:
        exports = common.find_entries(manifest, role="layered_export")
        if not exports:
            checks.append({
                "name": "verify:layered_source_file",
                "result": False,
                "detail": "no file with role layered_export in the bundle",
            })
        else:
            best = None
            for entry in exports:
                sim = common.perceptual_sim(common.bundle_file(bundle_dir, entry["path"]), image_path)
                best = sim if best is None else max(best, sim)
                checks.append({
                    "name": f"layered_export_sim:{entry['path']}",
                    "result": bool(sim >= 0.85),
                    "detail": f"perceptual sim to final image {sim:.4f}, threshold 0.85",
                })
            if best is not None and best >= 0.85:
                verified.append("layered_source_file")

    if "progress_sketches" in claimed:
        sketches = common.find_entries(manifest, item="progress_sketches")
        if not sketches:
            checks.append({
                "name": "verify:progress_sketches",
                "result": False,
                "detail": "no progress_sketches files in the bundle",
            })
        else:
            top = max(sketches, key=lambda e: e.get("step", 0))
            sim = common.perceptual_sim(common.bundle_file(bundle_dir, top["path"]), image_path)
            ok = sim >= 0.80
            checks.append({
                "name": "verify:progress_sketches",
                "result": bool(ok),
                "detail": f"highest step {top.get('step')} ({top['path']}) sim to final {sim:.4f}, threshold 0.80",
            })
            if ok:
                verified.append("progress_sketches")

    if "live_redraw" in claimed:
        redraws = common.find_entries(manifest, item="live_redraw")
        if not redraws:
            checks.append({
                "name": "verify:live_redraw",
                "result": False,
                "detail": "no live_redraw files in the bundle",
            })
        else:
            for entry in redraws:
                sim = common.redraw_sim(bundle_dir, manifest, entry)
                ok = sim >= 0.85
                checks.append({
                    "name": f"verify:live_redraw:{entry['path']}",
                    "result": bool(ok),
                    "detail": f"sim of redraw to final image cropped to region {entry.get('region')} is {sim:.4f}, threshold 0.85",
                })
                if ok and "live_redraw" not in verified:
                    verified.append("live_redraw")

    if "continuous_timelapse" in claimed:
        videos = [
            e for e in common.find_entries(manifest, item="continuous_timelapse")
            if os.path.splitext(e.get("path", ""))[1].lower() in common.VIDEO_EXTS
        ]
        if videos:
            checks.append({
                "name": "verify:continuous_timelapse",
                "result": True,
                "detail": f"video file present ({videos[0]['path']}), verified on metadata only, frames not audited by scanners",
            })
            verified.append("continuous_timelapse")
        else:
            checks.append({
                "name": "verify:continuous_timelapse",
                "result": False,
                "detail": "no video file entry for continuous_timelapse in the bundle",
            })

    return checks, verified, raw_scores, p_ai, thresholds


def run_examiner(examiner, role, short, tool, analyze_fn):
    parser = argparse.ArgumentParser(description=f"Humanmark examiner {examiner}")
    parser.add_argument("--case", required=True, dest="case_id")
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--dry-run", action="store_true",
                        help="analyze and write the report locally, skip commit and reveal")
    args = parser.parse_args()

    case = load_case(args.case_id, args.bundle, args.dry_run)
    integrity_ok, integrity_checks, manifest = common.verify_integrity(args.bundle, case)

    attestation_state = {}

    def attestation_cache():
        if "result" not in attestation_state:
            artist = case.get("artist") or manifest.get("artist", "")
            attestation_state["result"] = common.verify_attestation(
                args.bundle, manifest, artist, check_onchain=True
            )
        return attestation_state["result"]

    extra = analyze_fn(
        bundle_dir=args.bundle,
        manifest=manifest,
        case=case,
        integrity_ok=integrity_ok,
        integrity_checks=integrity_checks,
        attestation_cache=attestation_cache,
    )

    checks = list(integrity_checks) + list(extra.get("checks", []))
    if not integrity_ok:
        checks.append({
            "name": "integrity_precheck",
            "result": False,
            "detail": "integrity failed, this examiner verifies nothing for this case",
        })
        verified = []
    else:
        verified = [i for i in extra.get("verified_items", [])
                    if i in (case.get("claimed_items") or manifest.get("claimed_items", []))]

    notes = list(extra.get("notes", []))
    if not integrity_ok:
        notes.append("Integrity precheck failed, so no items were verified.")

    report = {
        "examiner": examiner,
        "role": role,
        "case_id": args.case_id,
        "tool": tool,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "threshold": extra.get("threshold"),
        "verified_items": sorted(verified),
        "notes": notes,
    }
    if "raw_scores" in extra:
        report["raw_scores"] = extra["raw_scores"]
    if "p_ai" in extra:
        report["p_ai"] = extra["p_ai"]

    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_path = os.path.join(REPORTS_DIR, f"{args.case_id}-{short}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    report_hash = common.sha256_file(report_path)

    result = {
        "examiner": examiner,
        "role": role,
        "case_id": args.case_id,
        "report": report_path,
        "report_hash": report_hash,
        "verified_items": sorted(verified),
        "dry_run": bool(args.dry_run),
    }

    if args.dry_run:
        print(json.dumps(result, indent=2))
        return result

    salt = secrets.token_hex(8)
    commitment = common.commitment_for(sorted(verified), report_hash, salt)
    cid = case_id_value(args.case_id)
    commit_tx = near.call(examiner, "commit_vote", {"case_id": cid, "commitment": commitment})
    reveal_tx = near.call(examiner, "reveal_vote", {
        "case_id": cid,
        "verified_items": sorted(verified),
        "report_hash": report_hash,
        "salt": salt,
    })
    result["salt"] = salt
    result["commitment"] = commitment
    result["commit_tx"] = commit_tx
    result["reveal_tx"] = reveal_tx
    print(json.dumps(result, indent=2))
    return result
