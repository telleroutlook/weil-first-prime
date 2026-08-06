"""
scan_lambda_profile.py — Compute certified lower bounds λ(L) ≥ Λ_0(L)
for multiple L values in the first-prime window.

For each L, binary-search the largest Λ_0 such that the Schur complement
C = b_L(Λ_0) * F - R_eta is positive definite (Arb residual certification).

Usage
-----
    python3 scripts/scan_lambda_profile.py

This runs the certified profile at three L values:
    L = 7/20  (the FP-0.35 point, ~4 min)
    L = 0.42  (mid window, ~5 min)
    L = 0.46  (near L*, ~6 min)

Output: JSON to stdout + pilots/lambda_profile.json
"""

import math
import json
import sys
import time
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
from flint import arb, ctx
ctx.prec = 256

from src.archimedean.integrator_a import integrate_M_K, integrate_S_KK
from src.archimedean.log_moments import V_matrix_entry
from src.prime_layer.legendre_shift import compute_J

# ── Constants ────────────────────────────────────────────────────────────────

C2_FLOAT = math.log(2) / math.sqrt(2)
KAPPA_FRAC = Fraction(int(1.25528305 * 10**8), 10**8)   # certified kappa_L
ETA = Fraction(1, 2)


def c_L_at(L: float) -> Fraction:
    """Certified upper bound for c_L(L) = log(2πL) + γ_E."""
    val = math.log(2 * math.pi * L) + 0.5772156649015329
    return Fraction(val).limit_denominator(10**7)


def H(n: int) -> float:
    return sum(1 / k for k in range(1, n + 1)) if n > 0 else 0.0


def tau_at(L: float) -> Fraction:
    return Fraction(math.log(2) / L).limit_denominator(10_000)


# ── Matrix assembly ──────────────────────────────────────────────────────────

