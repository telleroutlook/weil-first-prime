# Extended Goals — E1, E2, E3, and Post-FP-0.35 Routes

These goals are pursued after FP-0.35 is proved (Theorem 7.3, 2026-08-06).
E1–E3 are mathematically self-contained; Routes 0–3 are the post-proof programme.

---

## Post-FP-0.35 Research Routes

### Route 0 / Phase 0: λ(L) Lower-Bound Profile (THIS REPO, Task #14)

**Goal**: Replace the fixed $\Lambda_0 = 2^{-30}$ with a free variable, and binary-search the largest certified $\Lambda_0(L)$ for each $L$ in the first-prime window. Produces a true lower-bound profile $\lambda(L) \geq \Lambda_0(L)$.

**Method**: `scripts/scan_lambda_profile.py` — reuse existing Schur residual certification, add `--lambda0` parameter. Binary search per L (about 4-5 iterations × 4 min each = ~20 min per point).

**Important distinction** (from route_recommendation_v2):
- **Effect A** (algebraic, seconds): minimum N to keep $b_L > 0$ as L increases — scales as $e^{\Delta c_L}$ where $\Delta c_L \approx 0.45$ across window → N grows by ~1.6×
- **Effect B** (numerical, unknown): Arb interval inflation rate for high-order Legendre integrals — needs measurement, potentially worse than Effect A

**Data requirement**: at least 3 fully-certified points (binary search provides intermediate points). First-prime window data cannot constrain $L \to \infty$ asymptotics.

**Timescale**: 1–2 days once smoke test confirms script correctness.

---

### Route 1 / Phase 1: Effect B Measurement

Run the full Schur certification at 2–3 additional L values ($L = 0.42, 0.46$) and record the actual Arb interval widths. Plot inflation rate vs L. Decision point: if polynomial → Route 3 can wait; if exponential → Route 3 needs to start sooner.

---

### Route 2 / Phase 2: Second Prime Window — NEW REPO `weil-second-prime`

**Window**: $L \in (\frac{1}{2}\log 3,\ \log 2) \approx (0.549, 0.693)$

**Why new repo**: Different schema, different prime coupling ($J_{ij}(\tau_2, \tau_3)$ for both $n=2$ and $n=3$), different proofctl domain, different $c_L$ (≈1.82 at window right edge).

**Optimistic range**: Theorem 3.1's three-interval decomposition holds for $n=2,3$ throughout this window (single-hop regime for both). The $\mathbb{Q}[\tau]$ algebraisation extends, but needs new code for the cross-prime coupling terms.

**Hard boundary**: At $L = \log 2$, prime $n=2$ exits the single-hop regime and $n=4$ enters. The Theorem 3.1 framework needs genuine extension there. **Do not extrapolate beyond this window.**

**Timescale**: 1–2 months after Route 0 is confirmed working.

---

### Route 3 / Phase 2.5: Uniform-in-L Spectral Gap — Scoping (THIS REPO, Task #15)

**Scoping results** (2026-08-06, from full reading of Suzuki + Groskin):

**Suzuki arXiv:2606.09096**:
- Purely theoretical, no numerical content (confirmed)
- Theorem 4: $\lambda_a = \log(1/a) + \mu_1 - \log(2\pi) + \psi(2) - 1 + O(a)$ as $a \to 0^+$
- **$\mu_1 > 0$** is the unknown positive constant — exactly what our Schur certification computes numerically
- No finite-$a$ lower bound anywhere in the paper
- Section 7 (de Branges connection) assumes RH throughout — circular for our purposes
- **Conclusion**: Suzuki provides no shortcut for the finite-$L$ regime

**Groskin arXiv:2607.02828**:
- Works in frequency space (integer nodes $I_N$), not Legendre position space
- Dictionary theorem: exact finite Guinand–Weil formula (useful for verification)
- Tail-order theorem: archimedean tail increment $\Delta_{T_1,T_2}$ is positive definite with budget $B_T \sim (2N+1)\rho \log(T) / (\pi^2 T)$
- **Potential connection**: Groskin's $B_T$ budget could give a uniform error bound if translated to our Legendre/Schur framework — but the two discretizations are different and the translation is non-trivial
- **Conclusion**: Complementary framework, not a ready uniform-in-L bound

**Path to uniform-in-L** (if pursued):
Either (A) translate Groskin's $B_T$ to Legendre/Schur framework, or (B) prove a Poincaré-type inequality for the $\mathcal{L}(w)/\|w\|^2$ operator in Suzuki's framework giving $\inf \mathcal{L}(w)/\|w\|^2 > C$ uniformly. Both require 3–6 months of new theory.

