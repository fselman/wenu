"""Milestone 40A contracts for independent chart composition."""

import ast
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from wenu import (
    AllSkyChart,
    AtlasChartStyle,
    BoundaryKind,
    ChartContext,
    DetailOverrides,
    FixedDetailPolicy,
    FullSkyChart,
    PresentationMode,
    PrintMode,
    RegionalChart,
    ResolvedDetail,
    compose_chart,
)


def regional_chart():
    return RegionalChart(
        center_alt_deg=35.0,
        center_az_deg=210.0,
        field_width_deg=30.0,
        field_height_deg=20.0,
    )


def test_regional_chart_exposes_rectangular_context():
    chart = regional_chart()
    context = chart.chart_context
    assert isinstance(context, ChartContext)
    assert context.viewport == chart.viewport
    assert context.angular_width_deg == 30.0
    assert context.angular_height_deg == 20.0
    assert context.boundary_kind is BoundaryKind.RECTANGULAR
    assert context.clip_boundary is None


def test_full_sky_chart_exposes_circular_context():
    chart = FullSkyChart()
    context = chart.chart_context
    assert context.angular_width_deg == pytest.approx(180.0)
    assert context.angular_height_deg == pytest.approx(180.0)
    assert context.boundary_kind is BoundaryKind.CIRCULAR
    assert context.clip_boundary.closed
    assert context.clip_boundary.name == "horizon"
    assert context.visible_solid_angle_sq_deg == pytest.approx(
        20626.480624709635
    )


def test_all_sky_composition_halves_builtin_star_marker_diameters():
    atlas = compose_chart(AllSkyChart(), style="atlas", mode="print")
    full_sky = compose_chart(FullSkyChart(), style="atlas", mode="print")

    assert atlas.style.stars.area_scale == pytest.approx(
        full_sky.style.stars.area_scale * 0.25
    )


def test_named_atlas_uses_packaged_family_detail_without_example_policy():
    all_sky = compose_chart(AllSkyChart(), style="atlas", mode="print")
    regional = compose_chart(regional_chart(), style="atlas", mode="print")

    assert all_sky.detail.star_magnitude_limit == pytest.approx(5.0)
    assert not all_sky.detail.layer_enabled("open_clusters")
    assert not all_sky.detail.layer_enabled("planetary_nebulae")
    assert regional.detail.star_magnitude_limit == pytest.approx(6.5)


def test_named_cartoon_uses_restrained_bright_deep_sky_policy():
    detail = compose_chart(
        FullSkyChart(), style="cartoon", mode="presentation"
    ).detail

    assert detail.layer_enabled("milky_way")
    assert detail.layer_enabled("magellanic_clouds")
    assert detail.layer_enabled("galaxies")
    assert detail.layer_enabled("open_clusters")
    assert not detail.layer_enabled("planetary_nebulae")
    assert not detail.layer_enabled("supernova_remnants")
    assert detail.galaxy_magnitude_limit == pytest.approx(8.0)
    assert detail.minimum_open_cluster_size_arcmin == pytest.approx(60.0)
    assert detail.minimum_globular_cluster_size_arcmin == pytest.approx(30.0)


def test_modes_resolve_output_size_without_changing_geometry():
    chart = regional_chart()
    before = chart.viewport
    printed = PrintMode(width_inches=12.0).resolve(chart.chart_context)
    presented = PresentationMode(width_inches=12.0).resolve(
        chart.chart_context
    )
    expected_height = 12.0 / chart.viewport.aspect_ratio
    assert printed.width_inches == presented.width_inches == 12.0
    assert printed.height_inches == pytest.approx(expected_height)
    assert presented.height_inches == pytest.approx(expected_height)
    assert presented.font_scale > printed.font_scale
    assert chart.viewport == before


def test_composition_keeps_style_geometry_mode_and_detail_independent():
    chart = regional_chart()
    style = AtlasChartStyle()
    detail = FixedDetailPolicy(
        ResolvedDetail(
            star_magnitude_limit=8.0,
            galaxy_magnitude_limit=11.0,
        )
    )
    composition = compose_chart(
        chart,
        style=style,
        mode=PresentationMode(width_inches=10.0),
        detail=detail,
    )
    assert composition.context == chart.chart_context
    assert composition.style is not style
    assert composition.style != style
    assert style == AtlasChartStyle()
    assert composition.detail.star_magnitude_limit == 8.0
    assert composition.mode.font_scale == pytest.approx(1.35)


def test_explicit_detail_overrides_have_final_precedence():
    composition = compose_chart(
        regional_chart(),
        style=AtlasChartStyle(),
        detail=FixedDetailPolicy(
            ResolvedDetail(
                star_magnitude_limit=8.0,
                galaxy_magnitude_limit=10.0,
                label_density=0.8,
            )
        ),
        detail_overrides=DetailOverrides(
            star_magnitude_limit=11.0,
            label_density=1.2,
        ),
    )
    assert composition.detail.star_magnitude_limit == 11.0
    assert composition.detail.galaxy_magnitude_limit == 10.0
    assert composition.detail.label_density == 1.2


def test_composition_values_are_immutable():
    composition = compose_chart(
        regional_chart(),
        style=AtlasChartStyle(),
    )
    with pytest.raises(FrozenInstanceError):
        composition.detail.label_density = 2.0


def imported_modules(path):
    tree = ast.parse(path.read_text(), filename=str(path))
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.append(node.module)
    return tuple(imported)


def test_composition_contracts_do_not_import_matplotlib():
    import wenu.charts.composition as composition_module

    directory = Path(composition_module.__file__).parent
    for filename in (
        "context.py",
        "modes.py",
        "detail.py",
        "composition.py",
    ):
        for imported in imported_modules(directory / filename):
            assert imported != "matplotlib"
            assert not imported.startswith("matplotlib.")
