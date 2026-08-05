# weil-first-prime

**Certificate-first proof infrastructure for FP-0.35.**

FP-0.35 asks whether the local Weil quadratic form on L²(-7/20, 7/20) is
strictly positive. The interval L = 7/20 lies just past the first prime
threshold (½ log 2 < 7/20 < ½ log 3), making it the minimal non-trivial
target that requires genuine additive–multiplicative coupling.

This repository handles **only** the first-prime window. It depends on the
Archimedean primitives (M_V, M_K, S_VV, S_VK, S_KK) that were developed in
`weil-lower-bound`; those primitives are re-implemented here with the two P0
bugs fixed (see `docs/ARCHIMEDEAN_MIGRATION.md`).

## Status

| Item | Status | Evidence level |
|---|---|---|
| Theorem 1 + Corollaries 1–2 | Closed | Analytic proof, Lean-ready |
| Theorem 2: endpoint potential absorption | Closed | Analytic proof |
| Theorem 3: pure-rational certificate | Closed | Rational series certificate |
| Corollary 3.1: potential redistribution | Closed | Direct corollary |
| Theorem 4: prime Legendre matrix algebra | Closed | Q[τ] exact algebra |
| Theorem 5: split-residual Schur criterion | Closed | Analytic proof |
| Theorem 6: Path A strict negative witnesses | Closed | Rational + Arb-certified |
| FP-0.35 | **Conjecture** | Open |
| O1-A (weakened path) | Falsified | Two rational negative witnesses |
| O1-B even sector (N=8, d=16, η=1/2) | discovery positive, uncertified | Current main route |
| O1-B odd sector (N=6, d=13, η=1/2) | discovery positive, uncertified | Current main route |
| O2: trusted proof chain | **Unresolved** | Engineering bottleneck |

**FP-0.35 does not imply RH.** Results are finite-scale only.

## Repository layout

```
checker/
  archimedean/          Archimedean base primitive checker (Path A + Path B)
  first_prime/          FP-0.35 exact_prime_split_v1 checker
schemas/
  certificate-archimedean-v1.schema.json
  certificate-first-prime-v1.schema.json
src/
  archimedean/          Primitive integrators (P0 bugs fixed)
    integrator_a.py     Path A: GL quadrature with certified remainder
    integrator_b.py     Path B: Taylor + GL with correct 7s³/11520 coefficient
    assembler.py        M, S, R, F matrix assembly
  prime_layer/
    legendre_shift.py   J_{ij}(τ), E_{ij}(τ) via Legendre recurrence + Fraction
    assembler.py        M^(2), S^(2), R_2, R_η assembly
  assemble/
    assemble.py         Full Path B certificate assembly
docs/
  THEOREMS.md           All six closed theorems with proofs
  ARCHIMEDEAN_MIGRATION.md  P0 bug fixes from weil-lower-bound
  PASS_CONTRACT.md      Machine-checkable PASS conditions
  PROOF_STRUCTURE.md    Claim DAG and dependency graph
domains/fp035/
  policy-v2.json        proofctl policy for FP-0.35
  contracts/            ContractV2 JSON for each claim
policies/
  fp035-release-v1.json proofctl release policy
tests/
  archimedean/          Tests for base primitive integrators
  prime_layer/          Tests for Legendre shift algebra
  mutation/             Negative / mutation tests
```

## Using proofctl

This project is orchestrated by [proofctl](https://github.com/telleroutlook/proofctl).

```bash
# Check project health
proofctl doctor

# Show claim status
proofctl status

# Run checker on a specific claim
proofctl check @lem-thm3-rational-certificate

# Attempt release (dry run)
proofctl release --dry-run
```

## Pass contract

FP-0.35 is marked PASS only when **all** of the following hold simultaneously:

1. Frozen model identity verified (claim `def-frozen-model-fp`)
2. Theorem 3 rational certificate independently replayed
3. Window verified: 2 < e^{2L} < 3 (strictly, not by enumeration)
4. Certificate uses only `exact_prime_split_v1`; any θ field triggers rejection
5. Archimedean dual-path: both Path A and Path B re-verify M_V, M_K, S primitives
6. Checker recomputes J, E, M^(2), S^(2), R_2 from Legendre recurrence and frozen η=1/2
7. b_L > 0 and b_L·F − R_η ≻ 0 verified by interval LDL^T
8. Negative tests: swap parity, change N, remove one shift direction, zero R_2 → all reject
9. Fail-closed `proofverify`; no PASS/RELEASED written into certificate JSON
10. Conclusion bounded to "finite-scale Weil positivity at L ≤ 7/20"

## Dependency on weil-lower-bound

`weil-lower-bound` is archived as DEPRECATED. Its Archimedean primitive layer
has been migrated here with P0 fixes. Do not resume work in `weil-lower-bound`.

## License

MIT
