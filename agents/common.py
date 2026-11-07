"""Shared helpers for the Humanmark examiners.

Covers bundle loading, sha256 helpers, manifest and file integrity,
perceptual similarity with PIL, base58 decoding, and ed25519
attestation verification (PyNaCl when available, with a compact
pure python Ed25519 verifier vendored as a fallback).
No em dashes are used in any string produced here.
"""
import base64
import hashlib
import json
import os

import numpy as np
from PIL import Image

# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def commitment_for(verified_items, report_hash, salt) -> str:
    """Contract commitment formula, matched exactly:
    sha256 hex of sorted verified_items joined with "," + "|" + report_hash + "|" + salt.
    """
    payload = ",".join(sorted(verified_items)) + "|" + report_hash + "|" + salt
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Base58
# ---------------------------------------------------------------------------

_B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_B58_INDEX = {c: i for i, c in enumerate(_B58_ALPHABET)}


def base58_decode(text: str) -> bytes:
    n = 0
    for ch in text:
        if ch not in _B58_INDEX:
            raise ValueError(f"invalid base58 character: {ch!r}")
        n = n * 58 + _B58_INDEX[ch]
    leading = len(text) - len(text.lstrip("1"))
    body = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    return b"\x00" * leading + body


# ---------------------------------------------------------------------------
# Ed25519 verification: PyNaCl first, pure python fallback (RFC 8032)
# ---------------------------------------------------------------------------

