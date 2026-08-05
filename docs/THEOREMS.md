# Theorems — weil-first-prime

All six closed theorems with complete proofs. These are the analytic foundation
of the FP-0.35 program. FP-0.35 itself remains a conjecture.

---

## Theorem 1: Single-step overlap decomposition

**Setting.** Let b > 0 and b/2 < L < b. Define:
```
I_- = (-L, L-b),   I_0 = (L-b, -L+b),   I_+ = (-L+b, L)
```

**Claim.** H_L = L²(I_-) ⊕ L²(I_0) ⊕ L²(I_+). Under the unitary identification
T_b: L²(I_-) → L²(I_+) given by (T_b h)(x) = h(x-b):
```
C_{b,L} ≅ [[0,1],[1,0]] ⊗ I_{L²(I_-)} ⊕ 0_{L²(I_0)}
```
Hence σ(C_{b,L}) = {-1, 0, 1}, ‖C_{b,L}‖ = 1, all eigenvalues of infinite
multiplicity. C_{b,L} is infinite-rank and non-compact.

**Proof.** For h ∈ L²(I_-), T_b h ∈ L²(I_+) and:
- C_{b,L}(h + T_b h) = h + T_b h  (eigenvalue +1)
- C_{b,L}(h - T_b h) = -(h - T_b h)  (eigenvalue -1)
- For f ∈ L²(I_0): both S_{b,L}f = 0 and S*_{b,L}f = 0.

No point x,x+b,x+2b can all lie in I_L when b/2 < L < b, so the three
subspaces are genuinely disjoint. All conclusions follow. □

### Corollary 1: First prime layer exact sign structure

With b = log 2, in the first prime window (log2/2 < L < log3/2), only the
n=2 term enters the explicit formula, and:
```
σ(-(log2/√2) C_{log2,L}) = {-c_2, 0, +c_2},   c_2 = log2/√2
```
The layer is indefinite; both directions are infinite-dimensional.

### Corollary 2: No L² operator-norm small perturbation at threshold

For any L ∈ (log2/2, log2): ‖C_{log2,L}‖ = 1, regardless of how small
2L - log2 is. The norm jumps from 0 to 1 at the threshold. Continuity of
the bottom spectrum must come from Weil non-local coercivity, not prime
operator-norm continuity.

---

## Theorem 2: Endpoint potential absorption

**Setting.** Scale to (-1,1): w(t) = v(Lt), τ = log2/L, ε = 2 - τ.
For ½log2 < L < log2: τ ∈ (1,2), and C_{τ,1} couples only:
```
E_- = (-1, -1+ε),   E_+ = (1-ε, 1)
```
Let V(x) = -½ log(1-x²) and κ_edge(L) = ½ log(1/(2ε)) > 0.

**Claim.** For any w in the closed-form domain:
```
|⟨C_{τ,1}w, w⟩| ≤ ‖w‖²_{L²(E_- ∪ E_+)} ≤ κ_edge(L)⁻¹ ⟨Vw, w⟩
```
Hence if c_2 = log2/√2 < κ_edge(L):
```
V + P_{2,L} ≥ (1 - c_2/κ_edge(L)) V ≥ 0
```

**Proof.** First inequality: Corollary 1 + 2|ab| ≤ |a|² + |b|².
Second inequality: for x ∈ E_- ∪ E_+, (1-x²) ≤ 2ε, so V(x) ≥ ½ log(1/(2ε)).
Integrate; multiply by c_2. □

---

## Theorem 3: Pure-rational absorption certificate

**Claim.** At L = 7/20:   c_2 / κ_edge(7/20) < 31/100.
Hence:   V + P_{2,7/20} ≥ (69/100) V ≥ 0.

**Proof certificate.**

Step 1 — Bound log 2:
```
log 2 = 2 arctanh(1/3) = 2 Σ_{k≥0} 1/((2k+1)·3^{2k+1})

842/1215 < log 2 < 23581/34020 < 7/10
```
(partial sums + positive tail bound)

Step 2 — Bound ε:
```
ε = 2 - 20·log2/7 < 2 - (20/7)·(842/1215) = 34/1701 < 1/41
```

Step 3 — Bound κ_edge from below:
```
e < Σ_{k=0}^{6} 1/k! + (1/7!)·Σ_{j≥0} 1/8^j = 31967/11760 < 87/32

Integer comparison (exact):
  87^16 · 68^5 = 15662194229696887109605438749172023641088
              < 17215562650769453014744867057217543602176
            = 1701^5 · 32^16

Therefore: e^16 < (87/32)^16 < (1701/68)^5 < (1/(2ε))^5
```
Taking logs: κ_edge(7/20) = ½ log(1/(2ε)) > 8/5.

Step 4 — Bound c_2 from above:
```
c_2 = log2/√2 < (23581/34020) / (7/5) = 23581/47628 < 62/125
```

Step 5 — Ratio:
```
c_2 / κ_edge < (62/125) / (8/5) = 62·5 / (125·8) = 310/1000 = 31/100
```
□

### Corollary 3.1: Potential redistribution

