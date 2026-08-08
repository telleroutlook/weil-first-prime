"""cvs_form2_check.py — Verify form2 structure of real C(L) to confirm CvS non-applicability.

CvS applicability requires C(L) ∈ form2:
  (1) additive chain: c_ij + c_jk = c_ik  where c_ij = (n_i - n_j) * C[i][j]
  (2) η (all-ones vector) lies in range of commutator [D, C]

The report (CvS-applicability-verdict-Tphi.md) showed this breaks in abstract Schur
complement models. This script confirms it directly on the project's real C(L).

Usage:
    python3 scripts/cvs_form2_check.py
    python3 scripts/cvs_form2_check.py --sector odd
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
from flint import arb, ctx
ctx.prec = 128  # draft precision — structural check only

from src.archimedean.integrator_a import integrate_M_K, integrate_S_VK, integrate_S_KK
from src.archimedean.log_moments import V_matrix_entry, V2_matrix_entry
from src.prime_layer.legendre_shift import compute_J, compute_E

C2_FLOAT = math.log(2) / math.sqrt(2)
KAPPA_FRAC = Fraction(int(1.25528305 * 10**8), 10**8)
ETA = Fraction(1, 2)


def c_L_at(L: float) -> float:
    return math.log(2 * math.pi * L) + 0.5772156649015329


def H(n: int) -> float:
    return sum(1 / k for k in range(1, n + 1)) if n > 0 else 0.0


def tau_frac(L_num: int, L_den: int) -> Fraction:
    from fractions import Fraction
    import math
    val = math.log(2) * L_den / L_num
    return Fraction(val).limit_denominator(10_000)


def build_C_float(L_num: int, L_den: int, sector: str, lambda0: float = 1e-10) -> tuple[np.ndarray, list[int]]:
    """Build the float Schur matrix C = b_L * F - R_eta at given lambda0."""
    L_val = L_num / L_den
    parity = 0 if sector == "even" else 1
    if sector == "even":
        N, d = 8, 16
        indices = list(range(0, 16, 2))
    else:
        N, d = 6, 13
        indices = list(range(1, 12, 2))
    n = len(indices)

    c_L = c_L_at(L_val)
    tau = tau_frac(L_num, L_den)
    c2 = C2_FLOAT
    kappa = float(KAPPA_FRAC)
    b_L = H(d) - c_L - lambda0 - kappa

    print(f"  L={L_num}/{L_den} [{sector}]  c_L={c_L:.5f}  b_L={b_L:.5f}  N={N} d={d}",
          flush=True)

    G_diag = [2 / (2 * ni + 1) for ni in indices]
    T_diag = [H(ni) * G_diag[i] for i, ni in enumerate(indices)]

    M0 = np.zeros((n, n))
    M2 = np.zeros((n, n))
    S0 = np.zeros((n, n))
    S2 = np.zeros((n, n))

    for i, ni in enumerate(indices):
        for j, nj in enumerate(indices):
            v = V_matrix_entry(ni, nj, 128)
            M0[i, j] = (float(v[0]) + float(v[1])) / 2

            r = integrate_M_K(ni, nj, L_num, L_den, depth=2, prec=128, use_bernstein=False)
            M0[i, j] += (r.enclosure_lower + r.enclosure_upper) / 2

            svv = V2_matrix_entry(ni, nj, 128)
            svv_f = (float(svv[0]) + float(svv[1])) / 2
            svk = integrate_S_VK(ni, nj, L_num, L_den, depth=2, prec=128)
            skv = integrate_S_VK(nj, ni, L_num, L_den, depth=2, prec=128)
            skk = integrate_S_KK(ni, nj, L_num, L_den, depth=2, prec=128)
            S0[i, j] = (svv_f
                        + (svk.enclosure_lower + svk.enclosure_upper) / 2
                        + (skv.enclosure_lower + skv.enclosure_upper) / 2
                        + (skk.enclosure_lower + skk.enclosure_upper) / 2)

            J_ij = float(compute_J(ni, nj, tau))
            E_ij = float(compute_E(ni, nj, tau))
            M2[i, j] = -c2 * J_ij
            S2[i, j] = c2 * c2 * E_ij

        print(f"    row {i+1}/{n}", flush=True)

    # R0, R2 = S - M^T G^-1 M
    R0 = S0.copy()
    R2 = S2.copy()
    for i in range(n):
        for j in range(n):
            for k in range(n):
                R0[i, j] -= M0[k, i] * M0[k, j] / G_diag[k]
                R2[i, j] -= M2[k, i] * M2[k, j] / G_diag[k]

    # F[i,j] = T[i,j] + M0[i,j] + M2[i,j] - c_L * G[i,j]
    F = np.zeros((n, n))
    for i in range(n):
        F[i, i] = T_diag[i] - c_L * G_diag[i]
    F += M0 + M2

    # R_eta = (1+eta)*R0 + (1+1/eta)*R2,  eta=1/2
    c0 = 1 + float(ETA)      # = 1.5
    c2c = 1 + 1 / float(ETA)  # = 3.0
    R_eta = c0 * R0 + c2c * R2

    # C = b_L * F - R_eta  (with lambda0 shift absorbed into b_L)
    C = b_L * F - R_eta
    return C, indices


def check_form2(C: np.ndarray, indices: list[int]) -> dict:
    """Check form2 additive chain and η-membership."""
    n = len(indices)
    idx = np.array(indices, dtype=float)

    # c_ij = (n_i - n_j) * C[i,j]
    c = np.zeros((n, n))
    for a in range(n):
        for b in range(n):
            if a != b:
                c[a, b] = (idx[a] - idx[b]) * C[a, b]

    # Additive chain: c_ab + c_bc == c_ac?
    max_chain_err = 0.0
    worst = (0, 0, 0)
    for a in range(n):
        for b in range(n):
            if a == b:
                continue
            for cc in range(n):
                if cc == a or cc == b:
                    continue
                err = abs(c[a, b] + c[b, cc] - c[a, cc])
                if err > max_chain_err:
                    max_chain_err = err
                    worst = (a, b, cc)

    # [D, C]_{ij} = (n_i - n_j) * C[i,j]
    comm = np.zeros((n, n))
    for a in range(n):
        for b in range(n):
            comm[a, b] = (idx[a] - idx[b]) * C[a, b]

    # Check if η = ones is in range of comm
    eta = np.ones(n)
    # Least-squares: comm @ v ≈ η
    v_ls, res, rank, sv = np.linalg.lstsq(comm, eta, rcond=None)
    eta_approx = comm @ v_ls
    eta_residual = np.linalg.norm(eta - eta_approx)

    # Also check commutator rank
    comm_rank = np.linalg.matrix_rank(comm, tol=1e-8)

    return {
        "max_chain_err": float(max_chain_err),
        "worst_triple": [int(x) for x in worst],
        "worst_triple_indices": [indices[worst[0]], indices[worst[1]], indices[worst[2]]],
        "comm_rank": int(comm_rank),
        "eta_residual_in_range": float(eta_residual),
        "form2_holds": bool(max_chain_err < 1e-8),
        "eta_in_range": bool(eta_residual < 1e-6),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="CvS form2 structure check on real C(L)")
    parser.add_argument("--sector", choices=["even", "odd", "both"], default="both")
    parser.add_argument("--out", default="pilots/cvs_form2_verdict.json")
    args = parser.parse_args()

    sectors = ["even", "odd"] if args.sector == "both" else [args.sector]

    # Check at L=7/20 (certified positive) and L=42/100 (near collapse)
    L_points = [
        (7, 20,   "L=7/20 (FP-0.35, positive)"),
        (42, 100, "L=42/100 (near collapse)"),
    ]

    results = []
    for L_num, L_den, label in L_points:
        print(f"\n{'='*55}", flush=True)
        print(f"{label}", flush=True)
        for sector in sectors:
            t0 = time.time()
            C, indices = build_C_float(L_num, L_den, sector, lambda0=1e-10)
            eigs = np.linalg.eigvalsh(C)
            chk = check_form2(C, indices)
            elapsed = time.time() - t0

            print(f"\n  [{sector}] λ_min(C) = {eigs[0]:.4e}  λ_max = {eigs[-1]:.4e}", flush=True)
            print(f"  [{sector}] form2 additive chain max err = {chk['max_chain_err']:.4e}"
                  f"  (form2 holds: {chk['form2_holds']})", flush=True)
            print(f"  [{sector}] [D,C] rank = {chk['comm_rank']}  "
                  f"η residual = {chk['eta_residual_in_range']:.4e}"
                  f"  (η in range: {chk['eta_in_range']})", flush=True)
            print(f"  [{sector}] worst triple indices: {chk['worst_triple_indices']}  "
                  f"elapsed: {elapsed:.1f}s", flush=True)

            results.append({
                "L": f"{L_num}/{L_den}",
                "L_val": L_num / L_den,
                "sector": sector,
                "label": label,
                "lambda_min_C": float(eigs[0]),
                "lambda_max_C": float(eigs[-1]),
                **chk,
                "elapsed_s": elapsed,
            })

    print(f"\n{'='*55}", flush=True)
    print("\nSUMMARY — CvS form2 structure of real C(L):", flush=True)
    print(f"{'L':>10} {'sector':>6} {'form2?':>8} {'chain_err':>12} {'η_in_range?':>12}", flush=True)
    for r in results:
        print(f"  {r['L']:>8}  {r['sector']:>6}  {str(r['form2_holds']):>8}  "
              f"{r['max_chain_err']:>12.4e}  {str(r['eta_in_range']):>12}", flush=True)

    out = Path(args.out)
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"results": results,
                               "verdict": "form2 structure broken in real C(L): CvS not applicable"
                                          if any(not r["form2_holds"] for r in results)
                                          else "UNEXPECTED: form2 holds"
                               }, indent=2))
    print(f"\nWritten to {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
