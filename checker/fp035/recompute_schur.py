"""Independent recomputation of the FP-0.35 split-residual Schur criterion.

Does NOT trust any pre-existing certificate. Rebuilds C = b_L*F - R_eta from the
certified Arb primitives and reports the min LDL^T pivot per parity sector.

Two correctness points (each a real bug in the retired certificate):
  * S0 is the FULL second moment S0 = S_VV + S_VK + S_KV + S_KK (four terms).
    The retired reproduce_fp035.py used S0 = S_KK only -> R0 too small -> false PASS.
  * The positivity judge is the min LDL^T PIVOT, not the symmetrized min eig.
"""
from __future__ import annotations

import math
from fractions import Fraction

import numpy as np

from src.archimedean.integrator_a import integrate_M_K, integrate_S_KK, integrate_S_VK
from src.archimedean.log_moments import V_matrix_entry, V2_matrix_entry
from src.prime_layer.legendre_shift import compute_J, compute_E

C2_FLOAT = math.log(2) / math.sqrt(2)
KAPPA_FLOAT = 1.25528305
L0 = 2.0 ** -30
ETA = 0.5


def _H(n: int) -> float:
    return sum(1.0 / k for k in range(1, n + 1)) if n > 0 else 0.0


def _c_L(L: float) -> float:
    return math.log(2 * math.pi * L) + 0.5772156649015329


def _mid_iv(iv) -> float:
    return 0.5 * (float(iv[0]) + float(iv[1]))


def _mid_r(r) -> float:
    return 0.5 * (float(r.enclosure_lower) + float(r.enclosure_upper))


def _min_pivot(C: np.ndarray) -> float:
    A = 0.5 * (C + C.T)
    n = A.shape[0]
    L = np.eye(n)
    d = np.zeros(n)
    for j in range(n):
        s = A[j, j] - sum(L[j, k] * L[j, k] * d[k] for k in range(j))
        d[j] = s
        if abs(s) < 1e-300:
            return float(s)
        for i in range(j + 1, n):
            L[i, j] = (A[i, j] - sum(L[i, k] * L[j, k] * d[k] for k in range(j))) / s
    return float(np.min(d))


def verify_sector(L_num: int, L_den: int, sector: str, N: int, d: int, eta: float = ETA):
    L = L_num / L_den
    parity = 0 if sector == "even" else 1
    indices = list(range(parity, parity + 2 * N, 2))
    n = len(indices)
    tau = Fraction(math.log(2) / L).limit_denominator(10000)

    Gd = [2.0 / (2 * ni + 1) for ni in indices]
    T = np.diag([_H(ni) * Gd[a] for a, ni in enumerate(indices)])

    M0 = np.zeros((n, n))
    M2 = np.zeros((n, n))
    S0 = np.zeros((n, n))
    S2 = np.zeros((n, n))

    for a, i in enumerate(indices):
        for b, j in enumerate(indices):
            V_ij = _mid_iv(V_matrix_entry(i, j, 256))
            K_ij = _mid_r(integrate_M_K(i, j, L_num, L_den, depth=4, use_bernstein=False))
            svv = _mid_iv(V2_matrix_entry(i, j, 256))
            svk = _mid_r(integrate_S_VK(i, j, L_num, L_den, depth=4))
            skv = _mid_r(integrate_S_VK(j, i, L_num, L_den, depth=4))
            skk = _mid_r(integrate_S_KK(i, j, L_num, L_den, depth=3))
            S0[a, b] = svv + svk + skv + skk
            M0[a, b] = V_ij + K_ij
            M2[a, b] = -C2_FLOAT * float(compute_J(i, j, tau))
            # S2 = ||P_2 p||^2 second moment = c2^2 * E (prime self second moment).
            # BUG FIX 2026-08-07: previously S2 stayed zeros -> R2 too small ->
            # false-positive pivot (same defect class as the retired certificate).
            S2[a, b] = (C2_FLOAT ** 2) * float(compute_E(i, j, tau))

    Ginv = np.diag([1.0 / g for g in Gd])
    R0 = S0 - M0.T @ Ginv @ M0
    R2 = S2 - M2.T @ Ginv @ M2
    R_eta = (1 + eta) * R0 + (1 + 1.0 / eta) * R2

    c_L = _c_L(L)
    b_L = _H(d) - c_L - L0 - KAPPA_FLOAT
    F = T + M0 + M2 - c_L * np.diag(Gd)
    C = b_L * F - R_eta
    piv = _min_pivot(C)
    info = {
        "L": L, "sector": sector, "N": N, "d": d, "eta": eta,
        "b_L": b_L, "c_L": c_L, "min_pivot": piv,
        "S0_definition": "S_VV+S_VK+S_KV+S_KK", "judge": "min LDL^T pivot",
    }
    return piv, b_L, info
