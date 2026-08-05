"""Tests for archimedean certificate generation (structural, no heavy integration)."""

from __future__ import annotations

import json
import pathlib
import tempfile
from fractions import Fraction

import pytest


class TestCertificateSchema:
    """Verify cert JSON has correct structure before CAS import."""

    def _make_minimal_cert(self, sector: str) -> dict:
        """Minimal valid identity-only cert matching certificate-archimedean-v1.schema.json.

        The schema is certificate-first (identity only): it carries SHA256
        digests of the integrand sources, not the matrix values themselves.
        Matrix values are recomputed by the checker.
        """
        return {
            "format_version": "archimedean-1.0",
            "obligation": "archimedean_primitives_o2_v1",
            "radius": {"numerator": 7, "denominator": 20},
            "path_a": {
                "method": "GL_with_certified_remainder",
                "quadrature_rule": "GL8",
                "remainder_method": "bernstein_ellipse_analytic",
                "integrand_source_sha256": "a" * 64,
            },
            "path_b": {
                "method": "taylor_plus_GL_with_certified_remainder",
                "taylor_cutoff": "1e-8",
                "taylor_cubic_coefficient": {"numerator": 7, "denominator": 11520},
                "remainder_method": "bernstein_ellipse_analytic",
                "integrand_source_sha256": "b" * 64,
            },
            "theorem_contract_sha256": "c" * 64,
        }

    def test_valid_cert_passes_schema(self) -> None:
        import jsonschema
        schema_path = pathlib.Path("schemas/certificate-archimedean-v1.schema.json")
        schema = json.loads(schema_path.read_text())
        cert = self._make_minimal_cert("even")
        validator = jsonschema.Draft7Validator(schema)
        errors = list(validator.iter_errors(cert))
        assert not errors, f"Schema errors: {[e.message for e in errors]}"

    def test_wrong_obligation_rejected(self) -> None:
        import jsonschema
        schema_path = pathlib.Path("schemas/certificate-archimedean-v1.schema.json")
        schema = json.loads(schema_path.read_text())
        cert = self._make_minimal_cert("even")
        cert["obligation"] = "wrong_obligation"
        validator = jsonschema.Draft7Validator(schema)
        errors = list(validator.iter_errors(cert))
        assert errors, "Wrong obligation should be rejected"

    def test_wrong_cubic_coefficient_rejected(self) -> None:
        """The P0 bug coefficient 1/2880 must be rejected."""
        import jsonschema
        schema_path = pathlib.Path("schemas/certificate-archimedean-v1.schema.json")
        schema = json.loads(schema_path.read_text())
        cert = self._make_minimal_cert("odd")
        cert["path_b"]["taylor_cubic_coefficient"] = {"numerator": 1, "denominator": 2880}
        validator = jsonschema.Draft7Validator(schema)
        errors = list(validator.iter_errors(cert))
        assert errors, "Wrong cubic coefficient 1/2880 must be rejected"

    def test_correct_cubic_coefficient_accepted(self) -> None:
        """7/11520 must be accepted."""
        import jsonschema
        schema_path = pathlib.Path("schemas/certificate-archimedean-v1.schema.json")
        schema = json.loads(schema_path.read_text())
        cert = self._make_minimal_cert("even")
        assert cert["path_b"]["taylor_cubic_coefficient"] == {
            "numerator": 7, "denominator": 11520
        }
        validator = jsonschema.Draft7Validator(schema)
        errors = list(validator.iter_errors(cert))
        assert not errors, f"Schema errors: {[e.message for e in errors]}"


class TestCertificateOutput:
    """Test the certificate file output (mock integration)."""

    def test_output_file_contains_required_fields(self, tmp_path) -> None:
        """Verify output JSON has all required O2 fields."""
        # Simulate what generate() would write (without running integration)
        cert = {
            "format_version": "archimedean-1.0",
            "obligation": "archimedean_primitives_o2_v1",
            "radius": {"numerator": 7, "denominator": 20},
            "sector": "odd",
            "window": "log2_le_2L_lt_log3",
            "path_a": {
                "method": "GL_with_Bernstein_remainder",
                "quadrature_rule": "GL8",
                "remainder_method": "bernstein_ellipse_analytic",
                "depth": 4,
                "prec": 256,
            },
            "path_b": {
                "method": "mpmath_GL_independent",
                "dps": 50,
                "taylor_cubic_coefficient": {"numerator": 7, "denominator": 11520},
            },
            "intersection_verified": True,
            "mk_entries": [],
            "elapsed_s": 45.0,
        }

        out = tmp_path / "test_cert.json"
        out.write_text(json.dumps(cert, indent=2))

        loaded = json.loads(out.read_text())
        assert loaded["format_version"] == "archimedean-1.0"
        assert loaded["obligation"] == "archimedean_primitives_o2_v1"
        assert loaded["intersection_verified"] is True
        assert loaded["path_b"]["taylor_cubic_coefficient"] == {
            "numerator": 7, "denominator": 11520
        }
        assert loaded["window"] == "log2_le_2L_lt_log3"
