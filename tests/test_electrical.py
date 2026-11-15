from __future__ import annotations

import math

import pytest

from solenoid_calculator.electrical import dc_resistance_ohm
from solenoid_calculator.geometry import resolve_winding_geometry
from solenoid_calculator.models import SolenoidInputs, SolenoidResult


def test_published_resistance_reference(paper_result: SolenoidResult) -> None:
    assert paper_result.wire_length_m == pytest.approx(55.2348788496, rel=1e-11)
    assert paper_result.resistance_ohm == pytest.approx(25.94, rel=5e-4)


def test_ideal_series_impedance(paper_result: SolenoidResult) -> None:
    inputs = paper_result.inputs
    expected = complex(
        paper_result.resistance_ohm,
        2.0 * math.pi * inputs.frequency_hz * paper_result.inductance_h,
    )
    assert paper_result.impedance_ohm == expected


def test_resistance_scales_inversely_with_conductivity(
    paper_inputs: SolenoidInputs,
) -> None:
    doubled = SolenoidInputs(
        wire_radius_m=paper_inputs.wire_radius_m,
        coating_thickness_m=paper_inputs.coating_thickness_m,
        conductivity_s_per_m=2.0 * paper_inputs.conductivity_s_per_m,
        inner_radius_m=paper_inputs.inner_radius_m,
        outer_radius_m=paper_inputs.outer_radius_m,
        height_m=paper_inputs.height_m,
        current_a=paper_inputs.current_a,
        frequency_hz=paper_inputs.frequency_hz,
    )
    geometry = resolve_winding_geometry(paper_inputs)
    original = dc_resistance_ohm(paper_inputs, geometry)
    assert dc_resistance_ohm(doubled, geometry) == pytest.approx(0.5 * original)
