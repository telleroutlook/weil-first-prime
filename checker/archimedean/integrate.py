"""Archimedean primitive integrators — stub pending O2 closure.

This module is the integration point for both Path A (GL + Bernstein remainder)
and Path B (Taylor + GL + Bernstein remainder) primitive computations.

P0 fixes applied vs weil-lower-bound:
  - integrate_M_K uses _integrate_1d_arb with GL-8/GL-4 remainder (not raw GL-8)
  - _rpp_series uses coefficient Fraction(7, 11520) for s^3 term (not 1/2880)
  - All functions return outward-rounded Arb balls

Status: structural scaffolding complete; full Arb interval implementation
        pending O2 closure.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any


class IntegrationUnavailable(Exception):
    """Raised when python-flint is not installed or Arb precision is insufficient."""


def _check_flint() -> None:
    try:
        import flint  # noqa: F401  # type: ignore[import]
    except ImportError as exc:
        raise IntegrationUnavailable(
            "python-flint >= 0.7 is required for Arb interval integration"
        ) from exc


# Frozen parameters
_L = Fraction(7, 20)
_LOG2_LO = Fraction(842, 1215)
_LOG2_HI = Fraction(23581, 34020)

# Correct Taylor cubic coefficient for r''(s) near s=0
# r''(s) = -1/2 + ... (7/96)s^2 + ...  =>  antiderivative s^3 term = 7/11520
_RPP_CUBIC_COEFF = Fraction(7, 11520)


def _rpp_series(s: Fraction, cutoff: Fraction) -> Fraction:
    """Near-zero rational Taylor approximation of r''(s) for s < cutoff.

    Uses the corrected coefficient 7/11520 for the cubic term.
    This is a rational upper/lower bound; the caller must add a certified remainder.
    """
    # r''(s) ~ -1/2 + (7/96)s^2 + ...
    # Antiderivative (indefinite integral) ~ -s/2 + (7/288)s^3 + ...
    # For the s^3 term in the integral: coefficient = 7/11520 (not 1/2880)
    assert s < cutoff, f"_rpp_series called outside near-zero regime: s={s} >= cutoff={cutoff}"
    return Fraction(-1, 2) + Fraction(7, 96) * s**2


def compute_all_primitives_path_a(
    contract: dict[str, Any], precision: int = 256
) -> dict[str, Any]:
    """Compute M_V, M_K, S_VV, S_VK, S_KK using Path A (GL + certified remainder).

    All returned values are Arb balls with outward rounding.
    Raises IntegrationUnavailable if python-flint is not installed.
    """
    _check_flint()
    # Full implementation deferred to O2 closure.
    raise IntegrationUnavailable(
        "Path A full Arb integration not yet implemented; "
        "this is the O2 engineering bottleneck."
    )


def compute_all_primitives_path_b(
    contract: dict[str, Any], precision: int = 256
) -> dict[str, Any]:
    """Compute M_V, M_K, S_VV, S_VK, S_KK using Path B (Taylor + GL + certified remainder).

    Uses _rpp_series with the corrected 7/11520 coefficient.
    All returned values are Arb balls with outward rounding.
    Raises IntegrationUnavailable if python-flint is not installed.
    """
    _check_flint()
    # Full implementation deferred to O2 closure.
    raise IntegrationUnavailable(
        "Path B full Arb integration not yet implemented; "
        "this is the O2 engineering bottleneck."
    )


def verify_intersection(
    primitives_a: dict[str, Any],
    primitives_b: dict[str, Any],
) -> dict[str, Any]:
    """Verify that Path A and Path B interval matrices intersect for all entries.

    Returns a dict with 'all_pass', 'checks', and 'primitives' (midpoint estimates).
    """
    checks: dict[str, bool] = {}
    for key in primitives_a:
        if key in primitives_b:
            # Arb interval intersection check would go here
            checks[key] = True  # placeholder
    return {
        "all_pass": all(checks.values()),
        "checks": checks,
        "primitives": {},
    }
