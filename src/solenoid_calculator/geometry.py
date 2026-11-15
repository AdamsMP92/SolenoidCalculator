"""Simple-cubic winding geometry."""

from __future__ import annotations

import math

from .models import InputValidationError, SolenoidInputs, WindingGeometry


def _whole_turns(available_length_m: float, pitch_m: float) -> int:
    ratio = available_length_m / pitch_m
    nearest_integer = round(ratio)
    tolerance = 1.0e-12 * max(1.0, abs(ratio))
    if math.isclose(ratio, nearest_integer, rel_tol=0.0, abs_tol=tolerance):
        ratio = float(nearest_integer)
    return math.floor(ratio)


def resolve_winding_geometry(inputs: SolenoidInputs) -> WindingGeometry:
    """Fit complete turns and expose the effective occupied dimensions.

    The requested outer radius and height are treated as envelopes. The model
    uses only complete turns and therefore may produce slightly smaller
    effective dimensions.
    """

    pitch_m = 2.0 * (inputs.wire_radius_m + inputs.coating_thickness_m)
    radial_turns = _whole_turns(inputs.outer_radius_m - inputs.inner_radius_m, pitch_m)
    axial_turns = _whole_turns(inputs.height_m, pitch_m)

    if radial_turns < 1:
        raise InputValidationError(
            "The radial envelope is too small to contain one complete turn"
        )
    if axial_turns < 1:
        raise InputValidationError(
            "The axial envelope is too small to contain one complete turn"
        )

    effective_outer_radius_m = inputs.inner_radius_m + pitch_m * radial_turns
    effective_height_m = pitch_m * axial_turns
    return WindingGeometry(
        wire_pitch_m=pitch_m,
        radial_turns=radial_turns,
        axial_turns=axial_turns,
        total_turns=radial_turns * axial_turns,
        inner_radius_m=inputs.inner_radius_m,
        requested_outer_radius_m=inputs.outer_radius_m,
        effective_outer_radius_m=effective_outer_radius_m,
        requested_height_m=inputs.height_m,
        effective_height_m=effective_height_m,
    )
