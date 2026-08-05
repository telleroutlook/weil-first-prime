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

## proofctl v0.3.4 security invariants (INV-01–INV-12)

These are enforced by proofctl's kernel layer. Violations produce hard errors,
not warnings. Every PR that touches checker, runtime, or attestation code must
identify which INV it affects and provide a covering test.

| INV | Enforcement point in this project |
|---|---|
| INV-01 | Checker output has no `outcome`/`assurance` field — `obligation_results` only |
| INV-02 | Attestation binds full identity closure (statement + dep digests + checker digest) |
| INV-03 | `self_digest` recomputed on load; tampered attestations rejected at load time |
| INV-04 | Ed25519 signature verified against `.proofctl/keys/*.pub` (C05 condition) |
| INV-05 | Assurance derived from `ObligationResults` by proofctl; checker cannot assert it |
| INV-06 | Obligation exact-set: OBLIGATION_MISSING / EXTRA / DUPLICATE all → hard reject |
| INV-07 | Any evidence item failure → whole claim fails; no partial-pass masking |
| INV-08 | Dep not at required state → LOCALLY_VERIFIED (not GLOBALLY_VERIFIED) |
| INV-09 | Identity closure change → downstream claims go STALE automatically |
| INV-10 | `runtime.class: "scripted"` is the correct label for native Python checkers (v0.3.5). `scripted` can reach `GLOBALLY_VERIFIED`. `native-dev` and `native` are permanently capped at `LOCALLY_VERIFIED`. Never use `native-dev`, `native`, or the incorrect `wasi` label in contracts or graph.json. |
| INV-11 | `proofverify` never reads STATUS.json; derives state from v2 bundle files only |
| INV-12 | Release bundle is self-verifiable offline; all member digests checked |

**INV-10 is the most critical for this project.** All contracts use `wasi` runtime.
Never change `runtime.class` to `native` or `native-dev` in any contract or graph.json.

## v0.3.6 fixes (current)

- **derive.go Rule 6a comment**: `scripted` exclusion from the native cap is now documented in-code
- **fp035-policy template**: `version: "2"`, `forbidden_runtimes` includes `"native"` — matches our policy
- **bridge.py conditional Weil keys**: `path_keys_match`, `intervals_intersect`, `matrix_reconstructed`, `ldlt_passes` now read from cert field (`true`/`false`) and only emitted when the cert carries them. fp035 certs that omit these fields produce no spurious metadata entries. `digests_fresh` remains unconditional.

No changes needed in weil-first-prime for v0.3.6 — our policies already excluded the bogus keys.

## v0.3.5 additions

- **`scripted` runtime class**: honest label for native Python checkers. Can reach `GLOBALLY_VERIFIED`. All fp035 contracts use this.
- **bridge.py**: `window_verified`, `archimedean_obligation`, `pivot_count` now extracted from certificate fields (not hardcoded)
- **`compile --adapter contract-dir <dir>`**: compile `domains/fp035/contracts/` directly into `.proofctl/graph.json`
- **`graph_source` in config.json** now actually used by `loadProjectGraph`
- **`fp035` domain** registered in scaffold: `proofctl init --domain fp035` works

**Remaining bridge.py issue (not fixed in v0.3.5):** Four metadata keys (`path_keys_match`, `intervals_intersect`, `matrix_reconstructed`, `ldlt_passes`) are still hardcoded `"true"` whenever the checker exits 0. They provide no real verification signal. These keys are intentionally **excluded** from `required_metadata_keys` in our policy files.

## v0.3.4 behavioral changes vs v0.2.8

- **v1 attestations rejected at release gate** (`LEGACY_ATTESTATION_NOT_RELEASABLE`)
- **`proofverify --trust-root` is now required**; omitting it → exit 1
- **`obligation_ids` in CheckerInputV2 is authoritative**; bridge reads from Contract,
  not from certificate self-report (which can no longer shrink the set)
- **Empty ObligationResults → `OBLIGATION_EMPTY` hard error** (was silently true before)
- **`replay_profile` field required** in all ContractV2 JSON files

## proofctl usage in this project

See `docs/PROOFCTL_INTEGRATION.md` for full command reference.

Required env vars (auto-loaded from `.proofctl/env.json`):
```
BRIDGE_CHECKER=python3 checker/first_prime/check_first_prime_certificate.py
PROOFCTL_ADAPTERS=<path-to-proofctl-checkout>/adapters
```

### When to use which command

| Command | When | Why |
|---|---|---|
| `proofctl doctor` | Start of every session | Confirm env is wired before any check/replay |
| `proofctl status` | Daily, during active work | See all 17 claim states at a glance |
| `proofctl frontier thm-fp-035` | During O1-B work | See what directly blocks the main theorem right now |
| `proofctl graph --mermaid` | Weekly or before doc updates | Refresh the dependency diagram in docs/ |
| `proofctl pin checker --cmd ...` | After any checker script change | Lock checker_digest so cache keys are valid |
| `proofctl check --all` | After pinning | Verify all checkers run without protocol errors |
| `proofctl replay --dry-run` | Before generating a new certificate | Confirm CAS state and generator syntax are correct |
| `proofctl release --dry-run` | After O1-B closes | See exactly which conditions still block release |
| `proofctl snapshot` | At each milestone | Point-in-time progress record for comparison |
| `proofctl bundle create` | At final PASS only | Produce the offline-verifiable release bundle |

### What proofctl does NOT guarantee

proofctl verifies that:
- The exact pinned checker script was run (`checker_digest`)
- The evidence file hash matches what was declared (`evidence_digest`)
- Attestation self-digests have not been tampered with (INV-03)
- Obligation exact-sets match the ContractV2 declaration (INV-06)

proofctl does **not** verify that the checker's mathematics is correct.
Mathematical correctness comes from the checker code, the test suite, and
independent review. Do not conflate proofctl attestation with mathematical proof.

The `scripted` runtime means the trust anchor is `evidence_digest + checker_digest`
(same as a pinned binary, interpreted rather than compiled). Cross-machine
deterministic replay requires container isolation (OCI), which is not yet
implemented. Current `proofctl replay` is same-environment replay only.

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
