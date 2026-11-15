from __future__ import annotations

from shiny import App

from app import PRESETS, _field_profile_chart, _geometry_diagram, app
from solenoid_calculator.models import SolenoidResult


def test_shiny_app_constructs() -> None:
    assert isinstance(app, App)
    assert {"matlab", "versuch38"} <= PRESETS.keys()


def test_geometry_diagram_contains_winding_counts(
    paper_result: SolenoidResult,
) -> None:
    diagram = _geometry_diagram(paper_result)
    assert "34 radial × 37 axial turns" in diagram
    assert "requested envelope" in diagram
    assert "occupied winding" in diagram


def test_field_profile_chart_contains_accessible_svg(
    paper_result: SolenoidResult,
) -> None:
    chart = _field_profile_chart(paper_result)
    assert "Axial magnetic flux density profile" in chart
    assert "field-line" in chart
    assert "coil span" in chart
