# CLAUDE.md — weil-first-prime development rules

## Long-running computation requirements

Any computation that takes more than 30 seconds MUST satisfy three properties:

### 1. Observable
- Print progress to stdout as each unit of work completes, not only at the end
- Use `print(..., flush=True)` — Python buffers stdout by default; without flush,
  nothing appears until the process exits or the buffer fills
- Format: `[sector] step N/total: description (elapsed: Xs)`
- Every cache build, matrix row, and LDL^T step must emit at least one line

### 2. Pausable / killable cleanly
- Catch `KeyboardInterrupt` at the top level and save partial results to a JSON
  checkpoint file before exiting
- Checkpoint path: `pilots/<timestamp>-<sector>-<tier>.checkpoint.json`
- Checkpoint format: `{"sector", "tier", "mk_cache": {}, "completed_rows": [], "elapsed_s": N}`

### 3. Resumable from checkpoint
- On startup, check for an existing checkpoint matching the requested sector+tier
- If found, load the cached M_K values and skip already-completed rows
- CLI flag: `--resume` to explicitly load the latest checkpoint for that sector+tier
- This avoids restarting a 60-minute certify run from scratch after an interruption

### Implementation pattern for cache builds

```python
for i, (k, n) in enumerate(sorted(needed)):
    t = time.time()
    result = integrate_M_K(k, n, ...)
    cache[(k, n)] = result
    print(f"  M_K cache [{i+1}/{len(needed)}] k={k} n={n}  "
          f"[{float(result.enclosure_lower):.4e}, {float(result.enclosure_upper):.4e}]  "
          f"{time.time()-t:.2f}s", flush=True)
    checkpoint_save(cache, ...)  # save after every entry
```

### Why this matters
- The O1-B certify tier takes ~60 minutes; a crash at 59 minutes loses everything
- The pilot tier was expected to take 1 minute but ran 63 minutes silently,
  making it impossible to know if the process was stuck or making progress
- `flush=True` is not optional — it is a hard requirement for any long computation

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
- **FP-0.35 status (2026-08-07, corrected)**: Mathematically HOLDS — L=7/20 both sectors have positive Schur min-pivot (even +0.008704 / min_eig +0.00095; odd +0.053134), using the FULL four-term S0 = S_VV+S_VK+S_KV+S_KK, real c_L ≈ 1.36527, min-pivot judge; confirmed by two independent implementations (element-wise max|C_A−C_B|=4e-3). The retired certificate pilots/cert_schur_correct_cL.json is DEFECTIVE: S0 used S_KK only (min_eig inflated ~16x to 0.01494) and it was produced by shutil.copy — do NOT reuse its numbers. A clean certificate (real recomputation via checker/fp035/recompute_schur.py) is being regenerated. Even-sector margin is small but strictly positive. Bounded to finite-scale Weil positivity at L ≤ 7/20 (does NOT imply RH).
- **Window check mandatory.** Any certificate claiming the first-prime window must
  carry `log2 ≤ 2L < log3` verified by certified rational bounds, not enumeration.

## proofctl v0.3.16 release conditions & security invariants

proofctl is at v0.3.16 (this repo is its first pilot). Two release conditions
were ADDED because this pilot exposed them — every FP-0.35 certificate MUST
satisfy both:

- **C10 (no copy-only generator)**: an attestation claiming from-scratch
  recomputation whose generator_cmds is a pure file-copy (shutil.copy, cp, cat,
  ln) is BLOCKED. Checkers must genuinely recompute, not copy a stored cert.
- **C11 (checker mutation coverage)**: such an attestation must carry
  mutation_kill_rate == "100%" and a non-empty mutation_catalog_digest, proving
  the checker is sensitive to every asserted term. FP-0.35 catalog:
  checker/fp035/mutation_catalog.py (artifact pilots/mutation_catalog_fp035.json,
  6/6 kill). Catches the retired S_KK-only omitted-term bug.

Enable per-domain in policy-v2.json via forbid_copy_only_generators: true and
require_checker_mutation_coverage: true (both on for weil/fp035).

### proofctl security invariants (INV-01–INV-12)

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

## Lean 4 formalisation (E3)

Lean 4 project lives in `lean4/`. Toolchain: `leanprover/lean4:v4.32.2`.

```bash
export PATH="$HOME/.elan/bin:$PATH"
cd lean4
lake build WeilFirstPrime   # must succeed with 0 errors
```

**Current state**: `WeilFirstPrime/Theorem3.lean` — 11 theorems, all verified
by `native_decide`. No Mathlib required for the integer skeleton.

