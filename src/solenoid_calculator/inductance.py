"""Numerical DC self-inductance of the continuum thick-solenoid model."""

from __future__ import annotations

import math
import warnings
from functools import lru_cache

from scipy import integrate, special
from scipy.integrate import IntegrationWarning

from .constants import VACUUM_PERMEABILITY_H_PER_M
from .models import (
    InductanceDiagnostics,
    InductanceSettings,
    WindingGeometry,
)

DEFAULT_INDUCTANCE_SETTINGS = InductanceSettings()


def _integral_u_j1(u: float) -> float:
    """Return the stable primitive integral from 0 to u of t J1(t) dt."""

    if u == 0.0:
        return 0.0
    if u < 0.5:
        term = u**3 / 6.0
        total = term
        for k in range(20):
            term *= -(u * u) * (2 * k + 3) / (4.0 * (2 * k + 5) * (k + 1) * (k + 2))
            total += term
            if abs(term) <= 1.0e-16 * abs(total):
                break
        return total

    integral_j0, _ = special.itj0y0(u)
    return float(integral_j0 - u * special.j0(u))


def dimensionless_radial_factor(
    alpha: float, nu_inner: float, nu_outer: float
) -> float:
    """Evaluate the radial 1F2 difference without a hypergeometric call."""

    if alpha < 0.05:
        alpha2 = alpha * alpha
        delta3 = nu_outer**3 - nu_inner**3
        delta5 = nu_outer**5 - nu_inner**5
        delta7 = nu_outer**7 - nu_inner**7
        delta9 = nu_outer**9 - nu_inner**9
        return (
            delta3
            - 3.0 * alpha2 * delta5 / 40.0
            + alpha2**2 * delta7 / 448.0
            - alpha2**3 * delta9 / 27648.0
        )

    primitive_difference = _integral_u_j1(alpha * nu_outer) - _integral_u_j1(
        alpha * nu_inner
    )
    return 6.0 * primitive_difference / alpha**3


def _positive_exponential_remainder(alpha: float) -> float:
    if alpha < 1.0e-3:
        return alpha**2 * (
            0.5 + alpha * (-1.0 / 6.0 + alpha * (1.0 / 24.0 - alpha / 120.0))
        )
    return alpha + math.expm1(-alpha)


def _g_integrand(alpha: float, nu_inner: float, nu_outer: float) -> float:
    radial_factor = dimensionless_radial_factor(alpha, nu_inner, nu_outer)
    return _positive_exponential_remainder(alpha) * radial_factor**2


@lru_cache(maxsize=128)
def calculate_inductance_h(
    geometry: WindingGeometry,
    settings: InductanceSettings = DEFAULT_INDUCTANCE_SETTINGS,
) -> tuple[float, InductanceDiagnostics]:
    """Calculate inductance and convergence diagnostics.

    The improper integral is accumulated in finite segments. Convergence is
    based on the absolute value of successive positive tail contributions,
    correcting the signed-difference check in the legacy MATLAB app.
    """

    height = geometry.effective_height_m
    radial_span = geometry.radial_span_m
    nu_inner = geometry.inner_radius_m / height
    nu_outer = geometry.effective_outer_radius_m / height
    prefactor = (
        VACUUM_PERMEABILITY_H_PER_M
        * math.pi
        * geometry.total_turns**2
        * height**3
        / (18.0 * radial_span**2)
    )

    total_g = 0.0
    total_quadrature_error_g = 0.0
    previous_cutoff = 0.0
    stable_segments = 0
    last_increment_h = float("inf")
    warning_messages: list[str] = []
    converged = False
    cutoff = settings.initial_cutoff

    for segment_index in range(settings.max_segments):
        if segment_index > 0:
            cutoff = settings.initial_cutoff + segment_index * settings.cutoff_step
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", IntegrationWarning)
            segment_g, segment_error_g = integrate.quad(
                _g_integrand,
                previous_cutoff,
                cutoff,
                args=(nu_inner, nu_outer),
                epsabs=settings.quadrature_absolute_tolerance,
                epsrel=settings.quadrature_relative_tolerance,
                limit=settings.quadrature_limit,
            )
        warning_messages.extend(str(item.message) for item in caught)
        total_g += segment_g
        total_quadrature_error_g += segment_error_g
        last_increment_h = abs(prefactor * segment_g)
        inductance_h = prefactor * total_g

        if segment_index > 0:
            tolerance_h = max(
                settings.absolute_tolerance_h,
                settings.relative_tolerance * abs(inductance_h),
            )
            if last_increment_h <= tolerance_h:
                stable_segments += 1
            else:
                stable_segments = 0
            if stable_segments >= settings.stable_segments_required:
                converged = True
                break
        previous_cutoff = cutoff

    diagnostics = InductanceDiagnostics(
        converged=converged,
        cutoff=cutoff,
        segments=segment_index + 1,
        last_increment_h=last_increment_h,
        estimated_quadrature_error_h=prefactor * total_quadrature_error_g,
        warning_messages=tuple(warning_messages),
    )
    return inductance_h, diagnostics
