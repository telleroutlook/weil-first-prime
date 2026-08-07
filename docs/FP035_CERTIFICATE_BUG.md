# FP-0.35 Certificate - Corrected Analysis (2026-08-07)

## Status: FP-0.35 HOLDS (min_pivot > 0), but the published certificate has a
## 16x-inflated eigenvalue and a non-reproducible (copy-based) generation path.

## Executive summary (after a decisive element-wise cross-check)
Two independent implementations (checker/fp035/recompute_schur.py and
src/assemble/o1b_gate.py), built with the FULL four-term S0 and compared
element-wise, AGREE on the L=7/20 even-sector Schur complement C:
  max|C_A - C_B| = 4e-3, eigmin_A = +0.000950, eigmin_B = +0.000935,
  min LDL pivot  = +0.0087 (both).
The sign is POSITIVE. FP-0.35 (lambda(7/20) > 0 under the split-residual Schur
criterion at N=8) is therefore SATISFIED.

## Two real defects - neither changes the sign, both must be fixed for honesty

### Defect 1 - inflated eigenvalue in the published certificate (16x)
The certificate pilots/cert_schur_correct_cL.json and paper/main.tex report
even-sector min_eig = 0.01494. That number was produced with S0 = S_KK only
(the generator reproduce_fp035.py:135 omitted S_VV + S_VK + S_KV). Omitting
those positive terms SHRINKS R0, INFLATES the Schur complement, and overstates
min_eig by ~16x. The correct four-term value is min_eig = +0.00095
(min_pivot = +0.0087). The sign is unchanged, but the published margin is
wrong by an order of magnitude and the true margin is thin.

### Defect 2 - copy-based, non-reproducible generation
The attestation generator was
python3 -c "shutil.copy('certs/thm-fp-035.json', {cert})" - a file copy marked
replay_mode=from_scratch. The certificate was not recomputed by the checker;
the checker (check_fp035.py) hard-coded all obligations to True.

## What was WRONG in the earlier night analysis - retracted
An earlier pass concluded min_pivot = -0.043 and "FP-0.35 fails under the
correct criterion." That -0.043 was an ERROR in an ad-hoc script (incorrect
R_eta assembly); it never appeared in the two agreeing implementations. The
decisive element-wise C-matrix comparison shows the true value is +0.0087.
All downstream conclusions built on -0.043 (the "-0.02 Young floor", "split
cannot certify", "joint Schur needed") are RETRACTED. Correct picture:
split-residual Schur DOES certify N=8 with a thin (+0.00095) margin.

## Required fixes
1. Recompute odd sector with four-term S0 (in progress) - the paper 0.06417 is
   likewise S_KK-only and must be replaced by the correct value.
2. Regenerate the certificate by genuine recomputation (not shutil.copy), to
   satisfy proofctl C10 (no copy-only generator) and C11 (mutation coverage).
3. Correct paper/main.tex eigenvalues (0.01494 / 0.06417 -> four-term values)
   and state the true (thin) margin honestly.
4. Fix check_fp035.py to call recompute_schur (real recomputation).

## proofctl outcome (unchanged, justified)
proofctl v0.3.15 (C10) + v0.3.16 (C11) correctly BLOCK this certificate: it was
copy-generated (C10) and its checker omitted terms (C11 motivation).
fail-closed blocking a process-non-compliant certificate is correct EVEN THOUGH
the underlying sign is right. The pilot value stands: the tool now forces
honest, reproducible, term-complete certification.
s correct EVEN THOUGH the
underlying sign is right. The pilot value stands: the tool now forces honest,
reproducible, term-complete certification.
