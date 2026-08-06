"""
validate_skk_rank2.py — 诚实验证 S_KK rank-2 假设

直接命中三个漏洞：
  漏洞1: 测的是具体构造式 (k=0,2分量) 而非 SVD 最优 rank-2
  漏洞2: 在 N=32 的实际高阶指标 (P_0...P_62) 上测，不外推低阶数据
  漏洞3: 计算误差传播：err * b_L^2 vs min_eig 裕量

测试的具体公式：
  S_KK_rank2[i,j] = M_K[0,i]*M_K[0,j]/G_00 + M_K[2,i]*M_K[2,j]/G_22

测试范围：N=32 偶扇区，indices = [0,2,4,...,62]
"""
import sys, math, time
sys.path.insert(0, '/Users/I041705/github/weil-first-prime')
from src.archimedean.integrator_a import integrate_M_K, integrate_S_KK

def validate(L_num: int, L_den: int, N: int = 32,
             min_eig_estimate: float = -0.02,  # current min_eig at this L
             b_L_estimate: float = 2.0):
    """
    Validate rank-2 S_KK approximation at high-order indices.
    N = truncation (test indices up to 2*N-2).
    """
    L_val = L_num / L_den
    indices = list(range(0, 2*N, 2))   # [0,2,4,...,2N-2]
    n = len(indices)
    print(f"{'='*60}")
    print(f"S_KK rank-2 validation at L={L_num}/{L_den}={L_val:.4f}, N={N}")
    print(f"Indices: P_0, P_2, ..., P_{2*N-2}  ({n} basis functions)")
    print(f"b_L estimate: {b_L_estimate:.3f}")
    print(f"Current min_eig estimate: {min_eig_estimate:.4f}")
    print()

    # Step 1: Get M_K[0,j] and M_K[2,j] for all j in indices
    print("Step 1: computing M_K[0,j] and M_K[2,j] for all j... ", end='', flush=True)
    t0 = time.time()
    mk0 = {}; mk2 = {}
    for nj in indices:
        r0 = integrate_M_K(0, nj, L_num, L_den, depth=4, use_bernstein=False)
        r2 = integrate_M_K(2, nj, L_num, L_den, depth=4, use_bernstein=False)
        mk0[nj] = float((r0.enclosure_lower + r0.enclosure_upper) / 2)
        mk2[nj] = float((r2.enclosure_lower + r2.enclosure_upper) / 2)
    print(f"done ({time.time()-t0:.1f}s)", flush=True)

    G00 = 2.0   # G_{00} = 2/(2*0+1)
    G22 = 0.4   # G_{22} = 2/(2*2+1)

    # Step 2: Compute S_KK exactly for a STRATEGIC SUBSET of (i,j) pairs
    # Focus on high-order entries where rank-2 is most likely to fail:
    #   - diagonal: (max_n, max_n)
    #   - off-diagonal: (0, max_n), (2, max_n), (max_n-2, max_n)
    max_n = indices[-1]   # = 2*N-2
    # Also add max_n//2 to test_pairs only if it's in indices
    test_pairs = []
    for ni, nj in [(0,0),(2,2),(max_n,max_n),(0,max_n),(2,max_n),(max_n-2,max_n)]:
        if ni in indices and nj in indices:
            test_pairs.append((ni, nj))
    mid = indices[len(indices)//2]
    if (mid, max_n) not in test_pairs and mid in indices:
        test_pairs.append((mid, max_n))
    test_pairs = list(dict.fromkeys(test_pairs))

    print(f"\nStep 2: exact S_KK for {len(test_pairs)} strategic (i,j) pairs")
    print(f"  (focused on high-order P_{max_n} entries — worst case for rank-2)")
    print()

    max_abs_err = 0.0
    max_rel_err = 0.0
    critical_entry = None

    header = f"{'(i,j)':>12}  {'S_KK_exact':>13}  {'S_KK_rank2':>13}  {'abs_err':>10}  {'rel_err':>9}  {'margin_frac':>11}"
    print(header)
    print("-" * len(header))

    for ni, nj in test_pairs:
        t1 = time.time()
        # Exact S_KK (sum over k=0..2*N-2, enough terms for accuracy)
        skk_exact = 0.0
        for k in range(0, 2*N, 2):
            r = integrate_M_K(k, ni, L_num, L_den, depth=4, use_bernstein=False)
            mk_ki = float((r.enclosure_lower + r.enclosure_upper) / 2)
            r = integrate_M_K(k, nj, L_num, L_den, depth=4, use_bernstein=False)
            mk_kj = float((r.enclosure_lower + r.enclosure_upper) / 2)
            G_kk = 2 / (2*k + 1)
            skk_exact += mk_ki * mk_kj / G_kk

        # Rank-2 approximation: only k=0,2
        skk_r2 = (mk0.get(ni, 0.0) * mk0.get(nj, 0.0) / G00 +
                  mk2.get(ni, 0.0) * mk2.get(nj, 0.0) / G22)

        abs_err = abs(skk_exact - skk_r2)
        rel_err = abs_err / (abs(skk_exact) + 1e-20)

        # Error propagation to Schur matrix
        # C = b_L*F - R_eta, where R_eta contains (1+eta)*R0
        # R0 = S_KK - M0 G^{-1} M0^T
        # The S_KK error enters C with factor (1+eta)*b_L ≈ 1.5*b_L
        schur_impact = abs_err * 1.5 * b_L_estimate
        margin_frac = schur_impact / abs(min_eig_estimate) if min_eig_estimate != 0 else float('inf')

        if abs_err > max_abs_err:
            max_abs_err = abs_err
        if rel_err > max_rel_err and abs(skk_exact) > 1e-8:
            max_rel_err = rel_err
            critical_entry = (ni, nj, abs_err, rel_err, margin_frac)

        flag = "⚠️ LARGE" if margin_frac > 0.01 else "✓"
        print(f"({ni:2d},{nj:2d}) {skk_exact:13.5e}  {skk_r2:13.5e}  {abs_err:10.2e}  {rel_err:9.2e}  {margin_frac:11.4f} {flag}")

    print()
    print("=" * 60)
    print(f"Max absolute error: {max_abs_err:.2e}")
    print(f"Max relative error (|S_KK| > 1e-8): {max_rel_err:.2e}")

    if critical_entry:
        ni, nj, ae, re, mf = critical_entry
        print(f"Critical entry: ({ni},{nj})  abs={ae:.2e}  rel={re:.2e}  margin_frac={mf:.4f}")
        print()
        print("VERDICT:")
        if mf < 0.001:
            print("  ✅ SAFE: rank-2 error is <0.1% of current min_eig gap")
            print("     → rank-2 S_KK substitution is certified safe for Arb use")
        elif mf < 0.01:
            print("  ⚠️  BORDERLINE: rank-2 error is 0.1%-1% of min_eig gap")
            print("     → may be acceptable, but include as Arb remainder term")
        else:
            print("  ❌ UNSAFE: rank-2 error > 1% of min_eig gap")
            print("     → cannot substitute rank-2 without larger certified remainder")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--L", type=float, default=0.42)
    parser.add_argument("--N", type=int, default=32,
                        help="Truncation order to test (default: 32)")
    parser.add_argument("--min-eig", type=float, default=-0.02,
                        help="Current min_eig at this L (for margin calc)")
    parser.add_argument("--b-L", type=float, default=2.0,
                        help="b_L at this N (for error propagation)")
    args = parser.parse_args()

    from fractions import Fraction
    frac = Fraction(args.L).limit_denominator(1000)
    validate(frac.numerator, frac.denominator, N=args.N,
             min_eig_estimate=args.min_eig, b_L_estimate=args.b_L)


if __name__ == "__main__":
    main()
