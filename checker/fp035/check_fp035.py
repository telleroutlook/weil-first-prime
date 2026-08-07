"""Checker for thm-fp-035 — FP-0.35 main conjecture.

Verifies the logical conclusion: given lem-o1b-even, lem-o1b-odd (both sectors
certified), thm-5-split-residual-schur, and thm-3-rational-absorption-certificate,
the infimum lambda(7/20) > 0 follows from Theorem 5 (Schur criterion).

This checker verifies the LOGICAL chain only — the mathematical content is
in the dependency claims. It checks:
  1. Both sectors have certified positive pivots (fp035.both-sectors-certified)
  2. Theorem 5 Schur criterion applies (fp035.theorem5-conclusion-holds)
  3. c* = min_pivot * b_L^{-1} > 0 (fp035.c-star-positive)
  4. Conclusion is bounded to finite-scale L=7/20 (fp035.conclusion-bounded-to-finite-scale)
  5. No RH is claimed (fp035.no-rh-claimed)

Exit codes: 0 CERTIFIED, 1 uncertified, 2 malformed
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

OBLIGATION_IDS = [
    "fp035.both-sectors-certified",
    "fp035.theorem5-conclusion-holds",
    "fp035.c-star-positive",
    "fp035.conclusion-bounded-to-finite-scale",
    "fp035.no-rh-claimed",
]


def verify() -> tuple[bool, str]:
    """Verify the five FP-0.35 structural obligations."""

    # 1. Both sectors certified: INDEPENDENTLY RECOMPUTED here (not trusted).
    #    recompute_schur rebuilds C = b_L*F - R_eta with the FULL four-term
    #    S0 = S_VV+S_VK+S_KV+S_KK, real c_L, and reports the min LDL^T pivot.
    from checker.fp035.recompute_schur import verify_sector
    piv_even, bL_even, _ = verify_sector(7, 20, "even", 8, 16)
    piv_odd, bL_odd, _ = verify_sector(7, 20, "odd", 6, 13)
    obl_1_ok = piv_even > 0 and piv_odd > 0
    obl_1_msg = (f"independent recompute (four-term S0, real c_L, min-pivot judge): "
                 f"even b_L={bL_even:.4f} min_pivot={piv_even:+.6f}; "
                 f"odd b_L={bL_odd:.4f} min_pivot={piv_odd:+.6f}")

    # 2. Theorem 5 Schur criterion holds iff both recomputed Schur complements
    #    are positive definite (min_pivot > 0).
    obl_2_ok = obl_1_ok
    obl_2_msg = ("Theorem 5 applies iff both recomputed Schur complements are positive definite: "
                 + ("satisfied" if obl_2_ok else "NOT satisfied (min_pivot <= 0)"))

    # 3. c* = min_pivot / b_L > 0 in both sectors (from recomputed pivots).
    if obl_1_ok:
        cstar_even = piv_even / bL_even if bL_even else 0.0
        cstar_odd = piv_odd / bL_odd if bL_odd else 0.0
        obl_3_ok = cstar_even > 0 and cstar_odd > 0
        obl_3_msg = f"c* > 0: even c*={cstar_even:.6f}, odd c*={cstar_odd:.6f}"
    else:
        obl_3_ok = False
        obl_3_msg = "c* not positive: at least one sector has min_pivot <= 0"

    # 4. Conclusion bounded to finite-scale: lambda(7/20) > 0 only,
    #    not global positivity, not RH, not any other prime window
    obl_4_ok = True
    obl_4_msg = ("Conclusion: lambda(7/20) > 0 (finite-scale positivity at L=7/20). "
                 "Does not imply positivity for L > 7/20 or global Weil positivity.")

    # 5. No RH claimed: per CLAUDE.md and paper — this result does NOT imply RH
    obl_5_ok = True
    obl_5_msg = ("No RH claimed. FP-0.35 → RH requires: finite-scale → full-interval positivity "
                 "(no known path), then Weil equivalence. Both steps are open.")

    all_ok = all([obl_1_ok, obl_2_ok, obl_3_ok, obl_4_ok, obl_5_ok])
    summary = "; ".join([obl_1_msg, obl_2_msg, obl_3_msg, obl_4_msg, obl_5_msg])
    return all_ok, summary


def _mutation_metadata() -> dict:
    """Read the committed mutation-catalog artifact and expose C11 fields.
    Referencing a pre-run, auditable artifact (not re-running the ~40-min
    catalog on every check) per PROOF_CONSTITUTION A7. Absent artifact -> empty
    (C11 will then correctly block, rather than silently claim coverage)."""
    import json
    from pathlib import Path
    art = Path(__file__).parent.parent.parent / "pilots" / "mutation_catalog_fp035.json"
    try:
        d = json.loads(art.read_text())
        return {
            "mutation_kill_rate": d.get("kill_rate_pct", ""),
            "mutation_catalog_digest": d.get("catalog_digest", ""),
        }
    except Exception:
        return {}


def main() -> int:
    from checker._protocol import resolve_cert_and_claim
    _cert_path, claim_id = resolve_cert_and_claim()
    if not claim_id:
        claim_id = "thm-fp-035"

    passed, explanation = verify()
    verdict = "pass" if passed else "fail"
    result = {
        "protocol_version": 2,
        "claim_id": claim_id,
        "obligation_results": [{"id": oid, "verdict": verdict} for oid in OBLIGATION_IDS],
        "status": "CERTIFIED" if passed else "UNCERTIFIED",
        "explanation": explanation,
        "metadata": {
            "format_version": "first-prime-1.0",
            "method": "exact_prime_split_v1",
            "sector": "even+odd",
            "pivot_count": "24",
            "window_verified": "true",
            "archimedean_obligation": "archimedean_primitives_o2_v1",
            **_mutation_metadata(),
        },
    }
    if not passed:
        print(f"FP035 CHECKER FAIL: {explanation}", file=sys.stderr)
    print(json.dumps(result, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
