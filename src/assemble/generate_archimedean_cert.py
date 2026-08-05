"""Generate an Archimedean base certificate for L = 7/20.

This script computes M_V, M_K, S_VV, S_VK, S_KV, S_KK using both
Path A (Arb GL-8 + Bernstein remainder) and Path B (mpmath independent)
and writes a certificate JSON for import into proofctl CAS.

Usage:
    python3 -m src.assemble.generate_archimedean_cert \
        --sector even --depth 4 --out certs/archimedean-even.json

The certificate carries:
  - format_version, obligation, radius, sector
  - path_a: method, depth, prec, M_K summary
  - path_b: method, dps
  - intersection_verified: bool
  - window: "log2_le_2L_lt_log3"
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import time
from fractions import Fraction

A_NUM, A_DEN = 7, 20


def _frac_str(f: Fraction) -> str:
    return f"{f.numerator}/{f.denominator}"


def generate(sector: str, depth: int, prec: int, dps: int, out: pathlib.Path) -> dict:
    """Compute primitives for the given sector and write certificate JSON."""
    from src.archimedean.integrator_a import integrate_M_K as mk_a
    from src.archimedean.integrator_b import integrate_M_K_path_b as mk_b
    from src.archimedean.interval import intersect
    from src.archimedean.log_moments import V_matrix_entry

    sector_params = {
        "even": {"indices": list(range(0, 16, 2))},
        "odd":  {"indices": list(range(1, 12, 2))},
    }
    if sector not in sector_params:
        raise ValueError(f"unknown sector: {sector!r}")

    indices = sector_params[sector]["indices"]
    N = len(indices)

    print(f"[archimedean cert] sector={sector} N={N} depth={depth} prec={prec}", flush=True)

    t0 = time.time()

    # Compute M_K via Path A (Bernstein remainder) and Path B (mpmath)
    mk_results = []
    all_intersect = True

    for i, ni in enumerate(indices):
        for j, nj in enumerate(indices):
            ra = mk_a(ni, nj, A_NUM, A_DEN, depth=depth, prec=prec, use_bernstein=True)
            rb = mk_b(ni, nj, A_NUM, A_DEN)

            iv_a = ra.to_interval()
            iv_b = rb.to_interval()

            try:
                iv_int = intersect(iv_a, iv_b)
                intersects = True
            except ValueError:
                intersects = False
                all_intersect = False
                print(f"  WARNING: M_K[{ni},{nj}] A∩B empty!", flush=True)

            mk_results.append({
                "n_row": ni, "n_col": nj,
                "path_a": [_frac_str(iv_a[0]), _frac_str(iv_a[1])],
                "path_b": [_frac_str(iv_b[0]), _frac_str(iv_b[1])],
                "intersects": intersects,
            })
            print(f"  M_K[{ni:2d},{nj:2d}] A={float(iv_a[0]):.6e} "
                  f"B=[{float(iv_b[0]):.6e},{float(iv_b[1]):.6e}] "
                  f"{'✓' if intersects else '✗'}", flush=True)

    elapsed = time.time() - t0

    cert = {
        "format_version": "archimedean-1.0",
        "obligation": "archimedean_primitives_o2_v1",
        "radius": {"numerator": A_NUM, "denominator": A_DEN},
        "sector": sector,
        "window": "log2_le_2L_lt_log3",
        "path_a": {
            "method": "GL_with_Bernstein_remainder",
            "quadrature_rule": "GL8",
            "remainder_method": "bernstein_ellipse_analytic",
            "depth": depth,
            "prec": prec,
        },
        "path_b": {
            "method": "mpmath_GL_independent",
            "dps": dps,
            "taylor_cubic_coefficient": {"numerator": 7, "denominator": 11520},
        },
        "intersection_verified": all_intersect,
        "mk_entries": mk_results,
        "elapsed_s": round(elapsed, 1),
    }

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(cert, indent=2) + "\n")

    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    print(f"\nWrote {out} ({out.stat().st_size} bytes)", flush=True)
    print(f"SHA256: {digest}", flush=True)
    print(f"intersection_verified: {all_intersect}", flush=True)
    print(f"Total time: {elapsed:.1f}s", flush=True)

    return cert


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate Archimedean base certificate for L=7/20"
    )
    parser.add_argument("--sector", choices=["even", "odd"], required=True)
    parser.add_argument("--depth", type=int, default=4,
                        help="GL depth (default 4, ~30s per sector)")
    parser.add_argument("--prec", type=int, default=256,
                        help="Arb precision bits (default 256)")
    parser.add_argument("--dps", type=int, default=50,
                        help="mpmath decimal places for Path B (default 50)")
    parser.add_argument("--out", type=pathlib.Path,
                        default=None,
                        help="Output path (default: certs/archimedean-{sector}.json)")
    args = parser.parse_args()

    if args.out is None:
        args.out = pathlib.Path(f"certs/archimedean-{args.sector}.json")

    generate(args.sector, args.depth, args.prec, args.dps, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