#### Prolate / PSWF basis change — go/no-go gate (2026-08-06)

Computed the time-frequency product $c = L\Omega$ that governs the PSWF eigenvalue
cliff (significant dimension $\approx 2c/\pi$). The kernel $r''(a(x-y))$ is analytic
in the strip $|\mathrm{Im}| < \pi/a$ (nearest pole at $t = \pi i$; see
`integrator_a.py:634,851` and the Bernstein-ellipse $\rho = \exp(\mathrm{arcsinh}(\pi/(ah)))$
in `bernstein.py:18`). This gives Fourier decay $\sim e^{-(\pi/a)|\xi|}$, hence
half-bandwidth $\Omega_u \sim \frac{a}{\pi}\log(1/\epsilon)$, $c = 2\Omega_u$:

| target $\epsilon$ | $2c/\pi$ ($a=L$) | $2c/\pi$ ($a=2L$, conservative) |
|---|---|---|
| $10^{-8}$ | ~3 | ~6 |
| $10^{-16}$ | ~6 | ~13 |
| $10^{-30}$ | ~12 | ~24 |

Legendre needs $N \approx 32$–$40$ at $L=0.42$.

**Verdict**: prolate wins, but the realistic dividend is **~2.5–3×** (N≈32 → ~12)
at the FP-0.35 precision $\epsilon \sim 2^{-30}$, **NOT the ~8× "N=4" myth**. The
cliff scales linearly in $\log(1/\epsilon)$ and in $a \propto L$, so:
- higher certification precision erodes the advantage (linear in $\log(1/\epsilon)$);
- the dividend shrinks toward the second window ($c \propto L$, cliff rises ~40%
  by $L\approx0.6$) — **do not extrapolate the first-window ratio**.

**Recommended order IF N=32 comes back negative**:
1. **P3 — prolate/band-limited quadrature for the S_KK kernel, NO basis change.**
   Zero paradigm cost. Reuses the SAME $\pi/a$ analytic bandwidth already present
   in `bernstein.py` — turns it from an error bound into quadrature-node design.
   Directly attacks the measured 40s/pair S_KK wall. Try first.
2. **P1 — hybrid basis: prolate-ise only the $K_L$ block**, keep Legendre for
   $T, V, \mathcal{P}_L$ via a certified change-of-basis matrix $U$. Reduces to
   ~12 dims; preserves V closed-form and prime $\mathbb{Q}[\tau]$; one certified
   basis-change error layer.
3. **P2 — full prolate basis.** Last resort: $2c/\pi \sim 12$ makes full re-basing
   low-yield while destroying the $\mathbb{Q}[\tau]$ algebra and Lean chain.

**Repo policy**: P3 stays in this repo (quadrature swap, no structural change).
P1/P2 (actual basis change → breaks $\mathbb{Q}[\tau]$ + Lean) warrant a NEW repo.

**Honesty boundary**: every prolate variant is a *per-$L_k$ dimensionality
accelerator only*. It does not change the monotone decay of $\lambda(L)$ and does
not reach $L \to \infty$.

**Decision**: Defer to after Route 1 Effect B measurement. If Effect B is polynomial, uniform-in-L is worth pursuing; if exponential, computational approach to second window takes priority.

---

### Route 3-scoping addendum (2026-08-06): the $A + C - P$ operator reformulation

