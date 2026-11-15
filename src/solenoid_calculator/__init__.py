"""Public API for the Solenoid Calculator calculation core."""

from .calculator import calculate
from .field import axial_flux_density_t, central_flux_density_t
from .geometry import resolve_winding_geometry
from .inductance import calculate_inductance_h
from .models import (
    InductanceDiagnostics,
    InductanceSettings,
    InputValidationError,
    SolenoidInputs,
    SolenoidResult,
    WindingGeometry,
)

__all__ = [
    "InductanceDiagnostics",
    "InductanceSettings",
    "InputValidationError",
    "SolenoidInputs",
    "SolenoidResult",
    "WindingGeometry",
    "axial_flux_density_t",
    "calculate",
    "calculate_inductance_h",
    "central_flux_density_t",
    "resolve_winding_geometry",
]
