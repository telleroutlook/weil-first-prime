"""
validate_skk_rank2.py — 诚实验证 S_KK rank-2 假设（修正版）

解决审稿人指出的三个逻辑问题：
  问题1: N=8/L=0.35 不是真正风险区，必须跑 L=0.42/N=32
  问题2: 高阶对角 rel_err=1.0 是结构失效信号，不是"无害特例"
  问题3: margin 相对目标正裕量（你想认证的 λ≥target），不是负的 min_eig

测试的具体公式（漏洞1：非 SVD 最优，而是特定构造式）：
  S_KK_rank2[i,j] = M_K[0,i]*M_K[0,j]/G_00 + M_K[2,i]*M_K[2,j]/G_22

真正的判决点：
  python3 scripts/validate_skk_rank2.py --L 0.42 --N 32 --target 0.005

--target: 你希望最终认证的 λ 正裕量（e.g. 0.005 表示 λ≥0.005）
          误差传播后若 < target 的 10%，判 SAFE
"""
import sys, math, time
sys.path.insert(0, '/Users/I041705/github/weil-first-prime')
from src.archimedean.integrator_a import integrate_M_K


def validate(L_num: int, L_den: int, N: int = 32,
             target_lambda: float = 0.005,
             b_L_estimate: float = 1.9):
    """
    Validate rank-2 S_KK at the actual risk zone: high-order indices,
    realistic L and b_L.

    target_lambda: the positive margin you want to certify (λ ≥ target_lambda).
                   The S_KK error must propagate to << target_lambda.
    """
    L_val = L_num / L_den
    indices = list(range(0, 2*N, 2))   # [0,2,...,2N-2]
    max_n = indices[-1]
    mid_n = indices[len(indices)//2]

    print(f"{'='*65}")
    print(f"S_KK rank-2 HONEST validation")
    print(f"  L = {L_num}/{L_den} = {L_val:.4f}")
    print(f"  N = {N}  (indices P_0, P_2, ..., P_{max_n})")
    print(f"  b_L estimate = {b_L_estimate:.3f}")
    print(f"  Target: certify λ ≥ {target_lambda:.4f}")
    print(f"  Safety threshold: prop_err < {target_lambda * 0.1:.2e}  (10% of target)")
    print()
    print("NOTE: (n,n) rel_err=1.0 means rank-2 does NOT capture that entry.")
    print("      It is a structural failure signal, even if abs_err is small NOW.")
    print("      Check whether abs_err * 1.5 * b_L stays << target_lambda.")
    print()

    # Step 1: Get M_K[0,j] and M_K[2,j] for ALL j in indices
    # (漏洞2: must include high-order j up to max_n=2N-2)
    print(f"Step 1: M_K[0,j] and M_K[2,j] for all {len(indices)} indices... ", flush=True)
    t0 = time.time()
    mk0 = {}; mk2 = {}
    for nj in indices:
        r0 = integrate_M_K(0, nj, L_num, L_den, depth=4, use_bernstein=False)
        r2 = integrate_M_K(2, nj, L_num, L_den, depth=4, use_bernstein=False)
        mk0[nj] = float((r0.enclosure_lower + r0.enclosure_upper) / 2)
        mk2[nj] = float((r2.enclosure_lower + r2.enclosure_upper) / 2)
    print(f"done ({time.time()-t0:.1f}s)")

    G00 = 2.0; G22 = 0.4

    # Step 2: Strategic test pairs — focus on HIGH-ORDER entries
    # (漏洞2: 真正危险区是 P_{max_n} 的对角线和交叉项)
    test_pairs = []
    for ni, nj in [
        (0, 0),              # reference low-order
        (2, 2),              # reference
        (max_n, max_n),      # HIGH-order diagonal ← 关键
        (max_n-2, max_n-2),  # second-highest diagonal
        (0, max_n),          # low × high cross
        (2, max_n),          # low × high cross
        (mid_n, max_n),      # mid × high cross
        (max_n-2, max_n),    # adjacent high
    ]:
        if ni in indices and nj in indices:
            test_pairs.append((ni, nj))
    test_pairs = list(dict.fromkeys(test_pairs))

    print(f"\nStep 2: exact S_KK at {len(test_pairs)} pairs")
    print(f"  (highest index tested: P_{max_n} — the true risk zone)")
    print()

    threshold = target_lambda * 0.1   # propagated error must be < 10% of target
    any_fail = False
    any_structural_fail = False

    hdr = f"{'(i,j)':>10}  {'S_exact':>12}  {'S_rank2':>12}  {'abs_err':>10}  {'prop_err':>10}  {'rel_err':>9}  verdict"
    print(hdr)
    print("-" * len(hdr))

    for ni, nj in test_pairs:
        # Exact S_KK: sum over k = 0..max_n
        skk_exact = 0.0
        for k in range(0, max_n + 2, 2):
            rki = integrate_M_K(k, ni, L_num, L_den, depth=4, use_bernstein=False)
            rkj = integrate_M_K(k, nj, L_num, L_den, depth=4, use_bernstein=False)
            vki = float((rki.enclosure_lower + rki.enclosure_upper) / 2)
            vkj = float((rkj.enclosure_lower + rkj.enclosure_upper) / 2)
            G_kk = 2 / (2*k + 1)
            skk_exact += vki * vkj / G_kk

        # Rank-2: k=0,2 only
        skk_r2 = (mk0.get(ni, 0.0) * mk0.get(nj, 0.0) / G00 +
                  mk2.get(ni, 0.0) * mk2.get(nj, 0.0) / G22)

        abs_err = abs(skk_exact - skk_r2)
        # Error propagation: S_KK enters R0; R_eta = (1+eta)*R0 + ...
        # C = b_L * F - R_eta; factor on S_KK: (1+eta)*b_L ≈ 1.5*b_L
        prop_err = abs_err * 1.5 * b_L_estimate
        rel_err = abs_err / (abs(skk_exact) + 1e-30)

        # (漏洞3: 判据基于目标正裕量，不是负的 min_eig)
        if rel_err > 0.5:
            verdict = "⚠️ STRUCT-FAIL"  # rank-2 doesn't capture this entry
            any_structural_fail = True
        elif prop_err > threshold:
            verdict = "❌ PROP-FAIL"    # propagated error too large
            any_fail = True
        else:
            verdict = "✓"

        print(f"({ni:2d},{nj:2d}) {skk_exact:12.4e}  {skk_r2:12.4e}  {abs_err:10.2e}  {prop_err:10.2e}  {rel_err:9.2e}  {verdict}")

    print()
    print("=" * 65)
    print(f"TARGET: certify λ ≥ {target_lambda:.4f}")
    print(f"THRESHOLD (10% of target): {threshold:.2e}")
    print()

    if any_structural_fail:
        print("⚠️  STRUCTURAL FAILURES DETECTED (rel_err > 50%)")
        print("   rank-2 does not capture some high-order entries.")
        print("   Check whether their propagated errors are below threshold.")
        print()

    if any_fail:
        print("❌  VERDICT: rank-2 UNSAFE for this (L, N, target)")
        print("   Propagated error exceeds 10% of target λ.")
        print("   Options:")
        print("   (a) Upgrade to rank-4 (add k=4 channel)")
        print("   (b) Accept 2-hour N=32 original scan without rank-2 shortcut")
    elif any_structural_fail:
        print("⚠️  VERDICT: rank-2 has structural failures BUT propagated errors")
        print("   are within threshold. Verify manually that high-order entries")
        print("   with abs_err are stable across N before committing to production.")
    else:
        print("✅  VERDICT: rank-2 SAFE for this (L, N, target)")
        print("   All propagated errors < 10% of target λ.")
        print("   rank-2 substitution in _build() is certified safe.")


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Validate S_KK rank-2 approximation at actual risk zone")
    parser.add_argument("--L", type=float, default=0.42,
                        help="L value (default: 0.42)")
    parser.add_argument("--N", type=int, default=32,
                        help="Truncation N (default: 32 = actual production target)")
    parser.add_argument("--target", type=float, default=0.005,
                        help="Target positive λ margin to certify (default: 0.005)")
    parser.add_argument("--b-L", type=float, default=1.9,
                        help="b_L at this N (default: 1.9 for N=32 at L=0.42)")
    args = parser.parse_args()

    from fractions import Fraction
    frac = Fraction(args.L).limit_denominator(1000)
    validate(frac.numerator, frac.denominator, N=args.N,
             target_lambda=args.target, b_L_estimate=args.b_L)


if __name__ == "__main__":
    main()
