"""High-level orchestration for one complete solenoid calculation."""

from __future__ import annotations

from .electrical import (
    approximate_wire_length_m,
    dc_resistance_ohm,
    series_impedance_ohm,
)
from .field import central_flux_density_t, macroscopic_current_density_a_per_m2
from .geometry import resolve_winding_geometry
from .inductance import calculate_inductance_h
from .models import InductanceSettings, SolenoidInputs, SolenoidResult


def calculate(
    inputs: SolenoidInputs,
    settings: InductanceSettings | None = None,
) -> SolenoidResult:
    """Run the validated geometry, magnetic, and electrical model."""

    geometry = resolve_winding_geometry(inputs)
    inductance_h, diagnostics = calculate_inductance_h(
        geometry, settings or InductanceSettings()
    )
    wire_length_m = approximate_wire_length_m(inputs, geometry)
    resistance_ohm = dc_resistance_ohm(inputs, geometry)
    impedance_ohm = series_impedance_ohm(
        resistance_ohm, inductance_h, inputs.frequency_hz
    )
    return SolenoidResult(
        inputs=inputs,
        geometry=geometry,
        current_density_a_per_m2=macroscopic_current_density_a_per_m2(inputs, geometry),
        wire_length_m=wire_length_m,
        resistance_ohm=resistance_ohm,
        inductance_h=inductance_h,
        impedance_ohm=impedance_ohm,
        central_flux_density_t=central_flux_density_t(inputs, geometry),
        inductance_diagnostics=diagnostics,
    )
