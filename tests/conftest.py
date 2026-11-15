from __future__ import annotations

import pytest

from solenoid_calculator import SolenoidInputs, calculate
from solenoid_calculator.models import SolenoidResult


@pytest.fixture(scope="session")
def paper_inputs() -> SolenoidInputs:
    return SolenoidInputs.from_millimetres(
        wire_radius_mm=0.11,
        coating_thickness_mm=0.022,
        conductivity_s_per_m=56.0e6,
        inner_radius_mm=2.5,
        outer_radius_mm=11.6,
        height_mm=10.0,
        current_a=0.01,
        frequency_hz=0.0,
    )


@pytest.fixture(scope="session")
def paper_result(paper_inputs: SolenoidInputs) -> SolenoidResult:
    return calculate(paper_inputs)


@pytest.fixture(scope="session")
def matlab_default_inputs() -> SolenoidInputs:
    return SolenoidInputs.from_millimetres(
        wire_radius_mm=0.5,
        coating_thickness_mm=0.1,
        conductivity_s_per_m=56.0e6,
        inner_radius_mm=11.0,
        outer_radius_mm=18.2,
        height_mm=48.0,
        current_a=1.0,
        frequency_hz=50.0,
    )


@pytest.fixture(scope="session")
def matlab_default_result(
    matlab_default_inputs: SolenoidInputs,
) -> SolenoidResult:
    return calculate(matlab_default_inputs)
