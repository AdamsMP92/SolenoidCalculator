from __future__ import annotations

import numpy as np
import pytest

from solenoid_calculator import (
    SolenoidInputs,
    axial_flux_density_t,
    central_flux_density_t,
    resolve_winding_geometry,
)


def test_axis_field_is_even_and_matches_central_formula(
    paper_inputs: SolenoidInputs,
) -> None:
    geometry = resolve_winding_geometry(paper_inputs)
    extent = 2.0 * geometry.effective_height_m
    z = np.linspace(-extent, extent, 101)
    field = axial_flux_density_t(z, paper_inputs, geometry)
    assert isinstance(field, np.ndarray)
    np.testing.assert_allclose(field, field[::-1], rtol=2e-13, atol=1e-15)
    assert axial_flux_density_t(0.0, paper_inputs, geometry) == pytest.approx(
        central_flux_density_t(paper_inputs, geometry), rel=2e-14
    )


def test_axis_field_changes_sign_with_current(
    paper_inputs: SolenoidInputs,
) -> None:
    geometry = resolve_winding_geometry(paper_inputs)
    reversed_inputs = SolenoidInputs(
        wire_radius_m=paper_inputs.wire_radius_m,
        coating_thickness_m=paper_inputs.coating_thickness_m,
        conductivity_s_per_m=paper_inputs.conductivity_s_per_m,
        inner_radius_m=paper_inputs.inner_radius_m,
        outer_radius_m=paper_inputs.outer_radius_m,
        height_m=paper_inputs.height_m,
        current_a=-paper_inputs.current_a,
        frequency_hz=paper_inputs.frequency_hz,
    )
    assert axial_flux_density_t(0.0, reversed_inputs, geometry) == pytest.approx(
        -axial_flux_density_t(0.0, paper_inputs, geometry)
    )
