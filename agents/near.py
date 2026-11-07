"""NEAR helpers for the Humanmark swarm.

Reads go through the FastNEAR mirror RPC (rpc.testnet.near.org is
unreachable from this VM). Signed calls go through the official near
CLI with the legacy keychain, so private keys never enter this code;
they stay in ~/.near-credentials where the CLI put them.
"""
import base64
import json
import os
import re
import subprocess
import urllib.request

CONTRACT = os.environ.get("HUMANMARK_CONTRACT", "humanmark.bindingvow1106.testnet")
RPC = "https://rpc.testnet.fastnear.com"
NEAR_BIN = os.path.join(
    os.path.expanduser("~"),
    "tools/near-bin/near-cli-rs-x86_64-unknown-linux-gnu/near",
)


def _rpc(params, method="query"):
    # The FastNEAR mirror intermittently drops connections
    # (RemoteDisconnected) and rate limits bursts; retry with backoff.
    # RPC-level errors (for example a missing contract) are only
    # retried when they look like rate limiting.
    import time

    body = {"jsonrpc": "2.0", "id": "hm", "method": method, "params": params}
    last_exc = None
    for attempt in range(6):
        req = urllib.request.Request(
            RPC,
            data=json.dumps(body).encode("utf-8"),
            headers={"content-type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as res:
                data = json.loads(res.read().decode("utf-8"))
        except Exception as exc:  # connection dropped, timeout, 5xx, 429
            last_exc = exc
            time.sleep(1.5 * (attempt + 1))
            continue
        if "error" in data:
            msg = json.dumps(data["error"])
            if "rate" in msg.lower() or "limit" in msg.lower() or "timeout" in msg.lower():
                last_exc = RuntimeError("RPC error: " + msg)
                time.sleep(1.5 * (attempt + 1))
                continue
            raise RuntimeError("RPC error: " + msg)
        return data["result"]
    raise RuntimeError(f"RPC unreachable after retries: {last_exc}")


def view(method, args, contract=None):
    """Call a view method on the Humanmark contract. Returns parsed JSON or None."""
    result = _rpc(
        {
            "request_type": "call_function",
            "account_id": contract or CONTRACT,
            "method_name": method,
            "args_base64": base64.b64encode(json.dumps(args).encode("utf-8")).decode("ascii"),
            "finality": "final",
        }
    )
    raw = result.get("result") or []
    if not raw:
        return None
    return json.loads(bytes(raw).decode("utf-8"))


def view_access_key(account_id, public_key):
    """Return the access key record for (account_id, public_key), or None if absent."""
    try:
        result = _rpc(
            {
                "request_type": "view_access_key",
                "account_id": account_id,
                "public_key": public_key,
                "finality": "final",
            }
        )
    except Exception:
        return None
    return result


def view_access_key_list(account_id):
    """Return the list of access key records for an account (empty list on error).

    Retries a few times because the mirror occasionally returns a
    transient empty or error response for a healthy account.
    """
    import time

    for attempt in range(3):
        try:
            result = _rpc(
                {
                    "request_type": "view_access_key_list",
                    "account_id": account_id,
                    "finality": "final",
                }
            )
            keys = result.get("keys", []) or []
            if keys:
                return keys
        except Exception:
            pass
        if attempt < 2:
            time.sleep(1.5)
    return []


def call(signer, method, args, contract=None, deposit="0 NEAR", gas="100 TeraGas"):
    """Signed contract call via the near CLI. Returns the transaction id or None."""
    cmd = [
        NEAR_BIN,
        "contract", "call-function", "as-transaction",
        contract or CONTRACT, method,
        "json-args", json.dumps(args),
        "prepaid-gas", gas,
        "attached-deposit", deposit,
        "sign-as", signer,
        "network-config", "testnet", "sign-with-legacy-keychain", "send",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0 or "panicked" in out or "ExecutionError" in out:
        raise RuntimeError(f"tx {method} as {signer} failed: {out[-600:]}")
    m = re.search(r"Transaction ID: ([A-Za-z0-9]+)", out)
    return m.group(1) if m else None
