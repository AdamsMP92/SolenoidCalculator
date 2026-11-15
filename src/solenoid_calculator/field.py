"""Axial magnetic flux density of the continuum thick-solenoid model."""

from __future__ import annotations

from typing import cast

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .constants import VACUUM_PERMEABILITY_H_PER_M
from .models import SolenoidInputs, WindingGeometry

type FloatArray = NDArray[np.float64]


def macroscopic_current_density_a_per_m2(
    inputs: SolenoidInputs, geometry: WindingGeometry
) -> float:
    """Return J = N I / ((r2 - r1) h) in amperes per square metre."""

    return (
        geometry.total_turns
        * inputs.current_a
        / (geometry.radial_span_m * geometry.effective_height_m)
    )


def _radial_log_primitive(
    axial_offset_m: FloatArray,
    inner_radius_m: float,
    outer_radius_m: float,
) -> FloatArray:
    outer_root = np.hypot(outer_radius_m, axial_offset_m)
    inner_root = np.hypot(inner_radius_m, axial_offset_m)
    log_ratio = np.log(outer_radius_m + outer_root) - np.log(
        inner_radius_m + inner_root
    )
    return cast(FloatArray, axial_offset_m * log_ratio)


def axial_flux_density_t(
    z_m: ArrayLike,
    inputs: SolenoidInputs,
    geometry: WindingGeometry,
) -> float | FloatArray:
    """Evaluate B_z on the symmetry axis from the Biot-Savart integral."""

    z = np.asarray(z_m, dtype=np.float64)
    half_height = 0.5 * geometry.effective_height_m
    upper_offset = z + half_height
    lower_offset = z - half_height
    current_density = macroscopic_current_density_a_per_m2(inputs, geometry)
    primitive_difference = _radial_log_primitive(
        upper_offset,
        geometry.inner_radius_m,
        geometry.effective_outer_radius_m,
    ) - _radial_log_primitive(
        lower_offset,
        geometry.inner_radius_m,
        geometry.effective_outer_radius_m,
    )
    result = 0.5 * VACUUM_PERMEABILITY_H_PER_M * current_density * primitive_difference
    if result.ndim == 0:
        return float(result)
    return result


def central_flux_density_t(inputs: SolenoidInputs, geometry: WindingGeometry) -> float:
    """Evaluate the independent closed form for B_z at z = 0."""

    height = geometry.effective_height_m
    inner = geometry.inner_radius_m
    outer = geometry.effective_outer_radius_m
    log_ratio = np.log(
        (2.0 * outer + np.hypot(height, 2.0 * outer))
        / (2.0 * inner + np.hypot(height, 2.0 * inner))
    )
    return float(
        VACUUM_PERMEABILITY_H_PER_M
        * geometry.total_turns
        * inputs.current_a
        * log_ratio
        / (2.0 * geometry.radial_span_m)
    )
