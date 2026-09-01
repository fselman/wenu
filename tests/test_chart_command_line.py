"""Shared command-line adaptation for the ordinary chart-view facade."""

import argparse
from pathlib import Path

import pytest

from wenu import (
    ChartProduct,
    ChartStyleOverrides,
    DetailOverrides,
    LegendOptions,
    StellarMagnitudeSizing,
    add_chart_cli_arguments,
    chart_detail_overrides,
    chart_cli_furniture,
    draw_chart_view_from_arguments,
)


def parser():
    return add_chart_cli_arguments(
        argparse.ArgumentParser(),
        default_output="output/chart",
    )


def test_complete_cli_contract_includes_context_and_credits():
    arguments = parser().parse_args([
        "--credits", "--no-center", "--no-grid",
        "--location", "--date", "--local-time",
    ])

    assert arguments.credits is True
    assert arguments.center is False
    assert arguments.grid is False
    assert arguments.location is True
    assert arguments.date is True
    assert arguments.local_time is True
    assert arguments.equatorial_grid is True
    assert arguments.equatorial_grid_labels is True
    assert arguments.horizon is False
    assert arguments.horizon_mask is False


@pytest.mark.parametrize(
    ("arguments", "horizon", "horizon_mask"),
    (
        ([], False, False),
        (["--horizon"], True, False),
        (["--horizon-mask"], False, True),
        (["--horizon", "--horizon-mask"], True, True),
    ),
)
def test_cli_forwards_independent_horizon_controls(
    monkeypatch, arguments, horizon, horizon_mask
):
    calls = []
    monkeypatch.setattr(
        "wenu.charts.command_line.draw_chart_view",
        lambda *args, **kwargs: calls.append(kwargs) or object(),
    )
    view = type("View", (), {"family": "regional"})()

    draw_chart_view_from_arguments(
        view,
        parser().parse_args(arguments),
        stem="map",
    )

    assert calls[0]["horizon"] is horizon
    assert calls[0]["horizon_mask"] is horizon_mask


def test_ordinary_cli_can_omit_default_equatorial_grid():
    arguments = parser().parse_args(["--no-equatorial-grid"])

    assert arguments.equatorial_grid is False
    assert arguments.equatorial_grid_labels is False
    assert "equatorial_grid" in chart_detail_overrides(
        arguments
    ).disabled_layers


def test_all_sky_cli_uses_labeled_galactic_grid_by_default(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "wenu.charts.command_line.draw_chart_view",
        lambda *args, **kwargs: calls.append(kwargs) or object(),
    )
    view = type("View", (), {"family": "all_sky"})()

    draw_chart_view_from_arguments(view, parser().parse_args([]), stem="map")

    detail = calls[0]["detail_overrides"]
    assert detail.enabled_layer_additions == {"galactic_grid"}
    assert detail.grid_label_layers == {"galactic_grid"}
    assert "equatorial_grid" in detail.disabled_layers


def test_all_sky_cli_retains_explicit_equatorial_grid(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "wenu.charts.command_line.draw_chart_view",
        lambda *args, **kwargs: calls.append(kwargs) or object(),
    )
    view = type("View", (), {"family": "all_sky"})()

    arguments = parser().parse_args(["--equatorial-grid-labels"])
    draw_chart_view_from_arguments(view, arguments, stem="map")

    detail = calls[0]["detail_overrides"]
    assert detail.enabled_layer_additions == {"equatorial_grid"}
    assert detail.grid_label_layers == {"equatorial_grid"}


def test_cli_furniture_maps_references_poles_legends_and_context():
    arguments = parser().parse_args([
        "--grid-references", "equatorial,galactic",
        "--poles", "--pole-labels", "--legends", "--star-counts",
        "--credits", "--location",
    ])
    furniture = chart_cli_furniture(
        arguments,
        reference_labels={"galactic": "Plano galáctico"},
        pole_selection="both",
        copyright="© Fernando Selman",
    )

    assert furniture.references.celestial_equator.state == "labeled"
    assert furniture.references.ecliptic.state == "none"
    assert furniture.references.galactic_plane.label == "Plano galáctico"
    assert furniture.poles.celestial == "both"
    assert furniture.poles.labels is True
    assert furniture.footer.application is True
    assert furniture.footer.copyright == "© Fernando Selman"
    assert furniture.legends.objects is True
    assert furniture.legends.stellar_magnitudes is True
    assert furniture.legends.stellar_counts is True
    assert furniture.context.location is True


def test_cli_furniture_translates_reference_labels_from_product_language():
    arguments = parser().parse_args([
        "--grid-references", "equatorial,ecliptic",
    ])
    arguments.language = "es"

    furniture = chart_cli_furniture(arguments)

    assert furniture.references.celestial_equator.label == "Ecuador celeste"
    assert furniture.references.ecliptic.label == "Eclíptica"


