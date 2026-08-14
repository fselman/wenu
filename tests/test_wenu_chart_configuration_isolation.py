"""Installed-command configuration precedence and state isolation."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from wenu.charts.product_options import chart_product_options
from wenu.cli import chart


class _Observer:
    calls = []

    def __init__(self, **values):
        self.values = values
        self.calls.append(values)

    def close(self):
        pass


def _install_catalogue_free_runtime(monkeypatch, views, drawings, sky):
    monkeypatch.setattr(chart, "Observer", _Observer)
    monkeypatch.setattr(chart, "generate_celestial_sphere", lambda: sky)

    def get_view(_sky, observer, **values):
        assert _sky is sky
        views.append((observer, values))
        constellations = values.get("constellations")
        target = values.get("target")
        return SimpleNamespace(
            configuration=values["configuration"],
            family=values["family"],
            observer=observer,
            constellations=(
                None if constellations is None
                else SimpleNamespace(key="subject")
            ),
            target=(
                None if target is None else SimpleNamespace(key="target")
            ),
        )

    monkeypatch.setattr(chart, "get_chart_view", get_view)
    monkeypatch.setattr(
        chart,
        "draw_chart_view_from_arguments",
        lambda view, arguments, **values: (
            drawings.append((view, arguments, values)) or ()
        ),
    )


def test_sequential_partial_overlays_do_not_leak_between_commands(
    monkeypatch, tmp_path
):
    first_path = tmp_path / "first.toml"
    first_path.write_text(
        "schema_version = 1\n"
        "[observer]\nlocation = 'Papudo'\n"
        "[families.regional_single]\nwidth = 24.0\nheight = 16.0\n"
        "[products.default]\nstyle = 'cartoon'\n",
        encoding="utf-8",
    )
    second_path = tmp_path / "second.toml"
    second_path.write_text(
        "schema_version = 1\n"
        "[styles.atlas.canvas]\nbackground = '#654321'\n",
        encoding="utf-8",
    )
    views = []
    drawings = []
    sky = object()
    _Observer.calls = []
    _install_catalogue_free_runtime(monkeypatch, views, drawings, sky)

    chart.generate(chart.parser().parse_args([
        "regional", "--config", str(first_path),
    ]))
    chart.generate(chart.parser().parse_args([
        "regional", "--config", str(second_path),
    ]))
    chart.generate(chart.parser().parse_args(["regional"]))

    assert [call["location"] for call in _Observer.calls] == [
        "Papudo", "La Ligua", "La Ligua",
    ]
    assert all(view[0].values is call for view, call in zip(views, _Observer.calls))
    assert all(view[1]["configuration"] is drawing[0].configuration
               for view, drawing in zip(views, drawings))
    assert all(view[0].values is not None for view in views)

    configurations = [view[1]["configuration"] for view in views]
    first, second, packaged = configurations
    first_geometry = first.geometry_detail.view_defaults["regional-single"]
    second_geometry = second.geometry_detail.view_defaults["regional-single"]
    packaged_geometry = packaged.geometry_detail.view_defaults[
        "regional-single"
    ]

    assert first_geometry.field_width_deg == pytest.approx(24.0)
    assert first_geometry.field_height_deg == pytest.approx(16.0)
    assert second_geometry.field_width_deg is None
    assert second_geometry.field_height_deg is None
    assert packaged_geometry.field_width_deg is None
    assert packaged_geometry.field_height_deg is None
    assert first.style_mode.atlas.canvas.sky_color == "white"
    assert second.style_mode.atlas.canvas.sky_color == "#654321"
    assert packaged.style_mode.atlas.canvas.sky_color == "white"
    assert first.furniture_product_export.product.product.style == "cartoon"
    assert second.furniture_product_export.product.product.style == "atlas"
    assert packaged.furniture_product_export.product.product.style == "atlas"
    assert len({id(configuration) for configuration in configurations}) == 3
    assert len({id(view[0]) for view in views}) == 3


def test_explicit_command_values_override_conflicting_overlay(
    monkeypatch, tmp_path
):
    path = tmp_path / "conflicting.toml"
    path.write_text(
        "schema_version = 1\n"
        "[observer]\nlocation = 'La Ligua'\ntime = '2026-08-15 21:00'\n"
        "[subjects.regional_single]\nkind = 'constellations'\n"
        "constellations = ['Cru']\n"
        "[families.regional_group]\nwidth = 40.0\nheight = 25.0\n"
        "position_angle = 0.0\nmask = false\n"
        "[products.default]\nstyle = 'cartoon'\nmode = 'presentation'\n"
        "language = 'es'\ntitle = 'Configured title'\n",
        encoding="utf-8",
    )
    views = []
    drawings = []
    sky = object()
    _Observer.calls = []
    _install_catalogue_free_runtime(monkeypatch, views, drawings, sky)
    output = tmp_path / "explicit.svg"

    chart.generate(chart.parser().parse_args([
        "regional", "--config", str(path),
        "--observer-location", "Papudo",
        "--observer-time", "2026-08-15 22:00",
        "--constellations", "Cyg,Lyr,Aql",
        "--field-width", "55.0", "--field-height", "35.0",
        "--position-angle", "12.5", "--mask",
        "--style", "atlas", "--mode", "print",
        "--title", "Explicit title", "--language", "en",
        "--output", str(output),
    ]))

    assert _Observer.calls[0]["location"] == "Papudo"
    assert _Observer.calls[0]["time"] == "2026-08-15 22:00"
    request = views[0][1]
    assert request["constellations"] == ("Cyg", "Lyr", "Aql")
    assert request["field_width_deg"] == pytest.approx(55.0)
    assert request["field_height_deg"] == pytest.approx(35.0)
    assert request["position_angle_deg"] == pytest.approx(12.5)
    assert request["mask"] is True

    view, arguments, values = drawings[0]
    products = chart_product_options(
        arguments,
        defaults=view.configuration.furniture_product_export.product,
    )
    assert products.style == "atlas"
    assert products.mode == "print"
    assert products.output == Path(output)
    assert values["title"] == "Explicit title"
    assert values["language"] == "en"
