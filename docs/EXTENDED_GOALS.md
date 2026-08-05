# Extended Goals — E1, E2, E3

These three goals are pursued in parallel with FP-0.35. Each is mathematically
self-contained and publishable independently of whether FP-0.35 is completed.
They do not claim any connection to the Riemann Hypothesis.

---

## E1: Path A General Obstruction Theorem

### Statement (target)

For every L in the first-prime window (½ log 2, ½ log 3) and every θ satisfying

```
θ < 1 − c₂ / κ_edge(L),    c₂ = log2/√2,   κ_edge(L) = ½ log(1/(2ε))
```

the weakened form q̃_L = T + θV + K_L − c_L·I has a strictly negative direction.
Specifically, there exists an explicit rational Legendre vector v(L, θ) such that
q̃_L[v] < 0.

Theorem 6 is the special case L = 7/20, θ = 69/100.

### Why this is achievable

The auto-correlation polynomial method in Theorem 6 already gives the construction.
The key steps are:

1. Parametrise the negative-witness vector as v(L) = P_0 − α(L) P_2 where
   α(L) is chosen to minimise the kinetic term contribution.
2. The kernel integral K_L[v(L)] reduces to a one-dimensional integral whose
   sign depends continuously on L via the kernel r''(s·L).
3. An explicit rational bound on the integral (using |r''| ≤ 2 + analytic estimates)
   gives a continuous lower bound that is negative throughout the window.

No interval LDL^T is needed; the argument is purely analytic.

### Mathematical significance

- Proves Path A fails structurally, not accidentally, for the entire first-prime window
- Establishes that the potential-redistribution approach cannot be salvaged by
  choosing a different θ — the correct absorption coefficient must exceed
  1 − c₂/κ_edge(L) pointwise, which is exactly what Theorem 3 certifies at L = 7/20
- Gives a clean negative result that complements the positive result (FP-0.35)

### Target venue

*Journal of Spectral Theory* or *Integral Equations and Operator Theory*.
Estimated submission: October 2026 (independent of FP-0.35 completion).

---

## E2: Exact Effective Range of Endpoint Absorption

### Statement (target)

Define L* as the solution to c₂ = κ_edge(L*), i.e. the critical radius where the
Theorem 2 absorption method becomes an equality.

1. **Compute L* explicitly**: L* satisfies log2/√2 = ½ log(1/(2(2 − log2/L*))).
   Numerically L* ≈ 0.327. A certified rational bracket for L* via the methods
   of Theorem 3.

2. **Prove the method fails beyond L***: For L > L*, there exists an explicit
   function w_L such that V(w_L) + P_{2,L}(w_L) < 0. This is the exact converse
   of Theorem 2.

3. **Characterise the double-prime transition**: At L = ½ log 3 ≈ 0.549, prime 3
   enters the explicit formula. Prove that both the n=2 and n=3 layers together
   require a fundamentally different compensation mechanism — neither the
   Theorem 2 single-prime absorption nor the Theorem 5 split-residual approach
   extends directly. This sets the boundary of the current programme.

### Why this matters

This answers the natural follow-up question to FP-0.35: "How far can your method
go?" The answer is precise: up to L* ≈ 0.327 the absorption is direct; between
L* and 7/20 Path B is needed; beyond ½ log 3 the method requires new ideas.
This is useful negative information for researchers who might try to extend the
approach to larger L.

### Target venue

Can appear as Section 4 of the main FP-0.35 paper, or be submitted separately
to *Analysis and Mathematical Physics*.

---

## E3: Lean 4 Formalisation of Theorems 1–3

### Scope

Machine-checked proofs of:
- **Theorem 1**: Operator C_{b,L} decomposes as exchange matrix ⊕ zero; spectrum {−1,0,1}.
- **Theorem 2**: Endpoint potential absorption inequality.
- **Theorem 3**: Pure-rational certificate c₂/κ_edge < 31/100 at L = 7/20.

These three theorems are chosen because:
- They require no numerical integration (pure algebra and rational arithmetic)
- Theorem 3's key step — the integer inequality 87^16 · 68^5 < 1701^5 · 32^16 —
  is fully decidable by Lean's `native_decide` tactic
- Lean 4 / Mathlib already has L² spaces, self-adjoint operators, and basic
  spectral theory

### Lean infrastructure needed

| Ingredient | Mathlib status |
|---|---|
| L²(I) as Hilbert space | Available (`MeasureTheory.L2`) |
| Truncated shift operator S_{b,L} | Needs definition (~50 lines) |
| Self-adjoint C_{b,L} = S + S* | Follows from definition |
| Exchange matrix spectrum | Needs ~100 lines |
| Log endpoint potential V(x) = −½ log(1−x²) | Needs definition |
| Quadratic form inequality V + P ≥ cV | ~150 lines |
| `native_decide` for 87^16 integer computation | Automatic |

Estimated total: ~600–800 lines of Lean 4.

### Why this is valuable independently

The ITP and CPP communities do not require results to be novel mathematically —
they value correctness of formalisation. A fully machine-checked proof of
Theorem 3 (which has a genuinely non-trivial integer inequality at its core)
is a legitimate conference contribution regardless of the FP-0.35 status.

### Target venue

ITP 2027 (International Conference on Interactive Theorem Proving) or
CPP 2027 (Certified Programs and Proofs). Abstract submission typically
December 2026.

---

## Interaction between goals

```
Theorem 6 (closed) ──────→ E1 (parametrise over all L)
                                   │
                                   ↓
Theorem 2 (closed) ──────→ E2 (find where it breaks down)
                                   │
                                   ↓
                           boundary at L* and ½ log 3

Theorems 1–3 (closed) ───→ E3 (Lean 4 formalisation)
                            (independent of E1, E2, FP-0.35)
```

E1 and E2 are mathematically related (both about the limits of the absorption
approach) and could be combined into a single paper.

E3 is fully independent and can proceed in parallel at any time.

---

## What these goals do NOT claim

- None of E1, E2, E3 implies or suggests a proof of RH
- E1 proves a *negative* result (Path A fails); it does not prove FP-0.35
- E2 establishes a *boundary*; it does not extend the proof to larger L
- E3 is a formalisation of existing results; it adds no new mathematics
