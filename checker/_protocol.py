"""Common protocol helper for weil-first-prime checkers.

Supports two invocation modes:
  1. CLI mode (proofctl replay):  python3 checker.py <cert.json>
  2. Bridge mode (proofctl check): stdin = CheckerInputV2 JSON;
                                   cert path from evidence[].path_hint

Usage in a checker's main():
    cert_path, claim_id = resolve_cert_and_claim()
    # ... verify cert ...
    print(json.dumps(build_output(claim_id, obligation_results)))
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def resolve_cert_and_claim() -> tuple[Path | None, str]:
    """Return (cert_path, claim_id).

    CLI mode: argv[1] is the cert path; claim_id derived from cert JSON.
    Bridge mode: stdin has CheckerInputV2; cert path from evidence path_hint.
    """
    # Bridge mode: stdin is a tty means no stdin data; check if data is waiting.
    # Detect by checking if we have a positional argument first.
    if len(sys.argv) >= 2:
        # CLI mode
        cert_path = Path(sys.argv[1])
        try:
            cert_data = json.loads(cert_path.read_bytes())
            claim_id = cert_data.get("claim_id", "")
        except Exception:
            claim_id = ""
        return cert_path, claim_id

    # Bridge mode: read CheckerInputV2 from stdin
    try:
        inp = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"CHECKER PROTOCOL ERROR: malformed CheckerInput: {exc}", file=sys.stderr)
        sys.exit(3)

    claim_id = inp.get("claim_id", "")

    # Find cert path from evidence list
    for ev in inp.get("evidence", []):
        hint = ev.get("local_path", "") or ev.get("path_hint", "")
        if hint and Path(hint).exists():
            return Path(hint), claim_id

    return None, claim_id


def make_output(claim_id: str, obligation_results: list[dict],
                status: str = "CERTIFIED", **extra) -> dict:
    """Build a protocol v2 checker output dict."""
    out: dict = {
        "protocol_version": 2,
        "claim_id": claim_id,
        "obligation_results": obligation_results,
        "status": status,
    }
    out.update(extra)
    return out
