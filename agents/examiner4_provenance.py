#!/usr/bin/env python3
# Examiner 4, Provenance, account exam4.bindingvow1106.testnet. No ML.
# Method: forensic metadata examination with PIL. It reads the final
# image format, size, info dict and EXIF, scans the raw bytes and the
# PNG text chunks of the final image and every process artifact for AI
# generator signatures (parameters, stable diffusion, midjourney,
# dall-e, openai, c2pa, content credentials) and records every hit by
# name, checks dimension and format consistency between the final
# image and any layered_export, verifies the attestation signature
# plus onchain key ownership, and checks that the live_redraw file
# name contains the bundle challenge_code.
# Published verification rule: an item is verified only if the shared
# integrity precheck passes (image hash, bundle hash and every
# manifest file hash match the chain and the disk) AND none of this
# examiner's forensic checks for that item failed. An AI signature hit
# inside a process artifact fails that item. A signature hit in the
# final image alone is reported but does not by itself fail an item,
# because the case is decided by the process evidence, and that is
# stated in the report notes.
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import common
from examiner_base import run_examiner
from PIL import Image

EXAMINER = "exam4.bindingvow1106.testnet"
SIGNATURES = ["parameters", "stable diffusion", "midjourney", "dall-e",
              "openai", "c2pa", "content credentials"]


def png_text_chunks(path):
    """Return the text found in PNG tEXt, iTXt and zTXt chunks (best effort)."""
    texts = []
    try:
        with open(path, "rb") as f:
            data = f.read()
        if not data.startswith(b"\x89PNG"):
            return texts
        pos = 8
        while pos + 8 <= len(data):
            length = struct.unpack(">I", data[pos:pos + 4])[0]
            ctype = data[pos + 4:pos + 8]
            chunk = data[pos + 8:pos + 8 + length]
            if ctype in (b"tEXt", b"iTXt"):
                texts.append(chunk.decode("utf-8", errors="ignore"))
            elif ctype == b"zTXt":
                import zlib
                try:
                    _, _, rest = chunk.partition(b"\x00\x00")
                    texts.append(zlib.decompress(rest).decode("utf-8", errors="ignore"))
                except Exception:
                    pass
            pos += 12 + length
            if ctype == b"IEND":
                break
    except Exception:
        pass
    return texts


def signature_hits(path):
    """Lowercase byte and PNG text scan for AI generator signatures. Returns hit names."""
    hits = set()
    try:
        with open(path, "rb") as f:
            raw = f.read().lower()
    except Exception:
        return sorted(hits)
    text_blob = " ".join(png_text_chunks(path)).lower().encode("utf-8", errors="ignore")
    blob = raw + b" " + text_blob
    for sig in SIGNATURES:
        if sig.encode("utf-8") in blob:
            hits.add(sig)
    return sorted(hits)


