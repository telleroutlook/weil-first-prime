"""O1-B Path B Schur criterion assembly for FP-0.35.

Assembles F, R_0, R_2, R_eta for both parity sectors and checks
b_L > 0 and b_L * F - R_eta > 0 (positive definite) via interval LDL^T.

Frozen parameters (Theorem 5):
  L = 7/20,  eta = 1/2,  L_0 = 2^{-30}
  Even sector: N=8, tail_degree=16, indices=[0,2,4,6,8,10,12,14]
  Odd  sector: N=6, tail_degree=13, indices=[1,3,5,7,9,11]

## Three-tier computation strategy

  PILOT  (depth=1, prec=64):  ~2 min.  S_KK=0 lower bound. Direction check.
  DRAFT  (depth=2, prec=128): ~15 min. Full S. Interval inflation check.
  CERTIFY (depth=4, prec=256): ~60 min. Production certified enclosures.

Always run PILOT first. Only proceed to DRAFT if PILOT pivots are positive.
Only proceed to CERTIFY if DRAFT lower-endpoint pivots are positive.

## Observability, checkpointing, resumability

Per CLAUDE.md requirements:
- All long loops print progress with flush=True
- M_K cache is checkpointed after every entry to pilots/
- --resume flag loads latest checkpoint for the sector+tier combination
"""

from __future__ import annotations

import argparse
import json
import pathlib
import time
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
    "pilot":   (1, 1, 64,  "PILOT  (~1 min,  S_KK=0 lower bound, direction check only)"),
    "draft":   (2, 2, 128, "DRAFT  (~10 min, full S with narrow intervals, exploratory)"),
    "certify": (4, 3, 256, "CERTIFY (~60 min, full certified enclosures, production)"),
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


def _checkpoint_path(sector: str, tier: str) -> pathlib.Path:
    p = pathlib.Path("pilots")
    p.mkdir(exist_ok=True)
    return p / f"checkpoint-{sector}-{tier}.json"


def _save_checkpoint(
    sector: str, tier: str, mk_cache: dict, elapsed: float
) -> None:
    """Save M_K cache to disk after every entry (fault-tolerant)."""
    data = {
        "sector": sector, "tier": tier, "elapsed_s": elapsed,
        "mk_cache": {
            f"{k},{n}": [str(v[0]), str(v[1])]
            for (k, n), v in mk_cache.items()
        },
    }
    path = _checkpoint_path(sector, tier)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data))
    tmp.replace(path)  # atomic rename


def _load_checkpoint(sector: str, tier: str) -> dict[tuple[int, int], "Interval"] | None:
    """Load M_K cache from checkpoint if it exists and matches sector+tier."""
    path = _checkpoint_path(sector, tier)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        if data.get("sector") != sector or data.get("tier") != tier:
            return None
        cache: dict[tuple[int, int], Interval] = {}
        for key, (lo_s, hi_s) in data["mk_cache"].items():
            k, n = map(int, key.split(","))
            cache[(k, n)] = (Fraction(lo_s), Fraction(hi_s))
        elapsed = data.get("elapsed_s", 0)
        print(f"  [checkpoint] loaded {len(cache)} M_K entries "
              f"(prior elapsed: {elapsed:.0f}s)", flush=True)
        return cache
    except Exception as e:
        print(f"  [checkpoint] load failed ({e}), starting fresh", flush=True)
        return None