def _ed25519_verify_pure(public_key: bytes, message: bytes, signature: bytes) -> bool:
    """Compact pure python Ed25519 verification, used only if PyNaCl is absent."""
    if len(public_key) != 32 or len(signature) != 64:
        return False
    q = 2 ** 255 - 19
    l = 2 ** 252 + 27742317777372353535851937790883648493
    d = (-121665 * pow(121666, q - 2, q)) % q

    def decode_point(b):
        y = int.from_bytes(b, "little") & ((1 << 255) - 1)
        sign = (b[31] >> 7) & 1
        if y >= q:
            return None
        x2 = (y * y - 1) * pow(d * y * y + 1, q - 2, q) % q
        x = pow(x2, (q + 3) // 8, q)
        if (x * x - x2) % q != 0:
            x = x * pow(2, (q - 1) // 4, q) % q
        if (x * x - x2) % q != 0:
            return None
        if x & 1 != sign:
            x = q - x
        return (x, y)

    def add(p, qq):
        x1, y1 = p
        x2, y2 = qq
        t = d * x1 * x2 * y1 * y2 % q
        x3 = (x1 * y2 + x2 * y1) * pow(1 + t, q - 2, q) % q
        y3 = (y1 * y2 + x1 * x2) * pow(1 - t, q - 2, q) % q
        return (x3, y3)

    def mul(p, e):
        result = (0, 1)
        cur = p
        while e > 0:
            if e & 1:
                result = add(result, cur)
            cur = add(cur, cur)
            e >>= 1
        return result

    def encode_point(p):
        x, y = p
        b = bytearray(y.to_bytes(32, "little"))
        b[31] |= (x & 1) << 7
        return bytes(b)

    try:
        a_point = decode_point(public_key)
        r_bytes = signature[:32]
        s = int.from_bytes(signature[32:], "little")
        if a_point is None or decode_point(r_bytes) is None or s >= l:
            return False
        h = int.from_bytes(hashlib.sha512(r_bytes + public_key + message).digest(), "little")
        # Base point from its canonical encoding (0x58 followed by 0x66 * 31).
        b_point = decode_point(bytes.fromhex("58" + "66" * 31))
        left = mul(b_point, s)
        right = add(decode_point(r_bytes), mul(a_point, h))
        return encode_point(left) == encode_point(right)
    except Exception:
        return False


def ed25519_verify(public_key: bytes, message: bytes, signature: bytes) -> bool:
    try:
        from nacl.signing import VerifyKey
        from nacl.exceptions import BadSignatureError

        try:
            VerifyKey(public_key).verify(message, signature)
            return True
        except BadSignatureError:
            return False
    except ImportError:
        return _ed25519_verify_pure(public_key, message, signature)


# ---------------------------------------------------------------------------
# Bundle loading and integrity
# ---------------------------------------------------------------------------

VIDEO_EXTS = {".mp4", ".mov", ".webm", ".mkv", ".avi"}


def load_bundle(bundle_dir):
    """Load manifest.json from a bundle folder. Returns (manifest, manifest_bytes)."""
    manifest_path = os.path.join(bundle_dir, "manifest.json")
    with open(manifest_path, "rb") as f:
        manifest_bytes = f.read()
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    return manifest, manifest_bytes


def bundle_file(bundle_dir, rel_path):
    return os.path.join(bundle_dir, rel_path)


def find_entries(manifest, item=None, role=None):
    out = []
    for entry in manifest.get("files", []) or []:
        if item is not None and entry.get("item") != item:
            continue
        if role is not None and entry.get("role") != role:
            continue
        out.append(entry)
    return out


def verify_integrity(bundle_dir, case):
    """Integrity layer shared by all examiners.

    Checks: image file sha256 equals onchain image_hash, manifest.json
    sha256 equals onchain bundle_hash, and every files[] entry hash
    matches the file on disk. Returns (ok, checks list).
    """
    checks = []
    manifest, manifest_bytes = load_bundle(bundle_dir)

    manifest_hash = sha256_bytes(manifest_bytes)
    expected_bundle = (case or {}).get("bundle_hash")
    ok_bundle = expected_bundle is not None and manifest_hash == expected_bundle
    checks.append({
        "name": "bundle_hash_matches_chain",
        "result": bool(ok_bundle),
        "detail": f"manifest sha256 {manifest_hash} vs onchain bundle_hash {expected_bundle}",
    })

    image_file = manifest.get("image_file", "image.png")
    image_path = bundle_file(bundle_dir, image_file)
    expected_image = (case or {}).get("image_hash")
    if os.path.exists(image_path):
        image_hash = sha256_file(image_path)
        ok_image = expected_image is not None and image_hash == expected_image
        checks.append({
            "name": "image_hash_matches_chain",
            "result": bool(ok_image),
            "detail": f"image sha256 {image_hash} vs onchain image_hash {expected_image}",
        })
    else:
        checks.append({
            "name": "image_hash_matches_chain",
            "result": False,
            "detail": f"image file missing on disk: {image_file}",
        })

    all_files_ok = True
    for entry in manifest.get("files", []) or []:
        rel = entry.get("path", "")
        path = bundle_file(bundle_dir, rel)
        expected = entry.get("sha256")
        if not os.path.exists(path):
            checks.append({
                "name": f"file_hash:{rel}",
                "result": False,
                "detail": "file listed in manifest is missing on disk",
            })
            all_files_ok = False
            continue
        actual = sha256_file(path)
        match = actual == expected
        if not match:
            all_files_ok = False
        checks.append({
            "name": f"file_hash:{rel}",
            "result": bool(match),
            "detail": f"sha256 {actual} vs manifest {expected}",
        })

    ok = bool(ok_bundle) and any(
        c["name"] == "image_hash_matches_chain" and c["result"] for c in checks
    ) and all_files_ok
    return ok, checks, manifest


# ---------------------------------------------------------------------------
# Perceptual similarity (PIL, grayscale 64x64 thumbnails)
# ---------------------------------------------------------------------------

def _thumb_array(image: Image.Image) -> np.ndarray:
    gray = image.convert("L").resize((64, 64))
    return np.asarray(gray, dtype=np.float64)


def _sim_from_arrays(a: np.ndarray, b: np.ndarray) -> float:
    return float(1.0 - np.mean(np.abs(a - b)) / 255.0)


def perceptual_sim(path_a, path_b):
    """sim = 1 - mean_abs_diff/255 over grayscale 64x64 thumbnails."""
    a = _thumb_array(Image.open(path_a))
    b = _thumb_array(Image.open(path_b))
    return _sim_from_arrays(a, b)


def perceptual_sim_images(img_a: Image.Image, img_b: Image.Image):
    return _sim_from_arrays(_thumb_array(img_a), _thumb_array(img_b))


def crop_relative(image_path, region):
    """Crop an image to a relative region [x0, y0, x1, y1] in 0..1 coordinates."""
    img = Image.open(image_path)
    w, h = img.size
    x0, y0, x1, y1 = region
    box = (int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h))
    return img.crop(box)


def redraw_sim(bundle_dir, manifest, redraw_entry):
    """Similarity between a redraw file and the final image cropped to its region."""
    image_path = bundle_file(bundle_dir, manifest.get("image_file", "image.png"))
    redraw_path = bundle_file(bundle_dir, redraw_entry["path"])
    region = redraw_entry.get("region") or [0.0, 0.0, 1.0, 1.0]
    cropped = crop_relative(image_path, region)
    redraw_img = Image.open(redraw_path)
    return perceptual_sim_images(redraw_img, cropped)


# ---------------------------------------------------------------------------
# Attestation verification
# ---------------------------------------------------------------------------

def get_attestation(bundle_dir, manifest):
    """Attestation dict from the manifest, falling back to attestation.json on disk."""
    att = manifest.get("attestation")
    if att:
        return att
    for entry in manifest.get("files", []) or []:
        if os.path.basename(entry.get("path", "")) == "attestation.json":
            path = bundle_file(bundle_dir, entry["path"])
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
    path = bundle_file(bundle_dir, "attestation.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def verify_attestation(bundle_dir, manifest, artist, check_onchain=True):
    """Verify the passkey style attestation.

    Steps: parse the ed25519 public key (base58), verify the signature
    over attestation.message bytes, and (unless disabled) confirm the
    public key belongs to the artist account onchain via
    view_access_key_list. Returns (ok, checks list).
    """
    checks = []
    att = get_attestation(bundle_dir, manifest)
    if not att:
        checks.append({
            "name": "attestation_present",
            "result": False,
            "detail": "no attestation in manifest and no attestation.json in bundle",
        })
        return False, checks
    checks.append({
        "name": "attestation_present",
        "result": True,
        "detail": f"attestation for account {att.get('account_id')}",
    })

    pub = att.get("public_key", "")
    pub_bytes = None
    try:
        raw = pub.split(":", 1)[1] if pub.startswith("ed25519:") else pub
        pub_bytes = base58_decode(raw)
        ok_len = len(pub_bytes) == 32
        checks.append({
            "name": "attestation_public_key_parse",
            "result": bool(ok_len),
            "detail": f"public_key {pub} decoded to {len(pub_bytes)} bytes",
        })
        if not ok_len:
            return False, checks
    except Exception as exc:
        checks.append({
            "name": "attestation_public_key_parse",
            "result": False,
            "detail": f"base58 decode failed: {exc}",
        })
        return False, checks

    account_match = att.get("account_id") == artist
    checks.append({
        "name": "attestation_account_matches_artist",
        "result": bool(account_match),
        "detail": f"attestation account_id {att.get('account_id')} vs artist {artist}",
    })

    sig_ok = False
    try:
        signature = base64.b64decode(att.get("signature_b64", ""))
        message = (att.get("message", "") or "").encode("utf-8")
        sig_ok = ed25519_verify(pub_bytes, message, signature)
        checks.append({
            "name": "attestation_signature_valid",
            "result": bool(sig_ok),
            "detail": "ed25519 signature over attestation.message verified"
            if sig_ok else "ed25519 signature over attestation.message did NOT verify",
        })
    except Exception as exc:
        checks.append({
            "name": "attestation_signature_valid",
            "result": False,
            "detail": f"signature decode or verify error: {exc}",
        })

    owner_ok = False
    if check_onchain:
        try:
            from near import view_access_key_list

            keys = view_access_key_list(artist)
            onchain_keys = [k.get("public_key") for k in keys]
            owner_ok = pub in onchain_keys
            checks.append({
                "name": "attestation_key_owned_onchain",
                "result": bool(owner_ok),
                "detail": f"artist access keys onchain: {onchain_keys}",
            })
        except Exception as exc:
            checks.append({
                "name": "attestation_key_owned_onchain",
                "result": False,
                "detail": f"onchain key lookup failed: {exc}",
            })
    else:
        checks.append({
            "name": "attestation_key_owned_onchain",
            "result": False,
            "detail": "onchain key lookup skipped in this run",
        })

    ok = bool(account_match and sig_ok and (owner_ok if check_onchain else sig_ok))
    # In dry runs without onchain lookup the signature alone decides, and
    # the skipped lookup stays visible as a failed check in the report.
    if not check_onchain:
        ok = bool(account_match and sig_ok)
    return ok, checks
