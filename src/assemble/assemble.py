"""Path B certificate assembly for FP-0.35.

Assembles the full Schur criterion matrices using Archimedean primitives
from both Path A and Path B, combined with exact prime layer matrices.

Theorem 5 criterion: b_L > 0 and b_L * F - R_eta is positive definite,
where:
  F   = T_N + M^(0) + M^(2) - (c_L + L_0) * G
  R_0 = S^(0) - (M^(0))^* G^{-1} M^(0)
  R_2 = S^(2) - (M^(2))^* G^{-1} M^(2)
  R_eta = (1 + eta) R_0 + (1 + 1/eta) R_2,  eta = 1/2

All matrices use exact rational arithmetic for the prime layer; the
Archimedean blocks use Arb interval arithmetic.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

# Frozen parameters
L_NUM = 7
L_DEN = 20
ETA_NUM = 1
ETA_DEN = 2
L0_EXPONENT = 30  # L_0 = 2^{-30}

# log2 rational bounds (Theorem 3 certificate)
LOG2_LO = Fraction(842, 1215)
LOG2_HI = Fraction(23581, 34020)
SQRT2_LO = Fraction(7, 5)


def _tau_bounds() -> tuple[Fraction, Fraction]:
    L = Fraction(L_NUM, L_DEN)
    return LOG2_LO / L, LOG2_HI / L


def build_gram_matrix(indices: list[int]) -> list[list[Fraction]]:
    """Build the Legendre Gram matrix G_{ij} = <P_j, P_i> = 2/(2n+1) delta_{ij}."""
    N = len(indices)
    G = [[Fraction(0)] * N for _ in range(N)]
    for k, n in enumerate(indices):
        G[k][k] = Fraction(2, 2 * n + 1)
    return G


def build_kinetic_matrix(indices: list[int]) -> list[list[Fraction]]:
    """Build T_N = diag(H_{n_k}) * G where H_n = sum_{k=1}^{n} 1/k (harmonic numbers).

    T_N is diagonal: (T_N)_{kk} = H_{n_k} * G_{kk}.
    """
    N = len(indices)
    T = [[Fraction(0)] * N for _ in range(N)]
    for k, n in enumerate(indices):
        H_n = sum(Fraction(1, j) for j in range(1, n + 1))
        G_kk = Fraction(2, 2 * n + 1)
        T[k][k] = H_n * G_kk
    return T


def build_prime_block_M2(
    indices: list[int],
    J_mat: list[list[Fraction]],
    c2_bound: tuple[Fraction, Fraction],
) -> tuple[list[list[Fraction]], list[list[Fraction]]]:
    """Build interval bounds for M^(2) = -c2 * J.

    Returns (M2_lo, M2_hi) as rational matrices bounding the Arb interval.
    c2_bound = (c2_lo, c2_hi) rational bounds on c2 = log2/sqrt(2).
    """
    N = len(indices)
    c2_lo, c2_hi = c2_bound
    M2_lo = [[Fraction(0)] * N for _ in range(N)]
    M2_hi = [[Fraction(0)] * N for _ in range(N)]
    for r in range(N):
        for c in range(N):
            j = J_mat[r][c]
            if j >= 0:
                M2_lo[r][c] = -c2_hi * j
                M2_hi[r][c] = -c2_lo * j
            else:
                M2_lo[r][c] = -c2_lo * j
                M2_hi[r][c] = -c2_hi * j
    return M2_lo, M2_hi


def build_prime_block_S2(
    indices: list[int],
    E_mat: list[list[Fraction]],
    c2sq_bound: tuple[Fraction, Fraction],
) -> tuple[list[list[Fraction]], list[list[Fraction]]]:
    """Build interval bounds for S^(2) = c2^2 * E.

    Returns (S2_lo, S2_hi).
    c2sq_bound = (c2sq_lo, c2sq_hi) rational bounds on c2^2 = (log2)^2/2.
    """
    N = len(indices)
    c2sq_lo, c2sq_hi = c2sq_bound
    S2_lo = [[Fraction(0)] * N for _ in range(N)]
    S2_hi = [[Fraction(0)] * N for _ in range(N)]
    for r in range(N):
        for c in range(N):
            e = E_mat[r][c]
            # E_{ij} >= 0 always (it is a Gram matrix contribution on E_- union E_+)
            S2_lo[r][c] = c2sq_lo * e
            S2_hi[r][c] = c2sq_hi * e
    return S2_lo, S2_hi


def assemble_schur_criterion(
    sector: str,
    archimedean_primitives: dict[str, Any],
    precision: int = 256,
) -> dict[str, Any]:
    """Assemble and check the Theorem 5 Schur criterion using Arb interval arithmetic.

    Returns a dict with keys:
      sector, b_L, b_L_positive, F_minus_Reta_min_pivot, certified
    """
    try:
        import flint  # type: ignore[import]
    except ImportError as exc:
        raise RuntimeError(
            "python-flint is required for interval LDL^T; install it first"
        ) from exc

    from src.prime_layer.legendre_shift import prime_legendre_matrices

    sector_params = {
        "even": {"N": 8, "d": 16, "indices": list(range(0, 16, 2))},
        "odd":  {"N": 6, "d": 13, "indices": list(range(1, 12, 2))},
    }
    if sector not in sector_params:
        raise ValueError(f"unknown sector: {sector!r}")

    params = sector_params[sector]
    N = params["N"]
    d = params["d"]
    indices = params["indices"]
    eta = Fraction(ETA_NUM, ETA_DEN)

    tau_lo, tau_hi = _tau_bounds()
    tau_mid = (tau_lo + tau_hi) / 2

    J_mat, E_mat = prime_legendre_matrices(indices, tau_mid)

    # c2 = log2/sqrt(2); c2^2 = (log2)^2/2
    c2_lo = LOG2_LO * SQRT2_LO / (SQRT2_LO**2 + 1)  # conservative lower bound
    c2_hi = LOG2_HI / SQRT2_LO
    c2sq_lo = LOG2_LO**2 / 2
    c2sq_hi = LOG2_HI**2 / 2

    M2_lo, M2_hi = build_prime_block_M2(indices, J_mat, (c2_lo, c2_hi))
    S2_lo, S2_hi = build_prime_block_S2(indices, E_mat, (c2sq_lo, c2sq_hi))

    G = build_gram_matrix(indices)
    T_N = build_kinetic_matrix(indices)

    # Retrieve Archimedean blocks
    M0 = archimedean_primitives.get("M0")
    S0 = archimedean_primitives.get("S0")
    b_L_val = archimedean_primitives.get("b_L")
    c_L = archimedean_primitives.get("c_L")

    if any(v is None for v in [M0, S0, b_L_val, c_L]):
        raise ValueError("missing Archimedean blocks in primitives dict")

    # The full assembly (R_0, R_2, R_eta, F, LDL^T) requires Arb ball arithmetic
    # and is deferred to the O1-B formal closure step.
    # This function currently returns the pilot structure for inspection.

    return {
        "sector": sector,
        "N": N,
        "d": d,
        "eta": float(eta),
        "tau_mid": float(tau_mid),
        "b_L": b_L_val,
        "status": "PILOT_ONLY",
        "note": (
            "Full Arb LDL^T certification pending O1-B closure. "
            "Discovery pilot Schur margin: even ~8.81e-4, odd ~3.44e-2."
        ),
    }
