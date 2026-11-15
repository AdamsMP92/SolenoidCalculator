from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest
from shiny import App

from app import (
    PRESETS,
    _field_profile_chart,
    _geometry_diagram,
    app,
    documentation_panel,
    input_panel,
)
from solenoid_calculator.models import SolenoidResult


def test_shiny_app_constructs() -> None:
    assert isinstance(app, App)
    assert set(PRESETS) == {"default1", "default2"}
    input_html = str(input_panel)
    assert "Default 1" in input_html
    assert "Default 2" in input_html


def test_documentation_uses_latex_without_reference_check() -> None:
    documentation_html = str(documentation_panel)
    assert r"\frac{\mu_0\pi N^2h^3}" in documentation_html
    assert r"Z_0(\omega)" in documentation_html
    assert "Energy route to the DC inductance" in documentation_html
    assert "MAXWELL EQUATIONS" in documentation_html
    assert "CURRENT-DENSITY MODEL" in documentation_html
    assert r"\nabla\cdot\mathbf B" in documentation_html
    assert r"\begin{cases}" in documentation_html
    assert r"\mathbf q\times" in documentation_html
    assert r"G(\nu_1,\nu_2)" in documentation_html
    assert "generalized hypergeometric function" in documentation_html
    assert r"q&gt;0" in documentation_html or r"q>0" in documentation_html
    assert "REFERENCE CHECK" not in documentation_html
    assert "Versuch 38" not in documentation_html


def test_geometry_diagram_contains_winding_counts(
    paper_result: SolenoidResult,
) -> None:
    diagram = _geometry_diagram(paper_result)
    assert "1,258 turns · 34 radial ×" in diagram
    assert "37 axial packing" in diagram
    assert "requested envelope" in diagram
    assert "occupied winding" in diagram


def test_geometry_diagram_is_symmetric_and_uses_one_physical_scale(
    matlab_default_result: SolenoidResult,
) -> None:
    diagram = _geometry_diagram(matlab_default_result)
    root = ET.fromstring(diagram.strip())
    elements = {
        element.attrib["id"]: element
        for element in root.iter()
        if "id" in element.attrib
    }

    axis = elements["coil-axis"]
    left = elements["left-occupied"]
    right = elements["right-occupied"]
    pattern = elements["rightTurnPattern"]
    axis_x = float(axis.attrib["x1"])
    left_x = float(left.attrib["x"])
    right_x = float(right.attrib["x"])
    width = float(right.attrib["width"])
    height = float(right.attrib["height"])

    assert float(axis.attrib["x2"]) == pytest.approx(axis_x)
    assert float(left.attrib["width"]) == pytest.approx(width)
    assert left_x + width + right_x == pytest.approx(2.0 * axis_x)

    radial_pitch = width / matlab_default_result.geometry.radial_turns
    axial_pitch = height / matlab_default_result.geometry.axial_turns
    assert radial_pitch == pytest.approx(axial_pitch, rel=1.0e-4)
    assert float(pattern.attrib["width"]) == pytest.approx(radial_pitch, rel=1.0e-4)
    assert float(pattern.attrib["height"]) == pytest.approx(
        axial_pitch,
        rel=1.0e-4,
    )


def test_field_profile_chart_contains_accessible_svg(
    paper_result: SolenoidResult,
) -> None:
    chart = _field_profile_chart(paper_result)
    assert "Axial magnetic flux density profile" in chart
    assert "field-line" in chart
    assert "coil span" in chart
