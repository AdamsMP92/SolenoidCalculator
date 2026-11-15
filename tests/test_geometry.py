from __future__ import annotations

import pytest

from solenoid_calculator import (
    InputValidationError,
    SolenoidInputs,
    resolve_winding_geometry,
)


def test_matlab_default_winding_counts() -> None:
    inputs = SolenoidInputs.from_millimetres(
        wire_radius_mm=0.5,
        coating_thickness_mm=0.1,
        conductivity_s_per_m=56e6,
        inner_radius_mm=11.0,
        outer_radius_mm=18.2,
        height_mm=48.0,
    )
    geometry = resolve_winding_geometry(inputs)
    assert geometry.radial_turns == 6
    assert geometry.axial_turns == 40
    assert geometry.total_turns == 240
    assert geometry.effective_outer_radius_m == pytest.approx(18.2e-3)
    assert geometry.effective_height_m == pytest.approx(48.0e-3)


def test_reference_case_exposes_effective_dimensions(
    paper_inputs: SolenoidInputs,
) -> None:
    geometry = resolve_winding_geometry(paper_inputs)
    assert geometry.radial_turns == 34
    assert geometry.axial_turns == 37
    assert geometry.total_turns == 1258
    assert geometry.effective_outer_radius_m == pytest.approx(11.476e-3)
    assert geometry.effective_height_m == pytest.approx(9.768e-3)
    assert geometry.requested_outer_radius_m == pytest.approx(11.6e-3)
    assert geometry.requested_height_m == pytest.approx(10.0e-3)


def test_rejects_envelope_without_a_complete_turn() -> None:
    inputs = SolenoidInputs.from_millimetres(
        wire_radius_mm=1.0,
        coating_thickness_mm=0.1,
        conductivity_s_per_m=56e6,
        inner_radius_mm=10.0,
        outer_radius_mm=11.0,
        height_mm=10.0,
    )
    with pytest.raises(InputValidationError, match="radial envelope"):
        resolve_winding_geometry(inputs)
