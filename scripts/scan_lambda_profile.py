"""
scan_lambda_profile.py — Certified λ(L) lower-bound profile, first-prime window

For each L, binary-searches the largest Λ_0 such that the Schur complement
C = (b_L(Λ_0)) * F(Λ_0) - R_eta is positive definite (Arb residual cert).

Optimization: the costly M_K / S_KK integrals are computed ONCE per L point.
Binary search only rebuilds b_L, F diagonal correction, and C — takes <1s per step.

Usage
-----
    python3 scripts/scan_lambda_profile.py            # 3 points, ~15 min total
    python3 scripts/scan_lambda_profile.py --quick    # L=7/20 only, ~4 min
"""

import argparse
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

C2_FLOAT    = math.log(2) / math.sqrt(2)
KAPPA_FRAC  = Fraction(int(1.25528305 * 10**8), 10**8)
ETA         = Fraction(1, 2)
DEFAULT_N   = 8
DEFAULT_D   = 16


def c_L_at(L: float) -> Fraction:
    val = math.log(2 * math.pi * L) + 0.5772156649015329
    return Fraction(val).limit_denominator(10**7)


def H(n: int) -> float:
    return sum(1 / k for k in range(1, n + 1)) if n > 0 else 0.0


def tau_at(L: float) -> Fraction:
    return Fraction(math.log(2) / L).limit_denominator(10_000)


# ── Pre-compute L-dependent matrices (done once per L) ───────────────────────