A first-principles re-derivation of the Weil quadratic form as an operator
inequality was carried out (independent of this repo's Theorem numbering). It
expresses $Q_W^L(f) = \langle f, (\mathcal{A}_L + \mathcal{C}_L - \mathcal{P}_L) f\rangle$
and reduces the RH-equivalent statement to a single-sided operator-norm bound

$$\lambda_{\max}\big(\mathcal{A}_L^{-1/2} \mathcal{P}_L \mathcal{A}_L^{-1/2}\big) \le 1 \quad \forall L.$$

**Status: this is a *reformulation / discovery tool*, NOT a new computational
engine and NOT a route to RH.** Two honesty nails, both established below.

#### Equivalence dictionary — new framework ↔ existing code

| New-framework object | Existing repo object | Verification status |
|---|---|---|
| Prime matrix main integral $I_{ij}(\tau) = \int_{\tau-1}^{1} P_i(s)P_j(s-\tau)\,ds$ | `compute_J(j, i, tau)` in `src/prime_layer/legendre_shift.py:122` | **VERIFIED numerically**: $2\,I_{ij}(\tau) = J_{ji}(\tau)$ at 6 test points incl. $\tau=2$ boundary. They are the same object. |
| Archimedean multiplier $W_\infty(t) = \operatorname{Re}\psi(\tfrac14 + \tfrac{it}{2}) - \log\pi$ (single merged block) | `V_matrix_entry` (log potential) **+** `integrate_M_K` (Bessel kernel), two *separate* blocks | **DIFFERS in decomposition** — must be reconciled by one integral check before any use. Not yet done. |
| Pole block $\mathcal{C}_L$ (rank-2, $i_j(L/2)$ modified Bessel) | No explicit counterpart found in current code | **GAP** — either absorbed elsewhere or not separately handled. Must locate before trusting cross-framework numbers. |
| Computable criterion $\lambda_{\min}(A - P) \ge 0$ | Schur criterion $b_L F - R_\eta \succ 0$ in `scan_lambda_profile.py` | Same *class* of statement (finite-dim generalized eigenvalue); exact algebraic identity NOT yet checked. |

**Consequence of row 1**: the new framework's "$\mathbb{Q}[\tau]$ prime engine"
already exists as `compute_J`. Writing a fresh SymPy $I_{ij}(\tau)$ engine would
duplicate Theorem-4 logic already formalised in Lean — forbidden by the
no-duplicate-logic rule. The reformulation adds an *independent cross-check* of
Theorem 4, not new capability.

#### Honesty nail 1 — no additive prime budget can be RH-equivalent

Expanding $K_L = \sum_{p^k < e^{2L}} \frac{2\log p}{p^{k/2}} M_{p^k}(L)$ and applying
the triangle inequality gives a bound growing like $\sum_p \frac{\log p}{\sqrt p}$,
which diverges. Therefore any honest RH-equivalent inequality **must retain the
cross terms** $\langle M_p, M_q\rangle$; positivity depends entirely on phase
cancellation between primes. This *refutes the "reserve pays per prime jump"
accounting model at the structural level* — not for lack of engineering.

#### Honesty nail 2 — the tail term IS the logical gap, in one writable quantity

The only honest budget inequality is the segmented form (Weyl, keeping head
cancellation, conceding only the tail):

$$\lambda_{\max}\big(K_L^{\le X}\big) \le 1 - \tau(X,L), \qquad \tau(X,L) := \big\|K_L^{(X, e^{2L}]}\big\|.$$

For any **fixed** $X, L$ this is a true, publishable theorem. But making
$X, L \to \infty$ while keeping $\tau \to 0$ is *equivalent to RH itself*. The
tail's summability is the logical chasm, compressed into a single writable
quantity $\tau(X,L)$.

#### What this means for the programme

- The reformulation produces the SAME per-$L_k$ finite-scale positivity results
  as the current Legendre/Schur pipeline — it is **not** a ramp toward
  $L \to \infty$. It cannot be, by nail 2.
- Its genuine value is as (a) an independent verification of Theorem 4
  (row 1, done), and (b) a candidate *language* for the uniform-in-L statement
  and for a possible **obstruction theorem**: "any sign-preserving tail estimate
  necessarily overshoots." That obstruction, if proved, is itself publishable as
  a negative result (same venue class as E1).
- The frequency-side identity (prime block $\leftrightarrow -\zeta'/\zeta(\tfrac12+it)$,
  dominated by $W_\infty(t) \sim \log|t|$) is the natural signpost for a
  prolate/PSWF basis change IF (and only if) N=32 shows Legendre is structurally
  insufficient. It is a signpost, not an engine.

**Action gating**: do NOT write a SymPy $I_{ij}$ engine (duplicates `compute_J`).
Do NOT switch the certification backend to $A+C-P$ (reintroduces the
non-truncatable frequency-side problem). Before ANY cross-framework numerics,
close the two dictionary gaps (rows 2–3) — now resolved structurally below.

#### Dictionary gap resolution (2026-08-06, structural)

**Row 2 — $W_\infty$ vs $V + K_L$**: NOT a contradiction. $W_\infty(t) =
\operatorname{Re}\psi(\tfrac14 + \tfrac{it}{2}) - \log\pi$ has high-frequency
asymptotic $\sim \tfrac12\log|t|$. Inverse-transformed to position space this
$\log$ growth splits into (i) the endpoint log-singularity
$-\tfrac12\log(1-x^2)$ = the `V` block (`log_moments.V_matrix_entry`, computed by
exact Beta/digamma closed forms, ZERO quadrature error), plus (ii) a smooth
remainder = the `K_L` block (`integrate_M_K`). So the new framework's single
frequency block equals the existing framework's TWO position blocks:
$W_\infty \leftrightarrow V + K_L$. The existing decomposition is *finer and more
Arb-friendly* (V is closed-form; only K_L needs integration). A full numerical
confirmation would require running the $W_\infty$ oscillatory frequency integral
— exactly the expensive object the position-space framework was built to avoid —
so it is deferred until/unless a framework switch is actually chosen. Structurally
sound; not a blocker.

**Row 3 — pole block $\mathcal{C}_L$ FOUND**: the new framework's rank-2 pole
term $\mathcal{C}_L = 2(\int f\cosh\tfrac{x}{2})^2 - 2(\int f\sinh\tfrac{x}{2})^2$
is present in the existing framework, but **collapsed into the scalar Weil
constant** $c_L = \log(2\pi L) + \gamma$ (`scan_lambda_profile.c_L_at`, line 44).
The existing pipeline applies the pole contribution as an isotropic diagonal
shift $-c_L G$; the new framework keeps it as a rank-2 form acting only on the
$\cosh/\sinh$ directions.

**Actionable consequence of row 3**: the scalar $c_L$ shift penalises *every*
eigen-direction equally, whereas the true pole contribution is rank-2. This is
consistent with the E1 diagnostic ("Path A's negative direction is driven by the
$c_L \approx 1.365$ global negative shift"). It was hypothesised that replacing
$-c_L G$ with the explicit rank-2 $\mathcal{C}_L$ could recover margin for free.

**QUANTIFIED AND REJECTED (2026-08-06)**. Computed $c_j = \langle e_j, \cosh\tfrac{x}{2}\rangle$
on the L=0.42 even-sector N=8 subspace:

```
c_j = [0.9233, 0.006, 0, 0, 0, 0, 0, 0]   (indices 0,2,...,14)
```

$\cosh\tfrac{x}{2}$ is nearly constant on $[-0.42, 0.42]$ (varies < 2%), so it
projects almost entirely onto $P_0$. Consequences:
- The rank-2 pole (rank-1 in the even sector) acts **only on the $P_0$ direction**
  (eigenvector $\propto c/\|c\| = [1.0, 0.007, 0, \ldots]$).
- On high-order directions $P_2 \ldots P_{14}$ — exactly where min_eig's negative
  eigenvector lives — the rank-2 form contributes $\approx 0$, essentially
  identical to the scalar approximation. **No margin is recoverable there.**
- The only place they differ ($P_0$) is already the *most positive* direction
  ($F_{00} = +0.397$). Adding margin to the most-positive direction does nothing
  for min_eig (governed by the most-negative high-order direction).

This is the same geometric error as the $\kappa_L^2 I$ patch: the correction lands
on the wrong eigen-direction. **Net effect on min_eig ≈ 0, nowhere near the 0.024
deficit. Do NOT implement `acp_gate.py`. Do NOT retry this.**

**Score after full scoping**: of the five "elegant" reformulation identities
(operator-norm $\star$; frequency-side $-\zeta'/\zeta$; $\mathbb{Q}[\tau]$ algebra;
segmented $\tau(X,L)$; rank-2 pole), **zero advance the L=0.42 certification**.
$\star$ and the frequency side ARE RH (no computable content); $\mathbb{Q}[\tau]$
algebra already exists as `compute_J`; $\tau(X,L)$ is publishable only as a
*negative* obstruction result; rank-2 pole is geometrically inert here. The
framework is an elegant re-description plus one publishable obstruction theorem —
it hides no shortcut around the compute wall.

#### Repository policy: A+C-P stays in THIS repo

The $A+C-P$ reformulation is **the same first-window quadratic form in a different
notation**, not a new problem. Its prime engine IS `compute_J`; its pole block IS
$c_L$. It must NOT get its own repository:
- a second `compute_J`/`legendre_shift` violates the no-duplicate-logic rule and
  creates two rival "authorities" for the same algebra;
- separate certs could not be reconciled against the existing FP-0.35 chain;
- the `fp035` proofctl domain would fracture.

If pursued FOR CROSS-CHECK ONLY (not for margin — see rank-2 rejection above), it
would belong as an alternate assembler (e.g. `src/assemble/acp_gate.py`) that
REUSES `compute_J`, `log_moments`, and the existing Arb certification stack,
replacing only the matrix-assembly layer, yielding an independent cross-check of
Theorem 4. Low priority: the cross-check value is real but does not help any open
certification.

A genuinely new repo is warranted ONLY for a **basis change** (Legendre →
prolate/PSWF), because that breaks the $\mathbb{Q}[\tau]$ algebra and the Lean
chain — a paradigm-level split. $A+C-P$ is still Legendre, so it stays here.
(Contrast: `weil-second-prime` IS a new repo, because the second *prime window*
is a new problem — different coupling $J(\tau_2,\tau_3)$, schema, and domain.)

---

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