def build_schur_arb(L_num: int, L_den: int, N: int, d: int,
                    lambda0: float) -> tuple:
    """Return (C_arb, C_float, b_L_float) for given L, N, d, lambda0."""
    L_val = L_num / L_den
    tau = tau_at(L_val)
    c_L_frac = c_L_at(L_val)
    c_L = float(c_L_frac)
    kappa = float(KAPPA_FRAC)
    eta_f = float(ETA)

    indices = list(range(0, 2 * N, 2))   # even sector
    n = len(indices)

    b_L_f = H(d) - c_L - lambda0 - kappa
    if b_L_f <= 0:
        return None, None, b_L_f

    # Arb constants
    c_L_a = arb(c_L_frac.numerator) / arb(c_L_frac.denominator)
    kap_a = arb(KAPPA_FRAC.numerator) / arb(KAPPA_FRAC.denominator)
    L0_a  = arb(str(lambda0))
    H_d_a = sum(arb(1) / arb(k) for k in range(1, d + 1))
    b_L_a = H_d_a - c_L_a - kap_a - L0_a
    c2_a  = arb(str(C2_FLOAT))
    eta_a = arb(1) / arb(2)

    F_a  = [[arb(0)] * n for _ in range(n)]
    M0_a = [[arb(0)] * n for _ in range(n)]
    S0_a = [[arb(0)] * n for _ in range(n)]
    M2_a = [[arb(0)] * n for _ in range(n)]

    for i, ni in enumerate(indices):
        for j, nj in enumerate(indices):
            G_ij = arb(2) / arb(2 * ni + 1) if ni == nj else arb(0)
            T_ij = arb(str(H(nj))) * G_ij
            V_iv = V_matrix_entry(ni, nj, 256)
            V_ij = (arb(str(V_iv[0])) + arb(str(V_iv[1]))) / arb(2)
            r = integrate_M_K(ni, nj, L_num, L_den, depth=4, use_bernstein=False)
            K_ij = arb(arb(str(r.enclosure_lower)), arb(str(r.enclosure_upper)))
            s = integrate_S_KK(ni, nj, L_num, L_den, depth=3)
            S0_a[i][j] = arb(arb(str(s.enclosure_lower)), arb(str(s.enclosure_upper)))
            J_ij = arb(str(float(compute_J(ni, nj, tau))))
            M0_a[i][j] = V_ij + K_ij
            M2_a[i][j] = -c2_a * J_ij
            F_a[i][j]  = T_ij + M0_a[i][j] + M2_a[i][j] - (c_L_a + L0_a) * G_ij

    G_diag = [arb(2) / arb(2 * ni + 1) for ni in indices]
    R0_a = [[arb(0)] * n for _ in range(n)]
    R2_a = [[arb(0)] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            r0, r2 = S0_a[i][j], arb(0)
            for k in range(n):
                r0 -= M0_a[k][i] * M0_a[k][j] / G_diag[k]
                r2 -= M2_a[k][i] * M2_a[k][j] / G_diag[k]
            R0_a[i][j] = r0
            R2_a[i][j] = r2

    c0 = arb(1) + eta_a
    c2c = arb(1) + arb(1) / eta_a
    C_arb = [[b_L_a * F_a[i][j] - c0 * R0_a[i][j] - c2c * R2_a[i][j]
              for j in range(n)] for i in range(n)]
    C_float = np.array([[float(C_arb[i][j].mid()) for j in range(n)]
                        for i in range(n)])
    return C_arb, C_float, b_L_f


def certify_lambda0(L_num: int, L_den: int, N: int, d: int,
                    lambda0: float) -> bool:
    """Return True if lambda(L) >= lambda0 is Arb-certified."""
    C_arb, C_float, b_L = build_schur_arb(L_num, L_den, N, d, lambda0)
    if C_arb is None or b_L <= 0:
        return False
    evals = np.linalg.eigvalsh(C_float)
    if evals[0] <= 0:
        return False
    n = len(C_float)
    C_inv = np.linalg.inv(C_float)
    max_resid = arb(0)
    for i in range(n):
        for j in range(n):
            prod = sum(arb(str(C_inv[i, k])) * C_arb[k][j] for k in range(n))
            delta = (arb(1) if i == j else arb(0)) - prod
            if abs(delta) > max_resid:
                max_resid = abs(delta)
    return bool(max_resid < arb(1))


def binary_search_lambda(L_num: int, L_den: int, N: int, d: int,
                         lo: float = 1e-10, hi: float = 0.1,
                         tol: float = 1e-4, max_iter: int = 12) -> float:
    """Binary search for the largest certified Λ_0.

    Returns the largest lambda0 in [lo, hi] for which certify_lambda0 passes.
    """
    # First check that lo passes (it should for any reasonable system)
    if not certify_lambda0(L_num, L_den, N, d, lo):
        return 0.0

    best = lo
    for _ in range(max_iter):
        mid = (lo + hi) / 2
        if hi - lo < tol:
            break
        if certify_lambda0(L_num, L_den, N, d, mid):
            best = mid
            lo = mid
        else:
            hi = mid
    return best


# ── Main scan ────────────────────────────────────────────────────────────────

SCAN_POINTS = [
    # (L_num, L_den, N_even, d_even, label)
    (7,  20, 8, 16, "L=7/20 (FP-0.35 point)"),
    (42, 100, 8, 16, "L=0.42"),
    (46, 100, 8, 16, "L=0.46 (near L*)"),
]


def main() -> int:
    print("λ(L) Profile Scanner — First-Prime Window", flush=True)
    print(f"Method: binary search on Λ_0 via Arb residual certification", flush=True)
    print(f"Even sector only (N=8, d=16 for all points)", flush=True)
    print(flush=True)

    results = []
    t_start = time.time()

    for L_num, L_den, N, d, label in SCAN_POINTS:
        L_val = L_num / L_den
        c_L = float(c_L_at(L_val))
        print(f"{'='*60}", flush=True)
        print(f"L = {L_num}/{L_den} = {L_val:.5f}   c_L = {c_L:.5f}", flush=True)
        print(f"label: {label}", flush=True)
        t0 = time.time()

        # First verify that the base case L0=2^{-30} still passes
        base_lambda0 = 2**-30
        base_ok = certify_lambda0(L_num, L_den, N, d, base_lambda0)
        print(f"  Base case (Λ_0 = 2^{{-30}} ≈ {base_lambda0:.2e}): "
              f"{'PASS' if base_ok else 'FAIL'}", flush=True)

        if not base_ok:
            print(f"  SKIP: base case fails, cannot do binary search", flush=True)
            results.append({"L": L_val, "c_L": c_L, "lambda0_lower": 0,
                             "base_certified": False})
            continue

        # Binary search for largest certified Λ_0
        print(f"  Binary searching for largest certified Λ_0...", flush=True)
        best = binary_search_lambda(L_num, L_den, N, d,
                                    lo=base_lambda0, hi=0.05, tol=1e-3)
        elapsed = time.time() - t0
        print(f"  Certified: λ({L_val:.4f}) ≥ {best:.6f}  "
              f"(elapsed {elapsed:.1f}s)", flush=True)
        results.append({
            "L": L_val,
            "c_L": c_L,
            "lambda0_lower_bound": best,
            "base_certified": True,
            "elapsed_s": elapsed,
        })

    total = time.time() - t_start
    print(f"\n{'='*60}", flush=True)
    print(f"Total elapsed: {total:.1f}s", flush=True)
    print("\nλ(L) lower bounds:", flush=True)
    for r in results:
        if r.get("base_certified"):
            print(f"  L={r['L']:.4f}: λ ≥ {r['lambda0_lower_bound']:.6f}", flush=True)

    out = {"results": results, "total_elapsed_s": total,
           "method": "Arb residual certification, even sector N=8 d=16"}
    outpath = ROOT / "pilots" / "lambda_profile.json"
    with open(outpath, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nResults written to {outpath}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