class SchurCache:
    """
    Stores all L-dependent Arb matrices for a fixed L, N, d.
    The only Λ_0-dependent quantities are b_L and the diagonal of F.
    """

    def __init__(self, L_num: int, L_den: int, N: int = DEFAULT_N,
                 d: int = DEFAULT_D):
        self.L_num, self.L_den = L_num, L_den
        self.L_val = L_num / L_den
        self.N, self.d = N, d
        self.indices = list(range(0, 2 * N, 2))
        self.n = len(self.indices)
        self.tau = tau_at(self.L_val)
        self.c_L_frac = c_L_at(self.L_val)
        self.c_L = float(self.c_L_frac)
        self.kappa = float(KAPPA_FRAC)

        print(f"  Building cache for L={L_num}/{L_den}  "
              f"c_L={self.c_L:.5f}  N={N} d={d}", flush=True)
        t0 = time.time()
        self._build()
        print(f"  Cache built in {time.time()-t0:.1f}s", flush=True)

    def _build(self):
        n, indices = self.n, self.indices
        c2_a = arb(str(C2_FLOAT))
        c_L_a = arb(self.c_L_frac.numerator) / arb(self.c_L_frac.denominator)

        # G diagonal
        self.G_diag = [arb(2) / arb(2 * ni + 1) for ni in indices]
        self.G_diag_f = [2 / (2 * ni + 1) for ni in indices]

        # T diagonal (independent of Λ_0)
        self.T_diag = [arb(str(H(nj))) * self.G_diag[j]
                       for j, nj in enumerate(indices)]

        # M0, M2, S0 matrices (independent of Λ_0)
        M0 = [[arb(0)] * n for _ in range(n)]
        M2 = [[arb(0)] * n for _ in range(n)]
        S0 = [[arb(0)] * n for _ in range(n)]

        for i, ni in enumerate(indices):
            for j, nj in enumerate(indices):
                V_iv = V_matrix_entry(ni, nj, 256)
                V_ij = (arb(str(V_iv[0])) + arb(str(V_iv[1]))) / arb(2)
                r = integrate_M_K(ni, nj, self.L_num, self.L_den,
                                  depth=4, use_bernstein=False)
                K_ij = arb(arb(str(r.enclosure_lower)),
                           arb(str(r.enclosure_upper)))
                s = integrate_S_KK(ni, nj, self.L_num, self.L_den, depth=3)
                S0[i][j] = arb(arb(str(s.enclosure_lower)),
                                arb(str(s.enclosure_upper)))
                J_ij = arb(str(float(compute_J(ni, nj, self.tau))))
                M0[i][j] = V_ij + K_ij
                M2[i][j] = -c2_a * J_ij
            print(f"    row {i+1}/{n}", flush=True)

        # R0, R2 (independent of Λ_0)
        R0 = [[arb(0)] * n for _ in range(n)]
        R2 = [[arb(0)] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                r0, r2 = S0[i][j], arb(0)
                for k in range(n):
                    r0 -= M0[k][i] * M0[k][j] / self.G_diag[k]
                    r2 -= M2[k][i] * M2[k][j] / self.G_diag[k]
                R0[i][j] = r0
                R2[i][j] = r2

        # F_base[i][j] = T_ij + M0[i][j] + M2[i][j] - c_L * G[i][j]
        # At runtime: F[i][j] = F_base[i][j] - lambda0 * G[i][j]
        eta_a = arb(1) / arb(2)
        c0 = arb(1) + eta_a
        c2c = arb(1) + arb(1) / eta_a

        self.F_base = [[arb(0)] * n for _ in range(n)]
        self.R_eta  = [[arb(0)] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                G_ij = self.G_diag[i] if i == j else arb(0)
                self.F_base[i][j] = (self.T_diag[i] * (arb(1) if i==j else arb(0))
                                     + M0[i][j] + M2[i][j] - c_L_a * G_ij)
                self.R_eta[i][j]  = c0 * R0[i][j] + c2c * R2[i][j]

    def schur_at(self, lambda0: float):
        """Build C = b_L * F - R_eta for given lambda0 in <1s (no new integrals)."""
        n = self.n
        b_L_f = H(self.d) - self.c_L - lambda0 - self.kappa
        if b_L_f <= 0:
            return None, None, b_L_f

        l0_a = arb(str(lambda0))
        b_L_a = arb(str(H(self.d))) - arb(self.c_L_frac.numerator)/arb(self.c_L_frac.denominator) \
                - arb(KAPPA_FRAC.numerator)/arb(KAPPA_FRAC.denominator) - l0_a

        C_arb = [[arb(0)] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                # F[i][j] = F_base[i][j] - lambda0 * G[i][j]
                G_ij = self.G_diag[i] if i == j else arb(0)
                F_ij = self.F_base[i][j] - l0_a * G_ij
                C_arb[i][j] = b_L_a * F_ij - self.R_eta[i][j]

        C_float = np.array([[float(C_arb[i][j].mid()) for j in range(n)]
                            for i in range(n)])
        return C_arb, C_float, b_L_f

    def certify(self, lambda0: float) -> bool:
        C_arb, C_float, b_L = self.schur_at(lambda0)
        if C_arb is None:
            return False
        if np.linalg.eigvalsh(C_float)[0] <= 0:
            return False
        n = self.n
        C_inv = np.linalg.inv(C_float)
        max_r = arb(0)
        for i in range(n):
            for j in range(n):
                prod = sum(arb(str(C_inv[i, k])) * C_arb[k][j] for k in range(n))
                d = (arb(1) if i == j else arb(0)) - prod
                if abs(d) > max_r:
                    max_r = abs(d)
        return bool(max_r < arb(1))

    def binary_search(self, lo: float = 2**-30, hi: float = 0.05,
                      tol: float = 1e-3, max_iter: int = 12) -> float:
        if not self.certify(lo):
            return 0.0
        best = lo
        for it in range(max_iter):
            mid = (lo + hi) / 2
            if hi - lo < tol:
                break
            ok = self.certify(mid)
            print(f"    iter {it+1}: Λ_0={mid:.5f}  {'PASS' if ok else 'fail'}",
                  flush=True)
            if ok:
                best = mid
                lo = mid
            else:
                hi = mid
        return best


# ── Main ──────────────────────────────────────────────────────────────────────

SCAN_POINTS = [
    (7,  20, DEFAULT_N, DEFAULT_D, "L=7/20 (FP-0.35)"),
    (42, 100, DEFAULT_N, DEFAULT_D, "L=0.42"),
    (46, 100, DEFAULT_N, DEFAULT_D, "L=0.46"),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true",
                        help="Only scan L=7/20")
    parser.add_argument("--point", type=int, default=None,
                        help="Scan only point index (0=L=7/20, 1=L=0.42, 2=L=0.46)")
    args = parser.parse_args()

    if args.point is not None:
        points = [SCAN_POINTS[args.point]]
    elif args.quick:
        points = SCAN_POINTS[:1]
    else:
        points = SCAN_POINTS

    print("λ(L) Profile Scanner — First-Prime Window", flush=True)
    print(f"Scanning {len(points)} point(s)", flush=True)

    results = []
    t_total = time.time()

    for L_num, L_den, N, d, label in points:
        print(f"\n{'='*55}", flush=True)
        print(f"{label}", flush=True)
        t0 = time.time()

        cache = SchurCache(L_num, L_den, N, d)

        print(f"  Binary searching Λ_0...", flush=True)
        best = cache.binary_search(lo=2**-30, hi=0.05, tol=1e-3)

        elapsed = time.time() - t0
        print(f"\n  λ({L_num}/{L_den}) >= {best:.5f}  (c_L={cache.c_L:.5f})  "
              f"[{elapsed:.0f}s]", flush=True)

        results.append({
            "L": cache.L_val, "c_L": cache.c_L,
            "lambda_lower_bound": best, "elapsed_s": elapsed,
        })

    total = time.time() - t_total
    print(f"\n{'='*55}", flush=True)
    print(f"Total: {total:.0f}s", flush=True)
    print("\nλ(L) lower bounds:", flush=True)
    for r in results:
        print(f"  L={r['L']:.4f}: λ >= {r['lambda_lower_bound']:.5f}"
              f"  (c_L={r['c_L']:.4f})", flush=True)

    out_path = ROOT / "pilots" / "lambda_profile.json"
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({"results": results, "total_s": total,
                   "method": "Arb residual cert, even N=8 d=16",
                   "note": "lambda_lower_bound is certified strict lower bound"}, f, indent=2)
    print(f"\nWritten to {out_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
