# M1/M2 Findings — λ(L) profile and the absorption method's effective range

**Date:** 2026-08-07
**Status:** Self-contained data findings (M1 mostly complete, M2 complete). NOT part
of the main FP-0.35 paper, which is bounded to L = 7/20. Recorded here to preserve
the result without over-scoping the published conclusion.

**Scope boundary (unchanged):** everything below is finite-scale Weil positivity at
specific L values. It does **not** imply RH or global positivity.

## What was done

The rational-absorption Schur criterion (Theorem 5; full four-term
S⁰ = S_VV + S_VK + S_KV + S_KK, real c_L, prime self second moment S² = c₂²·E)
was evaluated across the first-prime window for both parity sectors, with
certified Arb-residual positivity checks.

- Tool: `scripts/scan_lambda_profile.py` (four-term S⁰, both sectors,
  checkpoint/resume). Fixed this session from two omitted-term bugs
  (S⁰ was S_KK-only; S² was zero) — its S⁰ assembly now matches the trusted
  `checker/fp035/recompute_schur.py` line for line.
- Artifacts: `pilots/lambda_profile.json`, `pilots/lstar_refine.json`,
  `pilots/lstar_even036.json`.

## Certified λ(L) lower-bound profile

Certified largest Λ₀ (via Arb residual) for which the Schur complement
C = b_L·F − R_η is positive definite; profile value = min over sectors.

| L | c_L | even sector | odd sector | notes |
|---|---|---|---|---|
| 0.35 (7/20) | 1.3653 | 7.8e-4 | 4.9e-2 | only robustly-positive point; even binding |
| 0.36 | 1.3934 | 7.8e-4 | — | even still genuinely certifies |
| 0.37 | 1.4208 | 2⁻³⁰ floor | 3.9e-3 | even drops to the search floor |
| 0.39 | 1.4735 | 2⁻³⁰ floor | **0 (fails)** | odd certification fails |
| 0.40 | 1.4988 | 2⁻³⁰ floor | 0 | |
| 0.42 | 1.5476 | 2⁻³⁰ floor | 0 | |
| 0.46 | 1.6386 | **0 (fails)** | 0 | even certification fails |

Caveats (honest reading):
- `7.8e-4` is the binary search's `tol=1e-3` resolution step, so it **lower-bounds**
  (does not resolve) the true even margin.
- `2⁻³⁰ floor` means certify passed at Λ₀ = 2⁻³⁰ but not higher — a boundary state,
  **not** a robust margin. Distinct from `0`, which means certify failed even at the floor.

## Critical radius L* (absorption method effective range)

- **Even sector:** L* ∈ (0.36, 0.37). Certifies with margin ≥ 7.8e-4 through L = 0.36;
  rides the 2⁻³⁰ floor 0.37–0.42; genuinely fails by 0.46.
- **Odd sector:** L* ∈ (0.37, 0.39).
- **Conclusion:** FP-0.35 (L = 7/20) sits at the *practical edge* of the absorption
  method's certified range; the even sector is the binding constraint.

## Explicit certified negative witness for L > L* (PLAN 附3 acceptance)

At L = 0.39, odd sector, Λ₀ = 2⁻³⁰, the Schur complement is not positive definite.
Explicit witness (rational, `scripts/lstar_negative_witness.py`):

    w = (−37/167, 12/611, −1/5, −56/197, −25/62, −370/453)
    wᵀ C w ∈ [−0.015546, −0.009942]   (Arb-certified, both endpoints < 0)

This rigorously proves the finite-scale positivity criterion **fails** for L > L*
in the odd sector — an explicit counterexample, as required.

## Known limitation (recorded, not pursued)

At L = 0.46 even the Schur complement is negative in float (min eig −1.2e-2), but the
Arb certification of wᵀCw straddles 0: the residual matrix R_η suffers interval
**dependency blowup** in the naive `S − Σ M[k][i]M[k][j]/G[k]` assembly (max entry
radius ≈ 27.7 vs a 0.012 signal). This is a method artifact of interval R-assembly at
larger L, **not** an integration-depth or fundamental-precision limit. Honest status:
**float-negative, Arb-pending.** A tighter R assembly (correlated/affine interval
arithmetic, or the exact-rational mpmath path used in `src/assemble/o1b_gate.py`) would
be needed to certify it — deliberately not pursued, as the odd@0.39 witness already
meets the acceptance and further L* precision is marginal value.
