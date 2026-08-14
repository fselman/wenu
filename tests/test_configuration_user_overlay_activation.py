"""Runtime and CLI precedence for one immutable user configuration."""

import argparse
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

from wenu import (
    RegionalChart,
    add_chart_cli_arguments,
    chart_cli_furniture,
    chart_configuration,
    chart_view_defaults,
    compose_chart,
    draw_chart_view_from_arguments,
)
from wenu.charts.export_workflow import _composition_export_options
from wenu.configuration import ConfigurationError


def _configuration(tmp_path, text):
    path = tmp_path / "wenu.toml"
    path.write_text("schema_version = 1\n" + text, encoding="utf-8")
    arguments = argparse.Namespace(config=path)
    return chart_configuration(arguments)


def _parser():
    return add_chart_cli_arguments(
        argparse.ArgumentParser(),
        default_output="output/chart",
    )


def test_composition_and_export_use_one_overlay_contract(tmp_path):
    configuration = _configuration(
        tmp_path,
        "[styles.atlas.canvas]\n"
        "background = '#123456'\n"
        "[modes.print]\n"
        "dpi = 240\n"
        "[detail.canonical]\n"
        "regional_star_limit = 6.25\n"
        "[export]\n"
        "metadata = { source = 'user' }\n"
        "padding = 0.125\n",
    )
    chart = RegionalChart(45.0, 180.0, 20.0, 15.0)

    composition = compose_chart(
        chart,
        style="atlas",
        mode="print",
        configuration=configuration,
    )
    export = _composition_export_options(composition)

    assert composition.configuration is configuration
    assert composition.style.canvas.sky_color == "#123456"
    assert composition.mode.dpi == 240
    assert composition.detail.star_magnitude_limit == pytest.approx(6.25)
    assert export.dpi == 240
    assert export.metadata == {"source": "user"}
    assert export.padding == 0.125


def test_view_geometry_uses_the_same_overlay_contract(tmp_path):
    configuration = _configuration(
        tmp_path,
        "[families.binocular]\nfield_diameter = 8.0\n"
        "[families.regional_single]\nwidth = 24.0\nheight = 16.0\n",
    )

    defaults = chart_view_defaults(
        "binocular",
        configuration=configuration,
    )

    assert defaults.field_diameter_deg == 8.0
    regional = chart_view_defaults(
        "regional",
        configuration=configuration,
    )
    assert regional.field_width_deg == 24.0
    assert regional.field_height_deg == 16.0


def test_omitted_cli_product_values_resolve_from_user_overlay(
    monkeypatch,
    tmp_path,
):
    path = tmp_path / "wenu.toml"
    path.write_text(
        "schema_version = 1\n"
        "[products.default]\n"
        "style = 'cartoon'\n"
        "mode = 'presentation'\n"
        "extension = '.svg'\n",
        encoding="utf-8",
    )
    arguments = _parser().parse_args([
        "--config", str(path), "--output", str(tmp_path / "gallery")
    ])
    view = SimpleNamespace(
        family="regional",
        configuration=chart_configuration(arguments),
    )
    calls = []
    monkeypatch.setattr(
        "wenu.charts.command_line.draw_chart_view",
        lambda *args, **kwargs: calls.append((args, kwargs)) or object(),
    )

    draw_chart_view_from_arguments(view, arguments, stem="map")

    assert calls[0][0][1] == tmp_path / "gallery" / (
        "map-cartoon-presentation.svg"
    )
    assert calls[0][1]["style"] == "cartoon"
    assert calls[0][1]["mode"] == "presentation"


def test_explicit_cli_product_values_override_user_overlay(
    monkeypatch,
    tmp_path,
):
    path = tmp_path / "wenu.toml"
    path.write_text(
        "schema_version = 1\n"
        "[products.default]\n"
        "style = 'cartoon'\n"
        "mode = 'presentation'\n",
        encoding="utf-8",
    )
    arguments = _parser().parse_args([
        "--config", str(path),
        "--style", "atlas", "--mode", "print",
        "--output", str(tmp_path / "explicit.png"),
    ])
    view = SimpleNamespace(
        family="regional",
        configuration=chart_configuration(arguments),
    )
    calls = []
    monkeypatch.setattr(
        "wenu.charts.command_line.draw_chart_view",
        lambda *args, **kwargs: calls.append(kwargs) or object(),
    )

    draw_chart_view_from_arguments(view, arguments, stem="map")

    assert calls[0]["style"] == "atlas"
    assert calls[0]["mode"] == "print"


def test_omitted_cli_furniture_values_resolve_from_user_overlay(tmp_path):
    path = tmp_path / "wenu.toml"
    path.write_text(
        "schema_version = 1\n"
        "[grids_references.poles]\nstate = 'visible'\nlabels = false\n"
        "[furniture.footer]\nenabled = true\n"
        "[furniture.context]\ncenter = false\nlocation = true\n",
        encoding="utf-8",
    )
    arguments = _parser().parse_args(["--config", str(path)])
    configuration = chart_configuration(arguments)

    furniture = chart_cli_furniture(
        arguments,
        configuration=configuration,
        family="regional",
    )

    assert furniture.poles.celestial == "visible"
    assert furniture.poles.labels is False
    assert furniture.footer.application is True
    assert furniture.context.center is False
    assert furniture.context.location is True


def test_sequential_cli_configurations_do_not_share_runtime_state(tmp_path):
    first = _configuration(
        tmp_path,
        "[modes.print]\ndpi = 240\n",
    )
    second_path = tmp_path / "second.toml"
    second_path.write_text(
        "schema_version = 1\n"
        "[styles.atlas.canvas]\nbackground = '#654321'\n",
        encoding="utf-8",
    )
    second = chart_configuration(argparse.Namespace(config=second_path))
    chart = RegionalChart(45.0, 180.0, 20.0, 15.0)

    first_product = compose_chart(
        chart, style="atlas", mode="print", configuration=first
    )
    second_product = compose_chart(
        chart, style="atlas", mode="print", configuration=second
    )
    packaged_product = compose_chart(
        chart, style="atlas", mode="print"
    )

    assert first_product.mode.dpi == 240
    assert first_product.style.canvas.sky_color == "white"
    assert second_product.mode.dpi == 300
    assert second_product.style.canvas.sky_color == "#654321"
    assert packaged_product.mode.dpi == 300
    assert packaged_product.style.canvas.sky_color == "white"


def test_canonical_configuration_fails_before_sphere_loading(monkeypatch):
    path = Path("examples/planisphere.py")
    spec = importlib.util.spec_from_file_location("planisphere", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    loaded = []

    def fail(arguments):
        del arguments
        raise ConfigurationError("styles.atlas.canvas.background: invalid")

    monkeypatch.setattr(module, "chart_configuration", fail)
    monkeypatch.setattr(
        module,
        "generate_celestial_sphere",
        lambda: loaded.append(True),
    )

    with pytest.raises(ConfigurationError):
        module.chart_view(module.parser().parse_args([]))

    assert loaded == []
