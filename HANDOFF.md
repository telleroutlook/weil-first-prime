# Handoff — 2026-08-07

## 1. One-line status
FP-0.35 (Weil quadratic form positive-definite at L=7/20) **holds mathematically**:
both sectors have positive Schur min-pivot (even +0.0087, odd +0.053), using the
FULL four-term S0 = S_VV+S_VK+S_KV+S_KK, real c_L ≈ 1.36527, min-pivot judge,
confirmed by two independent implementations (element-wise agreement). The
publishable certification chain (certificate + proofctl attestation) is being
regenerated because the old certificate has two process defects (§3).
**Scope boundary, non-negotiable: FP-0.35 does NOT imply RH.**

## 2. Code-trust map (read this first)
| File | Status | Note |
|---|---|---|
| checker/fp035/recompute_schur.py | TRUSTED | correct four-term S0 + min-pivot, independent recompute. Base new work on it. |
| checker/fp035/check_fp035.py | TRUSTED | calls recompute_schur (real recompute) + emits mutation metadata. |
| checker/fp035/mutation_catalog.py | TRUSTED | 6 mutants, kill_rate 100%. |
| scripts/reproduce_fp035.py | FIXED | four-term S0 + --out {cert}. Was S_KK-only (16x inflation), now fixed. |
| src/assemble/o1b_gate.py | TRUSTED | production four-term S0, mpmath LDL. |
| scripts/scan_lambda_profile.py | HAS KNOWN BUG | S0 = S_KK only. Must fix to four-term before use. |
| pilots/cert_schur_correct_cL.json | RETIRED / DO NOT USE | S_KK-only (16x inflated min_eig 0.01494) + shutil.copy. Do not reuse its numbers. |

Most dangerous bug pattern: omitting a second-moment term (S_VV/S_VK/S_KV or S2)
shrinks the residual and produces a false-positive pivot. Any Schur residual: S0
MUST be four terms.

## 3. The retired certificate's two defects (proofctl now blocks them; do not bypass)
1. S_KK-only: min_eig overstated 16x (0.01494 vs true +0.00095). Sign right, value wrong.
2. copy generation: generator was shutil.copy masquerading as from-scratch.
proofctl v0.3.16 C10 (no copy-only generator) + C11 (checker mutation coverage
== 100%) block this class. This is by design — do NOT disable C10/C11 or fake
mutation numbers to force a release; run the real recompute flow (§4).

## 4. The only active closeout chain (near-term)
Goal: put the already-true math through a clean proofctl certification.
```
1. python3 scripts/reproduce_fp035.py --out {cert}     # real recompute -> clean cert
2. proofctl replay --claim thm-fp-035 \
     --generator "python3 scripts/reproduce_fp035.py --out {cert}" \
     --checker  "python3 checker/fp035/check_fp035.py"
   # generator is real recompute (not copy) -> C10; checker emits mutation metadata -> C11
3. proofctl release --dry-run                          # expect C01-C11 all green
```
Acceptance: release --dry-run goes BLOCKED -> PASS, no C10/C11 blocker.

## 5. Environment prerequisites
- proofctl at ~/github/proofctl, needs v0.3.16 (has C10/C11); ~/bin/proofctl is the deployed copy.
- Python: python-flint (Arb), numpy. LaTeX: tectonic (paper/compile.sh).
- Long tasks (>2 min): use ~/.local/bin/run_and_wait.sh -t <sec> -- <cmd> (foreground-blocking; no bare &).
- Certify-grade four-term S0 recompute: even ~40 min, odd ~25 min. Do NOT issue
  verdicts from depth=2 fast scans (lesson: depth=2 rendered -0.022 as -0.0007, 30x error).

## 6. Three docs to read
- docs/PROOF_CONSTITUTION.md — computation/proof/handoff discipline (PART A-E):
  difficulty conservation, no-slack, narrative resistance, diff-artifacts-before-narrating,
  process-defect != wrong-conclusion. Every bug tonight violated one of these.
- docs/EXTENDED_GOALS.md — map of falsified directions (7 isomorphism mappings all
  dead; prolate = coordinate system not firepower; data-driven second-window steer).
  Do not re-run these dead ends.
- docs/SPECULATIVE_ROADMAP.md — long-term speculative route (core Lemma L is OPEN,
  no promises). Read its isolation disclaimer first.

## 7. Mid/long-term task entries — see PLAN.md 第四编-附3 (entry + acceptance for M1-M4, L1).

## 8. One sentence to the next maintainer
The biggest risk here is not mathematical difficulty but implicit assumptions
going unchecked — every bug tonight came from that. Keep the constitution's
skepticism: for any number, ask "is S0 four terms? is the judge min-pivot? where
is this script on the code-trust map?" An honest "stuck" or a negative result is
worth more than an unreviewed "pass."