**Mathlib integration**: `lakefile.toml` declares `mathlib` dependency.
After `lake update` (requires proxy), `import Mathlib` becomes available
for `Real.log`, `Real.sqrt`, and operator theory.

**Rules for Lean files**:
- Never use `sorry` in committed proofs — use `admit` clearly labelled `ADMIT:`
  with a comment explaining what axiom or library is missing
- `native_decide` is the correct tactic for all `Nat`/`Int` comparisons
- `norm_num` requires Mathlib; use `native_decide` until Mathlib is imported
- Every new theorem must correspond to a numbered result in `paper/main.tex`

**Adding Mathlib proofs**:
```lean
import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Data.Real.Sqrt
-- then Real.log, Real.sqrt, NNReal available
```

- **C01 no longer trusts writable `outcome` field for v2 attestations**: acceptance is now derived from `ObligationResults` (all verdicts must be `"pass"`). A hand-crafted `"outcome":"accepted"` JSON can no longer bypass the release gate.
- `ir.Attestation.ObligationResults` new field — populated automatically by `proofctl verify` and `proofctl check`. No changes needed to checker code or contracts.
- Three new adversarial regression tests in `gate_security_test.go`.

**weil-first-prime action required**: none. bridge.py already emits `obligation_results` with correct verdicts. `proofctl check/verify` will populate the new field automatically on next run.

**graph.json fix**: `proofctl pin checker` wrote `runtime.kind: "native"` (pre-scripted proofctl). Fixed to `"scripted"` after rebuild.

## v0.3.14 (current) — documentation only

- **CHANGELOG correction**: v0.3.12 changelog now correctly notes that
  `MaxWallClock` was raised in v0.3.13 (not v0.3.12).
- **README + CLAUDE.md**: `replay-partial` extension updated to `.debug`;
  `proofctl check --timeout` added to command reference.
- No code changes. No adaptation required in this project.

## v0.3.13 fixes

- **MaxWallClock raised to 60m**: `--timeout 20m` in v0.3.12 was silently capped at 10m.
  Now `proofctl check --timeout 20m --all` works correctly for archimedean checkers.

## v0.3.12 additions

- **`proofctl check --timeout <duration>`**: override per-checker wall-clock timeout.
  Archimedean checker needs ~600s for even sector — use `--timeout 20m` when running
  `proofctl check @lem-o1b-even` or `--all`.
  Example: `proofctl check --timeout 20m --all`

**weil-first-prime action required**: none for release gate (uses replay path).
Use `--timeout 20m` when running `proofctl check --all` for full verification.

## v0.3.11 fixes (current)

- **B6 — `proofctl attest` wrote obligation_results=[] causing REJECTED**: After B4 fix,
  `attest` wrote pv=2 but empty `obligation_results`, so `deriveStatus` returned REJECTED.
  Now reads obligations from `domains/*/contracts/<claim>.json` and fills all with `verdict: pass`.
  Falls back to synthetic `independent-review.accepted` when no contract found.

- **B3 — `proofctl replay` dropped `metadata` from checker stdout**: Checker JSON `"metadata"`
  map is now merged into attestation `Metadata`, enabling `required_metadata_keys` policy
  conditions to be satisfied without bridge.py.

**weil-first-prime action required**: none — replay attestations already use the new binary.
`proofctl attest` now works correctly for independent-review claims without workarounds.

## v0.3.10 fixes

- **B4 — `proofctl attest` wrote v1 attestations**: `buildAndWriteAttestation` now populates
  `att.Checker` from the graph's checkers array. Fixes `LEGACY_ATTESTATION_NOT_RELEASABLE`.
  Requires `--metadata reviewer=<name>` for independent-review assurance.

- **B5 — partial replay debug file `.json` extension crashed `proofctl status`**: Now uses
  `.debug` extension. No more manual cleanup needed after a failed replay.

- **D4 — CAS check reported "skipped"**: Now stats each declared blob individually.

- **D5 — REJECTED claims showed no reason**: Status line now includes rejection reason.

- **I2 — `compile --adapter contract-dir` wiped checkers array**: Now preserves existing
  checker entries from graph.json on re-compile.

**weil-first-prime action required**: none — all fixes are in the compiled binary.

## v0.3.6 fixes

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
active. Current `proofctl replay` is same-environment replay only.

`proofctl doctor` (v0.3.7+) will show a `⚠ scripted-runtime` warning — this
is expected and informational. Migrate to `isolated-oci` before external
publication (see `docs/OCI_MIGRATION.md`). The `Dockerfile` at repo root
pins all dependencies; after O1-B+O2 close, build, push, and update
`runtime.kind` and `runtime.digest` in graph.json.

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
