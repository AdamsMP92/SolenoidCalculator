"""Shiny web interface for the Solenoid Calculator."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from shiny import App, Inputs, Outputs, Session, reactive, render, req, ui

from solenoid_calculator import (
    InputValidationError,
    SolenoidInputs,
    SolenoidResult,
    axial_flux_density_t,
    calculate,
)

APP_DIR = Path(__file__).parent

PRESETS = {
    "matlab": {
        "wire_radius": 0.5,
        "coating_thickness": 0.1,
        "conductivity": 56.0,
        "inner_radius": 11.0,
        "outer_radius": 18.2,
        "height": 48.0,
        "current": 1.0,
        "frequency": 50.0,
    },
    "versuch38": {
        "wire_radius": 0.11,
        "coating_thickness": 0.022,
        "conductivity": 56.0,
        "inner_radius": 2.5,
        "outer_radius": 11.6,
        "height": 10.0,
        "current": 0.01,
        "frequency": 0.0,
    },
}


def _field(
    input_id: str,
    label: str,
    value: float,
    *,
    minimum: float,
    step: float,
    note: str,
) -> ui.Tag:
    return ui.div(
        ui.input_numeric(
            input_id,
            label,
            value,
            min=minimum,
            step=step,
            update_on="change",
        ),
        ui.tags.small(note, class_="field-note"),
        class_="field-block",
    )


def _metric_card(
    label: str,
    value: str,
    unit: str,
    detail: str,
    *,
    accent: str = "teal",
) -> ui.Tag:
    return ui.div(
        ui.div(
            ui.tags.span(label, class_="metric-label"),
            ui.tags.span(class_=f"metric-dot metric-dot-{accent}"),
            class_="metric-heading",
        ),
        ui.div(
            ui.tags.span(value, class_="metric-value"),
            ui.tags.span(unit, class_="metric-unit"),
            class_="metric-number",
        ),
        ui.tags.p(detail, class_="metric-detail"),
        class_=f"metric-card metric-card-{accent}",
    )


def _status_item(label: str, value: str) -> ui.Tag:
    return ui.div(
        ui.tags.dt(label),
        ui.tags.dd(value),
        class_="status-item",
    )


def _geometry_diagram(result: SolenoidResult) -> str:
    geometry = result.geometry
    requested_span = geometry.requested_outer_radius_m - geometry.inner_radius_m
    radial_fraction = geometry.radial_span_m / requested_span
    axial_fraction = geometry.effective_height_m / geometry.requested_height_m

    envelope_x = 92.0
    envelope_y = 34.0
    envelope_width = 360.0
    envelope_height = 188.0
    effective_width = envelope_width * radial_fraction
    effective_height = envelope_height * axial_fraction
    effective_y = envelope_y + 0.5 * (envelope_height - effective_height)

    visible_radial = min(geometry.radial_turns, 12)
    visible_axial = min(geometry.axial_turns, 18)
    radius = min(
        7.0,
        0.36 * effective_width / max(visible_radial, 1),
        0.36 * effective_height / max(visible_axial, 1),
    )
    circles: list[str] = []
    for radial_index in range(visible_radial):
        x = envelope_x + (radial_index + 0.5) * effective_width / visible_radial
        for axial_index in range(visible_axial):
            y = effective_y + (axial_index + 0.5) * effective_height / visible_axial
            circles.append(
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{radius:.2f}" '
                'fill="#d68a42" stroke="#9a4f20" stroke-width="1.2"/>'
            )

    sampling_note = ""
    if visible_radial != geometry.radial_turns or visible_axial != geometry.axial_turns:
        sampling_note = " · representative turns shown"

    return f"""
    <svg class="coil-svg" viewBox="0 0 520 280" role="img"
         aria-label="Schematic cross-section of the calculated winding">
      <defs>
        <linearGradient id="coilFill" x1="0" x2="1">
          <stop offset="0%" stop-color="#d9eff0" stop-opacity="0.85"/>
          <stop offset="100%" stop-color="#eef4ff" stop-opacity="0.9"/>
        </linearGradient>
      </defs>
      <text x="18" y="23" class="svg-axis-label">coil axis</text>
      <line x1="24" y1="128" x2="72" y2="128"
            stroke="#667085" stroke-width="2"/>
      <path d="M65 122 L73 128 L65 134" fill="none"
            stroke="#667085" stroke-width="2"/>
      <line x1="{envelope_x:.1f}" y1="24" x2="{envelope_x:.1f}" y2="234"
            stroke="#172033" stroke-width="5"/>
      <rect x="{envelope_x:.1f}" y="{envelope_y:.1f}"
            width="{envelope_width:.1f}" height="{envelope_height:.1f}"
            rx="8" fill="none" stroke="#9ca9ba" stroke-width="2"
            stroke-dasharray="7 6"/>
      <rect x="{envelope_x:.1f}" y="{effective_y:.1f}"
            width="{effective_width:.1f}" height="{effective_height:.1f}"
            rx="7" fill="url(#coilFill)" stroke="#136f7a" stroke-width="2.5"/>
      {"".join(circles)}
      <text x="{envelope_x + envelope_width / 2:.1f}" y="258"
            text-anchor="middle" class="svg-caption">
        {geometry.radial_turns} radial × {geometry.axial_turns} axial turns
        {sampling_note}
      </text>
      <g transform="translate(338,16)">
        <line x1="0" y1="0" x2="24" y2="0" stroke="#9ca9ba"
              stroke-width="2" stroke-dasharray="6 5"/>
        <text x="31" y="4" class="svg-legend">requested envelope</text>
      </g>
      <g transform="translate(338,34)">
        <line x1="0" y1="0" x2="24" y2="0" stroke="#136f7a"
              stroke-width="3"/>
        <text x="31" y="4" class="svg-legend">occupied winding</text>
      </g>
    </svg>
    """


def _field_profile_chart(result: SolenoidResult) -> str:
    """Render the axial field profile as a dependency-free responsive SVG."""
    geometry = result.geometry
    height_m = geometry.effective_height_m
    z_m = np.linspace(-1.35 * height_m, 1.35 * height_m, 401)
    field_mt = (
        np.asarray(
            axial_flux_density_t(z_m, result.inputs, geometry),
            dtype=float,
        )
        * 1.0e3
    )
    z_mm = z_m * 1.0e3

    width = 760.0
    height = 410.0
    margin_left = 74.0
    margin_right = 28.0
    margin_top = 38.0
    margin_bottom = 64.0
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom

    x_min = float(z_mm[0])
    x_max = float(z_mm[-1])
    raw_y_min = min(0.0, float(np.min(field_mt)))
    raw_y_max = max(0.0, float(np.max(field_mt)))
    if raw_y_min == raw_y_max:
        y_min, y_max = -0.001, 0.001
    elif raw_y_min >= 0.0:
        y_min, y_max = 0.0, raw_y_max * 1.14
    elif raw_y_max <= 0.0:
        y_min, y_max = raw_y_min * 1.14, 0.0
    else:
        padding = 0.08 * (raw_y_max - raw_y_min)
        y_min, y_max = raw_y_min - padding, raw_y_max + padding

    def map_x(value: float) -> float:
        return margin_left + (value - x_min) / (x_max - x_min) * plot_width

    def map_y(value: float) -> float:
        return margin_top + (y_max - value) / (y_max - y_min) * plot_height

    line_points = [
        (map_x(float(x_value)), map_y(float(y_value)))
        for x_value, y_value in zip(z_mm, field_mt, strict=True)
    ]
    line_path = " ".join(
        f"{'M' if index == 0 else 'L'} {x_value:.2f} {y_value:.2f}"
        for index, (x_value, y_value) in enumerate(line_points)
    )
    zero_y = map_y(0.0)
    area_path = (
        f"M {line_points[0][0]:.2f} {zero_y:.2f} "
        f"L {line_points[0][0]:.2f} {line_points[0][1]:.2f} "
        + " ".join(
            f"L {x_value:.2f} {y_value:.2f}" for x_value, y_value in line_points[1:]
        )
        + f" L {line_points[-1][0]:.2f} {zero_y:.2f} Z"
    )

    x_grid: list[str] = []
    for tick in np.linspace(x_min, x_max, 7):
        x_position = map_x(float(tick))
        x_grid.append(
            f'<line x1="{x_position:.2f}" y1="{margin_top:.2f}" '
            f'x2="{x_position:.2f}" y2="{margin_top + plot_height:.2f}" '
            'class="field-grid-line"/>'
            f'<text x="{x_position:.2f}" y="{height - 34:.2f}" '
            f'text-anchor="middle" class="field-tick">{tick:.3g}</text>'
        )

    y_grid: list[str] = []
    for tick in np.linspace(y_min, y_max, 5):
        y_position = map_y(float(tick))
        y_grid.append(
            f'<line x1="{margin_left:.2f}" y1="{y_position:.2f}" '
            f'x2="{margin_left + plot_width:.2f}" y2="{y_position:.2f}" '
            'class="field-grid-line"/>'
            f'<text x="{margin_left - 12:.2f}" y="{y_position + 4:.2f}" '
            f'text-anchor="end" class="field-tick">{tick:.3g}</text>'
        )

    half_height_mm = 0.5 * height_m * 1.0e3
    coil_x = map_x(-half_height_mm)
    coil_width = map_x(half_height_mm) - coil_x
    centre_index = len(field_mt) // 2
    centre_x = map_x(0.0)
    centre_y = map_y(float(field_mt[centre_index]))

    return f"""
    <svg class="field-profile-svg" viewBox="0 0 {width:.0f} {height:.0f}"
         role="img" aria-labelledby="field-profile-title field-profile-description">
      <title id="field-profile-title">Axial magnetic flux density profile</title>
      <desc id="field-profile-description">
        Magnetic flux density B z in millitesla along the solenoid axis in
        millimetres. The shaded vertical region marks the occupied coil span.
      </desc>
      <rect x="{coil_x:.2f}" y="{margin_top:.2f}" width="{coil_width:.2f}"
            height="{plot_height:.2f}" class="field-coil-span"/>
      {"".join(x_grid)}
      {"".join(y_grid)}
      <line x1="{margin_left:.2f}" y1="{zero_y:.2f}"
            x2="{margin_left + plot_width:.2f}" y2="{zero_y:.2f}"
            class="field-zero-line"/>
      <line x1="{coil_x:.2f}" y1="{margin_top:.2f}"
            x2="{coil_x:.2f}" y2="{margin_top + plot_height:.2f}"
            class="field-coil-edge"/>
      <line x1="{coil_x + coil_width:.2f}" y1="{margin_top:.2f}"
            x2="{coil_x + coil_width:.2f}" y2="{margin_top + plot_height:.2f}"
            class="field-coil-edge"/>
      <path d="{area_path}" class="field-area"/>
      <path d="{line_path}" class="field-line"/>
      <circle cx="{centre_x:.2f}" cy="{centre_y:.2f}" r="4.5"
              class="field-centre-point"/>
      <text x="{margin_left + plot_width / 2:.2f}" y="{height - 7:.2f}"
            text-anchor="middle" class="field-axis-label">
        Axial position z [mm]
      </text>
      <text x="18" y="{margin_top + plot_height / 2:.2f}"
            text-anchor="middle" class="field-axis-label"
            transform="rotate(-90 18 {margin_top + plot_height / 2:.2f})">
        Bz [mT]
      </text>
      <text x="{margin_left + plot_width / 2:.2f}" y="{margin_top + 18:.2f}"
            text-anchor="middle" class="field-span-label">coil span</text>
    </svg>
    """


def _equation(content: str, caption: str) -> ui.Tag:
    return ui.div(
        ui.HTML(content),
        ui.tags.p(caption),
        class_="equation-card",
    )


input_panel = ui.div(
    ui.div(
        ui.tags.span("INPUTS", class_="eyebrow"),
        ui.h2("Define the coil"),
        ui.tags.p(
            "Choose a reference setup or enter your own dimensions.",
            class_="panel-intro",
        ),
        class_="panel-heading",
    ),
    ui.div(
        ui.input_select(
            "preset",
            "Load a preset",
            {
                "matlab": "MATLAB app defaults",
                "versuch38": "Versuch 38 reference",
            },
            selected="matlab",
        ),
        ui.tags.small(
            "Presets update the fields below. Press calculate to apply.",
            class_="field-note",
        ),
        class_="preset-block",
    ),
    ui.div(
        ui.tags.span("01", class_="section-index"),
        ui.tags.span("Wire", class_="section-label"),
        class_="input-section-title",
    ),
    ui.div(
        _field(
            "wire_radius",
            "Copper radius r [mm]",
            0.5,
            minimum=0.001,
            step=0.01,
            note="Bare conductor radius",
        ),
        _field(
            "coating_thickness",
            "Coating c [mm]",
            0.1,
            minimum=0.0,
            step=0.01,
            note="Radial insulation thickness",
        ),
        class_="input-pair",
    ),
    _field(
        "conductivity",
        "Conductivity κ [MS/m]",
        56.0,
        minimum=0.001,
        step=0.1,
        note="56 MS/m is representative for copper",
    ),
    ui.div(
        ui.tags.span("02", class_="section-index"),
        ui.tags.span("Geometry", class_="section-label"),
        class_="input-section-title",
    ),
    _field(
        "inner_radius",
        "Inner radius r₁ [mm]",
        11.0,
        minimum=0.001,
        step=0.1,
        note="Distance from the axis to the winding",
    ),
    ui.div(
        _field(
            "outer_radius",
            "Outer radius r₂ [mm]",
            18.2,
            minimum=0.001,
            step=0.1,
            note="Requested radial envelope",
        ),
        _field(
            "height",
            "Height h [mm]",
            48.0,
            minimum=0.001,
            step=0.1,
            note="Requested axial envelope",
        ),
        class_="input-pair",
    ),
    ui.div(
        ui.tags.span("03", class_="section-index"),
        ui.tags.span("Operating point", class_="section-label"),
        class_="input-section-title",
    ),
    ui.div(
        _field(
            "current",
            "Current I [A]",
            1.0,
            minimum=-1.0e6,
            step=0.1,
            note="Sign controls field direction",
        ),
        _field(
            "frequency",
            "Frequency f [Hz]",
            50.0,
            minimum=0.0,
            step=1.0,
            note="Used for ideal R–L impedance",
        ),
        class_="input-pair",
    ),
    ui.input_action_button(
        "calculate",
        "Calculate solenoid",
        class_="btn-calculate",
    ),
    ui.div(
        ui.tags.span(class_="privacy-pulse"),
        ui.tags.span("All calculations run locally in your browser."),
        class_="privacy-note",
    ),
    class_="input-panel",
)


calculator_panel = ui.div(
    ui.div(input_panel, class_="calculator-sidebar"),
    ui.tags.main(
        ui.output_ui("calculation_message"),
        ui.output_ui("summary_cards"),
        ui.div(
            ui.div(
                ui.div(
                    ui.div(
                        ui.tags.span("FIELD PROFILE", class_="eyebrow"),
                        ui.h3("Axial magnetic flux density"),
                        class_="card-title-group",
                    ),
                    ui.tags.span("Biot–Savart", class_="method-chip"),
                    class_="visual-card-header",
                ),
                ui.output_ui("field_plot"),
                class_="visual-card field-card",
            ),
            ui.div(
                ui.div(
                    ui.tags.span("WINDING", class_="eyebrow"),
                    ui.h3("Discrete packing"),
                    class_="card-title-group",
                ),
                ui.output_ui("geometry_diagram"),
                ui.output_ui("geometry_table"),
                class_="visual-card geometry-card",
            ),
            class_="visual-grid",
        ),
        ui.div(
            ui.div(
                ui.tags.span("NUMERICS", class_="eyebrow"),
                ui.h3("Convergence diagnostics"),
                ui.output_ui("diagnostics"),
                class_="diagnostics-card",
            ),
            ui.div(
                ui.tags.span("MODEL BOUNDARY", class_="eyebrow"),
                ui.h3("What this result means"),
                ui.tags.p(
                    "The impedance is the ideal low-frequency series model. "
                    "Skin effect, proximity effect, parasitic capacitance, "
                    "leads, and magnetic materials are not included."
                ),
                ui.tags.p(
                    "Requested dimensions are treated as an envelope; only "
                    "complete turns enter the magnetic model."
                ),
                class_="assumption-card",
            ),
            class_="support-grid",
        ),
        class_="calculator-results",
    ),
    class_="calculator-grid",
)


documentation_panel = ui.tags.article(
    ui.div(
        ui.tags.span("MODEL & METHOD", class_="eyebrow"),
        ui.h2("From winding geometry to field and impedance"),
        ui.tags.p(
            "The calculator combines a discrete simple-cubic winding model "
            "with a continuum current-density model for a thick cylindrical "
            "solenoid.",
            class_="docs-lead",
        ),
        class_="docs-intro",
    ),
    ui.div(
        ui.tags.section(
            ui.tags.span("01", class_="docs-number"),
            ui.h3("Winding geometry"),
            ui.tags.p(
                "For conductor radius r and coating thickness c, the wire "
                "pitch is p = 2(r + c). Complete radial and axial turns are "
                "fitted inside the requested envelope."
            ),
            _equation(
                (
                    "<strong>N<sub>ρ</sub></strong> = "
                    "⌊(r<sub>2</sub> − r<sub>1</sub>) / 2(r + c)⌋"
                    "<br><strong>N<sub>z</sub></strong> = "
                    "⌊h / 2(r + c)⌋"
                ),
                "The total winding number is N = Nρ Nz.",
            ),
            class_="docs-section",
        ),
        ui.tags.section(
            ui.tags.span("02", class_="docs-number"),
            ui.h3("Continuum current source"),
            ui.tags.p(
                "The individual turns are represented by a homogeneous "
                "azimuthal current density over the occupied coil "
                "cross-section."
            ),
            _equation(
                ("<strong>J</strong> = N I / [(r<sub>2</sub> − r<sub>1</sub>) h]"),
                "J is a volume-current density measured in A/m².",
            ),
            class_="docs-section",
        ),
        ui.tags.section(
            ui.tags.span("03", class_="docs-number"),
            ui.h3("Axial field"),
            ui.tags.p(
                "The field curve is evaluated directly from the reduced "
                "Biot–Savart integral. At the centre it agrees with the "
                "independent closed expression below."
            ),
            _equation(
                (
                    "<strong>B<sub>z</sub>(0)</strong> = "
                    "μ<sub>0</sub> N I / [2(r<sub>2</sub> − r<sub>1</sub>)] "
                    "ln[(2r<sub>2</sub> + √(h² + 4r<sub>2</sub>²)) / "
                    "(2r<sub>1</sub> + √(h² + 4r<sub>1</sub>²))]"
                ),
                "No H-field decomposition is required for this calculation.",
            ),
            class_="docs-section",
        ),
        ui.tags.section(
            ui.tags.span("04", class_="docs-number"),
            ui.h3("Inductance and resistance"),
            ui.tags.p(
                "The DC self-inductance follows from the magnetostatic energy "
                "in Fourier space. The remaining improper integral is "
                "evaluated in finite tail segments with explicit convergence "
                "diagnostics."
            ),
            _equation(
                (
                    "<strong>L</strong> = μ<sub>0</sub> π N² h³ / "
                    "[18(r<sub>2</sub> − r<sub>1</sub>)²] "
                    "G(r<sub>1</sub>/h, r<sub>2</sub>/h)"
                    "<br><strong>R<sub>0</sub></strong> = ℓ / (κ π r²)"
                ),
                "The displayed AC impedance is Z = R₀ + i 2πfL.",
            ),
            class_="docs-section",
        ),
        class_="docs-grid",
    ),
    ui.div(
        ui.div(
            ui.tags.span("REFERENCE CHECK", class_="eyebrow"),
            ui.h3("Versuch 38"),
            ui.tags.p(
                "The published example specifies 1,258 turns and reports "
                "R₀ = 25.94 Ω and L = 10.97 mH."
            ),
            ui.div(
                ui.div(
                    ui.tags.span("Python"),
                    ui.tags.strong("25.947178 Ω"),
                    ui.tags.small("DC resistance"),
                ),
                ui.div(
                    ui.tags.span("Python"),
                    ui.tags.strong("10.973427 mH"),
                    ui.tags.small("DC inductance"),
                ),
                class_="reference-values",
            ),
            class_="reference-card",
        ),
        ui.div(
            ui.tags.span("OPEN SOURCE", class_="eyebrow"),
            ui.h3("Inspect the implementation"),
            ui.tags.p(
                "The equations, numerical choices, tests, and reference "
                "values are documented alongside the source code."
            ),
            ui.tags.a(
                "View the GitHub repository",
                href="https://github.com/AdamsMP92/SolenoidCalculator",
                target="_blank",
                rel="noopener noreferrer",
                class_="docs-link",
            ),
            class_="source-card",
        ),
        class_="docs-footer-grid",
    ),
    class_="documentation-panel",
)


app_ui = ui.page_bootstrap(
    ui.head_content(
        ui.tags.meta(
            name="description",
            content=(
                "Interactive scientific calculator for thick cylindrical solenoids."
            ),
        ),
        ui.tags.link(rel="icon", type="image/svg+xml", href="magnet.svg"),
        ui.tags.link(
            rel="preconnect",
            href="https://fonts.googleapis.com",
        ),
        ui.tags.link(
            rel="preconnect",
            href="https://fonts.gstatic.com",
            crossorigin="anonymous",
        ),
        ui.tags.link(
            rel="stylesheet",
            href=(
                "https://fonts.googleapis.com/css2?"
                "family=DM+Sans:wght@400;500;600;700&"
                "family=Newsreader:opsz,wght@6..72,600&display=swap"
            ),
        ),
    ),
    ui.include_css(APP_DIR / "www" / "styles.css"),
    ui.div(
        ui.div(
            ui.tags.header(
                ui.div(
                    ui.div(
                        ui.img(
                            src="magnet.svg",
                            alt="Red horseshoe magnet",
                            class_="hero-mark",
                        ),
                        ui.div(
                            ui.tags.span(
                                "MICHAEL P. ADAMS · SCIENTIFIC SOFTWARE",
                                class_="hero-kicker",
                            ),
                            ui.h1("Solenoid Calculator"),
                            ui.tags.p(
                                "Explore winding geometry, DC self-inductance, "
                                "resistance, impedance, and the axial magnetic "
                                "field in one transparent model."
                            ),
                        ),
                        class_="hero-copy",
                    ),
                    ui.div(
                        ui.tags.span(class_="runtime-dot"),
                        ui.div(
                            ui.tags.strong("Browser-native Python"),
                            ui.tags.small("Shinylive · no calculation server"),
                        ),
                        class_="runtime-badge",
                    ),
                    class_="hero-inner",
                ),
                class_="app-hero",
            ),
            ui.div(
                ui.navset_card_underline(
                    ui.nav_panel(
                        "Calculator",
                        calculator_panel,
                        value="calculator",
                    ),
                    ui.nav_panel(
                        "Model & documentation",
                        documentation_panel,
                        value="documentation",
                    ),
                    id="main_navigation",
                    selected="calculator",
                ),
                class_="main-nav-wrap",
            ),
            ui.tags.footer(
                ui.tags.span("Solenoid Calculator"),
                ui.tags.span("·"),
                ui.tags.span("Michael P. Adams"),
                ui.tags.span("·"),
                ui.tags.a(
                    "Source code",
                    href="https://github.com/AdamsMP92/SolenoidCalculator",
                    target="_blank",
                    rel="noopener noreferrer",
                ),
                class_="app-footer",
            ),
            class_="app-shell",
        ),
        class_="container-fluid app-page",
    ),
    title="Solenoid Calculator",
    lang="en",
)


def server(input: Inputs, output: Outputs, session: Session) -> None:
    @reactive.effect
    @reactive.event(input.preset)
    def _apply_preset() -> None:
        values = PRESETS[str(input.preset())]
        for input_id, value in values.items():
            ui.update_numeric(input_id, value=value)

    def _collect_inputs() -> SolenoidInputs:
        return SolenoidInputs.from_millimetres(
            wire_radius_mm=float(input.wire_radius()),
            coating_thickness_mm=float(input.coating_thickness()),
            conductivity_s_per_m=float(input.conductivity()) * 1.0e6,
            inner_radius_mm=float(input.inner_radius()),
            outer_radius_mm=float(input.outer_radius()),
            height_mm=float(input.height()),
            current_a=float(input.current()),
            frequency_hz=float(input.frequency()),
        )

    @reactive.calc
    @reactive.event(input.calculate, ignore_none=False)
    def calculation() -> tuple[SolenoidResult | None, str | None]:
        try:
            with ui.Progress(min=0, max=1) as progress:
                progress.set(
                    0.12,
                    message="Calculating solenoid",
                    detail="Resolving complete winding turns…",
                )
                result = calculate(_collect_inputs())
                progress.set(
                    1,
                    message="Calculation complete",
                    detail="Field and impedance are ready.",
                )
            return result, None
        except (InputValidationError, ArithmeticError, ValueError) as exc:
            return None, str(exc)
        except Exception as exc:
            return None, f"Numerical calculation failed: {exc}"

    def _result() -> SolenoidResult:
        result, _ = calculation()
        req(result is not None)
        assert result is not None
        return result

    @output
    @render.ui
    def calculation_message() -> ui.Tag | None:
        result, error = calculation()
        if error is not None:
            return ui.div(
                ui.tags.strong("Check the coil definition."),
                ui.tags.span(error),
                class_="calculation-message message-error",
            )
        req(result is not None)
        assert result is not None
        geometry = result.geometry
        radial_delta_mm = (
            geometry.requested_outer_radius_m - geometry.effective_outer_radius_m
        ) * 1.0e3
        axial_delta_mm = (
            geometry.requested_height_m - geometry.effective_height_m
        ) * 1.0e3
        if radial_delta_mm > 1.0e-9 or axial_delta_mm > 1.0e-9:
            return ui.div(
                ui.tags.strong("Envelope fitted to complete turns."),
                ui.tags.span(
                    f"Unused radial allowance: {radial_delta_mm:.3f} mm · "
                    f"unused axial allowance: {axial_delta_mm:.3f} mm"
                ),
                class_="calculation-message message-info",
            )
        return ui.div(
            ui.tags.strong("Exact turn fit."),
            ui.tags.span(
                "The requested outer radius and height are completely occupied."
            ),
            class_="calculation-message message-success",
        )

    @output
    @render.ui
    def summary_cards() -> ui.Tag:
        result = _result()
        geometry = result.geometry
        return ui.div(
            _metric_card(
                "Total turns",
                f"{geometry.total_turns:,}",
                "",
                f"{geometry.radial_turns} radial × {geometry.axial_turns} axial",
                accent="indigo",
            ),
            _metric_card(
                "DC inductance",
                f"{result.inductance_h * 1.0e3:.6g}",
                "mH",
                "Magnetostatic energy model",
            ),
            _metric_card(
                "DC resistance",
                f"{result.resistance_ohm:.6g}",
                "Ω",
                f"{result.wire_length_m:.4g} m estimated wire",
                accent="copper",
            ),
            _metric_card(
                "Impedance magnitude",
                f"{result.impedance_magnitude_ohm:.6g}",
                "Ω",
                f"ideal series model at {result.inputs.frequency_hz:g} Hz",
                accent="indigo",
            ),
            _metric_card(
                "Central field",
                f"{result.central_flux_density_t * 1.0e3:.6g}",
                "mT",
                f"at {result.inputs.current_a:g} A",
            ),
            _metric_card(
                "Current density",
                f"{result.current_density_a_per_m2 / 1.0e6:.6g}",
                "MA/m²",
                "continuum winding model",
                accent="copper",
            ),
            class_="metrics-grid",
        )

    @output
    @render.ui
    def field_plot() -> ui.HTML:
        return ui.HTML(_field_profile_chart(_result()))

    @output
    @render.ui
    def geometry_diagram() -> ui.HTML:
        return ui.HTML(_geometry_diagram(_result()))

    @output
    @render.ui
    def geometry_table() -> ui.Tag:
        geometry = _result().geometry

        def row(label: str, requested: float, effective: float) -> ui.Tag:
            return ui.tags.tr(
                ui.tags.th(label),
                ui.tags.td(f"{requested * 1.0e3:.4g} mm"),
                ui.tags.td(f"{effective * 1.0e3:.4g} mm"),
            )

        return ui.tags.table(
            ui.tags.thead(
                ui.tags.tr(
                    ui.tags.th("Dimension"),
                    ui.tags.th("Requested"),
                    ui.tags.th("Occupied"),
                )
            ),
            ui.tags.tbody(
                row(
                    "Outer radius",
                    geometry.requested_outer_radius_m,
                    geometry.effective_outer_radius_m,
                ),
                row(
                    "Height",
                    geometry.requested_height_m,
                    geometry.effective_height_m,
                ),
            ),
            class_="geometry-table",
        )

    @output
    @render.ui
    def diagnostics() -> ui.Tag:
        diagnostic = _result().inductance_diagnostics
        status_label = "Converged" if diagnostic.converged else "Check result"
        status_class = "status-ok" if diagnostic.converged else "status-warning"
        warning_note: ui.Tag | None = None
        if diagnostic.warning_messages:
            warning_note = ui.tags.p(
                " · ".join(diagnostic.warning_messages),
                class_="diagnostic-warning",
            )
        return ui.div(
            ui.div(
                ui.tags.span(class_=f"status-light {status_class}"),
                ui.tags.strong(status_label),
                class_="status-line",
            ),
            ui.tags.dl(
                _status_item("Integration cutoff", f"{diagnostic.cutoff:g}"),
                _status_item("Tail segments", str(diagnostic.segments)),
                _status_item(
                    "Last contribution",
                    f"{diagnostic.last_increment_h * 1.0e9:.4g} nH",
                ),
                _status_item(
                    "Quadrature estimate",
                    f"{diagnostic.estimated_quadrature_error_h * 1.0e9:.4g} nH",
                ),
                class_="status-grid",
            ),
            warning_note,
        )


app = App(
    app_ui,
    server,
    static_assets=APP_DIR / "www",
)
