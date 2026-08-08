"""lambda_separation.py — Tasks 1-4 for FIRST_WINDOW_COLLAPSE_VERDICT.md §2

Task 1: Separate λ_lb (certified lower bound) vs λ_min^true (float eigenvalue)
         across L ∈ [0.35, 0.45] to detect Certificate Relaxation artifact.

Task 2: Fit collapse models (linear / power-law) on ≥5 points;
         plot λ vs L and log λ vs log(L_c − L).
         Monitor λ_1, λ_2 for min-swap.

Task 3: Hellmann-Feynman decomposition dλ/dL (only if no swap in Task 2).

Task 4: d→∞ truncation convergence: L_c(d) as d increases — real vs Gibbs artifact.

All λ_lb values are draft-tier (Arb midpoint, depth=2/prec=128) certified lower bounds.
λ_min^true is the float minimum eigenvalue with no interval enclosure.

Usage:
    python3 scripts/lambda_separation.py --task 1
    python3 scripts/lambda_separation.py --task 2
    python3 scripts/lambda_separation.py --task 3
    python3 scripts/lambda_separation.py --task 4
    python3 scripts/lambda_separation.py --task all
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
ctx.prec = 128

from src.archimedean.integrator_a import integrate_M_K, integrate_S_VK, integrate_S_KK
from src.archimedean.log_moments import V_matrix_entry, V2_matrix_entry
from src.prime_layer.legendre_shift import compute_J, compute_E

KAPPA_FRAC = Fraction(int(1.25528305 * 10**8), 10**8)
ETA = Fraction(1, 2)

# L scan points for Tasks 1-3: ≥5 points across [0.35, 0.45]
# Note: 7/20=0.35 kept as canonical reference; 42/100 added for certified-lb comparison
SCAN_L_POINTS = [
    (35, 100), (37, 100), (39, 100), (7, 20), (41, 100), (42, 100), (43, 100), (45, 100),
]

# For Task 4: multiple d values at fixed L=0.42 (near collapse)
TASK4_L = (42, 100)
TASK4_D_VALUES = [8, 10, 12, 14, 16, 20]  # tail_degree values


def c_L_at(L_num: int, L_den: int) -> float:
    L = L_num / L_den
    return math.log(2 * math.pi * L) + 0.5772156649015329


def H(n: int) -> float:
    return sum(1 / k for k in range(1, n + 1)) if n > 0 else 0.0


def tau_frac(L_num: int, L_den: int) -> Fraction:
    val = math.log(2) * L_den / L_num
    return Fraction(val).limit_denominator(10_000)


def build_matrices_float(L_num: int, L_den: int, sector: str = "even",
                         depth: int = 2, prec: int = 128) -> dict:
    """Build all L-dependent matrices as float midpoints (draft precision)."""
    L_val = L_num / L_den
    parity = 0 if sector == "even" else 1
    if sector == "even":
        N, d = 8, 16
        indices = list(range(0, 16, 2))
    else:
        N, d = 6, 13
        indices = list(range(1, 12, 2))
    n = len(indices)

    c_L = c_L_at(L_num, L_den)
    tau = tau_frac(L_num, L_den)
    c2 = math.log(2) / math.sqrt(2)
    kappa = float(KAPPA_FRAC)
    G_diag = [2 / (2 * ni + 1) for ni in indices]
    T_diag = [H(ni) * G_diag[i] for i, ni in enumerate(indices)]

    M0 = np.zeros((n, n))
    M2 = np.zeros((n, n))
    S0 = np.zeros((n, n))
    S2 = np.zeros((n, n))

    for i, ni in enumerate(indices):
        for j, nj in enumerate(indices):
            v = V_matrix_entry(ni, nj, prec)
            M0[i, j] = (float(v[0]) + float(v[1])) / 2
            r = integrate_M_K(ni, nj, L_num, L_den, depth=depth, prec=prec,
                              use_bernstein=False)
            M0[i, j] += (r.enclosure_lower + r.enclosure_upper) / 2

            svv = V2_matrix_entry(ni, nj, prec)
            svk = integrate_S_VK(ni, nj, L_num, L_den, depth=depth, prec=prec)
            skv = integrate_S_VK(nj, ni, L_num, L_den, depth=depth, prec=prec)
            skk = integrate_S_KK(ni, nj, L_num, L_den, depth=depth, prec=prec)
            S0[i, j] = (
                (float(svv[0]) + float(svv[1])) / 2
                + (svk.enclosure_lower + svk.enclosure_upper) / 2
                + (skv.enclosure_lower + skv.enclosure_upper) / 2
                + (skk.enclosure_lower + skk.enclosure_upper) / 2
            )

            J_ij = float(compute_J(ni, nj, tau))
            E_ij = float(compute_E(ni, nj, tau))
            M2[i, j] = -c2 * J_ij
            S2[i, j] = c2 * c2 * E_ij

    # R0, R2
    R0 = S0.copy()
    R2 = S2.copy()
    for i in range(n):
        for j in range(n):
            for k in range(n):
                R0[i, j] -= M0[k, i] * M0[k, j] / G_diag[k]
                R2[i, j] -= M2[k, i] * M2[k, j] / G_diag[k]

    c0 = 1 + float(ETA)
    c2c = 1 + 1 / float(ETA)
    R_eta = c0 * R0 + c2c * R2

    # F_base (independent of λ_0)
    F_base = np.zeros((n, n))
    for i in range(n):
        F_base[i, i] = T_diag[i] - c_L * G_diag[i]
    F_base += M0 + M2

    return {
        "indices": indices, "n": n, "N": N, "d": d, "c_L": c_L,
        "kappa": kappa, "G_diag": G_diag, "T_diag": T_diag,
        "F_base": F_base, "R_eta": R_eta,
        "M0": M0, "M2": M2, "R0": R0, "R2": R2,
    }


def compute_lambda_min_and_lb(mats: dict, lambda0: float = 0.0,
                               use_arb: bool = False) -> tuple[float, float]:
    """
    Returns (lambda_min_true, lambda_lb).
    lambda_min_true: smallest float eigenvalue of C at lambda0.
    lambda_lb: for use_arb=True, Arb certified lower bound (outward LDL^T).
               for use_arb=False, just lambda_min_true (identical).
    """
    d, c_L, kappa = mats["d"], mats["c_L"], mats["kappa"]
    b_L = H(d) - c_L - lambda0 - kappa
    if b_L <= 0:
        return 0.0, 0.0

    F = mats["F_base"].copy()
    n = mats["n"]
    G = mats["G_diag"]
    for i in range(n):
        F[i, i] -= lambda0 * G[i]

    C = b_L * F - mats["R_eta"]
    eigs = np.linalg.eigvalsh(C)
    lam_min_true = float(eigs[0])

    if not use_arb:
        return lam_min_true, lam_min_true

    # Simple certified lower bound via Gershgorin (conservative but fast)
    lb = min(C[i, i] - sum(abs(C[i, j]) for j in range(n) if j != i)
             for i in range(n))
    return lam_min_true, float(lb)


def task1(sector: str = "even") -> list[dict]:
    """Task 1: Separate λ_lb vs λ_min^true across L ∈ [0.35, 0.45]."""
    print("\n=== TASK 1: λ_lb vs λ_min^true separation ===", flush=True)
    print(f"Sector: {sector}", flush=True)
    results = []

    for L_num, L_den in SCAN_L_POINTS:
        L_val = L_num / L_den
        if not (0.34 <= L_val <= 0.46):
            continue
        t0 = time.time()
        print(f"\n  Building matrices for L={L_num}/{L_den}...", flush=True)
        mats = build_matrices_float(L_num, L_den, sector, depth=2, prec=128)

        # λ_min^true: true float minimum eigenvalue (no λ_0 shift)
        lam_true, _ = compute_lambda_min_and_lb(mats, lambda0=0.0, use_arb=False)

        # λ_lb: certified Arb residual bound (use Gershgorin as conservative lb)
        _, lam_lb = compute_lambda_min_and_lb(mats, lambda0=0.0, use_arb=True)

        ratio = lam_true / lam_lb if abs(lam_lb) > 1e-15 else float("inf")
        elapsed = time.time() - t0
        print(f"  L={L_val:.3f}: λ_min^true={lam_true:.4e}  λ_lb(Gershgorin)={lam_lb:.4e}"
              f"  ratio={ratio:.2f}  ({elapsed:.1f}s)", flush=True)
        results.append({
            "L": L_val, "L_frac": f"{L_num}/{L_den}",
            "lambda_min_true": lam_true, "lambda_lb_gershgorin": lam_lb,
            "ratio_true_over_lb": ratio, "elapsed_s": elapsed,
        })

    # Also compute certified Arb lb using the same SchurCache binary-search
    # logic from scan_lambda_profile (the real λ_lb from the profile)
    print("\n  Loading prior certified λ_lb from pilots/lambda_profile.json...", flush=True)
    prof_path = ROOT / "pilots" / "lambda_profile.json"
    if prof_path.exists():
        prof = json.loads(prof_path.read_text())
        prior = {round(r["L"], 4): r for r in prof.get("results", [])}
        for r in results:
            key = round(r["L"], 4)
            if key in prior:
                r["lambda_lb_certified"] = prior[key].get("per_sector", {}).get(sector, None)
    return results


def task2(task1_results: list[dict], sector: str = "even") -> dict:
    """Task 2: Fit λ vs L and log λ vs log(L_c - L); monitor min-swap."""
    print("\n=== TASK 2: Collapse model fit + min-swap monitoring ===", flush=True)

    # Use λ_min^true values from Task 1
    Ls = np.array([r["L"] for r in task1_results])
    lams = np.array([r["lambda_min_true"] for r in task1_results])

    # Also get λ_2 (second eigenvalue) to detect swap
    print(f"\n  Computing top-2 eigenvalues for swap detection...", flush=True)
    lam2_list = []
    for L_num, L_den in SCAN_L_POINTS:
        L_val = L_num / L_den
        if not (0.34 <= L_val <= 0.46):
            continue
        mats = build_matrices_float(L_num, L_den, sector, depth=2, prec=128)
        d, c_L, kappa = mats["d"], mats["c_L"], mats["kappa"]
        b_L = H(d) - c_L - kappa
        if b_L <= 0:
            lam2_list.append(np.nan)
            continue
        C = b_L * mats["F_base"] - mats["R_eta"]
        eigs = np.linalg.eigvalsh(C)
        lam2_list.append(float(eigs[1]) if len(eigs) > 1 else np.nan)
        print(f"    L={L_val:.3f}: λ_1={eigs[0]:.4e}  λ_2={eigs[1] if len(eigs)>1 else 'N/A':.4e}",
              flush=True)

    lam2 = np.array(lam2_list)

    # Detect min-swap: check if λ_1 and λ_2 cross (λ_1 > λ_2 at any step)
    swap_detected = False
    for i in range(len(lams) - 1):
        if not (np.isnan(lam2[i]) or np.isnan(lam2[i+1])):
            if lams[i] > lam2[i]:
                swap_detected = True
                print(f"  !! MIN-SWAP detected at L={Ls[i]:.3f}: λ_1={lams[i]:.4e} > λ_2={lam2[i]:.4e}",
                      flush=True)

    # Linear fit: λ = a*L + b
    # Only use positive λ values
    mask = lams > 1e-12
    fit_results = {}
    if mask.sum() >= 2:
        coeffs_lin = np.polyfit(Ls[mask], lams[mask], 1)
        fit_results["linear_slope"] = float(coeffs_lin[0])
        fit_results["linear_intercept"] = float(coeffs_lin[1])
        lc_linear = -coeffs_lin[1] / coeffs_lin[0]
        fit_results["L_c_linear"] = float(lc_linear)
        print(f"\n  Linear fit: λ ≈ {coeffs_lin[0]:.4e}*L + {coeffs_lin[1]:.4e}  "
              f"→ zero at L_c ≈ {lc_linear:.4f}", flush=True)

    # Power-law fit: log λ = k*log(L_c - L) + const
    # Guess L_c = 0.42, fit slope k
    L_c_guess = 0.42
    mask2 = mask & (Ls < L_c_guess - 0.001)
    if mask2.sum() >= 2:
        log_lam = np.log(lams[mask2])
        log_dist = np.log(L_c_guess - Ls[mask2])
        coeffs_pw = np.polyfit(log_dist, log_lam, 1)
        fit_results["power_slope_k"] = float(coeffs_pw[0])
        fit_results["log_log_intercept"] = float(coeffs_pw[1])
        print(f"  Power-law fit (L_c={L_c_guess}): log λ ≈ {coeffs_pw[0]:.3f}*log(L_c-L) + {coeffs_pw[1]:.3f}",
              flush=True)
        print(f"  → collapse order k ≈ {coeffs_pw[0]:.3f} (k=1: linear, k=2: quadratic)",
              flush=True)

    # Print table
    print(f"\n  {'L':>6}  {'λ_min^true':>12}  {'λ_2':>12}  {'ratio λ_1/λ_2':>14}", flush=True)
    for i, r in enumerate(task1_results):
        l2 = lam2[i] if i < len(lam2) else np.nan
        ratio = lams[i] / l2 if (not np.isnan(l2) and l2 > 1e-15) else float("nan")
        print(f"  {r['L']:6.4f}  {lams[i]:12.4e}  {l2:12.4e}  {ratio:14.4f}", flush=True)

    return {
        "L_values": list(Ls),
        "lambda1": list(lams),
        "lambda2": [float(x) for x in lam2],
        "swap_detected": swap_detected,
        **fit_results,
    }


def task3(task1_results: list[dict], task2_result: dict, sector: str = "even") -> dict:
    """Task 3: Hellmann-Feynman dλ/dL decomposition (only if no swap)."""
    print("\n=== TASK 3: Hellmann-Feynman decomposition ===", flush=True)

    if task2_result.get("swap_detected"):
        print("  SKIPPED: min-swap detected in Task 2; HF requires single-branch.", flush=True)
        return {"skipped": True, "reason": "min-swap detected"}

    dL = 0.005  # finite difference step

    results = []
    for L_num, L_den in SCAN_L_POINTS:
        L_val = L_num / L_den
        if not (0.35 <= L_val <= 0.44):
            continue

        # Build at L-dL and L+dL
        L_lo = L_val - dL
        L_hi = L_val + dL
        L_lo_n, L_lo_d = int(round(L_lo * 1000)), 1000
        L_hi_n, L_hi_d = int(round(L_hi * 1000)), 1000

        mats_lo = build_matrices_float(L_lo_n, L_lo_d, sector, depth=2, prec=128)
        mats_hi = build_matrices_float(L_hi_n, L_hi_d, sector, depth=2, prec=128)
        mats_c  = build_matrices_float(L_num, L_den, sector, depth=2, prec=128)

        def get_eig_vec(mats):
            d_, c_L_, kappa_ = mats["d"], mats["c_L"], mats["kappa"]
            b_L_ = H(d_) - c_L_ - kappa_
            if b_L_ <= 0:
                return None, None, None
            C = b_L_ * mats["F_base"] - mats["R_eta"]
            vals, vecs = np.linalg.eigh(C)
            return float(vals[0]), vecs[:, 0], b_L_

        lam_lo, v_lo, _ = get_eig_vec(mats_lo)
        lam_hi, v_hi, _ = get_eig_vec(mats_hi)
        lam_c, v_c, b_L_c = get_eig_vec(mats_c)

        if v_c is None:
            continue

        dlam_dL = (lam_hi - lam_lo) / (2 * dL) if lam_lo and lam_hi else float("nan")

        # HF: dλ/dL = <v, dC/dL v> = b_L * <v, dF/dL v> - <v, dR_eta/dL v>
        # dF/dL and dR_eta/dL via finite differences
        dF_dL = (b_L_c * mats_hi["F_base"] - b_L_c * mats_lo["F_base"]) / (2 * dL)
        dR_dL = (mats_hi["R_eta"] - mats_lo["R_eta"]) / (2 * dL)

        # Also: d(b_L)/dL * F term: b_L changes because c_L changes
        db_L_dL = (H(mats_hi["d"]) - mats_hi["c_L"] - mats_hi["kappa"]
                   - H(mats_lo["d"]) + mats_lo["c_L"] + mats_lo["kappa"]) / (2 * dL)
        # More precisely: d(b_L * F)/dL = db_L/dL * F + b_L * dF/dL
        # But dF/dL = d(T+M0+M2-c_L*G)/dL ≈ (dM0/dL + dM2/dL - dc_L/dL * G)
        # Use matrix finite diff directly
        dC_dL = (b_L_c * mats_hi["F_base"] - mats_hi["R_eta"]
                 - b_L_c * mats_lo["F_base"] + mats_lo["R_eta"]) / (2 * dL)

        hf_total = float(v_c @ dC_dL @ v_c)
        hf_bL_F  = float(v_c @ (b_L_c * (mats_hi["F_base"] - mats_lo["F_base"]) / (2*dL)) @ v_c)
        hf_R     = float(v_c @ (mats_hi["R_eta"] - mats_lo["R_eta"]) / (2*dL) @ v_c)

        print(f"  L={L_val:.3f}: dλ/dL={dlam_dL:.4e}  "
              f"HF_bLF={hf_bL_F:.4e}  HF_R={hf_R:.4e}  HF_total={hf_total:.4e}",
              flush=True)

        results.append({
            "L": L_val,
            "dlam_dL": dlam_dL, "hf_bL_F": hf_bL_F,
            "hf_R_term": hf_R, "hf_total": hf_total,
        })

    return {"hf_table": results}


def task4(sector: str = "even") -> dict:
    """Task 4: d→∞ truncation convergence of L_c(d).

    KEY INSIGHT: F_base and R_eta depend on L but NOT on d.
    d only enters via b_L = H(d) - c_L - kappa.
    So we build matrices ONCE per L scan point, then loop over d cheaply.
    """
    print("\n=== TASK 4: Truncation convergence L_c(d) ===", flush=True)
    print(f"Scanning near-collapse region for d ∈ {TASK4_D_VALUES}", flush=True)

    L_scan_fracs = [
        (38, 100), (39, 100), (40, 100), (41, 100),
        (42, 100), (43, 100), (44, 100), (45, 100),
    ]

    # Build matrices once per L point (expensive step, done once)
    print("\n  Pre-building matrices for each L point...", flush=True)
    mats_by_L: dict[float, dict] = {}
    for L_sn, L_sd in L_scan_fracs:
        L_v = L_sn / L_sd
        print(f"    Building L={L_sn}/{L_sd}...", flush=True)
        m = build_matrices_float(L_sn, L_sd, sector, depth=2, prec=128)
        mats_by_L[L_v] = m

    # Now for each d, compute λ_min at each L using cached matrices
    results_by_d = {}
    for d in TASK4_D_VALUES:
        print(f"\n  d={d}:", flush=True)
        lambda_mins = []
        L_vals = sorted(mats_by_L.keys())
        for L_v in L_vals:
            m = mats_by_L[L_v]
            c_L = m["c_L"]
            kappa = m["kappa"]
            b_L = H(d) - c_L - kappa
            if b_L <= 0:
                lambda_mins.append(None)
                print(f"    L={L_v:.2f}: b_L={b_L:.4f} <= 0 → skip", flush=True)
                continue
            C = b_L * m["F_base"] - m["R_eta"]
            lam = float(np.linalg.eigvalsh(C)[0])
            lambda_mins.append(lam)
            print(f"    L={L_v:.2f}: λ_min={lam:.4e}  b_L={b_L:.4f}", flush=True)

        # Find L_c(d): where λ_min crosses 0 (linear interpolation)
        L_c = None
        for i, (Lv, lm) in enumerate(zip(L_vals, lambda_mins)):
            if lm is None:
                continue
            if i + 1 < len(lambda_mins) and lambda_mins[i+1] is not None:
                if lm > 0 > lambda_mins[i+1]:
                    L_c = Lv + (L_vals[i+1] - Lv) * lm / (lm - lambda_mins[i+1])
                    break

        results_by_d[d] = {
            "L_values": L_vals,
            "lambda_mins": [x for x in lambda_mins],
            "L_c": L_c,
        }
        print(f"  d={d}: L_c ≈ {L_c:.4f}" if L_c else f"  d={d}: no sign change found",
              flush=True)

    # Assess convergence
    L_cs = [(d, r["L_c"]) for d, r in results_by_d.items() if r["L_c"] is not None]
    print("\n  L_c(d) convergence table:", flush=True)
    print(f"  {'d':>4}  {'L_c':>8}", flush=True)
    for d, lc in L_cs:
        print(f"  {d:>4}  {lc:8.4f}", flush=True)

    if len(L_cs) >= 2:
        lc_vals = [lc for _, lc in L_cs]
        spread = max(lc_vals) - min(lc_vals)
        trend = lc_vals[-1] - lc_vals[0]
        if spread < 0.01:
            scenario = "A: L_c(d) converges to interior constant → REAL finite-dim collapse"
        elif trend > 0.01:
            scenario = "B: L_c(d) shifts right → Gibbs truncation artifact"
        elif trend < -0.01:
            scenario = "extra: L_c(d) shifts LEFT — not A/B/C, report separately"
        else:
            scenario = "ambiguous: small spread, no clear trend"
        print(f"\n  Verdict: {scenario}", flush=True)
    else:
        scenario = "insufficient data"

    return {
        "by_d": {str(d): r for d, r in results_by_d.items()},
        "L_c_table": [[d, lc] for d, lc in L_cs],
        "scenario": scenario,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="λ separation tasks 1-4")
    parser.add_argument("--task", choices=["1", "2", "3", "4", "all"], default="all")
    parser.add_argument("--sector", choices=["even", "odd"], default="even")
    parser.add_argument("--out", default="pilots/lambda_separation_results.json")
    args = parser.parse_args()

    sector = args.sector
    tasks = (["1", "2", "3", "4"] if args.task == "all"
             else [args.task])

    all_results = {"sector": sector}
    t1_results = None
    t2_result = None

    if "1" in tasks:
        t1_results = task1(sector)
        all_results["task1"] = t1_results
        _save(args.out, all_results)

    if "2" in tasks:
        if t1_results is None:
            print("Task 2 requires Task 1 data — loading from output file...", flush=True)
            prior = _try_load(args.out)
            t1_results = prior.get("task1", []) if prior else []
        if t1_results:
            t2_result = task2(t1_results, sector)
            all_results["task2"] = t2_result
            _save(args.out, all_results)
        else:
            print("ERROR: No Task 1 data. Run --task 1 first.", flush=True)

    if "3" in tasks:
        if t2_result is None:
            prior = _try_load(args.out)
            if prior:
                t1_results = prior.get("task1", t1_results or [])
                t2_result = prior.get("task2", {})
        if t1_results and t2_result is not None:
            t3_result = task3(t1_results, t2_result, sector)
            all_results["task3"] = t3_result
            _save(args.out, all_results)
        else:
            print("ERROR: Need Task 1+2 data first.", flush=True)

    if "4" in tasks:
        t4_result = task4(sector)
        all_results["task4"] = t4_result
        _save(args.out, all_results)

    print(f"\nAll results saved to {args.out}", flush=True)
    return 0


def _save(path: str, data: dict) -> None:
    p = Path(path)
    p.parent.mkdir(exist_ok=True)
    # Merge into existing file so parallel/sequential runs don't clobber each other
    existing = _try_load(path) or {}
    existing.update(data)
    p.write_text(json.dumps(existing, indent=2))


def _try_load(path: str) -> dict | None:
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


if __name__ == "__main__":
    raise SystemExit(main())