def analyze(bundle_dir, manifest, case, integrity_ok, integrity_checks, attestation_cache):
    checks = []
    verified = []
    notes = [
        "A signature hit in the final image is reported but the item verdict follows "
        "the artifact checks, since the case is decided by evidence.",
        "No ML is used by this examiner.",
    ]
    image_rel = manifest.get("image_file", "image.png")
    image_path = common.bundle_file(bundle_dir, image_rel)

    # Metadata of the final image.
    final_meta = None
    if os.path.exists(image_path):
        try:
            with Image.open(image_path) as im:
                exif = {}
                try:
                    exif = {str(k): str(v) for k, v in (im.getexif() or {}).items()}
                except Exception:
                    exif = {}
                final_meta = {"format": im.format, "size": list(im.size),
                              "mode": im.mode, "info_keys": sorted(str(k) for k in im.info.keys())}
                checks.append({
                    "name": "final_image_metadata",
                    "result": True,
                    "detail": f"format {im.format}, size {im.size}, mode {im.mode}, "
                              f"info keys {final_meta['info_keys']}, EXIF entries {len(exif)}: {exif}",
                })
        except Exception as exc:
            checks.append({
                "name": "final_image_metadata",
                "result": False,
                "detail": f"could not open final image with PIL: {exc}",
            })
    else:
        checks.append({
            "name": "final_image_metadata",
            "result": False,
            "detail": "final image missing on disk",
        })

    # Signature scan per file, final image reported separately.
    hits_by_path = {}
    all_paths = [image_rel] + [e.get("path", "") for e in manifest.get("files", [])]
    for rel in dict.fromkeys(p for p in all_paths if p):
        path = common.bundle_file(bundle_dir, rel)
        if not os.path.exists(path):
            continue
        hits = signature_hits(path)
        hits_by_path[rel] = hits
        checks.append({
            "name": f"ai_signature_scan:{rel}",
            "result": True,
            "detail": f"AI generator signature hits: {hits if hits else 'none'}"
                      + (" (final image: reported, does not by itself fail items)"
                         if rel == image_rel and hits else ""),
        })

    # Dimension and format consistency between final and layered exports.
    consistency_ok = None
    exports = common.find_entries(manifest, role="layered_export")
    if exports and final_meta:
        consistency_ok = True
        for entry in exports:
            path = common.bundle_file(bundle_dir, entry["path"])
            try:
                with Image.open(path) as im:
                    same = list(im.size) == final_meta["size"] and im.format == final_meta["format"]
                checks.append({
                    "name": f"export_consistency:{entry['path']}",
                    "result": bool(same),
                    "detail": f"export format and size compared to final image ({final_meta['format']} {final_meta['size']})",
                })
                consistency_ok = consistency_ok and bool(same)
            except Exception as exc:
                consistency_ok = False
                checks.append({
                    "name": f"export_consistency:{entry['path']}",
                    "result": False,
                    "detail": f"could not open layered export: {exc}",
                })

    if not integrity_ok:
        return {"checks": checks, "verified_items": [], "threshold": None, "notes": notes}

    claimed = list(common.FULL_MENU)
    challenge_code = manifest.get("challenge_code", "")

    def artifact_hits(item):
        rels = [e["path"] for e in common.find_entries(manifest, item=item)]
        found = {}
        for rel in rels:
            if hits_by_path.get(rel):
                found[rel] = hits_by_path[rel]
        return found

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
        entries = common.find_entries(manifest, item="layered_source_file")
        hits = artifact_hits("layered_source_file")
        ok = bool(entries) and not hits and consistency_ok is not False
        if consistency_ok is None and entries:
            ok = bool(entries) and not hits
            checks.append({
                "name": "verify:layered_source_file",
                "result": bool(ok),
                "detail": "no layered_export to compare dimensions with, verdict follows artifact signature scan",
            })
        else:
            checks.append({
                "name": "verify:layered_source_file",
                "result": bool(ok),
                "detail": f"entries {len(entries)}, artifact signature hits {hits}, export consistency {consistency_ok}",
            })
        if ok:
            verified.append("layered_source_file")

    if "progress_sketches" in claimed:
        entries = common.find_entries(manifest, item="progress_sketches")
        hits = artifact_hits("progress_sketches")
        ok = bool(entries) and not hits
        checks.append({
            "name": "verify:progress_sketches",
            "result": bool(ok),
            "detail": f"entries {len(entries)}, artifact signature hits {hits}",
        })
        if ok:
            verified.append("progress_sketches")

    if "live_redraw" in claimed:
        entries = common.find_entries(manifest, item="live_redraw")
        name_ok = bool(entries) and all(challenge_code and challenge_code in os.path.basename(e["path"]) for e in entries)
        for entry in entries:
            checks.append({
                "name": f"redraw_filename_challenge_code:{entry['path']}",
                "result": bool(challenge_code and challenge_code in os.path.basename(entry["path"])),
                "detail": f"file name must contain challenge_code {challenge_code}",
            })
        hits = artifact_hits("live_redraw")
        ok = bool(entries) and name_ok and not hits
        checks.append({
            "name": "verify:live_redraw",
            "result": bool(ok),
            "detail": f"filename challenge code ok {name_ok}, artifact signature hits {hits}",
        })
        if ok:
            verified.append("live_redraw")

    if "continuous_timelapse" in claimed:
        entries = common.find_entries(manifest, item="continuous_timelapse")
        videos = [e for e in entries if os.path.splitext(e.get("path", ""))[1].lower() in common.VIDEO_EXTS]
        hits = artifact_hits("continuous_timelapse")
        ok = bool(videos) and not hits
        checks.append({
            "name": "verify:continuous_timelapse",
            "result": bool(ok),
            "detail": f"video entries {len(videos)}, artifact signature hits {hits}, metadata only",
        })
        if ok:
            verified.append("continuous_timelapse")

    if "aged_social_account" in claimed:
        checks.append({
            "name": "verify:aged_social_account",
            "result": False,
            "detail": "no forensic check for aged_social_account in this bundle format, not verified by Provenance",
        })
    if "live_challenge" in claimed:
        ok = bool(challenge_code) and any(
            challenge_code in os.path.basename(e.get("path", "")) for e in manifest.get("files", [])
        )
        checks.append({
            "name": "verify:live_challenge",
            "result": bool(ok),
            "detail": f"challenge_code {challenge_code} present in a bundle file name: {ok}",
        })
        if ok:
            verified.append("live_challenge")

    return {
        "checks": checks,
        "verified_items": verified,
        "threshold": "an item fails if any forensic check for that item fails",
        "notes": notes,
    }


if __name__ == "__main__":
    run_examiner(
        examiner=EXAMINER,
        role="Provenance",
        short="provenance",
        tool="PIL metadata and EXIF inspection plus raw byte and PNG text chunk signature scan (no ML)",
        analyze_fn=analyze,
    )
