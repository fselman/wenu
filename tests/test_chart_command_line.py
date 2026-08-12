"""Shared command-line adaptation for the ordinary chart-view facade."""

import argparse
from pathlib import Path

import pytest

from wenu import (
    ChartProduct,
    ChartStyleOverrides,
    DetailOverrides,
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


def test_ordinary_cli_can_omit_default_equatorial_grid():
    arguments = parser().parse_args(["--no-equatorial-grid"])

    assert arguments.equatorial_grid is False
    assert arguments.equatorial_grid_labels is False
    assert "equatorial_grid" in chart_detail_overrides(
        arguments
    ).disabled_layers


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
            "altaz_grid", "galactic_grid",
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
        "--style", "cartoon", "--constellation-line-color", "white"
    ])
    detail = object()
    sizing = StellarMagnitudeSizing()

    draw_chart_view_from_arguments(
        "view", arguments, stem="example",
        product_details={"cartoon": detail},
        style_overrides=ChartStyleOverrides(stellar_magnitude_sizing=sizing),
    )

    assert calls[0]["detail"] is detail
    assert calls[0]["style_overrides"].constellation_line_color == "white"
    assert calls[0]["style_overrides"].stellar_magnitude_sizing is sizing
