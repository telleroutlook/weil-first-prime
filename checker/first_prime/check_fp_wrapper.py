#!/usr/bin/env python3
"""Wrapper for check_first_prime_certificate.py that injects fixed path arguments.

Invoked by proofctl replay as:
    python3 checker/first_prime/check_fp_wrapper.py <cert_path>

Automatically resolves --base-certificate, --base-checker, --base-schema,
and --theorem-contract relative to the repository root.

The sector (even/odd) is read from the certificate JSON to select the correct
archimedean base certificate.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent


def main() -> int:
    sys.path.insert(0, str(_ROOT))
    from checker._protocol import resolve_cert_and_claim
    cert_path, claim_id = resolve_cert_and_claim()

    if cert_path is None:
        # proofctl check with no evidence: run verification using default cert paths
        # determined by the claim_id
        sector_map = {
            "lem-o1b-even": "even",
            "lem-o1b-odd": "odd",
        }
        sector = sector_map.get(claim_id)
        if sector is None:
            print(f"WRAPPER ERROR: no cert and unknown claim_id {claim_id!r}", file=sys.stderr)
            return 2
        cert_path = _ROOT / "certs" / f"first-prime-{sector}.json"
        if not cert_path.exists():
            print(f"WRAPPER ERROR: default cert not found: {cert_path}", file=sys.stderr)
            return 2

    try:
        cert = json.loads(cert_path.read_bytes())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"WRAPPER ERROR: cannot read certificate: {exc}", file=sys.stderr)
        return 2

    sector = cert.get("sector")
    if sector not in ("even", "odd"):
        print(f"WRAPPER ERROR: unknown sector {sector!r}", file=sys.stderr)
        return 2

    base_cert    = _ROOT / "certs" / f"archimedean-{sector}.json"
    base_checker = _ROOT / "checker" / "archimedean" / "check_archimedean.py"
    base_schema  = _ROOT / "schemas" / "certificate-archimedean-v1.schema.json"
    theorem_contract = _ROOT / "domains" / "fp035" / "contracts" / \
                       "thm-3-rational-absorption-certificate.json"

    import subprocess
    result = subprocess.run(
        [
            sys.executable,
            str(_ROOT / "checker" / "first_prime" / "check_first_prime_certificate.py"),
            str(cert_path),
            "--base-certificate", str(base_cert),
            "--base-checker",     str(base_checker),
            "--base-schema",      str(base_schema),
            "--theorem-contract", str(theorem_contract),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
