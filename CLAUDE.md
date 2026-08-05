# CLAUDE.md — weil-first-prime development rules

## Project identity

weil-first-prime is a **certificate-first proof repository** for the FP-0.35
conjecture: the Weil quadratic form on L²(-7/20, 7/20) has strictly positive
infimum. The interval L = 7/20 lies in the first prime window (½ log 2 < L < ½ log 3).

This repository consolidates work from `weil-lower-bound` (DEPRECATED) and adds
the first-prime layer. Do not resume work in weil-lower-bound.

## Hard invariants

- **No PASS/RELEASED in certificate JSON.** Only `proofverify` may derive status
  from obligations. A certificate that self-reports its conclusion is a P0 defect.
- **No floating-point conclusions.** All bounds entering a certificate must be
  outward-rounded interval arithmetic (Arb balls). Float centers are pilot only.
- **No cross-path mixing.** Path A (potential redistribution θ=69/100) is strictly
  falsified by Theorem 6. A certificate may not combine Path A coefficients with
  Path B prime matrices to obtain "double credit."
- **Conclusion boundary.** Published conclusions are bounded to "finite-scale Weil
  positivity at L ≤ 7/20." Never write RH, "near RH," or equivalent in any file.
- **Window check mandatory.** Any certificate claiming the first-prime window must
  carry `log2 ≤ 2L < log3` verified by certified rational bounds, not enumeration.

## Architecture

```
checker/
  archimedean/    Base primitive checker (archimedean_primitives_o2_v1)
  first_prime/    FP-0.35 main checker  (exact_prime_split_v1)
src/
  archimedean/    Primitive integrators (P0 bugs from weil-lower-bound fixed here)
  prime_layer/    Legendre shift algebra (Fraction polynomials, no quadrature)
  assemble/       Full Path B certificate assembly
schemas/          JSON Schema (additionalProperties: false, fail-closed)
domains/fp035/    proofctl ContractV2 + policy-v2.json
policies/         proofctl release policy
tests/            pytest suite — must be zero failures
docs/             THEOREMS.md, PASS_CONTRACT.md, ARCHIMEDEAN_MIGRATION.md
```

## Python conventions

- After any Python change: `python -m pytest tests/ -x` — zero failures is the bar
- All numeric results that enter a certificate must be `python-flint` Arb balls
  with outward rounding. Never pass `float()` through to a certificate.
- `Fraction` arithmetic for Q[τ] polynomial algebra — no mpmath, no sympy shortcuts
- stdlib only in `checker/` and `schemas/` — no numpy/scipy imports in checker code
- Type annotations required in `src/` and `checker/`
- Exit codes for all checkers: 0=certified, 1=uncertified, 2=malformed/resource, 3=O2_BLOCKED

## P0 bugs fixed from weil-lower-bound (never re-introduce)

1. `integrator_a.integrate_M_K` — must call `_integrate_1d_arb` with GL-8/GL-4
   remainder; returning a raw GL-8 Arb ball without truncation error coverage is
   a P0 defect.
2. `integrator_b._rpp_mpmath` — near-zero Taylor cubic coefficient is `7s³/11520`,
   not `s³/2880`. Using `4|GL₁₄ − GL₈|` as a remainder without an analytic domain,
   Bernstein ellipse bound, and theorem constant is not a certified remainder.

## proofctl integration

- `proofctl doctor` must pass before any `proofctl check` or `proofctl release`
- `proofctl contract lint` must pass for all `domains/fp035/contracts/*.json`
- `BRIDGE_CHECKER` for archimedean base: `python3 checker/archimedean/check_archimedean.py`
- `BRIDGE_CHECKER` for first-prime: `python3 checker/first_prime/check_first_prime_certificate.py`
- `proofctl release --dry-run` is the safe path; never run `proofctl release` without
  reviewing the dry-run output first
- Do not use `--semantic` flag for production attestations — `exact-replay` is required

## Mutation / negative test requirements

Every push must pass the full mutation suite in `tests/mutation/`:
- Changing θ from 69/100 to any other value → checker rejects
- Swapping even/odd sector parameters → checker rejects
- Setting R_2 to zero matrix → checker rejects
- Removing one shift direction from C_{τ,1} → checker rejects
- Changing log2/√2 weight → checker rejects
- Submitting a Path A θ field alongside exact_prime_split_v1 → schema rejects (unknown field)
- Changing N_even from 8 or N_odd from 6 → checker rejects
- Changing η from 1/2 → checker rejects

## Schema conventions

- `additionalProperties: false` on every schema — unknown fields are rejected, not ignored
- `format_version: "first-prime-1.0"` and `method: "exact_prime_split_v1"` are const fields
- No matrix, eigenvalue, pivot, or conclusion values in certificate JSON — these are
  recomputed by the checker or refused as unknown fields
- `archimedean_base.obligation` must be `"archimedean_primitives_o2_v1"` exactly

## Commit conventions

- Commit messages in English
- Do not commit floating-point discovery pilot values as proof artifacts
- Do not commit certificates that have not been independently replayed by the checker
- `git status` before any commit; never stage `.proofctl/attestations/` without review

## File naming

- Python modules: `snake_case.py`
- JSON schemas: `kebab-case-v{N}.schema.json`
- Contract files: `{claim-id}.json`
- Certificate files: `cert-{sector}-{timestamp}.json`

## What this project does NOT do

- Does not claim to prove RH or any consequence of RH
- Does not contain a full proof of FP-0.35 (O1-B and O2 are open)
- Does not supersede or replace proofctl (proofctl is the orchestration layer)
- Does not provide a general Weil solver (scope is L = 7/20 only)
