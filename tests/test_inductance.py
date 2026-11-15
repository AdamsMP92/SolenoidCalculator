from __future__ import annotations

import pytest
from scipy import integrate, special

from solenoid_calculator.inductance import dimensionless_radial_factor
from solenoid_calculator.models import SolenoidResult


def test_radial_factor_has_correct_zero_limit() -> None:
    nu_inner = 0.25
    nu_outer = 1.16
    assert dimensionless_radial_factor(0.0, nu_inner, nu_outer) == pytest.approx(
        nu_outer**3 - nu_inner**3
    )


@pytest.mark.parametrize("alpha", [0.1, 1.0, 10.0, 100.0])
def test_radial_factor_matches_direct_bessel_quadrature(alpha: float) -> None:
    nu_inner = 0.25
    nu_outer = 1.16
    bessel_integral, _ = integrate.quad(
        lambda nu: nu * special.j1(alpha * nu),
        nu_inner,
        nu_outer,
        epsabs=1.0e-13,
        epsrel=1.0e-13,
    )
    expected = 6.0 * bessel_integral / alpha
    assert dimensionless_radial_factor(alpha, nu_inner, nu_outer) == pytest.approx(
        expected, rel=2.0e-10, abs=1.0e-13
    )


def test_published_inductance_reference(paper_result: SolenoidResult) -> None:
    assert paper_result.inductance_h == pytest.approx(10.97e-3, rel=2e-3)
    assert paper_result.inductance_diagnostics.converged
    assert paper_result.inductance_diagnostics.last_increment_h > 0.0


def test_inductance_is_positive_and_has_no_quadrature_warnings(
    paper_result: SolenoidResult,
) -> None:
    assert paper_result.inductance_h > 0.0
    assert paper_result.inductance_diagnostics.warning_messages == ()
