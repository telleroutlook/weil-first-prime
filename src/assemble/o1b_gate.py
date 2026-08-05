"""O1-B Path B Schur criterion assembly for FP-0.35.

Assembles F, R_0, R_2, R_eta for both parity sectors and checks
b_L > 0 and b_L * F - R_eta > 0 (positive definite) via interval LDL^T.

Frozen parameters (Theorem 5):
  L = 7/20,  eta = 1/2,  L_0 = 2^{-30}
  Even sector: N=8, tail_degree=16, indices=[0,2,4,6,8,10,12,14]
  Odd  sector: N=6, tail_degree=13, indices=[1,3,5,7,9,11]

## Three-tier computation strategy

This module implements the "explore first, certify later" principle:

  PILOT  (depth=1, prec=64):  ~1 min.  Float-centre only.  No proof value.
                               Purpose: confirm sign direction before committing.
  DRAFT  (depth=2, prec=128): ~5 min.  Narrow interval, may be too wide to pass.
                               Purpose: detect if margin survives interval inflation.
  CERTIFY (depth=4, prec=256): ~60 min. Production-quality certified enclosures.
                               Purpose: formal O1-B gate closure.

Always run PILOT first.  Only proceed to DRAFT if PILOT shows positive pivots.
Only proceed to CERTIFY if DRAFT shows positive lower endpoints.
"""

from __future__ import annotations

import argparse
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

C2_LO = LOG2_LO * SQRT2_LO / (SQRT2_LO**2 + 1)
C2_HI = LOG2_HI / SQRT2_LO
C2SQ_LO = LOG2_LO**2 / 2
C2SQ_HI = LOG2_HI**2 / 2

TAU_LO = LOG2_LO * L_DEN / L_NUM
TAU_HI = LOG2_HI * L_DEN / L_NUM
TAU_MID = (TAU_LO + TAU_HI) / 2

SECTOR_PARAMS = {
    "even": {"N": 8, "d": 16, "indices": list(range(0, 16, 2))},
    "odd":  {"N": 6, "d": 13, "indices": list(range(1, 12, 2))},
}

