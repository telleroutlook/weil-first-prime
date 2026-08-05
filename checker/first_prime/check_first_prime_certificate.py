"""Independent checker for ``exact_prime_split_v1``.

Exit codes:
    0  CERTIFIED
    1  mathematically uncertified (e.g. non-positive LDL pivot)
    2  malformed contract, unknown field, identity mismatch, or resource error
    3  O2_BLOCKED / independent primitive replay unavailable

The submitted JSON contains no matrices, integrals, eigenvalues, pivots or
conclusion.  Those values are recomputed by the checker or not accepted at all.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from checker.archimedean.replay import (
    O2Blocked,
    replay_archimedean_base,
    sha256_file,
)
from checker.first_prime.exact_split import (
    certify_with_archimedean_base,
    recompute_prime_layer,
)

SCHEMA = _ROOT / "schemas" / "certificate-first-prime-v1.schema.json"
MAX_CONTRACT_BYTES = 1024 * 1024
MAX_JSON_DEPTH = 20
CHECKER_PRECISION = 256


def _depth(value: object, depth: int = 0) -> int:
    if isinstance(value, dict):
        return max((_depth(v, depth + 1) for v in value.values()), default=depth)
    if isinstance(value, list):
        return max((_depth(v, depth + 1) for v in value), default=depth)
    return depth


def _load_contract(path: Path) -> dict:
    raw = path.read_bytes()
    if len(raw) > MAX_CONTRACT_BYTES:
        raise ValueError("first-prime contract exceeds the 1 MiB limit")
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("contract root must be an object")
    if _depth(value) > MAX_JSON_DEPTH:
        raise ValueError("contract nesting exceeds the depth limit")
    return value


def validate_contract(contract: dict) -> None:
    # Permissive fallback is intentionally absent: a missing schema engine is
    # an environment failure, not permission to perform shallow validation.
    try:
        import jsonschema
    except ImportError as exc:
        raise RuntimeError("jsonschema is required for strict validation") from exc

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft7Validator(schema)
    errors = sorted(validator.iter_errors(contract), key=lambda e: list(e.path))
    if errors:
        rendered = []
        for error in errors:
            path = "/".join(str(item) for item in error.path) or "<root>"
            rendered.append(f"{path}: {error.message}")
        raise ValueError("; ".join(rendered))


def check(args: argparse.Namespace) -> int:
    try:
        contract = _load_contract(args.contract)
        validate_contract(contract)

        theorem_digest = sha256_file(args.theorem_contract)
        if theorem_digest != contract["theorem_contract_sha256"]:
            raise ValueError(
                "theorem_contract_sha256 mismatch: the algebraic theorem "
                "contract is not the file bound by this certificate"
            )

        # Recompute the complete exact prime layer before consulting any
        # generator result.  This also checks the frozen window and direction,
        # sign, parity and c2^2 invariants.
        prime = recompute_prime_layer(contract["sector"], CHECKER_PRECISION)

        base = replay_archimedean_base(
            contract["archimedean_base"],
            args.base_certificate,
            args.base_checker,
            args.base_schema,
        )
        result = certify_with_archimedean_base(
            contract["sector"], base, CHECKER_PRECISION
        )
    except O2Blocked as exc:
        print(
            json.dumps(
                {
                    "status": "O2_BLOCKED",
                    "method": "exact_prime_split_v1",
                    "reason": str(exc),
                },
                sort_keys=True,
            )
        )
        return 3
    except (OSError, RuntimeError, ValueError, ArithmeticError) as exc:
        print(f"FIRST-PRIME CHECKER REJECT: {exc}", file=sys.stderr)
        return 2

    # Status is derived exclusively from the recomputed pivots.
    if not all(pivot[0] > 0 for pivot in result["pivots"]):
        print("FIRST-PRIME CHECKER UNCERTIFIED: non-positive pivot", file=sys.stderr)
        return 1

    sector = contract["sector"]
    prefix = f"o1b-{sector}"
    obligation_ids = [
        f"{prefix}.window-verified",
        f"{prefix}.archimedean-base-certified",
        f"{prefix}.J-E-matrices-exact",
        f"{prefix}.b_L-positive",
        f"{prefix}.F-matrix-assembled",
        f"{prefix}.R-eta-assembled",
        f"{prefix}.ldlt-all-pivots-positive",
    ]
    print(
        json.dumps(
            {
                "protocol_version": 2,
                "obligation_results": [
                    {"id": oid, "verdict": "pass"} for oid in obligation_ids
                ],
                "status": "CERTIFIED",
                "method": "exact_prime_split_v1",
                "sector": sector,
                "pivot_count": len(result["pivots"]),
            },
            sort_keys=True,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Independent checker for exact_prime_split_v1 certificates."
    )
    parser.add_argument("contract", type=Path, help="Path to first-prime certificate JSON")
    parser.add_argument("--base-certificate", required=True, type=Path,
                        help="Archimedean base certificate JSON")
    parser.add_argument("--base-checker", required=True, type=Path,
                        help="Archimedean base checker script")
    parser.add_argument("--base-schema", required=True, type=Path,
                        help="Archimedean base certificate schema JSON")
    parser.add_argument("--theorem-contract", required=True, type=Path,
                        help="Algebraic theorem contract file (SHA256 bound check)")
    return parser


def main() -> int:
    return check(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
