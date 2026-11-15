"""Validated inputs and immutable calculation result models."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


class InputValidationError(ValueError):
    """Raised when a solenoid input cannot describe a valid model."""


def _require_finite(name: str, value: float) -> None:
    if not isfinite(value):
        raise InputValidationError(f"{name} must be finite, got {value!r}")


@dataclass(frozen=True, slots=True)
class SolenoidInputs:
    """User inputs in SI units.

    Lengths are in metres, conductivity in siemens per metre, current in
    amperes, and frequency in hertz.
    """

    wire_radius_m: float
    coating_thickness_m: float
    conductivity_s_per_m: float
    inner_radius_m: float
    outer_radius_m: float
    height_m: float
    current_a: float = 1.0
    frequency_hz: float = 0.0

    def __post_init__(self) -> None:
        for name, value in (
            ("wire_radius_m", self.wire_radius_m),
            ("coating_thickness_m", self.coating_thickness_m),
            ("conductivity_s_per_m", self.conductivity_s_per_m),
            ("inner_radius_m", self.inner_radius_m),
            ("outer_radius_m", self.outer_radius_m),
            ("height_m", self.height_m),
            ("current_a", self.current_a),
            ("frequency_hz", self.frequency_hz),
        ):
            _require_finite(name, value)

        if self.wire_radius_m <= 0.0:
            raise InputValidationError("wire_radius_m must be greater than zero")
        if self.coating_thickness_m < 0.0:
            raise InputValidationError(
                "coating_thickness_m must be greater than or equal to zero"
            )
        if self.conductivity_s_per_m <= 0.0:
            raise InputValidationError("conductivity_s_per_m must be greater than zero")
        if self.inner_radius_m <= 0.0:
            raise InputValidationError("inner_radius_m must be greater than zero")
        if self.outer_radius_m <= self.inner_radius_m:
            raise InputValidationError(
                "outer_radius_m must be greater than inner_radius_m"
            )
        if self.height_m <= 0.0:
            raise InputValidationError("height_m must be greater than zero")
        if self.frequency_hz < 0.0:
            raise InputValidationError(
                "frequency_hz must be greater than or equal to zero"
            )

    @classmethod
    def from_millimetres(
        cls,
        *,
        wire_radius_mm: float,
        coating_thickness_mm: float,
        conductivity_s_per_m: float,
        inner_radius_mm: float,
        outer_radius_mm: float,
        height_mm: float,
        current_a: float = 1.0,
        frequency_hz: float = 0.0,
    ) -> SolenoidInputs:
        """Construct inputs from the millimetre values used by the UI."""

        millimetre = 1.0e-3
        return cls(
            wire_radius_m=wire_radius_mm * millimetre,
            coating_thickness_m=coating_thickness_mm * millimetre,
            conductivity_s_per_m=conductivity_s_per_m,
            inner_radius_m=inner_radius_mm * millimetre,
            outer_radius_m=outer_radius_mm * millimetre,
            height_m=height_mm * millimetre,
            current_a=current_a,
            frequency_hz=frequency_hz,
        )


@dataclass(frozen=True, slots=True)
class WindingGeometry:
    """Discrete winding counts and their resulting effective dimensions."""

    wire_pitch_m: float
    radial_turns: int
    axial_turns: int
    total_turns: int
    inner_radius_m: float
    requested_outer_radius_m: float
    effective_outer_radius_m: float
    requested_height_m: float
    effective_height_m: float

    @property
    def radial_span_m(self) -> float:
        return self.effective_outer_radius_m - self.inner_radius_m

    @property
    def mean_winding_radius_m(self) -> float:
        return 0.5 * (self.inner_radius_m + self.effective_outer_radius_m)


@dataclass(frozen=True, slots=True)
class InductanceSettings:
    """Controls for the truncated improper integral used for inductance."""

    initial_cutoff: float = 150.0
    cutoff_step: float = 100.0
    max_segments: int = 10
    stable_segments_required: int = 2
    absolute_tolerance_h: float = 1.0e-10
    relative_tolerance: float = 1.0e-7
    quadrature_absolute_tolerance: float = 1.0e-10
    quadrature_relative_tolerance: float = 1.0e-8
    quadrature_limit: int = 400

    def __post_init__(self) -> None:
        positive_values = (
            ("initial_cutoff", self.initial_cutoff),
            ("cutoff_step", self.cutoff_step),
            ("absolute_tolerance_h", self.absolute_tolerance_h),
            ("relative_tolerance", self.relative_tolerance),
            ("quadrature_absolute_tolerance", self.quadrature_absolute_tolerance),
            ("quadrature_relative_tolerance", self.quadrature_relative_tolerance),
        )
        for name, value in positive_values:
            _require_finite(name, value)
            if value <= 0.0:
                raise InputValidationError(f"{name} must be greater than zero")
        if self.max_segments < 2:
            raise InputValidationError("max_segments must be at least two")
        if self.stable_segments_required < 1:
            raise InputValidationError("stable_segments_required must be at least one")
        if self.stable_segments_required >= self.max_segments:
            raise InputValidationError(
                "stable_segments_required must be smaller than max_segments"
            )
        if self.quadrature_limit < 50:
            raise InputValidationError("quadrature_limit must be at least 50")


@dataclass(frozen=True, slots=True)
class InductanceDiagnostics:
    """Convergence information accompanying every inductance result."""

    converged: bool
    cutoff: float
    segments: int
    last_increment_h: float
    estimated_quadrature_error_h: float
    warning_messages: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SolenoidResult:
    """Complete output of one solenoid calculation."""

    inputs: SolenoidInputs
    geometry: WindingGeometry
    current_density_a_per_m2: float
    wire_length_m: float
    resistance_ohm: float
    inductance_h: float
    impedance_ohm: complex
    central_flux_density_t: float
    inductance_diagnostics: InductanceDiagnostics

    @property
    def impedance_magnitude_ohm(self) -> float:
        return abs(self.impedance_ohm)
