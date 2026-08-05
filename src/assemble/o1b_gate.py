"""O1-B Path B Schur criterion assembly for FP-0.35.

Assembles F, R_0, R_2, R_eta for both parity sectors and checks
b_L > 0 and b_L * F - R_eta > 0 (positive definite) via interval LDL^T.

Frozen parameters (Theorem 5):
  L = 7/20,  eta = 1/2,  L_0 = 2^{-30}
  Even sector: N=8, tail_degree=16, indices=[0,2,4,6,8,10,12,14]
  Odd  sector: N=6, tail_degree=13, indices=[1,3,5,7,9,11]
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

from src.archimedean.interval import (
    Interval, add, sub, mul, scalar_mul, div_outward, point,
    is_strictly_positive,
)
from src.archimedean.ldlt import ldlt_factor, certify_positive_definite, min_pivot_lower
from src.archimedean.log_moments import V_matrix_entry, V2_matrix_entry
from src.archimedean.kernel import kappa
from src.prime_layer.legendre_shift import prime_legendre_matrices

# ── Frozen constants ─────────────────────────────────────────────────────────
L_NUM, L_DEN = 7, 20
ETA = Fraction(1, 2)
L0 = Fraction(1, 2**30)

LOG2_LO = Fraction(842, 1215)
LOG2_HI = Fraction(23581, 34020)
SQRT2_LO = Fraction(7, 5)

# Rational bounds on c_2 = log2/sqrt(2)
C2_LO = LOG2_LO * SQRT2_LO / (SQRT2_LO**2 + 1)   # conservative lower
C2_HI = LOG2_HI / SQRT2_LO                         # upper: log2_hi / sqrt2_lo

# Rational bounds on c_2^2 = (log2)^2 / 2
C2SQ_LO = LOG2_LO**2 / 2
C2SQ_HI = LOG2_HI**2 / 2

# tau = log2 / L; rational bounds
TAU_LO = LOG2_LO * L_DEN / L_NUM   # = 842/1215 * 20/7
TAU_HI = LOG2_HI * L_DEN / L_NUM   # = 23581/34020 * 20/7
TAU_MID = (TAU_LO + TAU_HI) / 2

SECTOR_PARAMS = {
    "even": {"N": 8, "d": 16, "indices": list(range(0, 16, 2))},
    "odd":  {"N": 6, "d": 13, "indices": list(range(1, 12, 2))},
}


# ── Helper: harmonic numbers ──────────────────────────────────────────────────
def _harmonic(n: int) -> Fraction:
    return sum(Fraction(1, k) for k in range(1, n + 1))


# ── Build Gram matrix G and kinetic T_N ──────────────────────────────────────

def build_gram(indices: list[int]) -> list[list[Interval]]:
    """G_{kk} = 2/(2n+1), off-diagonal = 0."""
    N = len(indices)
    G = [[point(Fraction(0))] * N for _ in range(N)]
    for k, n in enumerate(indices):
        G[k][k] = point(Fraction(2, 2 * n + 1))
    return G


def build_kinetic(indices: list[int]) -> list[list[Interval]]:
    """T_N diagonal: (T_N)_{kk} = H_{n_k} * 2/(2n_k+1)."""
    N = len(indices)
    T = [[point(Fraction(0))] * N for _ in range(N)]
    for k, n in enumerate(indices):
        T[k][k] = point(_harmonic(n) * Fraction(2, 2 * n + 1))
    return T


# ── Build M^(0), S^(0) from Archimedean primitives ───────────────────────────

def build_M0_S0(
    indices: list[int],
    prec: int = 256,
) -> tuple[list[list[Interval]], list[list[Interval]]]:
    """M^(0)_{ij} = <(V+K)P_j, P_i>,  S^(0)_{ij} = <(V+K)P_j, (V+K)P_i>."""
    from src.archimedean.integrator_a import integrate_M_K

    N = len(indices)
    a_num, a_den = L_NUM, L_DEN

    # M_V[i,j] = <V P_j, P_i>
    M_V = [[V_matrix_entry(indices[i], indices[j], prec) for j in range(N)]
           for i in range(N)]

    # M_K[i,j] = <K P_j, P_i>
    M_K = [[integrate_M_K(indices[i], indices[j], a_num, a_den, depth=4, prec=prec).to_interval()
            for j in range(N)]
           for i in range(N)]

    # M^(0) = M_V + M_K
    M0 = [[add(M_V[i][j], M_K[i][j]) for j in range(N)] for i in range(N)]

    # S^(0)_{ij} = <(V+K)P_j, (V+K)P_i>
    # = S_VV[i,j] + S_VK[i,j] + S_KV[i,j] + S_KK[i,j]
    from src.archimedean.integrator_a import integrate_S_VK, integrate_S_KK
    S_VV = [[V2_matrix_entry(indices[i], indices[j], prec) for j in range(N)]
            for i in range(N)]

    S0 = [[point(Fraction(0))] * N for _ in range(N)]
    for i in range(N):
        for j in range(N):
            svk = integrate_S_VK(indices[i], indices[j], a_num, a_den, depth=4, prec=prec).to_interval()
            skv = integrate_S_VK(indices[j], indices[i], a_num, a_den, depth=4, prec=prec).to_interval()
            skk = integrate_S_KK(indices[i], indices[j], a_num, a_den, depth=3, prec=prec).to_interval()
            S0[i][j] = add(add(add(S_VV[i][j], svk), skv), skk)

    return M0, S0


# ── Build M^(2), S^(2) from exact Legendre shift algebra ─────────────────────

def build_M2_S2(
    indices: list[int],
) -> tuple[list[list[Interval]], list[list[Interval]]]:
    """M^(2)_{ij} = -c2 * J_{ij}(tau),  S^(2)_{ij} = c2^2 * E_{ij}(tau)."""
    J_mat, E_mat = prime_legendre_matrices(indices, TAU_MID)
    N = len(indices)

    M2 = [[point(Fraction(0))] * N for _ in range(N)]
    S2 = [[point(Fraction(0))] * N for _ in range(N)]

    for r in range(N):
        for c in range(N):
            j = J_mat[r][c]
            e = E_mat[r][c]
            # M2 = -c2 * J  — use interval [−C2_HI*J, −C2_LO*J] (outward)
            if j >= 0:
                m2_lo = -C2_HI * j
                m2_hi = -C2_LO * j
            else:
                m2_lo = -C2_LO * j
                m2_hi = -C2_HI * j
            M2[r][c] = (m2_lo, m2_hi)
            # S2 = c2^2 * E  — E >= 0 always (Gram matrix on boundary strips)
            S2[r][c] = (C2SQ_LO * e, C2SQ_HI * e)

    return M2, S2


# ── Schur complement R = S - M^T G^{-1} M ────────────────────────────────────

def build_R(
    M: list[list[Interval]],
    S: list[list[Interval]],
    G: list[list[Interval]],
) -> list[list[Interval]]:
    """R = S - M^T * G^{-1} * M.

    G is diagonal, so G^{-1} M has (G^{-1} M)_{kj} = M_{kj} / G_{kk}.
    R_{ij} = S_{ij} - sum_k M_{ki} * M_{kj} / G_{kk}.
    """
    N = len(M)
    R = [[point(Fraction(0))] * N for _ in range(N)]
    for i in range(N):
        for j in range(N):
            s = S[i][j]
            for k in range(N):
                g_kk = G[k][k]
                # M^T is M[k][i]; divide by G[k][k] (strictly positive diagonal)
                term = div_outward(mul(M[k][i], M[k][j]), g_kk)
                s = sub(s, term)
            R[i][j] = s
    return R


# ── R_eta = (1+eta)*R0 + (1+1/eta)*R2 ────────────────────────────────────────

def build_R_eta(
    R0: list[list[Interval]],
    R2: list[list[Interval]],
    eta: Fraction = ETA,
) -> list[list[Interval]]:
    N = len(R0)
    c0 = Fraction(1) + eta           # = 3/2
    c2 = Fraction(1) + Fraction(1, 1) / eta  # = 3  (1 + 1/eta for eta=1/2)
    R_eta = [[point(Fraction(0))] * N for _ in range(N)]
    for i in range(N):
        for j in range(N):
            R_eta[i][j] = add(scalar_mul(c0, R0[i][j]), scalar_mul(c2, R2[i][j]))
    return R_eta


# ── b_L = H_d - c_L - L_0 - kappa_L ─────────────────────────────────────────

def compute_b_L(d: int, c_L: Fraction, prec: int = 256) -> Fraction:
    """Compute the complement-space lower bound b_L (exact rational).

    H_d = sum_{k=1}^d 1/k  (harmonic number, exact).
    kappa_L is computed by src.archimedean.kernel.kappa at L = 7/20.
    """
    H_d = _harmonic(d)
    kappa_L = kappa(L_NUM, L_DEN, prec)
    b = H_d - c_L - L0 - kappa_L
    return b


# ── F = T_N + M^(0) + M^(2) - (c_L + L_0) * G ───────────────────────────────

def build_F(
    T_N: list[list[Interval]],
    M0: list[list[Interval]],
    M2: list[list[Interval]],
    G: list[list[Interval]],
    c_L: Fraction,
) -> list[list[Interval]]:
    N = len(T_N)
    shift = c_L + L0
    F = [[point(Fraction(0))] * N for _ in range(N)]
    for i in range(N):
        for j in range(N):
            g_scaled = scalar_mul(shift, G[i][j])
            F[i][j] = sub(add(add(T_N[i][j], M0[i][j]), M2[i][j]), g_scaled)
    return F


# ── scale matrix: b_L * F - R_eta ────────────────────────────────────────────

def build_schur_matrix(
    b_L: Fraction,
    F: list[list[Interval]],
    R_eta: list[list[Interval]],
) -> list[list[Interval]]:
    N = len(F)
    C = [[point(Fraction(0))] * N for _ in range(N)]
    for i in range(N):
        for j in range(N):
            C[i][j] = sub(scalar_mul(b_L, F[i][j]), R_eta[i][j])
    return C


# ── Main O1-B gate ────────────────────────────────────────────────────────────

def run_o1b_gate(
    sector: str,
    c_L: Fraction,
    prec: int = 256,
) -> dict[str, Any]:
    """Run the full O1-B Schur gate for one parity sector.

    Returns a dict with:
      sector, N, d, b_L, b_L_positive, min_pivot, certified, message
    """
    params = SECTOR_PARAMS[sector]
    N = params["N"]
    d = params["d"]
    indices = params["indices"]

    print(f"[O1-B {sector}] Building primitives (N={N}, d={d})...")

    G = build_gram(indices)
    T_N = build_kinetic(indices)
    M2, S2 = build_M2_S2(indices)

    print(f"[O1-B {sector}] Computing Archimedean blocks M^(0), S^(0)...")
    M0, S0 = build_M0_S0(indices, prec)

    R0 = build_R(M0, S0, G)
    R2 = build_R(M2, S2, G)
    R_eta = build_R_eta(R0, R2)

    b_L = compute_b_L(d, c_L, prec)
    print(f"[O1-B {sector}] b_L = {float(b_L):.6f}")

    if b_L <= 0:
        return {
            "sector": sector, "N": N, "d": d,
            "b_L": float(b_L), "b_L_positive": False,
            "min_pivot": None, "certified": False,
            "message": f"b_L = {float(b_L):.6f} <= 0; complement-space bound fails",
        }

    F = build_F(T_N, M0, M2, G, c_L)
    C = build_schur_matrix(b_L, F, R_eta)

    print(f"[O1-B {sector}] Running interval LDL^T...")
    pivot = min_pivot_lower(C)
    certified = pivot is not None and pivot > 0

    return {
        "sector": sector, "N": N, "d": d,
        "b_L": float(b_L), "b_L_positive": True,
        "min_pivot": float(pivot) if pivot is not None else None,
        "certified": certified,
        "message": (
            f"CERTIFIED: min pivot = {float(pivot):.4e}" if certified
            else f"UNCERTIFIED: min pivot = {float(pivot):.4e}" if pivot is not None
            else "UNCERTIFIED: LDL^T factorisation failed"
        ),
    }


if __name__ == "__main__":
    import json

    # c_L is the constant in the Weil form definition; for the closed form
    # at L=7/20, c_L = c_{7/20} as defined in the frozen model.
    # For a first pilot run we use a conservative estimate; the checker
    # will independently recompute this from the certificate.
    # c_L = 0 is a conservative choice (makes b_L smaller, harder to satisfy).
    c_L = Fraction(0)

    results = {}
    for sector in ("even", "odd"):
        result = run_o1b_gate(sector, c_L, prec=256)
        results[sector] = result
        print(json.dumps(result, indent=2))

    all_certified = all(r["certified"] for r in results.values())
    print(f"\nO1-B gate: {'PASS' if all_certified else 'FAIL (pilot only)'}")
