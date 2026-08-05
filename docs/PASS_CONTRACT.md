# Pass Contract — FP-0.35

FP-0.35 may be marked PASS only when **all ten conditions** hold simultaneously.
This document is the authoritative machine-checkable specification.

## Condition 1: Proposition identity

The normalized statement must fix:
- Form: Q_W on L²(-7/20, 7/20), Suzuki convention (2.5)/(2.11)
- Inner product: L² on I_L = (-7/20, 7/20)
- Endpoint: L = 7/20 exactly (not 0.35, not 69/200)
- Constants: c_2 = log2/√2, c_{7/20} as in the frozen model contract

## Condition 2: Raw witnesses

All integral values entering the certificate must be recomputed from:
- Basis functions (Legendre polynomials via exact recurrence)
- Piecewise domains with exact rational endpoints
- Outward-rounded Arb interval arithmetic
- Analytic remainder bounds (Bernstein ellipse)

Self-reported integral values or minimum eigenvalues in the certificate JSON
are automatically rejected as unknown fields (schema enforces this).

## Condition 3: Prime completeness

The checker must verify `log2 ≤ 2L < log3` using certified rational bounds,
not by enumeration or floating-point comparison. The rational certificate is:
- 2L = 7/10; log2 < 23581/34020 < 7/10 → 2L > log2
- 7/10 < 1 < log3 → 2L < log3

## Condition 4: Path identity

The certificate method field must be `"exact_prime_split_v1"`.
Any θ field, potential_coefficient, matrix, pivot, or conclusion field
triggers `additionalProperties: false` rejection from the schema.
Path A and Path B cannot be mixed.

## Condition 5: Continuous space closure

The checker must independently verify:
- Theorem 3 rational certificate: c_2/κ_edge < 31/100
- QTQ ≥ H_d Q: complement-space kinetic lower bound
- ‖K_L‖ ≤ κ_L: Archimedean kernel norm bound
- b_L = H_d - c_L - L_0 - κ_L > 0

## Condition 6: Archimedean dual-path

Two independent primitive integration paths must re-verify:
- M_V, M_K (Path A: GL quadrature with Bernstein ellipse remainder)
- S_VV, S_VK, S_KV, S_KK (both paths)
- Paths must have distinct integrand source SHA256s
- Intersection: Path A ∩ Path B non-empty per matrix entry

## Condition 7: Prime layer obligation

The checker recomputes from first principles:
- J_{ij}(τ) via Legendre recurrence and exact polynomial arithmetic
- E_{ij}(τ) via same
- M^(2) = -c_2 · J with rational-bounded c_2
- S^(2) = c_2² · E with rational-bounded c_2²
- R_2 = S^(2) - (M^(2))* G^{-1} M^(2)
- R_η = (1 + η) R_0 + (1 + 1/η) R_2 with frozen η = 1/2
- Final: b_L · F - R_η via interval LDL^T

## Condition 8: Negative tests

The following mutations must all be rejected:
| Mutation | Expected outcome |
|---|---|
| θ field present | schema rejects (unknown field) |
| Swap even/odd sector | schema rejects (N/tail_degree mismatch) |
| Change N_even from 8 | schema rejects |
| Change N_odd from 6 | schema rejects |
| Change η from 1/2 | schema rejects |
| Relax prime list (remove n=2) | checker rejects (window check fails) |
| Flip prime term sign | checker rejects (wrong c_2 direction) |
| Remove one shift direction from C_{τ,1} | checker rejects (J matrix wrong) |
| Set R_2 = 0 | checker rejects (Schur criterion not met) |
| Change log2/√2 weight | checker rejects (c_2 hash mismatch) |

## Condition 9: Fail-closed proofverify

- `proofverify` is the only process that may derive the PASS/FAIL status
- Certificate JSON must not contain any `status`, `conclusion`, `certified`, or
  `released` field — schema rejects these as unknown
- `proofctl release` evaluates C01–C09 + domain conditions
- Shadow mode must be disabled (`shadow_mode: false`) before a real release

## Condition 10: Conclusion boundary

The published conclusion is bounded to:
> "The local Weil quadratic form Q_W^L on L²(-L, L) is strictly positive
>  for all L ≤ 7/20."

The following statements are **forbidden** in any published output:
- "This proves the Riemann Hypothesis"
- "This implies RH"
- "This is close to a proof of RH"
- Any claim about zeros of the Riemann zeta function
- Any claim about the critical line beyond the finite-scale result

---

## Status check commands

```bash
# Verify all claims are in expected state
proofctl status

# Dry-run release (no files written)
proofctl release --dry-run

# Run mutation test suite
python -m pytest tests/mutation/ -v

# Run full test suite
python -m pytest tests/ -v

# Offline bundle verification
proofverify bundle.verify .proofctl/bundle/
```
