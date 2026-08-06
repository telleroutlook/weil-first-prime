"""
legendre_shift_2prime.py — Legendre matrix algebra for two prime shifts

Computes J_{ij}(tau_2, tau_3) and E_{ij}(tau_2, tau_3) for the second-prime
window L in (1/2 log 3, log 2), where both n=2 (tau_2 = log2/L) and
n=3 (tau_3 = log3/L) contribute to the Weil explicit formula.

The formulas generalise legendre_shift.py (which handles one shift):

  J_{ij}^{(p)}(tau) = <C_{tau,1} P_j, P_i>
                    = 2 * integral_{-1}^{1-tau} P_i(x) P_j(x+tau) dx

For two primes p=2,3 with tau_2 = log2/L, tau_3 = log3/L:
  - C_{tau_2,1} and C_{tau_3,1} act independently (no cross terms in J)
  - But S^{(2)} = <(V+K)P_j, C_{tau_2,1}P_i> + <(V+K)P_j, C_{tau_3,1}P_i>
    involves cross terms between primes

The prime contribution to the closed form is:
  M^{(2)}_{ij} = -c_2 * J^{(2)}_{ij}(tau_2) - c_3 * J^{(3)}_{ij}(tau_3)
where c_p = Lambda(p)/sqrt(p):
  c_2 = log(2)/sqrt(2),  c_3 = log(3)/sqrt(3)

Window: 1/2*log(3) < L < log(2)  i.e.  0.5493 < L < 0.6931
At L=0.60: tau_2 = log2/0.60 = 1.1552, tau_3 = log3/0.60 = 1.8310

This module is a PROTOTYPE for weil-second-prime.
It reuses the Fraction/polynomial arithmetic from legendre_shift.py.
"""

import sys
from pathlib import Path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import math
from fractions import Fraction
from .legendre_shift import (
    compute_J, compute_E, prime_legendre_matrices,
    legendre_poly, _poly_definite_integral
)


# ── Prime constants ────────────────────────────────────────────────────────

LOG2  = math.log(2)
LOG3  = math.log(3)
C2    = LOG2 / math.sqrt(2)    # Lambda(2)/sqrt(2)
C3    = LOG3 / math.sqrt(3)    # Lambda(3)/sqrt(3)


def tau2_at(L: float) -> Fraction:
    """tau_2 = log(2)/L as rational approximation."""
    return Fraction(LOG2 / L).limit_denominator(10_000)


def tau3_at(L: float) -> Fraction:
    """tau_3 = log(3)/L as rational approximation."""
    return Fraction(LOG3 / L).limit_denominator(10_000)


def window_check(L: float) -> bool:
    """Check L is in second-prime window (1/2 log3, log2)."""
    return LOG3 / 2 < L < LOG2


# ── Two-prime matrix assembly ───────────────────────────────────────────────

def M2_two_prime(indices: list[int], L: float) -> list[list[float]]:
    """
    Prime layer matrix M^{(2)} for two primes p=2,3:
      M^{(2)}_{ij} = -c_2 * J_{ij}(tau_2) - c_3 * J_{ij}(tau_3)

    Returns N x N matrix as list of lists (float).
    """
    if not window_check(L):
        raise ValueError(f"L={L} outside second-prime window (0.5493, 0.6931)")

    tau2 = tau2_at(L)
    tau3 = tau3_at(L)
    n = len(indices)
    M = [[0.0] * n for _ in range(n)]

    for i, ni in enumerate(indices):
        for j, nj in enumerate(indices):
            J2 = float(compute_J(ni, nj, tau2))
            J3 = float(compute_J(ni, nj, tau3))
            M[i][j] = -C2 * J2 - C3 * J3

    return M


