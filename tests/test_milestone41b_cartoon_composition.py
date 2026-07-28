from types import SimpleNamespace

import pytest

from wenu import (
    BoundaryKind,
    ChartContext,
    ChartMode,
    DetailOverrides,
    PresentationMode,
    PrintMode,
    ResolvedDetail,
    cartoon_output_mode,
    compose_cartoon_chart,
)
from wenu.geometry.viewport import Viewport


def chart():
    return SimpleNamespace(
        chart_context=ChartContext(
            viewport=Viewport(-2.0, 2.0, -1.0, 1.0),
            angular_width_deg=60.0,
            angular_height_deg=30.0,
            tangent_longitude_deg=180.0,
            tangent_latitude_deg=-30.0,
            boundary_kind=BoundaryKind.RECTANGULAR,
        )
    )


def test_named_modes_resolve_to_chart_mode_objects():
    assert isinstance(cartoon_output_mode("print"), PrintMode)
    assert isinstance(
        cartoon_output_mode("presentation"),
        PresentationMode,
    )


def test_existing_chart_mode_passes_through():
    mode = ChartMode(width_inches=9.0)
    assert cartoon_output_mode(mode) is mode


def test_unknown_named_mode_is_rejected():
    with pytest.raises(ValueError, match="print or presentation"):
        cartoon_output_mode("night")


def test_print_composition_keeps_concerns_separate():
    composition = compose_cartoon_chart(chart(), mode="print")
    assert composition.context.angular_width_deg == pytest.approx(60.0)
    assert composition.style.canvas.sky_color == "white"
    assert composition.mode.dpi == 300
    assert composition.detail.enabled_layers == frozenset(
        {"stars", "constellation_lines", "constellation_labels"}
    )


def test_presentation_changes_style_and_output_not_content():
    printed = compose_cartoon_chart(chart(), mode="print")
    presented = compose_cartoon_chart(chart(), mode="presentation")
    assert presented.style.canvas.sky_color == "#1677A6"
    assert (
        presented.style.grids.constellation_line_color == "#FFE066"
    )
    assert presented.mode.dpi == 160
    assert presented.mode.font_scale > printed.mode.font_scale
    assert presented.detail == printed.detail
    assert presented.context == printed.context


def test_explicit_detail_policy_is_supported():
    fixed = SimpleNamespace(
        resolve=lambda context, mode: ResolvedDetail(
            star_magnitude_limit=2.0,
            enabled_layers=frozenset({"stars"}),
        )
    )
    composition = compose_cartoon_chart(
        chart(),
        detail_policy=fixed,
    )
    assert composition.detail.star_magnitude_limit == pytest.approx(2.0)
    assert composition.detail.enabled_layers == frozenset({"stars"})


def test_detail_overrides_apply_without_touching_style():
    composition = compose_cartoon_chart(
        chart(),
        mode="presentation",
        detail_overrides=DetailOverrides(
            star_magnitude_limit=0.5,
        ),
    )
    assert composition.detail.star_magnitude_limit == pytest.approx(0.5)
    assert composition.style.canvas.sky_color == "#1677A6"
