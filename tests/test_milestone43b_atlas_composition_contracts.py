"""Milestone 43B contracts for the canonical atlas control plane."""

import numpy as np
import pytest

from wenu import (
    AtlasChartStyle,
    CelestialSphere,
    FixedDetailPolicy,
    PresentationMode,
    PrintMode,
    RegionalChart,
    ResolvedDetail,
    compose_chart,
)
from wenu.geometry.projected import ProjectedPoints
from wenu.geometry.spherical import SphericalPoints
from wenu.sky.sky_layer import SkyLayer


def regional_chart():
    return RegionalChart(
        center_alt_deg=35.0,
        center_az_deg=210.0,
        field_width_deg=30.0,
        field_height_deg=20.0,
    )


@pytest.mark.parametrize("requested", (None, "print", "paper", PrintMode()))
def test_print_mode_has_one_stable_identity(requested):
    composition = compose_chart(
        regional_chart(),
        style="atlas",
        mode=requested,
    )
    assert composition.style_name == "atlas"
    assert composition.mode_name == "print"
    assert isinstance(composition.style, AtlasChartStyle)


@pytest.mark.parametrize(
    "requested",
    ("presentation", PresentationMode()),
)
def test_presentation_mode_has_one_stable_identity(requested):
    composition = compose_chart(
        regional_chart(),
        style="atlas",
        mode=requested,
    )
    assert composition.style_name == "atlas"
    assert composition.mode_name == "presentation"
    assert isinstance(composition.style, AtlasChartStyle)


def test_direct_atlas_style_construction_remains_supported():
    style = AtlasChartStyle()
    composition = compose_chart(regional_chart(), style=style)
    assert composition.style is style
    assert composition.style_name == "atlas"


def test_unknown_style_and_mode_names_are_rejected():
    chart = regional_chart()
    with pytest.raises(ValueError, match="Unknown chart style"):
        compose_chart(chart, style="special-style")
    with pytest.raises(ValueError, match="Unknown chart mode"):
        compose_chart(chart, style="atlas", mode="slides")


def test_mode_resolution_changes_no_chart_geometry_or_content():
    chart = regional_chart()
    detail = FixedDetailPolicy(
        ResolvedDetail(
            star_magnitude_limit=7.0,
            enabled_layers=frozenset({"stars", "open_clusters"}),
        )
    )
    printed = compose_chart(
        chart,
        style="atlas",
        mode="print",
        detail=detail,
    )
    presented = compose_chart(
        chart,
        style="atlas",
        mode="presentation",
        detail=detail,
    )

    assert printed.context == presented.context == chart.chart_context
    assert printed.context.viewport == chart.viewport
    assert printed.context.clip_boundary is None
    assert printed.detail == presented.detail
    assert printed.style != presented.style
    assert printed.mode != presented.mode


class SpyLayer(SkyLayer):
    layer_name = "open_clusters"

    def __init__(self):
        self.received = None
        self.output = SphericalPoints(
            lon_deg=np.asarray([20.0]),
            lat_deg=np.asarray([30.0]),
        )

    def spherical_geometry(self, observer, **options):
        self.received = (observer, options)
        return self.output


class IdentityProjection:
    def project_geometry(self, spherical):
        return ProjectedPoints(
            x=spherical.lon_deg,
            y=spherical.lat_deg,
        )


class RecordingRenderer:
    def __init__(self):
        self.viewport = None

    def apply_viewport(self, viewport):
        self.viewport = viewport

    def draw(self, projected, **options):
        return (projected, options)


def test_resolved_detail_configures_layer_but_layer_produces_geometry():
    observer = object()
    sky = CelestialSphere(observer)
    layer = SpyLayer()
    sky.add(layer)
    composition = compose_chart(
        regional_chart(),
        style="atlas",
        detail=FixedDetailPolicy(
            ResolvedDetail(
                enabled_layers=frozenset({"open_clusters"}),
                minimum_open_cluster_size_arcmin=12.0,
            )
        ),
    )
    application = composition.layer_options(
        sky,
        reload_catalogues=False,
    )

    result = sky.draw_chart(
        projection=IdentityProjection(),
        renderer=RecordingRenderer(),
        viewport=composition.context.viewport,
        layer_options=application.layer_options,
    )

    assert layer.received == (
        observer,
        {"minimum_size_arcmin": 12.0},
    )
    assert result.layers[0].spherical is layer.output
