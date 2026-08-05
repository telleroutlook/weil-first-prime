# weil-first-prime

[![CI](https://github.com/telleroutlook/weil-first-prime/actions/workflows/ci.yml/badge.svg)](https://github.com/telleroutlook/weil-first-prime/actions/workflows/ci.yml)

**Certificate-first proof infrastructure for FP-0.35 and related results.**

FP-0.35 asks whether the local Weil quadratic form on L²(-7/20, 7/20) is
strictly positive. The interval L = 7/20 lies just past the first prime
threshold (½ log 2 < 7/20 < ½ log 3), making it the minimal non-trivial
target that requires genuine additive–multiplicative coupling.

**Note on scope.** FP-0.35, even if proved, does not imply the Riemann
Hypothesis. There is no known path from finite-scale Weil positivity to the
full statement. This repository pursues results that stand on their own
mathematical merit, with three extended goals (E1–E3) that are publishable
independently of whether FP-0.35 is completed.

This repository consolidates `weil-lower-bound` (archived DEPRECATED) with the
first-prime window infrastructure and two P0 integrator bug fixes
(see `docs/ARCHIMEDEAN_MIGRATION.md`).

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
| O1-B even sector (N=8, d=16, η=1/2) | **CERTIFIED** min_pivot=0.529 | certify tier (depth=4, dps=100) |
| O1-B odd sector (N=6, d=13, η=1/2)  | **CERTIFIED** min_pivot=0.560 | certify tier (depth=4, dps=100) |
| Path A ∩ Path B (100 M_K entries)   | **Verified**  all intersect   | depth=4, 23 tests |
| O2: trusted proof chain | **In progress** | Bernstein remainder + replay pending |

**FP-0.35 does not imply RH.** Results are finite-scale only.

## Extended goals (independent of FP-0.35)

Three additional results are pursued in parallel. Each is publishable on its
own merits regardless of whether FP-0.35 is completed.

| Goal | Description | Target venue | Independent? |
|---|---|---|---|
| **E1** — Path A general obstruction theorem | Generalise Theorem 6: for *all* L in the first-prime window, any potential-redistribution coefficient θ below the absorption threshold produces a negative direction. A structural negative result for the whole window. | *Journal of Spectral Theory* | **Yes** |
| **E2** — Exact effective range of endpoint absorption | Identify the critical L* where the Theorem 2 method becomes tight, prove it fails beyond L*, and characterise the structural change when a second prime (log 3/2) enters. Establishes the precise "range of fire" of this proof route. | Appendix of FP-0.35 paper, or *Analysis and Mathematical Physics* | Partial |
| **E3** — Lean 4 formalisation of Theorems 1–3 | Machine-checked proofs. Theorem 3's integer comparison (87¹⁶ · 68⁵ < 1701⁵ · 32¹⁶) verified by `native_decide`. Mathlib integration in progress. | ITP 2027 or CPP 2027 | **Yes** |

**Timeline (updated 2026-08-05)**

| Period | Milestone | Status |
|---|---|---|
| Aug 2026 | G1–G2 integrator migration, Legendre algebra | ✅ Done |
| Aug 2026 | O1-B certify (both sectors) | ✅ Done (min_pivot 0.529/0.560) |
| Aug 2026 | Path A ∩ Path B dual-path verification | ✅ Done (100 entries) |
| Aug 2026 | proofctl v0.3.8 integration, checkers pinned | ✅ Done |
| Aug 2026 | E3 Lean 4 Theorem 3 integer skeleton | ✅ Done (`native_decide`) |
| Aug 2026 | LaTeX preprint framework (Theorems 1–6) | ✅ Done (`paper/main.tex`) |
| Aug 2026 | CI (pytest + schema + proofctl lint) | ✅ Done |
| Aug–Sep 2026 | O2: Bernstein ellipse analytic remainder | In progress |
| Aug–Sep 2026 | E3: Mathlib Real.log/sqrt integration | In progress |
| Sep–Oct 2026 | proofctl replay cold-start; arXiv preprint | Planned |
| Oct–Nov 2026 | E1 Path A obstruction theorem paper | Planned |
| Dec 2026–Feb 2027 | E2 effective range analysis; ITP/CPP submission | Planned |

Optimistic total: **2–3 publishable results by end of 2026.**

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

## proofctl trust model

This project uses [proofctl](https://github.com/telleroutlook/proofctl) as the
proof orchestration layer. The trust model is explicit:

**What proofctl guarantees:**
- The exact pinned checker script was run (`checker_digest` in graph.json)
- The evidence file hash matches what was declared (`evidence_digest`)
- Attestation `self_digest` has not been tampered with (INV-03)
- Obligation exact-sets match the ContractV2 declaration (INV-06)
- `native-dev` / `native` runtime results are permanently capped at
  `LOCALLY_VERIFIED` and cannot reach `RELEASED` (INV-10)

**What proofctl does NOT guarantee:**
- The mathematical correctness of the checker code
- Cross-machine deterministic replay (current `scripted` runtime; see
  `docs/OCI_MIGRATION.md` for the path to `isolated-oci`)

Mathematical correctness is established by: the checker test suite (102 tests),
independent Path A ∩ Path B intersection verification, schema `additionalProperties:
false` blocking self-reported conclusions, and the mutation test suite (24 tests).

`proofverify` is the offline-only verification binary. It reads no STATUS.json and
derives claim states solely from the v2 attestation bundle — see
`docs/PROOFCTL_INTEGRATION.md` for full command reference.

## Benchmark timing

Measured on Apple Silicon (single-core equivalent):

| Operation | Time |
|---|---|
| `pytest tests/` (102 tests) | ~10 s |
| `o1b_gate --tier pilot` (one sector) | ~2 min |
| `o1b_gate --tier certify` (both sectors) | ~3 min |
| Path A ∩ Path B verification (100 entries) | ~45 s |

For environments without `python-flint`, all tests except the flint-marked ones
still pass. The `--resume` flag allows interrupted certify runs to continue from
the last checkpoint (`pilots/checkpoint-*.json`).

## License

MIT
