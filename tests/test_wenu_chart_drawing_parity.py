"""Resolved drawing parity for the installed ``wenu_chart`` adapter."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from wenu.charts import command_line
from wenu.cli import chart
from wenu.configuration import (
    load_configuration,
    translate_configuration_defaults,
)


class _Observer:
    def __init__(self, **values):
        self.values = values

    def close(self):
        pass


def _install_catalogue_free_runtime(monkeypatch, captured):
    values = load_configuration()
    configuration = translate_configuration_defaults(values)
    view = SimpleNamespace(
        configuration=configuration,
        family="regional",
        constellations=SimpleNamespace(key="cyg-lyr-aql"),
        target=None,
    )

    monkeypatch.setattr(chart, "load_configuration", lambda path=None: values)
    monkeypatch.setattr(
        chart,
        "translate_configuration_defaults",
        lambda effective: configuration,
    )
    monkeypatch.setattr(chart, "Observer", _Observer)
    monkeypatch.setattr(chart, "generate_celestial_sphere", object)
    monkeypatch.setattr(chart, "get_chart_view", lambda *args, **kwargs: view)

    def draw(_view, destination, **options):
        captured.append((destination, options))
        return SimpleNamespace(output=destination)

    monkeypatch.setattr(command_line, "draw_chart_view", draw)


def test_complete_command_resolves_the_shared_drawing_request(
    monkeypatch, tmp_path
):
    captured = []
    _install_catalogue_free_runtime(monkeypatch, captured)
    destination = tmp_path / "teaching-chart.svg"

    outputs = chart.generate(chart.parser().parse_args([
        "regional", "--constellations", "Cyg,Lyr,Aql",
        "--observer-location", "La Ligua",
        "--observer-time", "2026-08-15 21:00",
        "--style", "cartoon", "--mode", "presentation",
        "--output", str(destination),
        "--magnitude-limit", "4.25",
        "--constellation-lines", "--constellation-labels",
        "--constellation-boundaries",
        "--horizon", "--horizon-mask",
        "--altaz-grid", "--altaz-grid-labels",
        "--equatorial-grid", "--equatorial-grid-labels",
        "--ecliptic-grid", "--ecliptic-grid-labels",
        "--galactic-grid", "--galactic-grid-labels",
        "--grid-references", "all", "--poles", "--pole-labels",
        "--legends", "--star-counts", "--credits",
        "--no-center", "--no-grid", "--location", "--date",
        "--local-time",
        "--constellation-line-width", "1.75",
        "--constellation-line-color", "#102030",
        "--constellation-label-color", "navy",
        "--constellation-boundary-width", "0.8",
        "--constellation-boundary-color", "#405060",
        "--title", "Summer Triangle", "--language", "es",
    ]))

    assert outputs == (destination,)
    assert len(captured) == 1
    output, request = captured[0]
    assert output == destination
    assert request["style"] == "cartoon"
    assert request["mode"] == "presentation"
    assert request["detail"] is None
    assert request["horizon"] is True
    assert request["horizon_mask"] is True
    assert request["title"] == "Summer Triangle"
    assert request["language"] == "es"

    detail = request["detail_overrides"]
    assert detail.star_magnitude_limit == pytest.approx(4.25)
    assert detail.enabled_layer_additions == frozenset({
        "constellation_lines", "constellation_labels",
        "constellation_boundaries", "altaz_grid", "equatorial_grid",
        "ecliptic_grid", "galactic_grid",
    })
    assert detail.grid_label_layers == frozenset({
        "altaz_grid", "equatorial_grid", "ecliptic_grid",
        "galactic_grid",
    })
    assert detail.constellation_star_mode == "selected"

    appearance = request["style_overrides"]
    assert appearance.constellation_linewidth == pytest.approx(1.75)
    assert appearance.constellation_line_color == "#102030"
    assert appearance.constellation_label_color == "navy"
    assert appearance.boundary_linewidth == pytest.approx(0.8)
    assert appearance.boundary_color == "#405060"

    furniture = request["furniture"]
    assert furniture.references.celestial_equator.state == "labeled"
    assert furniture.references.ecliptic.state == "labeled"
    assert furniture.references.galactic_plane.state == "labeled"
    assert furniture.poles.celestial == "visible"
    assert furniture.poles.ecliptic == "visible"
    assert furniture.poles.galactic == "visible"
    assert furniture.poles.labels is True
    assert furniture.footer.application is True
    assert furniture.legends.objects is True
    assert furniture.legends.stellar_magnitudes is True
    assert furniture.legends.stellar_counts is True
    assert furniture.context.center is False
    assert furniture.context.grid is False
    assert furniture.context.location is True
    assert furniture.context.date is True
    assert furniture.context.local_time is True


def test_all_products_resolve_the_canonical_export_matrix(
    monkeypatch, tmp_path
):
    captured = []
    _install_catalogue_free_runtime(monkeypatch, captured)
    destination = tmp_path / "gallery"

    outputs = chart.generate(chart.parser().parse_args([
        "regional", "--constellations", "Cyg,Lyr,Aql",
        "--observer-location", "La Ligua",
        "--observer-time", "2026-08-15 21:00",
        "--all-products", "--output", str(destination),
    ]))

    assert outputs == tuple(item[0] for item in captured)
    assert [(item[1]["style"], item[1]["mode"]) for item in captured] == [
        ("atlas", "print"),
        ("atlas", "presentation"),
        ("cartoon", "print"),
        ("cartoon", "presentation"),
    ]
    assert [item[0].name for item in captured] == [
        "regional-cyg-lyr-aql-atlas-print.png",
        "regional-cyg-lyr-aql-atlas-presentation.png",
        "regional-cyg-lyr-aql-cartoon-print.png",
        "regional-cyg-lyr-aql-cartoon-presentation.png",
    ]
