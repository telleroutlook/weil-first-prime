"""
convergence_diagnosis.py — Schur min_eig asymptotic convergence test

Tests whether min_eig(N) → positive limit or → negative asymptote as N→∞.
Decision: if L_inf > 0, route continues; if L_inf < 0, current basis fails.

Usage:
    python3 scripts/convergence_diagnosis.py           # uses existing data
    python3 scripts/convergence_diagnosis.py --n32 VAL  # add N=32 result
"""
import argparse
import json
import numpy as np
from pathlib import Path

try:
    from scipy.optimize import curve_fit
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


def _fit_asymptotic_numpy(N_arr, e_arr):
    """
    Fit min_eig(N) = L_inf - A * r^(N/2) using iterative grid search.
    Returns (L_inf, A, r, rmse) or None on failure.
    """
    best = None
    best_rmse = float('inf')
    # Grid over r in (0.5, 0.9999) and L_inf in (-0.1, 0.1)
    for r_try in [i/100 for i in range(50, 100)]:
        # For fixed r, L_inf and A are determined by linear regression on:
        # e = L_inf - A * r^(N/2)  =>  e = L_inf * 1 + (-A) * r^(N/2)
        x = np.array([r_try ** (n/2) for n in N_arr])
        # Least squares: [1, -x] * [L_inf, A]^T = e
        X = np.column_stack([np.ones(len(e_arr)), -x])
        try:
            coeffs, _, _, _ = np.linalg.lstsq(X, e_arr, rcond=None)
            L_inf, A = coeffs
            if A <= 0:
                continue
            pred = L_inf - A * x
            rmse = float(np.sqrt(np.mean((pred - e_arr)**2)))
            if rmse < best_rmse:
                best_rmse = rmse
                best = (float(L_inf), float(A), float(r_try), rmse)
        except Exception:
            continue
    return best


# Known data: (N, float64_min_eig) at L=0.42, even sector, c_L=1.548
DATA = [
    (8,  -0.032),
    (10, -0.029),
    (12, -0.026),
    (14, -0.024),
]


def asymptotic_model(N, L_inf, A, r):
    """min_eig(N) = L_inf - A * r^(N/2)"""
    return L_inf - A * (r ** (N / 2))


def linear_extrapolate(data):
    """Simple linear fit for comparison."""
    N_arr = np.array([d[0] for d in data], dtype=float)
    e_arr = np.array([d[1] for d in data], dtype=float)
    coeffs = np.polyfit(N_arr, e_arr, 1)
    slope, intercept = coeffs
    N_zero = -intercept / slope if slope > 0 else None
    return slope, intercept, N_zero


def geometric_ratio_estimate(data):
    """Estimate decay ratio r from consecutive differences."""
    deltas = [data[i+1][1] - data[i][1] for i in range(len(data)-1)]
    ratios = [deltas[i+1]/deltas[i] for i in range(len(deltas)-1) if deltas[i] != 0]
    return ratios, np.mean(ratios) if ratios else None


