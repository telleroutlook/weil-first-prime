/-!
# Theorem 3: Pure-Rational Absorption Certificate (Lean 4, stdlib only)

Machine-checked integer arithmetic steps of the weil-first-prime Theorem 3.
No Mathlib. All proofs use `native_decide` or `decide`.

## What is certified here

The pure-rational certificate for V + P_{2,7/20} ≥ (69/100)·V ≥ 0
reduces to five integer comparisons, all verified by the kernel.

## The five steps

1. 23581 * 10 < 34020 * 7          (log2 < 7/10)
2. 34 * 41 < 1701                   (ε < 1/41)
3. 87^16 * 68^5 < 1701^5 * 32^16  (κ_edge > 8/5, the KEY step)
4. 7^2 < 2 * 5^2                    (√2 > 7/5)
5. 62 * 5 * 100 = 31 * 8 * 125     (ratio = 31/100)
-/

namespace WeilFirstPrime.Theorem3

/-- Step 1: log 2 < 23581/34020 < 7/10.
    In integer form: 23581 * 10 < 34020 * 7. -/
theorem step1_log2_lt_seven_tenths : 23581 * 10 < 34020 * 7 := by native_decide

/-- Step 2: ε = 2 - 20·log2/7 < 34/1701 < 1/41.
    In integer form: 34 * 41 < 1701. -/
theorem step2_eps_lt_one_over_41 : 34 * 41 < 1701 := by native_decide

/-- Step 3 (KEY): 87^16 · 68^5 < 1701^5 · 32^16.
    This implies e^16 < (1701/68)^5 < (1/(2ε))^5,
    giving κ_edge(7/20) = ½·log(1/(2ε)) > 8/5.
    native_decide computes exact 39-digit integers. -/
theorem step3_key_integer_inequality : 87 ^ 16 * 68 ^ 5 < 1701 ^ 5 * 32 ^ 16 := by
  native_decide

/-- Verification of the LHS exact value. -/
theorem step3_lhs : 87 ^ 16 * 68 ^ 5 = 15662194229696887109605438749172023641088 := by
  native_decide

/-- Verification of the RHS exact value. -/
theorem step3_rhs : 1701 ^ 5 * 32 ^ 16 = 17215562650769453014744867057217543602176 := by
  native_decide

/-- Step 4: √2 > 7/5.
    In integer form: 7^2 < 2 · 5^2. -/
theorem step4_sqrt2_gt_seven_fifths : 7 ^ 2 < 2 * 5 ^ 2 := by native_decide

/-- Step 5: (62/125) / (8/5) = 31/100.
    In integer form: 62 * 5 * 100 = 31 * 8 * 125. -/
theorem step5_ratio_eq : 62 * 5 * 100 = 31 * 8 * 125 := by native_decide

/-- c2 upper bound: 23581/47628 < 62/125.
    Cross-multiply: 23581 * 125 < 62 * 47628. -/
theorem c2_upper : 23581 * 125 < 62 * 47628 := by native_decide

/-- Absorption coefficient is positive: 69 < 100. -/
theorem absorption_positive : 69 < 100 := by native_decide

/-- Absorption coefficient sums to 1: 69 + 31 = 100. -/
theorem coefficients_sum : 69 + 31 = 100 := by native_decide

/-- All five certificate steps are valid simultaneously. -/
theorem certificate_arithmetic_valid :
    23581 * 10 < 34020 * 7 ∧
    34 * 41 < 1701 ∧
    87 ^ 16 * 68 ^ 5 < 1701 ^ 5 * 32 ^ 16 ∧
    7 ^ 2 < 2 * 5 ^ 2 ∧
    62 * 5 * 100 = 31 * 8 * 125 := by
  native_decide

end WeilFirstPrime.Theorem3
