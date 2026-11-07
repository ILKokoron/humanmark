#!/usr/bin/env python3
"""Humanmark swarm orchestrator.

Runs the 5 examiner scripts sequentially as subprocesses with the
venv python, then calls finalize signed as bindingvow1106.testnet
(permissionless on the contract), then prints the final get_case
result. Progress lines are logged to stdout.
Usage: python orchestrator.py --case CASE_ID --bundle DIR [--dry-run]
In dry run mode the examiners only analyze and write reports locally,
and finalize is skipped.
No em dashes are used in any string produced here.
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import near

HERE = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.expanduser("~/workspace/human-cert/venv/bin/python")
EXAMINERS = [
    "examiner1_scanner_a.py",
    "examiner2_scanner_b.py",
    "examiner3_scanner_c.py",
    "examiner4_provenance.py",
    "examiner5_process.py",
]
FINALIZE_SIGNER = "bindingvow1106.testnet"


def main():
    parser = argparse.ArgumentParser(description="Humanmark swarm orchestrator")
    parser.add_argument("--case", required=True, dest="case_id")
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--dry-run", action="store_true",
                        help="run examiners in dry run mode and skip finalize")
    args = parser.parse_args()

    for script in EXAMINERS:
        print(f"[orchestrator] running {script} for case {args.case_id}", flush=True)
        cmd = [VENV_PYTHON, os.path.join(HERE, script),
               "--case", str(args.case_id), "--bundle", args.bundle]
        if args.dry_run:
            cmd.append("--dry-run")
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)
        if proc.stdout:
            print(proc.stdout.strip(), flush=True)
        if proc.returncode != 0:
            print(f"[orchestrator] {script} FAILED with exit code {proc.returncode}", flush=True)
            if proc.stderr:
                print(proc.stderr[-2000:], flush=True)
            sys.exit(proc.returncode)
        print(f"[orchestrator] {script} done", flush=True)

    if args.dry_run:
        print("[orchestrator] dry run, finalize skipped", flush=True)
        return

    from examiner_base import case_id_value

    print(f"[orchestrator] calling finalize as {FINALIZE_SIGNER}", flush=True)
    tx_id = near.call(FINALIZE_SIGNER, "finalize", {"case_id": case_id_value(args.case_id)})
    print(f"[orchestrator] finalize tx: {tx_id}", flush=True)

    print("[orchestrator] final case state:", flush=True)
    case = near.view("get_case", {"case_id": case_id_value(args.case_id)})
    print(json.dumps(case, indent=2), flush=True)


if __name__ == "__main__":
    main()
