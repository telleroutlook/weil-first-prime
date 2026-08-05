import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Analysis.SpecialFunctions.Pow.Real
import Mathlib.Analysis.Real.Sqrt
import Mathlib.Tactic

/-!
# Theorem 3: Pure-Rational Absorption Certificate (with Mathlib)

Part A — Integer arithmetic (native_decide): five comparisons, no axioms.
Part B — Transcendental bounds: log 2 < 7/10 and sqrt 2 > 7/5 via Mathlib.
-/

namespace WeilFirstPrime.Theorem3

/-! ## Part A: Integer arithmetic (native_decide) -/

theorem step1_log2_lt_seven_tenths : 23581 * 10 < 34020 * 7 := by native_decide
theorem step2_eps_lt_one_over_41   : 34 * 41 < 1701         := by native_decide
theorem step3_key_integer_inequality : 87 ^ 16 * 68 ^ 5 < 1701 ^ 5 * 32 ^ 16 := by native_decide
theorem step3_lhs : 87 ^ 16 * 68 ^ 5 = 15662194229696887109605438749172023641088 := by native_decide
theorem step3_rhs : 1701 ^ 5 * 32 ^ 16 = 17215562650769453014744867057217543602176 := by native_decide
theorem step4_sqrt2_gt_seven_fifths : 7 ^ 2 < 2 * 5 ^ 2    := by native_decide
theorem step5_ratio_eq              : 62 * 5 * 100 = 31 * 8 * 125 := by native_decide
theorem c2_upper                    : 23581 * 125 < 62 * 47628    := by native_decide

theorem certificate_arithmetic_valid :
    23581 * 10 < 34020 * 7 ∧
    34 * 41 < 1701 ∧
    87 ^ 16 * 68 ^ 5 < 1701 ^ 5 * 32 ^ 16 ∧
    7 ^ 2 < 2 * 5 ^ 2 ∧
    62 * 5 * 100 = 31 * 8 * 125 := by native_decide

/-! ## Part B: Transcendental bounds (Mathlib) -/

/-- log 2 > 0 -/
theorem log2_pos : (0 : ℝ) < Real.log 2 := by
  apply Real.log_pos; norm_num

/-- log 2 < 7/10.
    Proof: exp(7/10) > 2 via the partial sum 1 + 7/10 + (7/10)²/2 + (7/10)³/6 = 12013/6000 > 2. -/
theorem log2_lt_seven_tenths : Real.log 2 < 7 / 10 := by
  have key : (2:ℝ) < Real.exp (7/10) := by
    have h1 := Real.sum_le_exp_of_nonneg (show (0:ℝ) ≤ 7/10 by norm_num) 4
    have hval : (2:ℝ) < ∑ i ∈ Finset.range 4, (7/10:ℝ)^i / i.factorial := by
      norm_num [Finset.sum_range_succ]
    linarith
  linarith [Real.log_lt_log (by norm_num : (0:ℝ) < 2) key,
            Real.log_exp (7/10 : ℝ)]

/-- sqrt 2 > 7/5. Proof: (7/5)^2 = 49/25 < 2. -/
theorem sqrt2_gt_seven_fifths : (7 : ℝ) / 5 < Real.sqrt 2 := by
  rw [show (7 : ℝ) / 5 = Real.sqrt ((7/5)^2) from by
    rw [Real.sqrt_sq (by norm_num : (7:ℝ)/5 ≥ 0)]]
  apply Real.sqrt_lt_sqrt (by norm_num)
  norm_num

/-- The full certificate: combining integer steps with transcendental bounds. -/
theorem theorem3_combined :
    Real.log 2 < 7 / 10 ∧
    (7 : ℝ) / 5 < Real.sqrt 2 ∧
    87 ^ 16 * 68 ^ 5 < 1701 ^ 5 * (32 : ℕ) ^ 16 := by
  exact ⟨log2_lt_seven_tenths, sqrt2_gt_seven_fifths, step3_key_integer_inequality⟩

end WeilFirstPrime.Theorem3