```
P_{2,7/20} + (31/100) V ≥ 0
```
Hence in closed-form ordering:
```
q̄_{7/20} ≥ q̃_{7/20} := T + (69/100)V + K_{7/20} - c_{7/20} I
```
Proving q̃_{7/20} ≥ L_0·I with L_0 > 0 is sufficient for FP-0.35
(strictly sufficient, not equivalent — Path A uses this and was falsified
by Theorem 6, but q̄ ≥ q̃ still holds).

---

## Theorem 4: First-prime Legendre matrix algebraization

**Definitions.**
```
J_{ij}(τ) = ⟨C_{τ,1} P_j, P_i⟩
E_{ij}(τ) = ⟨C_{τ,1} P_j, C_{τ,1} P_i⟩
```

**Claim.** J_{ij} = E_{ij} = 0 when i+j is odd. When i+j is even:
```
J_{ij}(τ) = 2 ∫_{-1}^{1-τ} P_i(x) P_j(x+τ) dx  ∈ ℚ[τ]

E_{ij}(τ) = 2 ∫_{-1}^{1-τ} P_i(x) P_j(x) dx      ∈ ℚ[τ]
```
Sample values: J_{00} = 4-2τ, J_{11} = τ³/3 - 2τ + 4/3, J_{02} = -τ³+3τ²-2τ.

**Proof.** Reflection x↦-x maps the second shift integral to the first times
(-1)^{i+j}, giving the parity formula. For E_{ij}: C_{τ,1}² = 1_{E_- ∪ E_+}
(from Theorem 1), so E_{ij} is an ordinary Legendre Gram integral on two
boundary strips. Legendre recurrence generates P_n ∈ ℚ[x]; composition,
multiplication, and antiderivative in ℚ[x] yield J,E ∈ ℚ[τ]. □

---

## Theorem 5: Split-residual Schur criterion

**Setting.** Write q̄_L = T + V + K_L + 𝒫_{2,L} - c_L·I. Let Π_N be the
Legendre projection onto N basis functions in a parity sector, 𝒬_N = I - Π_N,
d = first complement degree. By Theorem 3: V + 𝒫_{2,L} ≥ 0 at L=7/20.

**Notation.**
```
G_{ij} = ⟨P_j, P_i⟩,   (T_N)_{ij} = H_{n_j} G_{ij}
M^(0)_{ij} = ⟨(V+K_L)P_j, P_i⟩,   S^(0)_{ij} = ⟨(V+K_L)P_j, (V+K_L)P_i⟩
M^(2)_{ij} = -c_2 J_{ij}(τ),        S^(2)_{ij} = c_2² E_{ij}(τ)
F = T_N + M^(0) + M^(2) - (c_L + L_0) G
R_0 = S^(0) - (M^(0))* G⁻¹ M^(0)
R_2 = S^(2) - (M^(2))* G⁻¹ M^(2)
R_η = (1+η) R_0 + (1+1/η) R_2
```

**Claim.** If b_L = H_d - c_L - L_0 - κ_L > 0 and b_L·F - R_η ≻ 0, then:
```
q̄_L[w] ≥ L_0 ‖w‖² for all w in the parity sector closed-form domain.
```

**Proof.** For p ∈ Ran(Π_N), q ∈ Ran(𝒬_N), write the cross-term as u+v where
u = 𝒬_N(V+K_L)p and v = 𝒬_N 𝒫_{2,L}p. Weighted Young:
```
‖u+v‖² ≤ (1+η)‖u‖² + (1+1/η)‖v‖²
```
Gram matrices of u and v on the finite basis are exactly R_0 and R_2.
Complete the square with b_L to obtain the block matrix condition. □

**Key engineering benefit.** No cross-integrals ⟨(V+K_L)P_i, 𝒫_{2,L}P_j⟩ needed.
Prime layer adds only M^(2), S^(2), R_2 ∈ ℚ[log2, √2]; Archimedean paths
handle M^(0), S^(0), R_0 independently.

---

## Theorem 6: Path A strict negative witnesses (path falsification)

**Claim.** With L_0 = 2^{-30}, θ = 69/100, define q̃ - L_0·I as in Corollary 3.1.
The rational vectors v_even = P_0 - P_2 and v_odd = P_1 - ½P_3 satisfy:
```
(q̃ - L_0)[v_even] ∈ [-0.053384, -0.052711]  (upper endpoint < 0)
(q̃ - L_0)[v_odd]  ∈ [-0.032327, -0.032119]  (upper endpoint < 0)
```
**Path A is strictly falsified.** (This does not falsify FP-0.35 or q̄_{7/20} ≥ 0.)

**Proof sketch.**
Auto-correlations computed exactly from Legendre recurrence:
```
C_{v_even}(t) = 12/5 - 3t² + (3/2)t³ - (3/40)t⁵
C_{v_odd}(t)  = 31/42 - t/4 - (5/2)t² + (23/12)t³ - (7/32)t⁵ + (5/448)t⁷
```
Kernel integral K_{7/20}[v] = 2∫₀² (-7/20)·r''(7t/20) C_v(t) dt.
Near-zero endpoint (t ∈ [0,10⁻⁴]): bounded by |r''| < 2 + Cauchy–Schwarz.
Remaining [10⁻⁴, 2]: 256-bit Arb complex analytic integration.
Both interval upper endpoints are strictly negative. □
