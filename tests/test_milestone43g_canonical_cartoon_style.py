"""Milestone 43G contracts for cartoon style on the canonical pipeline."""

from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest
from astropy import units as u
from astropy.coordinates import AltAz, EarthLocation
from astropy.time import Time

from wenu import (
    CartoonChartStyle,
    CartoonDetailPolicy,
    CircumpolarChart,
    DetailOverrides,
    FixedDetailPolicy,
    FullSkyChart,
    RegionalChart,
    ResolvedDetail,
    cartoon_chart_style,
    compose_cartoon_chart,
    compose_chart,
)


def charts():
    observer = SimpleNamespace(
        altaz_frame=AltAz(
            obstime=Time("2026-08-02T00:00:00"),
            location=EarthLocation(
                lat=-32.44 * u.deg,
                lon=-71.23 * u.deg,
            ),
        )
    )
    return (
        RegionalChart(
            center_alt_deg=35.0,
            center_az_deg=210.0,
            field_width_deg=30.0,
            field_height_deg=20.0,
        ),
        FullSkyChart(),
        CircumpolarChart(
            observer=observer,
            pole="south",
            limiting_declination_deg=-30.0,
        ),
    )


@pytest.mark.parametrize("chart", charts())
@pytest.mark.parametrize("mode", ("print", "presentation"))
def test_named_cartoon_style_uses_canonical_composition(chart, mode):
    composition = compose_chart(chart, style="cartoon", mode=mode)

    assert composition.style_name == "cartoon"
    assert composition.mode_name == mode
    assert isinstance(composition.style, CartoonChartStyle)
    assert composition.detail == CartoonDetailPolicy().resolve(
        composition.context,
        composition.mode,
    )
    assert composition.detail.enabled_layers == frozenset(
        {"stars", "constellation_lines", "constellation_labels"}
    )
    assert composition.detail.constellation_star_mode == "selected"


@pytest.mark.parametrize("chart", charts())
def test_cartoon_mode_changes_no_chart_geometry_or_content(chart):
    printed = compose_chart(chart, style="cartoon", mode="print")
    presented = compose_chart(
        chart,
        style="cartoon",
        mode="presentation",
    )

    assert_same_geometry(printed.context, presented.context)
    assert_same_geometry(presented.context, chart.chart_context)
    assert printed.detail == presented.detail
    assert printed.style.canvas.sky_color == "white"
    assert presented.style.canvas.sky_color == "#1677A6"


def assert_same_geometry(left, right):
    """Compare contexts without ambiguous NumPy array equality."""
    assert replace(left, clip_boundary=None) == replace(
        right,
        clip_boundary=None,
    )
    left_boundary = left.clip_boundary
    right_boundary = right.clip_boundary
    if left_boundary is None or right_boundary is None:
        assert left_boundary is right_boundary is None
        return
    assert left_boundary.closed == right_boundary.closed
    assert left_boundary.name == right_boundary.name
    np.testing.assert_allclose(left_boundary.x, right_boundary.x)
    np.testing.assert_allclose(left_boundary.y, right_boundary.y)


def test_explicit_detail_policy_replaces_cartoon_recommendation():
    detail = FixedDetailPolicy(
        ResolvedDetail(
            star_magnitude_limit=4.0,
            enabled_layers=frozenset({"stars", "milky_way"}),
        )
    )
    composition = compose_chart(
        charts()[0],
        style="cartoon",
        detail=detail,
    )

    assert composition.detail.star_magnitude_limit == 4.0
    assert composition.detail.enabled_layers == frozenset(
        {"stars", "milky_way"}
    )


def test_optional_milky_way_is_render_local():
    chart = charts()[0]
    with_milky_way = compose_chart(
        chart,
        style="cartoon",
        detail_overrides=DetailOverrides(
            enabled_layers=frozenset(
                {
                    "stars",
                    "constellation_lines",
                    "constellation_labels",
                    "milky_way",
                }
            )
        ),
    )
    default_again = compose_chart(chart, style="cartoon")

    assert with_milky_way.detail.layer_enabled("milky_way")
    assert not default_again.detail.layer_enabled("milky_way")


def test_explicit_constellation_label_controls_remain_supported():
    style = cartoon_chart_style(
        "print",
        constellation_label_positions={"Sco": "ur"},
        constellation_label_offsets={"Sco": (0.1, -0.2)},
    )
    composition = compose_chart(
        charts()[0],
        style=style,
        detail=CartoonDetailPolicy(),
    )

    assert composition.style_name == "cartoon"
    assert composition.style.grids.constellation_label_offsets["Sco"] == (
        pytest.approx(0.34),
        pytest.approx(0.0),
    )


def test_legacy_wrapper_is_not_adapted_twice():
    legacy = compose_cartoon_chart(
        charts()[0],
        mode="presentation",
    )
    canonical = compose_chart(
        charts()[0],
        style="cartoon",
        mode="presentation",
    )

    assert legacy.style.stars.area_scale == canonical.style.stars.area_scale
    assert legacy.style.canvas.label_fontsize == (
        canonical.style.canvas.label_fontsize
    )
    assert legacy.style.output_mode_name == "presentation"