def diagnose(data, n32_val=None):
    if n32_val is not None:
        data = data + [(32, n32_val)]

    N_arr = np.array([d[0] for d in data], dtype=float)
    e_arr = np.array([d[1] for d in data], dtype=float)

    print("=" * 60)
    print("Schur min_eig Convergence Diagnosis — L=0.42, even sector")
    print("=" * 60)
    print()
    print("Data points:")
    for N, e in data:
        print(f"  N={N:2d}: min_eig = {e:+.5f}")
    print()

    # Geometric ratio estimate
    ratios, r_mean = geometric_ratio_estimate(data)
    print(f"Consecutive delta ratios: {[f'{r:.3f}' for r in ratios]}")
    if r_mean is not None:
        print(f"Mean decay ratio r ≈ {r_mean:.4f}  (threshold: 0.917)")
        if r_mean >= 0.917:
            print("  → r ≥ 0.917: series sums to finite positive → may converge to 0")
        else:
            print("  → r < 0.917: series sums to bounded negative → WARNING")
    print()

    # Linear extrapolation
    slope, intercept, N_zero_lin = linear_extrapolate(data)
    print(f"Linear fit: slope = {slope:.5f}/step  (per N unit)")
    if N_zero_lin:
        print(f"  Linear zero crossing: N ≈ {N_zero_lin:.0f}")
    print()

    # Asymptotic fit (uses numpy grid search if scipy unavailable)
    if HAS_NUMPY and len(data) >= 4:
        fit = None
        if HAS_SCIPY:
            try:
                popt, _ = curve_fit(
                    asymptotic_model, N_arr, e_arr,
                    p0=[-0.01, 0.05, 0.8],
                    bounds=([-0.5, 0, 0.01], [0.5, 2.0, 0.9999]),
                    maxfev=50000,
                )
                L_inf, A, r_fit = popt
                residuals = e_arr - asymptotic_model(N_arr, *popt)
                rmse = float(np.sqrt(np.mean(residuals**2)))
                fit = (L_inf, A, r_fit, rmse)
            except Exception:
                pass
        if fit is None:
            fit = _fit_asymptotic_numpy(N_arr, e_arr)

        if fit:
            L_inf, A, r_fit, rmse = fit
            print(f"Asymptotic fit: min_eig(N) = {L_inf:.5f} - {A:.4f} * {r_fit:.4f}^(N/2)")
            print(f"  L_inf (asymptote) = {L_inf:+.5f}")
            print(f"  decay rate r      = {r_fit:.4f}")
            print(f"  fit RMSE          = {rmse:.2e}")
            print()

            print("=" * 60)
            if L_inf > 0.001:
                print("VERDICT: CONVERGES TO POSITIVE")
                print(f"  The asymptotic limit is +{L_inf:.5f} > 0.")
                N_zero_pred = 2 * np.log(L_inf / A) / np.log(r_fit)
                print(f"  Predicted zero crossing: N ≈ {N_zero_pred:.0f}")
                t_est = 24 * (N_zero_pred/14)**2
                print(f"  Estimated compute time at N={N_zero_pred:.0f}: ~{t_est:.0f} min")
                print()
                print("  Action: Route 2 (weil-second-prime) is viable.")
                print("  Run N≈{:.0f} to certify λ(0.42) > 0.".format(N_zero_pred + 4))
            elif L_inf < -0.005:
                print("VERDICT: CONVERGES TO NEGATIVE ASYMPTOTE")
                print(f"  The asymptotic limit is {L_inf:.5f} < 0.")
                print("  Increasing N further will NOT help.")
                print()
                print("  Action: Current Legendre basis has structural truncation leakage.")
                print("  → Route 3 (change basis or analytic uniform bound) is required.")
                print("  → Do NOT build weil-second-prime until basis issue resolved.")
            else:
                print("VERDICT: AMBIGUOUS (L_inf ≈ 0)")
                print(f"  Asymptote ≈ {L_inf:.5f}, within noise.")
                print("  Need more data points (N=20, N=24) to decide.")
                print("  → Run N=20 before committing to Route 2 or Route 3.")
            print("=" * 60)

    else:
        print("Using linear extrapolation only (numpy not available):")
        if N_zero_lin:
            print(f"  Linear zero crossing at N ≈ {N_zero_lin:.0f}")

    # Save diagnosis
    result = {
        "data": data,
        "r_mean": float(r_mean) if r_mean else None,
        "n32_included": n32_val is not None,
    }
    out = Path(__file__).parent.parent / "pilots" / "convergence_diagnosis.json"
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nResult saved to {out}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n32", type=float, default=None,
                        help="N=32 min_eig result to add to dataset")
    args = parser.parse_args()
    diagnose(DATA, n32_val=args.n32)


if __name__ == "__main__":
    main()