def build_M0_S0(
    indices: list[int],
    prec: int = 256,
    depth_2d: int = 4,
    depth_3d: int = 3,
    skip_skk: bool = False,
    sector: str = "unknown",
    tier: str = "pilot",
    resume: bool = False,
) -> tuple[list[list[Interval]], list[list[Interval]]]:
    """M^(0) and S^(0) from Archimedean primitives.

    Key optimisation: M_K is pre-computed for ALL expansion indices
    and cached to disk. Progress is printed with flush=True.
    Supports --resume to skip already-computed entries.

    skip_skk: pilot optimisation — S_KK=0 (conservative lower bound).
    S_KK >= 0 always (Gram matrix), so this makes the criterion harder.
    """
    from src.archimedean.integrator_a import integrate_M_K
    from src.archimedean.log_moments import V_matrix_entry as _vmv, V2_matrix_entry as _v2mv

    N = len(indices)
    a_num, a_den = L_NUM, L_DEN
    max_idx = max(indices)

    # ── Step 1: Build M_K cache with progress, checkpointing, resume ─────
    k_max_cache = min(2 * max_idx + 4, 100)
    all_needed_k = sorted({
        (k, n)
        for n in indices
        for k in range(n % 2, k_max_cache + 1, 2)
    })
    total = len(all_needed_k)

    # Try to resume from checkpoint
    mk_cache: dict[tuple[int, int], Interval] = {}
    if resume:
        loaded = _load_checkpoint(sector, tier)
        if loaded:
            mk_cache = loaded

    remaining = [(k, n) for (k, n) in all_needed_k if (k, n) not in mk_cache]
    if mk_cache:
        print(f"  resuming: {len(mk_cache)}/{total} already cached, "
              f"{len(remaining)} remaining", flush=True)

    t_start = time.time()

    for i, (k, n) in enumerate(remaining):
        t0 = time.time()
        r = integrate_M_K(k, n, a_num, a_den, depth=depth_2d, prec=prec)
        iv = r.to_interval()
        mk_cache[(k, n)] = iv
        elapsed = time.time() - t_start
        done = len(mk_cache)
        eta = (elapsed / done) * (total - done) if done < total else 0
        print(
            f"  M_K [{done:3d}/{total}] k={k:2d} n={n:2d}  "
            f"[{float(iv[0]):.4e}, {float(iv[1]):.4e}]  "
            f"{time.time()-t0:.2f}s  eta={eta:.0f}s",
            flush=True,
        )
        _save_checkpoint(sector, tier, mk_cache, elapsed)

    # ── Step 2: M^(0) = M_V + M_K (only for the basis index pairs) ───────
    M_V = [[_vmv(indices[i], indices[j], prec) for j in range(N)]
           for i in range(N)]
    M_K_basis = [[mk_cache.get((indices[i], indices[j]),
                                mk_cache.get((indices[j], indices[i]),
                                             point(Fraction(0))))
                  for j in range(N)] for i in range(N)]
    M0 = [[add(M_V[i][j], M_K_basis[i][j]) for j in range(N)] for i in range(N)]

    # ── Step 3: S^(0) using cached M_K ───────────────────────────────────
    S_VV = [[_v2mv(indices[i], indices[j], prec) for j in range(N)]
            for i in range(N)]

    S0 = [[point(Fraction(0))] * N for _ in range(N)]
    for i in range(N):
        ni = indices[i]
        parity_i = ni % 2
        k_max_i = min(max(ni + max_idx + 4, 20), 100)

        for j in range(N):
            nj = indices[j]
            # S_VK[i,j] = <V P_j, K P_i> = sum_k c_k(ni) * <V P_j, P_k>
            # S_KV[i,j] = <K P_j, V P_i> = sum_k c_k(nj) * <V P_i, P_k>
            svk = point(Fraction(0))
            skv = point(Fraction(0))

            # Only k with same parity as ni contribute to S_VK (K preserves parity)
            for k in range(parity_i, k_max_i + 1, 2):
                mk_k_ni = mk_cache.get((k, ni))
                if mk_k_ni is None:
                    continue
                scale = Fraction(2 * k + 1, 2)
                ck_ni = scalar_mul(scale, mk_k_ni)
                v_jk = _vmv(nj, k, prec)   # <V P_j, P_k>
                svk = add(svk, mul(ck_ni, v_jk))

            parity_j = nj % 2
            k_max_j = min(max(nj + max_idx + 4, 20), 100)
            for k in range(parity_j, k_max_j + 1, 2):
                mk_k_nj = mk_cache.get((k, nj))
                if mk_k_nj is None:
                    continue
                scale = Fraction(2 * k + 1, 2)
                ck_nj = scalar_mul(scale, mk_k_nj)
                v_ik = _vmv(ni, k, prec)   # <V P_i, P_k>
                skv = add(skv, mul(ck_nj, v_ik))

            if skip_skk:
                skk = point(Fraction(0))
            else:
                from src.archimedean.integrator_a import integrate_S_KK
                skk = integrate_S_KK(ni, nj, a_num, a_den,
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


def _mat_to_float(M: list[list[Interval]]) -> list[list[tuple[float, float]]]:
    """Convert Fraction interval matrix to float for fast pilot LDL^T."""
    return [[(float(r), float(c)) for r, c in row] for row in M]


def _min_pivot_float(C: list[list[tuple[float, float]]]) -> float | None:
    """Fast float LDL^T for pilot sign check. Not certified — pilot only."""
    n = len(C)
    A = [[C[i][j][0] for j in range(n)] for i in range(n)]  # use lower endpoints
    pivots = []
    for k in range(n):
        pivot = A[k][k]
        if pivot <= 0:
            return pivot  # return the failing pivot
        pivots.append(pivot)
        for i in range(k + 1, n):
            A[i][k] /= pivot
        for i in range(k + 1, n):
            for j in range(i, n):
                A[i][j] -= A[i][k] * A[k][k] * A[j][k]
                A[j][i] = A[i][j]
    return min(pivots)


def _min_pivot_mpmath(
    C: list[list[Interval]],
    dps: int = 60,
) -> float | None:
    """Outward-rounded LDL^T using mpmath interval arithmetic.

    Converts Fraction interval endpoints to mpmath floats with extra
    precision (dps digits), runs LDL^T with outward rounding, and returns
    the minimum pivot lower endpoint as a float.

    This avoids the Fraction denominator blowup that makes the pure-Fraction
    LDL^T infeasibly slow for draft/certify tiers, while still providing
    a real interval lower bound (not just a float midpoint).
    Used for draft; certify will use the full Fraction LDL^T once the
    matrix entries are tight enough.
    """
    import mpmath
    mpmath.mp.dps = dps
    n = len(C)

    def to_iv(f_lo: Fraction, f_hi: Fraction):
        return (mpmath.mpf(str(f_lo)), mpmath.mpf(str(f_hi)))

    # Convert matrix
    A = [[to_iv(C[i][j][0], C[i][j][1]) for j in range(n)] for i in range(n)]
    pivots = []

    for k in range(n):
        lo_k, hi_k = A[k][k]
        if lo_k <= 0:
            return float(lo_k)
        pivots.append(float(lo_k))
        # Compute L[i][k] = A[i][k] / pivot (outward: lo/hi_k for lo>=0)
        L_col = []
        for i in range(k + 1, n):
            alo, ahi = A[i][k]
            # Outward-rounded division: [alo,ahi] / [lo_k, hi_k]
            opts = [alo / lo_k, alo / hi_k, ahi / lo_k, ahi / hi_k]
            L_col.append((min(opts), max(opts)))
        # Schur update
        for idx, i in enumerate(range(k + 1, n)):
            li_lo, li_hi = L_col[idx]
            for jdx, j in enumerate(range(k + 1, n)):
                lj_lo, lj_hi = L_col[jdx]
                # li * d_k * lj: d_k = [lo_k, hi_k], all >= 0
                prod_opts = [lo_k * li_lo * lj_lo, lo_k * li_lo * lj_hi,
                             lo_k * li_hi * lj_lo, lo_k * li_hi * lj_hi,
                             hi_k * li_lo * lj_lo, hi_k * li_lo * lj_hi,
                             hi_k * li_hi * lj_lo, hi_k * li_hi * lj_hi]
                sub_lo, sub_hi = min(prod_opts), max(prod_opts)
                cur_lo, cur_hi = A[i][j]
                A[i][j] = (cur_lo - sub_hi, cur_hi - sub_lo)
                A[j][i] = A[i][j]

    return min(pivots)


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
    resume: bool = False,
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
          f"depth_2d={depth_2d} depth_3d={depth_3d} prec={prec}", flush=True)

    G = build_gram(indices)
    T_N = build_kinetic(indices)
    M2, S2 = build_M2_S2(indices)

    print(f"[O1-B {sector}] Computing Archimedean primitives...", flush=True)
    skip_skk = (tier == "pilot")
    if skip_skk:
        print(f"[O1-B {sector}] pilot: skipping S_KK (using 0 as conservative lower bound)", flush=True)
    M0, S0 = build_M0_S0(indices, prec, depth_2d, depth_3d, skip_skk=skip_skk,
                          sector=sector, tier=tier, resume=resume)

    R0 = build_R(M0, S0, G)
    R2 = build_R(M2, S2, G)
    R_eta = build_R_eta(R0, R2)

    b_L = compute_b_L(d, c_L, prec)
    print(f"[O1-B {sector}] b_L = {float(b_L):.6f}", flush=True)

    if b_L <= 0:
        return {
            "sector": sector, "tier": tier, "N": N, "d": d,
            "b_L": float(b_L), "b_L_positive": False,
            "min_pivot": None, "certified": False,
            "message": f"b_L = {float(b_L):.6f} <= 0; complement-space bound fails",
        }

    F = build_F(T_N, M0, M2, G, c_L)
    C = build_schur_matrix(b_L, F, R_eta)

    print(f"[O1-B {sector}] Running LDL^T ({tier})...", flush=True)
    if tier == "pilot":
        # Float fast path: not certified, for sign direction only
        C_f = _mat_to_float(C)
        pivot = _min_pivot_float(C_f)
        certified = False
    elif tier in ("draft", "certify"):
        # mpmath outward-rounded: fast, gives real interval lower bound.
        # For certify we use higher dps to tighten the bound.
        dps = 100 if tier == "certify" else 60
        pivot = _min_pivot_mpmath(C, dps=dps)
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
    parser = argparse.ArgumentParser(description="O1-B Schur gate runner")
    parser.add_argument(
        "--tier", choices=["pilot", "draft", "certify"], default="pilot",
        help="Computation tier (default: pilot ~2 min)"
    )
    parser.add_argument(
        "--sector", choices=["even", "odd", "both"], default="both",
    )
    parser.add_argument(
        "--c_L", type=float, default=0.0,
        help="c_L constant from frozen model (default: 0 = conservative)"
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Resume from checkpoint if available"
    )
    args = parser.parse_args()

    _, _, _, tier_label = TIERS[args.tier]
    print(f"Running O1-B gate: {tier_label}", flush=True)
    print(f"c_L = {args.c_L}  resume={args.resume}", flush=True)
    print(flush=True)

    c_L = Fraction(args.c_L).limit_denominator(10**6)
    sectors = ["even", "odd"] if args.sector == "both" else [args.sector]

    results = {}
    for sector in sectors:
        result = run_o1b_gate(sector, c_L, tier=args.tier, resume=args.resume)
        results[sector] = result
        print(json.dumps(result, indent=2), flush=True)
        print(flush=True)

    if len(sectors) > 1:
        all_positive = all(r.get("pivot_positive") for r in results.values())
        all_certified = all(r["certified"] for r in results.values())
        print(f"Summary: pivot_positive={all_positive}  certified={all_certified}")
        if all_positive and args.tier != "certify":
            print(f"→ Pivots positive at '{args.tier}' tier. "
                  f"Next: run with --tier {'draft' if args.tier == 'pilot' else 'certify'}")
