from __future__ import annotations

import pytest

from solenoid_calculator.models import SolenoidResult


def test_result_keeps_requested_and_effective_geometry(
    paper_result: SolenoidResult,
) -> None:
    geometry = paper_result.geometry
    assert geometry.requested_outer_radius_m > geometry.effective_outer_radius_m
    assert geometry.requested_height_m > geometry.effective_height_m
    assert paper_result.current_density_a_per_m2 == pytest.approx(
        geometry.total_turns
        * paper_result.inputs.current_a
        / (geometry.radial_span_m * geometry.effective_height_m)
    )


def test_matlab_default_ported_baseline(
    matlab_default_result: SolenoidResult,
) -> None:
    result = matlab_default_result
    assert result.geometry.radial_turns == 6
    assert result.geometry.axial_turns == 40
    assert result.geometry.total_turns == 240
    assert result.wire_length_m == pytest.approx(22.01628131635727, rel=1e-13)
    assert result.resistance_ohm == pytest.approx(0.5005714285714286, rel=1e-13)
    assert result.inductance_h == pytest.approx(0.0006534096580775216, rel=1e-9)
    assert result.central_flux_density_t == pytest.approx(
        0.005365073460931817, rel=1e-13
    )
    assert result.impedance_magnitude_ohm == pytest.approx(
        0.5410262995518419, rel=1e-12
    )
    assert result.inductance_diagnostics.converged
