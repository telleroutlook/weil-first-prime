"""Mutation / negative tests for the first-prime checker and schema.

These tests verify that the checker rejects every known attack vector.
All tests in this file must PASS (i.e. the checker must REJECT the mutant).
A mutation test that does not reject is a P0 defect.
"""

from __future__ import annotations

import json
import tempfile
from fractions import Fraction
from pathlib import Path

import pytest

_ROOT = Path(__file__).parent.parent.parent
_SCHEMA = _ROOT / "schemas" / "certificate-first-prime-v1.schema.json"


def _base_contract(sector: str = "even") -> dict:
    """Return a structurally valid contract (will fail on archimedean replay, not schema)."""
    if sector == "even":
        return {
            "format_version": "first-prime-1.0",
            "method": "exact_prime_split_v1",
            "radius": {"numerator": 7, "denominator": 20},
            "window": "log2_le_2L_lt_log3",
            "sector": "even",
            "N": 8,
            "tail_degree": 16,
            "index_set": [0, 2, 4, 6, 8, 10, 12, 14],
            "eta": {"numerator": 1, "denominator": 2},
            "archimedean_base": {
                "certificate_sha256": "a" * 64,
                "checker_sha256": "b" * 64,
                "schema_sha256": "c" * 64,
                "obligation": "archimedean_primitives_o2_v1",
            },
            "theorem_contract_sha256": "d" * 64,
        }
    return {
        "format_version": "first-prime-1.0",
        "method": "exact_prime_split_v1",
        "radius": {"numerator": 7, "denominator": 20},
        "window": "log2_le_2L_lt_log3",
        "sector": "odd",
        "N": 6,
        "tail_degree": 13,
        "index_set": [1, 3, 5, 7, 9, 11],
        "eta": {"numerator": 1, "denominator": 2},
        "archimedean_base": {
            "certificate_sha256": "a" * 64,
            "checker_sha256": "b" * 64,
            "schema_sha256": "c" * 64,
            "obligation": "archimedean_primitives_o2_v1",
        },
        "theorem_contract_sha256": "d" * 64,
    }


def _validate(contract: dict) -> list[str]:
    """Return list of schema error messages (empty = valid)."""
    import jsonschema

    schema = json.loads(_SCHEMA.read_text())
    validator = jsonschema.Draft7Validator(schema)
    errors = sorted(validator.iter_errors(contract), key=lambda e: list(e.path))
    return [e.message for e in errors]


class TestSchemaRejectsPathAFields:
    """Any θ field or path-A arithmetic field must trigger unknown-field rejection."""

    def test_theta_field_rejected(self) -> None:
        c = _base_contract()
        c["theta"] = "69/100"
        errors = _validate(c)
        assert errors, "theta field must be rejected as unknown"

    def test_potential_coefficient_rejected(self) -> None:
        c = _base_contract()
        c["potential_coefficient"] = 0.69
        errors = _validate(c)
        assert errors

    def test_matrix_field_rejected(self) -> None:
        c = _base_contract()
        c["M"] = [[1, 0], [0, 1]]
        errors = _validate(c)
        assert errors

    def test_pivot_field_rejected(self) -> None:
        c = _base_contract()
        c["min_pivot"] = 0.001
        errors = _validate(c)
        assert errors

    def test_conclusion_field_rejected(self) -> None:
        c = _base_contract()
        c["conclusion"] = "certified"
        errors = _validate(c)
        assert errors

    def test_eigenvalue_field_rejected(self) -> None:
        c = _base_contract()
        c["eigenvalues"] = [0.1, 0.2]
        errors = _validate(c)
        assert errors


class TestSchemaRejectsWrongMethod:
    def test_wrong_method(self) -> None:
        c = _base_contract()
        c["method"] = "potential_redistribution_v1"
        errors = _validate(c)
        assert errors

    def test_wrong_format_version(self) -> None:
        c = _base_contract()
        c["format_version"] = "first-prime-2.0"
        errors = _validate(c)
        assert errors

    def test_wrong_obligation(self) -> None:
        c = _base_contract()
        c["archimedean_base"]["obligation"] = "archimedean_primitives_v1"
        errors = _validate(c)
        assert errors


class TestSchemaRejectsWrongSectorParams:
    """Schema must enforce frozen N, tail_degree, index_set per sector."""

    def test_even_wrong_N(self) -> None:
        c = _base_contract("even")
        c["N"] = 6  # should be 8
        errors = _validate(c)
        assert errors, "N=6 for even sector must be rejected"

    def test_odd_wrong_N(self) -> None:
        c = _base_contract("odd")
        c["N"] = 8  # should be 6
        errors = _validate(c)
        assert errors, "N=8 for odd sector must be rejected"

    def test_even_wrong_tail_degree(self) -> None:
        c = _base_contract("even")
        c["tail_degree"] = 13
        errors = _validate(c)
        assert errors

    def test_odd_wrong_tail_degree(self) -> None:
        c = _base_contract("odd")
        c["tail_degree"] = 16
        errors = _validate(c)
        assert errors

    def test_even_wrong_index_set(self) -> None:
        c = _base_contract("even")
        c["index_set"] = [1, 3, 5, 7, 9, 11]  # odd indices
        errors = _validate(c)
        assert errors

    def test_odd_wrong_index_set(self) -> None:
        c = _base_contract("odd")
        c["index_set"] = [0, 2, 4, 6, 8, 10, 12, 14]  # even indices
        errors = _validate(c)
        assert errors


class TestSchemaRejectsWrongEta:
    """eta must be frozen to 1/2."""

    def test_eta_numerator_changed(self) -> None:
        c = _base_contract()
        c["eta"]["numerator"] = 2
        errors = _validate(c)
        assert errors

    def test_eta_denominator_changed(self) -> None:
        c = _base_contract()
        c["eta"]["denominator"] = 3
        errors = _validate(c)
        assert errors


class TestSchemaRejectsWrongRadius:
    """Radius must be 7/20."""

    def test_wrong_numerator(self) -> None:
        c = _base_contract()
        c["radius"]["numerator"] = 3
        errors = _validate(c)
        assert errors

    def test_wrong_denominator(self) -> None:
        c = _base_contract()
        c["radius"]["denominator"] = 10
        errors = _validate(c)
        assert errors


class TestSchemaRejectsWrongWindow:
    def test_wrong_window(self) -> None:
        c = _base_contract()
        c["window"] = "prime_free"
        errors = _validate(c)
        assert errors


class TestSchemaRejectsMalformedDigests:
    def test_short_sha256(self) -> None:
        c = _base_contract()
        c["theorem_contract_sha256"] = "abc123"
        errors = _validate(c)
        assert errors

    def test_uppercase_sha256(self) -> None:
        c = _base_contract()
        c["theorem_contract_sha256"] = "A" * 64
        errors = _validate(c)
        assert errors


class TestValidContractPassesSchema:
    """A well-formed contract must pass schema validation."""

    def test_even_valid(self) -> None:
        c = _base_contract("even")
        errors = _validate(c)
        assert not errors, f"Valid even contract rejected: {errors}"

    def test_odd_valid(self) -> None:
        c = _base_contract("odd")
        errors = _validate(c)
        assert not errors, f"Valid odd contract rejected: {errors}"