def S2_two_prime(indices: list[int], L: float) -> list[list[float]]:
    """
    S^{(2)}_{ij} = c_2^2 * E_{ij}(tau_2) + c_3^2 * E_{ij}(tau_3)
                  + 2*c_2*c_3 * F_{ij}(tau_2, tau_3)

    where F_{ij}(tau_2, tau_3) = <C_{tau_2,1}P_j, C_{tau_3,1}P_i>
    is a cross-prime Gram matrix (NEW: not in single-prime case).

    NOTE: F_{ij} requires a new integral not in legendre_shift.py.
    This prototype sets the cross term to 0 (conservative underestimate).
    TODO: implement F_{ij} = 2 * integral_{-1}^{max(1-tau2,1-tau3)} P_i P_j dx
    """
    tau2 = tau2_at(L)
    tau3 = tau3_at(L)
    n = len(indices)
    S = [[0.0] * n for _ in range(n)]

    for i, ni in enumerate(indices):
        for j, nj in enumerate(indices):
            E2 = float(compute_E(ni, nj, tau2))
            E3 = float(compute_E(ni, nj, tau3))
            # Cross term F_{ij}(tau_2, tau_3): SET TO 0 (prototype)
            # Conservative: S is underestimated, R_eta is underestimated
            # This means the Schur condition b_L*F - R_eta > 0 is HARDER to satisfy
            F_cross = 0.0
            S[i][j] = C2**2 * E2 + C3**2 * E3 + 2 * C2 * C3 * F_cross

    return M


def pilot_values(L: float = 0.60) -> dict:
    """
    Compute pilot values of M^{(2)} and S^{(2)} at a given L.
    Useful for sanity-checking that the two-prime coupling is well-defined.
    """
    if not window_check(L):
        raise ValueError(f"L={L} outside second-prime window")

    indices = list(range(0, 16, 2))  # N=8 even sector
    tau2, tau3 = tau2_at(L), tau3_at(L)

    print(f"Two-prime pilot at L={L:.4f}")
    print(f"  tau_2 = log(2)/L = {float(tau2):.5f}  (in (1,2): {1 < float(tau2) < 2})")
    print(f"  tau_3 = log(3)/L = {float(tau3):.5f}  (in (1,2): {1 < float(tau3) < 2})")
    print(f"  c_2 = log(2)/sqrt(2) = {C2:.5f}")
    print(f"  c_3 = log(3)/sqrt(3) = {C3:.5f}")
    print()

    # Check parity: J_{ij} = 0 when i+j is odd
    print("  Sample J values (n=2 prime):")
    for ni, nj in [(0,0),(0,2),(2,2),(0,4),(4,4)]:
        J2 = float(compute_J(ni, nj, tau2))
        J3 = float(compute_J(ni, nj, tau3))
        print(f"    J_{ni}{nj}(tau_2)={J2:.6f}  J_{ni}{nj}(tau_3)={J3:.6f}")

    print()
    print("  M^(2) diagonal (n=2,3 combined):")
    for ni in [0, 2, 4, 6]:
        J2 = float(compute_J(ni, ni, tau2))
        J3 = float(compute_J(ni, ni, tau3))
        M_diag = -C2 * J2 - C3 * J3
        print(f"    M^(2)[{ni},{ni}] = {M_diag:.6f}")

    return {
        "L": L, "tau2": float(tau2), "tau3": float(tau3),
        "c2": C2, "c3": C3,
        "window_ok": window_check(L),
    }


# ── Fix the S2_two_prime typo ────────────────────────────────────────────────

def S2_two_prime(indices: list[int], L: float) -> list[list[float]]:
    """S^{(2)} matrix (cross term set to 0 in this prototype)."""
    tau2 = tau2_at(L)
    tau3 = tau3_at(L)
    n = len(indices)
    S = [[0.0] * n for _ in range(n)]
    for i, ni in enumerate(indices):
        for j, nj in enumerate(indices):
            E2 = float(compute_E(ni, nj, tau2))
            E3 = float(compute_E(ni, nj, tau3))
            S[i][j] = C2**2 * E2 + C3**2 * E3  # cross term = 0
    return S


if __name__ == "__main__":
    # Sanity check at L=0.60 (middle of second-prime window)
    result = pilot_values(L=0.60)
    print(f"\nWindow check passed: {result['window_ok']}")
    print("Prototype ready. TODO: implement cross-prime F_{ij} integral.")