def test_cli_furniture_selects_labeled_ecliptic_keypoints():
    arguments = parser().parse_args([
        "--grid-references", "ecliptic",
    ])

    furniture = chart_cli_furniture(
        arguments,
        ecliptic_keypoints="labeled",
    )

    assert furniture.references.ecliptic_keypoints == "labeled"


def test_cli_furniture_translates_keypoint_legend_and_reference_magnitude():
    arguments = parser().parse_args([])
    arguments.language = "es"

    furniture = chart_cli_furniture(
        arguments,
        ecliptic_keypoints="labeled",
        ecliptic_keypoint_legend=True,
        stellar_reference_magnitude=3,
        stellar_label_suffix=" mag",
    )

    assert furniture.references.ecliptic_keypoint_legend is True
    assert furniture.references.ecliptic_keypoint_names == (
        "Equinoccio de marzo",
        "Solsticio de junio",
        "Equinoccio de septiembre",
        "Solsticio de diciembre",
    )
    assert furniture.references.ecliptic_keypoint_zodiac_names == (
        "Aries",
        "Cáncer",
        "Libra",
        "Capricornio",
    )
    assert furniture.legends.stellar_reference_magnitude == 3
    assert furniture.legends.stellar_label_suffix == " mag"


def test_cli_furniture_accepts_an_explicit_shared_legend_plan():
    arguments = parser().parse_args(["--magnitude-legend"])
    plan = LegendOptions().resolve("regional").plan.with_stars(
        anchor=(0.99, 0.055),
    )

    furniture = chart_cli_furniture(arguments, legend_plan=plan)

    assert furniture.legends.plan is plan


def test_adapter_delegates_selected_products_to_ordinary_drawing(
    monkeypatch, tmp_path
):
    calls = []

    def draw(view, destination, **options):
        calls.append((view, Path(destination), options))
        return destination

    monkeypatch.setattr(
        "wenu.charts.command_line.draw_chart_view", draw
    )
    arguments = parser().parse_args([
        "--all-products", "--output", str(tmp_path),
        "--magnitude-limit", "5.5", "--ecliptic-grid-labels",
        "--constellation-line-color", "white",
    ])
    special = object()
    products = tuple(
        ChartProduct(style, mode)
        for style in ("atlas", "cartoon")
        for mode in ("print", "presentation")
    )
    results = draw_chart_view_from_arguments(
        "view",
        arguments,
        stem="example",
        product_details={products[0]: special},
        title="Example",
        language="es",
    )

    assert len(results) == 4
    assert [path.name for _, path, _ in calls] == [
        "example-atlas-print.png",
        "example-atlas-presentation.png",
        "example-cartoon-print.png",
        "example-cartoon-presentation.png",
    ]
    assert calls[0][2]["detail"] is special
    assert calls[1][2]["detail"] is None
    assert calls[0][2]["detail_overrides"] == DetailOverrides(
        star_magnitude_limit=5.5,
        enabled_layer_additions=frozenset({
            "equatorial_grid", "ecliptic_grid"
        }),
        disabled_layers=frozenset({
            "constellation_lines", "constellation_labels",
                "constellation_boundaries", "coordinate_grids",
                "altaz_grid", "galactic_grid", "mercury", "venus", "mars",
                "jupiter", "saturn", "uranus", "neptune", "moon",
        }),
        grid_label_layers=frozenset({
            "equatorial_grid", "ecliptic_grid"
        }),
        constellation_star_mode="none",
    )
    assert calls[0][2]["style_overrides"] == ChartStyleOverrides(
        constellation_line_color="white"
    )
    assert calls[0][2]["title"] == "Example"
    assert calls[0][2]["language"] == "es"


def test_adapter_rejects_invalid_product_detail_contract():
    arguments = parser().parse_args([])
    with pytest.raises(TypeError):
        draw_chart_view_from_arguments(
            "view", arguments, stem="example", product_details=()
        )
    with pytest.raises(ValueError):
        draw_chart_view_from_arguments(
            "view",
            arguments,
            stem="example",
            product_details={ChartProduct("cartoon", "print"): object()},
        )


def test_style_detail_and_family_style_overrides_are_composed(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "wenu.charts.command_line.draw_chart_view",
        lambda *args, **kwargs: calls.append(kwargs) or object(),
    )
    arguments = parser().parse_args([
        "--style", "cartoon",
        "--sky-color", "#1F699B",
        "--constellation-line-color", "white",
    ])
    detail = object()
    sizing = StellarMagnitudeSizing()

    draw_chart_view_from_arguments(
        "view", arguments, stem="example",
        product_details={"cartoon": detail},
        style_overrides=ChartStyleOverrides(stellar_magnitude_sizing=sizing),
    )

    assert calls[0]["detail"] is detail
    assert calls[0]["style_overrides"].sky_color == "#1F699B"
    assert calls[0]["style_overrides"].constellation_line_color == "white"
    assert calls[0]["style_overrides"].stellar_magnitude_sizing is sizing