# Three-tier presets: (depth_2d, depth_3d, prec, label)
TIERS = {
    "pilot":   (1, 1, 64,  "PILOT  (~1 min,  float-centre, no proof value)"),
    "draft":   (2, 2, 128, "DRAFT  (~5 min,  narrow interval, exploratory)"),
    "certify": (4, 3, 256, "CERTIFY (~60 min, production-quality certified)"),
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _harmonic(n: int) -> Fraction:
    return sum(Fraction(1, k) for k in range(1, n + 1))


def build_gram(indices: list[int]) -> list[list[Interval]]:
    N = len(indices)
    G = [[point(Fraction(0))] * N for _ in range(N)]
    for k, n in enumerate(indices):
        G[k][k] = point(Fraction(2, 2 * n + 1))
    return G


def build_kinetic(indices: list[int]) -> list[list[Interval]]:
    N = len(indices)
    T = [[point(Fraction(0))] * N for _ in range(N)]
    for k, n in enumerate(indices):
        T[k][k] = point(_harmonic(n) * Fraction(2, 2 * n + 1))
    return T


def build_M2_S2(
    indices: list[int],
) -> tuple[list[list[Interval]], list[list[Interval]]]:
    J_mat, E_mat = prime_legendre_matrices(indices, TAU_MID)
    N = len(indices)
    M2 = [[point(Fraction(0))] * N for _ in range(N)]
    S2 = [[point(Fraction(0))] * N for _ in range(N)]
    for r in range(N):
        for c in range(N):
            j = J_mat[r][c]
            e = E_mat[r][c]
            if j >= 0:
                M2[r][c] = (-C2_HI * j, -C2_LO * j)
            else:
                M2[r][c] = (-C2_LO * j, -C2_HI * j)
            S2[r][c] = (C2SQ_LO * e, C2SQ_HI * e)
    return M2, S2


def build_M0_S0(
    indices: list[int],
    prec: int = 256,
    depth_2d: int = 4,
    depth_3d: int = 3,
) -> tuple[list[list[Interval]], list[list[Interval]]]:
    """M^(0) and S^(0) from Archimedean primitives.

    depth_2d: integration depth for M_K, S_VK (2D integrals)
    depth_3d: integration depth for S_KK (3D / expansion)
    Lower depths run faster but produce wider interval enclosures.
    """
    from src.archimedean.integrator_a import (
        integrate_M_K, integrate_S_VK, integrate_S_KK,
    )
    N = len(indices)
    a_num, a_den = L_NUM, L_DEN

    M_V = [[V_matrix_entry(indices[i], indices[j], prec) for j in range(N)]
           for i in range(N)]
    M_K = [[integrate_M_K(indices[i], indices[j], a_num, a_den,
                          depth=depth_2d, prec=prec).to_interval()
            for j in range(N)] for i in range(N)]
    M0 = [[add(M_V[i][j], M_K[i][j]) for j in range(N)] for i in range(N)]

    S_VV = [[V2_matrix_entry(indices[i], indices[j], prec) for j in range(N)]
            for i in range(N)]
    S0 = [[point(Fraction(0))] * N for _ in range(N)]
    for i in range(N):
        for j in range(N):
            svk = integrate_S_VK(indices[i], indices[j], a_num, a_den,
                                 depth=depth_2d, prec=prec).to_interval()
            skv = integrate_S_VK(indices[j], indices[i], a_num, a_den,
                                 depth=depth_2d, prec=prec).to_interval()
            skk = integrate_S_KK(indices[i], indices[j], a_num, a_den,
                                 depth=depth_3d, prec=prec).to_interval()
            S0[i][j] = add(add(add(S_VV[i][j], svk), skv), skk)

    return M0, S0


def build_R(
    M: list[list[Interval]],
    S: list[list[Interval]],
    G: list[list[Interval]],
) -> list[list[Interval]]:
    N = len(M)
    R = [[point(Fraction(0))] * N for _ in range(N)]
    for i in range(N):
        for j in range(N):
            s = S[i][j]
            for k in range(N):
                term = div_outward(mul(M[k][i], M[k][j]), G[k][k])
                s = sub(s, term)
            R[i][j] = s
    return R


def build_R_eta(
    R0: list[list[Interval]],
    R2: list[list[Interval]],
    eta: Fraction = ETA,
) -> list[list[Interval]]:
    N = len(R0)
    c0 = Fraction(1) + eta
    c2 = Fraction(1) + Fraction(1) / eta
    return [[add(scalar_mul(c0, R0[i][j]), scalar_mul(c2, R2[i][j]))
             for j in range(N)] for i in range(N)]


def compute_b_L(d: int, c_L: Fraction, prec: int = 256) -> Fraction:
    H_d = _harmonic(d)
    kappa_L = kappa(L_NUM, L_DEN, prec)
    return H_d - c_L - L0 - kappa_L


def build_F(
    T_N: list[list[Interval]],
    M0: list[list[Interval]],
    M2: list[list[Interval]],
    G: list[list[Interval]],
    c_L: Fraction,
) -> list[list[Interval]]:
    N = len(T_N)
    shift = c_L + L0
    return [[sub(add(add(T_N[i][j], M0[i][j]), M2[i][j]),
                 scalar_mul(shift, G[i][j]))
             for j in range(N)] for i in range(N)]


def build_schur_matrix(
    b_L: Fraction,
    F: list[list[Interval]],
    R_eta: list[list[Interval]],
) -> list[list[Interval]]:
    return [[sub(scalar_mul(b_L, F[i][j]), R_eta[i][j])
             for j in range(len(F))] for i in range(len(F))]


# ── Main gate ─────────────────────────────────────────────────────────────────

def run_o1b_gate(
    sector: str,
    c_L: Fraction,
    tier: str = "pilot",
    prec: int | None = None,
) -> dict[str, Any]:
    """Run O1-B Schur gate for one parity sector.

    tier: 'pilot' | 'draft' | 'certify'  (see TIERS table above)
    prec: override precision (default from tier)
    """
    depth_2d, depth_3d, default_prec, tier_label = TIERS[tier]
    if prec is None:
        prec = default_prec

    params = SECTOR_PARAMS[sector]
    N, d, indices = params["N"], params["d"], params["indices"]

    print(f"[O1-B {sector}] tier={tier.upper()}  N={N} d={d}  "
          f"depth_2d={depth_2d} depth_3d={depth_3d} prec={prec}")

    G = build_gram(indices)
    T_N = build_kinetic(indices)
    M2, S2 = build_M2_S2(indices)

    print(f"[O1-B {sector}] Computing Archimedean primitives...")
    M0, S0 = build_M0_S0(indices, prec, depth_2d, depth_3d)

    R0 = build_R(M0, S0, G)
    R2 = build_R(M2, S2, G)
    R_eta = build_R_eta(R0, R2)

    b_L = compute_b_L(d, c_L, prec)
    print(f"[O1-B {sector}] b_L = {float(b_L):.6f}")

    if b_L <= 0:
        return {
            "sector": sector, "tier": tier, "N": N, "d": d,
            "b_L": float(b_L), "b_L_positive": False,
            "min_pivot": None, "certified": False,
            "message": f"b_L = {float(b_L):.6f} <= 0; complement-space bound fails",
        }

    F = build_F(T_N, M0, M2, G, c_L)
    C = build_schur_matrix(b_L, F, R_eta)

    print(f"[O1-B {sector}] Running interval LDL^T...")
    pivot = min_pivot_lower(C)
    certified = (tier == "certify") and pivot is not None and pivot > 0
    positive = pivot is not None and pivot > 0

    status = ("CERTIFIED" if certified else
              "POSITIVE (not yet certified — run certify tier)" if positive else
              "FAIL")

    return {
        "sector": sector, "tier": tier, "N": N, "d": d,
        "b_L": float(b_L), "b_L_positive": True,
        "min_pivot": float(pivot) if pivot is not None else None,
        "pivot_positive": positive,
        "certified": certified,
        "message": f"{status}: min pivot = {float(pivot):.4e}" if pivot is not None
                   else "FAIL: LDL^T factorisation failed",
    }


if __name__ == "__main__":
    import json

    parser = argparse.ArgumentParser(description="O1-B Schur gate runner")
    parser.add_argument(
        "--tier", choices=["pilot", "draft", "certify"], default="pilot",
        help="Computation tier (default: pilot ~1 min)"
    )
    parser.add_argument(
        "--sector", choices=["even", "odd", "both"], default="both",
    )
    parser.add_argument(
        "--c_L", type=float, default=0.0,
        help="c_L constant from frozen model (default: 0 = conservative)"
    )
    args = parser.parse_args()

    _, _, _, tier_label = TIERS[args.tier]
    print(f"Running O1-B gate: {tier_label}")
    print(f"c_L = {args.c_L}")
    print()

    c_L = Fraction(args.c_L).limit_denominator(10**6)
    sectors = ["even", "odd"] if args.sector == "both" else [args.sector]

    results = {}
    for sector in sectors:
        result = run_o1b_gate(sector, c_L, tier=args.tier)
        results[sector] = result
        print(json.dumps(result, indent=2))
        print()

    if len(sectors) > 1:
        all_positive = all(r.get("pivot_positive") for r in results.values())
        all_certified = all(r["certified"] for r in results.values())
        print(f"Summary: pivot_positive={all_positive}  certified={all_certified}")
        if all_positive and args.tier != "certify":
            print(f"→ Pivots positive at '{args.tier}' tier. "
                  f"Next: run with --tier {'draft' if args.tier == 'pilot' else 'certify'}")
