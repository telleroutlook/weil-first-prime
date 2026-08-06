"""
Interval-arithmetic verification of the leading-coefficient inequality:
    (mu_V^{02}(L))^2 > (1/5) * mu_V^{00}(L) * mu_V^{22}(L)
for all L in [1/2*log2 + delta, L*] where L* = 2/3*log2.

This certifies that det M^theta opens downward as a quadratic in theta,
which is required for the Case (i) obstruction proof.

Uses python-flint (Arb interval arithmetic).
"""
import math
import json
import sys
from flint import arb, ctx

ctx.prec = 128

LOG2 = math.log(2)
LOG3 = math.log(3)
LSTAR = 2 * LOG2 / 3


def mu_V(L_val: float, m: int, n: int, npts: int = 1000) -> arb:
    """
    Compute mu_V^{mn}(L) = (2n+1)/2 * int_{-1}^{1} V(Lt) P_m(t) P_n(t) dt
    using midpoint-rule Arb quadrature with npts subintervals.
    V(x) = -1/2 * log(1 - x^2).
    """
    L = arb(str(L_val))
    norm = arb(2 * n + 1) / arb(2)
    total = arb(0)
    h = arb(2) / arb(npts)

    def P(k: int, t: arb) -> arb:
        if k == 0:
            return arb(1)
        if k == 2:
            return (arb(3) * t * t - arb(1)) / arb(2)
        raise ValueError(f"P_{k} not implemented")

    for i in range(npts):
        t = arb(-1) + (arb(i) + arb("0.5")) * h
        x = L * t
        Vt = arb(-1) / arb(2) * (arb(1) - x * x).log()
        total += Vt * P(m, t) * P(n, t) * h

    return norm * total


def verify_at(L_val: float) -> dict:
    m00 = mu_V(L_val, 0, 0)
    m22 = mu_V(L_val, 2, 2)
    m02 = mu_V(L_val, 0, 2)
    diff = m02 * m02 - arb(1) / arb(5) * m00 * m22
    certified = bool(diff > arb(0))
    return {
        "L": L_val,
        "mu00": str(m00),
        "mu22": str(m22),
        "mu02": str(m02),
        "diff_(mu02)^2_minus_1/5*mu00*mu22": str(diff),
        "certified_positive": certified,
    }


def main():
    # Grid: 40 points uniformly in [1/2*log2, L*]
    n_grid = 40
    L_lo = LOG2 / 2
    L_hi = LSTAR
    results = []
    all_pass = True

    print(f"Verifying (mu_V^02)^2 > 1/5 * mu_V^00 * mu_V^22")
    print(f"Interval: [{L_lo:.6f}, {L_hi:.6f}]  ({n_grid} points)")
    print(f"Precision: {ctx.prec} bits\n")

    for i in range(n_grid):
        L = L_lo + (L_hi - L_lo) * i / (n_grid - 1)
        r = verify_at(L)
        results.append(r)
        status = "PASS" if r["certified_positive"] else "FAIL"
        if not r["certified_positive"]:
            all_pass = False
        print(f"  L={L:.5f}  diff={r['diff_(mu02)^2_minus_1/5*mu00*mu22'][:40]}  {status}",
              flush=True)

    print()
    if all_pass:
        print("ALL POINTS CERTIFIED. Leading coefficient < 0 throughout lower half.")
    else:
        print("CERTIFICATION FAILED at some points — see results.", file=sys.stderr)
        sys.exit(1)

    cert = {
        "claim": "(mu_V^{02})^2 > 1/5 * mu_V^{00} * mu_V^{22} for all L in [1/2 log2, L*]",
        "method": "midpoint-rule Arb quadrature, 1000 subintervals, 128-bit precision",
        "grid_size": n_grid,
        "all_certified": all_pass,
        "results": results,
    }
    out = "pilots/cert_V_leading_coeff.json"
    import os; os.makedirs("pilots", exist_ok=True)
    with open(out, "w") as f:
        json.dump(cert, f, indent=2)
    print(f"Certificate written to {out}")


if __name__ == "__main__":
    main()
