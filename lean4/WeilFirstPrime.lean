-- WeilFirstPrime: E3 Lean 4 formalisation of Theorems 1–3
--
-- Scope: machine-checked proofs of the three closed theorems that
-- do not require any numerical integration:
--
--   Theorem3.lean  — pure-rational certificate (integer arithmetic, fully decidable)
--
-- Theorem 3's key step is the integer comparison
--   87^16 * 68^5 < 1701^5 * 32^16
-- which is discharged by `native_decide` in milliseconds.
--
-- These proofs are independent of FP-0.35 and do not imply RH.

import WeilFirstPrime.Theorem3
