from __future__ import annotations

import pytest

from solenoid_calculator import InputValidationError, SolenoidInputs


def test_rejects_nonphysical_radii() -> None:
    with pytest.raises(InputValidationError, match="outer_radius_m"):
        SolenoidInputs(
            wire_radius_m=0.5e-3,
            coating_thickness_m=0.1e-3,
            conductivity_s_per_m=56e6,
            inner_radius_m=11e-3,
            outer_radius_m=10e-3,
            height_m=48e-3,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("wire_radius_m", 0.0),
        ("coating_thickness_m", -1.0e-4),
        ("conductivity_s_per_m", 0.0),
        ("height_m", 0.0),
        ("frequency_hz", -1.0),
    ],
)
def test_rejects_invalid_scalar_inputs(field: str, value: float) -> None:
    values = {
        "wire_radius_m": 0.5e-3,
        "coating_thickness_m": 0.1e-3,
        "conductivity_s_per_m": 56e6,
        "inner_radius_m": 11e-3,
        "outer_radius_m": 18.2e-3,
        "height_m": 48e-3,
        "frequency_hz": 50.0,
    }
    values[field] = value
    with pytest.raises(InputValidationError):
        SolenoidInputs(**values)


def test_signed_current_is_allowed() -> None:
    inputs = SolenoidInputs.from_millimetres(
        wire_radius_mm=0.5,
        coating_thickness_mm=0.1,
        conductivity_s_per_m=56e6,
        inner_radius_mm=11.0,
        outer_radius_mm=18.2,
        height_mm=48.0,
        current_a=-1.0,
    )
    assert inputs.current_a == -1.0
