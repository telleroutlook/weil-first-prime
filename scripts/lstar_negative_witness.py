"""
lstar_negative_witness.py — Explicit certified negative witness for L > L*.

M1 acceptance (PLAN 附3): for L beyond the absorption method's critical radius
L*, exhibit an explicit vector w_L for which the Schur complement quadratic form
is strictly negative, i.e. the finite-scale positivity criterion provably fails.

Method (no new integrals; reuses scan_lambda_profile.SchurCache four-term S0):
  1. Build C_arb = b_L*F - R_eta at (L, sector, Λ_0) as an Arb interval matrix.
  2. Take w = the float min-eigenvector of the midpoint matrix (a candidate
     descent direction). Rationalize w to exact Fractions.
  3. Certify wᵀ C_arb w with outward-rounded Arb arithmetic. If its certified
     UPPER endpoint is < 0, then wᵀ C w < 0 for the true matrix — a rigorous
     negative witness (the quadratic form is not positive definite at this L).

This is the honest converse of the certify() path: certify proves > 0 via a
residual bound; here we prove < 0 via a single explicit vector, which needs no
inversion and no residual — just one outward-rounded quadratic form evaluation.

Usage:
    python3 scripts/lstar_negative_witness.py --L 37/100 --sector even
    python3 scripts/lstar_negative_witness.py --L 37/100 --sector even --lambda0 9.3e-10 --out pilots/witness_even_037.json
"""

import argparse
import json
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
from flint import arb, ctx
ctx.prec = 256

from scripts.scan_lambda_profile import SchurCache, SECTOR_ND


def find_witness(L_num: int, L_den: int, sector: str, lambda0: float,
                 resume: bool = False) -> dict:
    N, d = SECTOR_ND[sector]
    cache = SchurCache(L_num, L_den, N, d, sector=sector, resume=resume)
    C_arb, C_float, b_L = cache.schur_at(lambda0)
    if C_arb is None:
        raise ValueError(f"b_L = {b_L:.6f} <= 0 at lambda0={lambda0}; "
                         "no Schur matrix (trivial failure)")
    n = cache.n

    # Symmetrize the float midpoint and take the min-eigenvalue eigenvector.
    A = 0.5 * (C_float + C_float.T)
    evals, evecs = np.linalg.eigh(A)
    w_float = evecs[:, 0]           # eigenvector of the smallest eigenvalue
    min_eig_float = float(evals[0])

    # Rationalize w to exact Fractions with SMALL denominators. wᵀCw is scale-
    # invariant in sign, so we do NOT clear denominators (that produced ~1e40
    # integer entries and a useless ~1e84-wide enclosure). Bounded entries keep
    # the outward-rounded quadratic form tight enough to certify the sign.
    w_frac = [Fraction(float(x)).limit_denominator(1000) for x in w_float]
    # Guard: if rounding collapsed the vector to ~0, keep the raw float weights.
    if all(f == 0 for f in w_frac):
        w_frac = [Fraction(float(x)).limit_denominator(10**6) for x in w_float]

    # Certify wᵀ C_arb w with outward-rounded Arb arithmetic (exact rational w).
    w_a = [arb(f.numerator) / arb(f.denominator) for f in w_frac]
    q = arb(0)
    for i in range(n):
        for j in range(n):
            q = q + w_a[i] * C_arb[i][j] * w_a[j]

    q_lo = float(q.lower())
    q_hi = float(q.upper())
    norm2 = float(sum(f * f for f in w_frac))
    certified_negative = q_hi < 0

    return {
        "L": L_num / L_den, "L_num": L_num, "L_den": L_den,
        "sector": sector, "N": N, "d": d, "lambda0": lambda0,
        "b_L": float(b_L), "c_L": cache.c_L,
        "min_eig_float": min_eig_float,
        "witness_w": [f"{f.numerator}/{f.denominator}" for f in w_frac],
        "witness_norm_sq": norm2,
        "quadratic_form_wCw_enclosure": [q_lo, q_hi],
        "quadratic_form_str": str(q),
        "certified_negative": bool(certified_negative),
        "note": ("wᵀ C w certified enclosure upper endpoint < 0 proves the Schur "
                 "complement is NOT positive definite at this L: an explicit "
                 "negative witness for L > L*."),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--L", required=True, help="L as num/den, e.g. 37/100")
    ap.add_argument("--sector", choices=["even", "odd"], default="even")
    ap.add_argument("--lambda0", type=float, default=2.0**-30,
                    help="Λ_0 shift (default 2^-30, the paper's L_0)")
    ap.add_argument("--resume", action="store_true",
                    help="reuse cached integral matrices if present")
    ap.add_argument("--out", default=None, help="write witness JSON to this path")
    args = ap.parse_args()

    ln, ld = (int(x) for x in args.L.split("/"))
    print(f"Searching negative witness: L={ln}/{ld} [{args.sector}] "
          f"Λ_0={args.lambda0:.3e}", flush=True)
    res = find_witness(ln, ld, args.sector, args.lambda0, resume=args.resume)

    print(f"\n  min_eig (float)   = {res['min_eig_float']:+.6e}", flush=True)
    print(f"  wᵀ C w enclosure  = [{res['quadratic_form_wCw_enclosure'][0]:.4e}, "
          f"{res['quadratic_form_wCw_enclosure'][1]:.4e}]", flush=True)
    print(f"  ||w||²            = {res['witness_norm_sq']}", flush=True)
    if res["certified_negative"]:
        print(f"\n  *** CERTIFIED NEGATIVE WITNESS at L={ln}/{ld} [{args.sector}] ***",
              flush=True)
        print(f"      wᵀ C w < 0 (upper endpoint {res['quadratic_form_wCw_enclosure'][1]:.4e} < 0)",
              flush=True)
        print(f"      The Schur complement is NOT positive definite: L > L*.", flush=True)
    else:
        print(f"\n  NOT certified negative (enclosure straddles/above 0); "
              f"try a different Λ_0 or this L may still be positive.", flush=True)

    if args.out:
        Path(args.out).write_text(json.dumps(res, indent=2, sort_keys=True))
        print(f"\n  witness written to {args.out}", flush=True)
    return 0 if res["certified_negative"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
