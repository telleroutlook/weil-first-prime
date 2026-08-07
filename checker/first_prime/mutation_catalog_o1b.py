"""Mutation catalog for the O1-B first-prime checker (proofctl C11 evidence).

Proves check_first_prime_certificate.py (engine: exact_split -> o1b_gate) is
genuinely sensitive to every term it asserts. This is the C11 companion of
checker/fp035/mutation_catalog.py, but for the o1b Schur path (lem-o1b-even /
lem-o1b-odd), whose assembly is distinct (reads the certified Archimedean base
primitives, builds R0/R2/R_eta/F via o1b_gate, judges the min LDL^T pivot).

Each mutant perturbs ONE building-block matrix (or removes a coercive term) in
the exact same matrix dict the checker assembles (assemble_o1b_matrices) and
judges with the exact same positivity judge (judge_o1b_pivot, raise_on_fail=
False). No assembly or judge logic is duplicated here — a mutant that fails to
move the verdict is a real checker blind spot, not a catalog artefact.

Design follows PROOF_CONSTITUTION PART E:
  - JUDGE-sensitivity mutants (zero the second moment S0, flip M0 diagonal,
    remove kinetic coercivity T) MUST flip or severely move the verdict.
  - RECOMPUTE-verification mutants (large-factor scaling of a small-influence
    term such as S2/M2) must MOVE the pivot measurably, proving the term is
    truly consumed by the computation (not silently omitted).

Output: kill_rate and a catalog digest for the attestation metadata proofctl
C11 requires (mutation_kill_rate == "100%", non-empty mutation_catalog_digest).
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Relative move threshold for a mutant to count as "killed" when it does not
# flip the sign: the pivot must move by at least this fraction of the baseline
# magnitude. Sign flips always count as killed.
REL_MOVE_THRESHOLD = 0.10


def _neg_iv(iv):
    return (-iv[1], -iv[0])


def _scale_iv(iv, factor: Fraction):
    lo, hi = iv[0] * factor, iv[1] * factor
    return (min(lo, hi), max(lo, hi))


def _apply_mutation(mats: dict, name: str) -> dict:
    """Return a mutated copy of the o1b matrix dict for the named mutant."""
    m = copy.deepcopy(mats)
    n = m["N"]
    if name == "S0_zero":
        # Omit the entire (V+K) second moment S0 (retired-bug class: shrinking
        # the residual R0 produces a false-positive pivot).
        m["S0"] = [[(Fraction(0), Fraction(0)) for _ in range(n)] for _ in range(n)]
    elif name == "flip_M0_diag":
        for i in range(n):
            m["M0"][i][i] = _neg_iv(m["M0"][i][i])
    elif name == "T_zero":
        # Remove kinetic coercivity (the T diagonal); the c_L=0 lower bound
        # relies on T for positivity, so zeroing it must be detected.
        m["T_N"] = [[(Fraction(0), Fraction(0)) for _ in range(n)] for _ in range(n)]
    elif name == "M2_scale_100x":
        m["M2"] = [[_scale_iv(m["M2"][i][j], Fraction(100)) for j in range(n)]
                   for i in range(n)]
    elif name == "S2_scale_100x":
        m["S2"] = [[_scale_iv(m["S2"][i][j], Fraction(100)) for j in range(n)]
                   for i in range(n)]
    elif name == "M0_scale_1p5x":
        # Perturb the Archimedean coupling M0 by 1.5x: enters both F and R0, a
        # dominant term — must move the verdict.
        m["M0"] = [[_scale_iv(m["M0"][i][j], Fraction(3, 2)) for j in range(n)]
                   for i in range(n)]
    else:
        raise ValueError(f"unknown mutant {name!r}")
    return m


MUTANTS = [
    ("S0_zero", "judge", "omit the (V+K) second moment S0 (retired-bug class)"),
    ("flip_M0_diag", "judge", "flip sign of M0 diagonal (matrix no longer matches)"),
    ("T_zero", "judge", "remove kinetic coercivity T (loses positivity)"),
    ("M0_scale_1p5x", "recompute", "scale Archimedean coupling M0 by 1.5x (dominant term)"),
    ("M2_scale_100x", "recompute", "scale prime coupling M2 by 100x (probe M2 truly consumed)"),
    ("S2_scale_100x", "recompute", "scale prime self second moment S2 by 100x"),
]


def _load_base(sector: str) -> dict:
    """Replay the Archimedean base and return its certified primitives dict —
    the exact input the o1b checker consumes."""
    from checker.archimedean.replay import replay_archimedean_base
    cert = json.loads((_ROOT / "certs" / f"first-prime-{sector}.json").read_bytes())
    ab = cert["archimedean_base"]
    base_cert   = _ROOT / "certs" / f"archimedean-{sector}.json"
    base_checker = _ROOT / "checker" / "archimedean" / "check_archimedean.py"
    base_schema = _ROOT / "schemas" / "certificate-archimedean-v1.schema.json"
    return replay_archimedean_base(ab, base_cert, base_checker, base_schema)


def run_catalog(sector: str = "even", precision: int = 256,
                verbose: bool = True) -> dict:
    from checker.first_prime.exact_split import (
        assemble_o1b_matrices, judge_o1b_pivot,
    )
    if verbose:
        print(f"  replaying Archimedean base for {sector} sector ...", flush=True)
    base = _load_base(sector)
    mats = assemble_o1b_matrices(sector, base, precision)
    base_res = judge_o1b_pivot(mats, precision, raise_on_fail=False)
    base_val = base_res["min_pivot"]

    results = []
    killed = 0
    for name, kind, desc in MUTANTS:
        mut = _apply_mutation(mats, name)
        val = judge_o1b_pivot(mut, precision, raise_on_fail=False)["min_pivot"]
        sign_flip = (val < 0) != (base_val < 0)
        rel_move = abs(val - base_val) / max(abs(base_val), 1e-12)
        is_killed = sign_flip or rel_move >= REL_MOVE_THRESHOLD
        if is_killed:
            killed += 1
        results.append({
            "mutant": name, "kind": kind, "desc": desc,
            "baseline": base_val, "mutated": val,
            "sign_flip": sign_flip, "rel_move": rel_move,
            "killed": is_killed,
        })
        if verbose:
            tag = "KILLED" if is_killed else "SURVIVED"
            print(f"  [{tag}] {name}: base={base_val:+.6f} -> {val:+.6f} "
                  f"(rel_move={rel_move:.3f}, sign_flip={sign_flip})", flush=True)

    kill_rate = killed / len(MUTANTS)
    catalog_src = json.dumps([m[0] for m in MUTANTS], sort_keys=True)
    catalog_digest = "sha256:" + hashlib.sha256(catalog_src.encode()).hexdigest()
    return {
        "target": f"lem-o1b-{sector}",
        "sector": sector,
        "baseline_min_pivot": base_val,
        "n_mutants": len(MUTANTS), "n_killed": killed,
        "kill_rate": kill_rate,
        "kill_rate_pct": f"{int(round(kill_rate*100))}%",
        "catalog_digest": catalog_digest,
        "mutants": results,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sector", default="even", choices=["even", "odd"])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", default=None, help="write the summary artifact JSON")
    args = ap.parse_args()
    print(f"O1-B mutation catalog — {args.sector} sector", flush=True)
    summary = run_catalog(sector=args.sector, verbose=not args.json)
    print()
    print(f"kill_rate = {summary['kill_rate_pct']} "
          f"({summary['n_killed']}/{summary['n_mutants']})", flush=True)
    print(f"catalog_digest = {summary['catalog_digest']}", flush=True)
    if args.out:
        Path(args.out).write_text(json.dumps(summary, indent=2, sort_keys=True))
        print(f"artifact written to {args.out}", flush=True)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["kill_rate"] == 1.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
