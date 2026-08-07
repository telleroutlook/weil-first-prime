"""Generate first-prime certificate for L = 7/20.

The first-prime certificate is a lightweight identity-only JSON that binds:
  - frozen model parameters (sector, N, tail_degree, index_set, eta)
  - archimedean base certificate by digest (certificate_sha256, checker_sha256,
    schema_sha256, obligation)
  - algebraic theorem contract by digest (theorem_contract_sha256)

It does NOT contain matrix values or pivots — those are recomputed by the checker.

Usage:
    python3 -m src.assemble.generate_first_prime_cert --sector even
    python3 -m src.assemble.generate_first_prime_cert --sector odd
    python3 -m src.assemble.generate_first_prime_cert --sector both
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

_ROOT = pathlib.Path(__file__).parent.parent.parent

_ARCHIMEDEAN_CHECKER = _ROOT / "checker" / "archimedean" / "check_archimedean.py"
_ARCHIMEDEAN_SCHEMA  = _ROOT / "schemas" / "certificate-archimedean-v1.schema.json"
_THEOREM_CONTRACT    = _ROOT / "domains" / "fp035" / "contracts" / \
                       "thm-3-rational-absorption-certificate.json"

_SECTOR_PARAMS: dict[str, dict] = {
    "even": {"N": 8, "tail_degree": 16, "index_set": list(range(0, 16, 2))},
    "odd":  {"N": 6, "tail_degree": 13, "index_set": list(range(1, 12, 2))},
}


def _sha256(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def generate(sector: str, out: pathlib.Path) -> str:
    """Build and write first-prime certificate for sector. Returns SHA256."""
    params = _SECTOR_PARAMS[sector]
    archimedean_cert = _ROOT / "certs" / f"archimedean-{sector}.json"

    if not archimedean_cert.exists():
        raise FileNotFoundError(
            f"Archimedean certificate not found: {archimedean_cert}\n"
            f"Run: python3 -m src.assemble.generate_archimedean_cert --sector {sector}"
        )

    cert = {
        "format_version": "first-prime-1.0",
        "method": "exact_prime_split_v1",
        "radius": {"numerator": 7, "denominator": 20},
        "window": "log2_le_2L_lt_log3",
        "sector": sector,
        **params,
        "eta": {"numerator": 1, "denominator": 2},
        "archimedean_base": {
            "certificate_sha256": _sha256(archimedean_cert),
            "checker_sha256":     _sha256(_ARCHIMEDEAN_CHECKER),
            "schema_sha256":      _sha256(_ARCHIMEDEAN_SCHEMA),
            "obligation":         "archimedean_primitives_o2_v1",
        },
        "theorem_contract_sha256": _sha256(_THEOREM_CONTRACT),
    }

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(cert, indent=2) + "\n")
    digest = _sha256(out)
    print(f"[first-prime cert] sector={sector} -> {out} ({out.stat().st_size} bytes)")
    print(f"SHA256: {digest}")
    return digest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate first-prime certificate for L=7/20"
    )
    parser.add_argument("--sector", choices=["even", "odd", "both"], required=True)
    parser.add_argument("--out", default=None,
                        help="write the certificate to this path (single sector only; "
                             "used by proofctl replay's {cert} placeholder). Defaults to "
                             "certs/first-prime-<sector>.json.")
    args = parser.parse_args()

    sectors = ["even", "odd"] if args.sector == "both" else [args.sector]
    if args.out is not None and args.sector == "both":
        parser.error("--out cannot be combined with --sector both")
    for sector in sectors:
        out = pathlib.Path(args.out) if args.out is not None \
            else _ROOT / "certs" / f"first-prime-{sector}.json"
        generate(sector, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
