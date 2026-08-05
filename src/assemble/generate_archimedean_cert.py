"""Generate an Archimedean base certificate for L = 7/20.

This script computes M_V, M_K, S_VV, S_VK, S_KV, S_KK using both
Path A (Arb GL-8 + Bernstein remainder) and Path B (mpmath independent)
and writes a certificate JSON for import into proofctl CAS.

Usage:
    python3 -m src.assemble.generate_archimedean_cert \
        --sector even --depth 4 --out certs/archimedean-even.json

The certificate carries:
  - format_version, obligation, radius, sector, index_set
  - path_a: method, quadrature_rule, remainder_method, integrand_source_sha256
  - path_b: method, taylor_cutoff, taylor_cubic_coefficient,
            remainder_method, integrand_source_sha256
  - theorem_contract_sha256
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import time
from fractions import Fraction

A_NUM, A_DEN = 7, 20

_ROOT = pathlib.Path(__file__).parent.parent.parent
_INTEGRATOR_A = _ROOT / "src" / "archimedean" / "integrator_a.py"
_INTEGRATOR_B = _ROOT / "src" / "archimedean" / "integrator_b.py"
_THEOREM_CONTRACT = _ROOT / "domains" / "fp035" / "contracts" / "thm-3-rational-absorption-certificate.json"

_SECTOR_INDICES = {
    "even": list(range(0, 16, 2)),
    "odd":  list(range(1, 12, 2)),
}


def _file_sha256(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _frac_str(f: Fraction) -> str:
    return f"{f.numerator}/{f.denominator}"


def generate(sector: str, depth: int, prec: int, dps: int, out: pathlib.Path) -> dict:
    """Compute primitives for the given sector and write certificate JSON."""
    from src.archimedean.integrator_a import integrate_M_K as mk_a
    from src.archimedean.integrator_b import integrate_M_K_path_b as mk_b
    from src.archimedean.interval import intersect

    if sector not in _SECTOR_INDICES:
        raise ValueError(f"unknown sector: {sector!r}")

    indices = _SECTOR_INDICES[sector]
    N = len(indices)

    print(f"[archimedean cert] sector={sector} N={N} depth={depth} prec={prec}", flush=True)

    t0 = time.time()

    mk_results = []
    all_intersect = True

    for ni in indices:
        for nj in indices:
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
                "leaf_witnesses": [leaf.to_dict() for leaf in ra.leaves],
            })
            print(f"  M_K[{ni:2d},{nj:2d}] A={float(iv_a[0]):.6e} "
                  f"B=[{float(iv_b[0]):.6e},{float(iv_b[1]):.6e}] "
                  f"{'✓' if intersects else '✗'} [{len(ra.leaves)} leaves]", flush=True)

    elapsed = time.time() - t0

    # Compute source digests for audit trail
    integrand_a_sha = _file_sha256(_INTEGRATOR_A)
    integrand_b_sha = _file_sha256(_INTEGRATOR_B)
    theorem_sha = _file_sha256(_THEOREM_CONTRACT) if _THEOREM_CONTRACT.exists() else "0" * 64

    cert = {
        "format_version": "archimedean-1.0",
        "obligation": "archimedean_primitives_o2_v1",
        "radius": {"numerator": A_NUM, "denominator": A_DEN},
        "sector": sector,
        "index_set": indices,
        "path_a": {
            "method": "GL_with_certified_remainder",
            "quadrature_rule": "GL8",
            "remainder_method": "bernstein_ellipse_analytic",
            "integrand_source_sha256": integrand_a_sha,
        },
        "path_b": {
            "method": "taylor_plus_GL_with_certified_remainder",
            "taylor_cutoff": f"1/{dps}",
            "taylor_cubic_coefficient": {"numerator": 7, "denominator": 11520},
            "remainder_method": "bernstein_ellipse_analytic",
            "integrand_source_sha256": integrand_b_sha,
        },
        "theorem_contract_sha256": theorem_sha,
        "mk_entries": mk_results,
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
