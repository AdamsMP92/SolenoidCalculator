"""Wire length, resistance, and ideal low-frequency impedance."""

from __future__ import annotations

import math

from .models import SolenoidInputs, WindingGeometry


def approximate_wire_length_m(
    inputs: SolenoidInputs, geometry: WindingGeometry
) -> float:
    """Return the simple-cubic winding estimate of conductor length."""

    layer_step_m = inputs.wire_radius_m + inputs.coating_thickness_m
    return (
        2.0
        * math.pi
        * geometry.total_turns
        * (inputs.inner_radius_m + geometry.radial_turns * layer_step_m)
    )


def dc_resistance_ohm(inputs: SolenoidInputs, geometry: WindingGeometry) -> float:
    """Return conductor resistance using R = length / (conductivity * area)."""

    conductor_area_m2 = math.pi * inputs.wire_radius_m**2
    return approximate_wire_length_m(inputs, geometry) / (
        inputs.conductivity_s_per_m * conductor_area_m2
    )


def series_impedance_ohm(
    resistance_ohm: float, inductance_h: float, frequency_hz: float
) -> complex:
    """Return the ideal series impedance R + i 2 pi f L."""

    return complex(resistance_ohm, 2.0 * math.pi * frequency_hz * inductance_h)
