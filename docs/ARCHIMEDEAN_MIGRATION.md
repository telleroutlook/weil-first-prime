# Archimedean Migration from weil-lower-bound

## Summary

`weil-lower-bound` (archived as DEPRECATED) developed the Archimedean
primitive integrators for M_V, M_K, S_VV, S_VK, S_KK. The code was
migrated here with two P0-class bugs fixed. **Do not resume work in
weil-lower-bound.**

## P0 Bug 1: integrate_M_K missing quadrature truncation error

**Location in weil-lower-bound:** `src/integrator_a.py::integrate_M_K`

**Bug:** The function returned the direct result of a GL-8 quadrature rule
as an Arb ball, covering only floating-point rounding of the node arithmetic.
It did not call `_integrate_1d_arb`, which includes a GL-8/GL-4 remainder
term covering quadrature truncation error.

**Consequence:** The returned interval was far narrower than the true
uncertainty. Any certificate whose M_K relied on this function has an
interval that does not enclose the true integral value.

**Fix in this repository:** `src/archimedean/integrator_a.py::integrate_M_K`
always calls `_integrate_1d_arb` with the Bernstein ellipse analytic remainder.
The interval width is wider but correct.

**Test:** `tests/archimedean/test_integrator_a.py::test_mk_interval_includes_gl14`
verifies that the GL-14 estimate lies within the returned GL-8 + remainder ball.

## P0 Bug 2: _rpp_mpmath wrong Taylor cubic coefficient

**Location in weil-lower-bound:** `src/integrator_b.py::_rpp_mpmath`

**Bug:** The near-zero Taylor series for r''(s) used the coefficient `s³/2880`
for the cubic term. The correct coefficient is `7s³/11520`.

Derivation: r(s) = s²/2 log(s) - (3/4)s² + ..., giving
r''(s) = log(s) + 1 + ... The near-zero expansion to order s³ is:
```
r''(s) = -2 cosh(u) + (1/4)(1/sinh(u) - 1/u) + 1/(4 cosh(u))
       ≈ -1/2 + (7/96)s² + ...
```
The s³ antiderivative coefficient is 7/(11520), not 1/2880.

**Secondary bug:** Using `4|GL_14 - GL_8|` as the remainder bound is an
empirical convergence estimate, not a certified bound. A certified remainder
requires:
1. An analytic continuation domain (Bernstein ellipse or explicit strip)
2. A proven bound on |f| on that domain
3. The Gauss–Legendre error formula with the above constants

**Fix in this repository:** `src/archimedean/integrator_b.py::_rpp_series`
uses coefficient `Fraction(7, 11520)` (exact rational). The remainder uses
a Bernstein ellipse bound with the analytic domain explicitly verified.

**Test:** `tests/archimedean/test_integrator_b.py::test_cubic_coefficient_exact`
asserts the coefficient is exactly `Fraction(7, 11520)`.

## What was NOT broken in weil-lower-bound

The following components from weil-lower-bound are mathematically sound and
were migrated without change:

- D1 (normalization.tex): Fourier/Weil/scaling conventions — correct
- D2 (reduction.tex): closed-form domain, parity decomposition — correct (post-2026-08-03 fix)
- D3 (legendre-tail.tex): Legendre diagonalization, QTQ ≥ H_d Q — correct (post-2026-08-03 fix)
- Matrix assembly structure (assemble.py): R = S - M* G^{-1} M and bF-R — correct
- Schur complement completion-of-square argument — correct

## Migration checklist

- [x] integrator_a: GL-8 + remainder replaces raw GL-8
- [x] integrator_b: 7s³/11520 coefficient; Bernstein ellipse remainder
- [x] All integrators return Arb balls with outward rounding
- [x] No `float()` calls in integrator output paths
- [x] Legacy certificate files not imported (no provenance contamination)
- [ ] Full dual-path (A ∩ B) intersection test — pending O2 closure
- [ ] Arb LDL^T with interval matrix arithmetic — pending O1-B closure
