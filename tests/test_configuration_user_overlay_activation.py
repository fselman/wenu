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
    path.write_text("schema_version = 2\n" + text, encoding="utf-8")
    arguments = argparse.Namespace(config=path)
    return chart_configuration(arguments)


def _parser():
    return add_chart_cli_arguments(
        argparse.ArgumentParser(),
        default_output="output/chart",
    )


def test_cli_stellar_selectors_replace_only_their_toml_list(monkeypatch, tmp_path):
    path = tmp_path / "labels.toml"
    path.write_text("schema_version = 2\n[detail.star_labels]\nnames = ['Sco:Antares']\nbayer = ['And:alpha']\nshow_full_bayer_designation = true\n[reports]\nstellar_designations = true\n")
    arguments = _parser().parse_args([
        "--config", str(path), "--star-label-bayer", "Peg:delta",
        "--star-label-bayer", "Aur:gamma", "--no-stellar-report",
    ])
    view = SimpleNamespace(family="regional", configuration=chart_configuration(arguments))
    calls = []
    monkeypatch.setattr("wenu.charts.command_line.draw_chart_view", lambda *args, **kw: calls.append(kw))
    draw_chart_view_from_arguments(view, arguments, stem="map")
    selected = calls[0]["detail_overrides"].star_labels
    assert selected.names == ("Sco:Antares",)
    assert selected.bayer == ("Peg:delta", "Aur:gamma")
    assert selected.show_full_bayer_designation
    assert calls[0]["stellar_report"] is False


@pytest.mark.parametrize("text", [
    "[detail.star_labels]\nnames = [123]\n",
    "[detail.star_labels]\nbayer = ['And:']\n",
    "[detail.star_labels]\nbayer = ['And:unicorn']\n",
    "[reports]\nstellar_designations = 'true'\n",
    "[detail.star_labels]\nshow_full_bayer_designation = 1\n",
])
def test_stellar_settings_reject_malformed_inputs(tmp_path, text):
    with pytest.raises((ConfigurationError, ValueError)):
        _configuration(tmp_path, text)


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


def test_cartoon_presentation_preserves_user_mask_appearance(tmp_path):
    configuration = _configuration(
        tmp_path,
        "[styles.cartoon.mask]\n"
        "color = '#ffffff'\n"
        "opacity = 1.0\n",
    )
    chart = RegionalChart(45.0, 180.0, 20.0, 15.0)

    composition = compose_chart(
        chart,
        style="cartoon",
        mode="presentation",
        configuration=configuration,
    )

    assert composition.style.canvas.sky_color == "#0262AD"
    assert composition.style.mask.color == "#ffffff"
    assert composition.style.mask.alpha == pytest.approx(1.0)


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
        "schema_version = 2\n"
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
        "schema_version = 2\n"
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
        "schema_version = 2\n"
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
        "schema_version = 2\n"
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



def test_constellation_publication_overlay_translates_into_existing_contracts(tmp_path):
    from wenu.configuration import load_configuration_defaults
    from wenu.charts.style_components import GridStyle, StellarStyle
    from wenu.charts.style_overrides import ChartStyleOverrides
    overlay = tmp_path / "figure.toml"
    overlay.write_text('schema_version = 2\n[detail.content]\nstar_constellations = ["Sco", "Lib"]\n'
                       '[styles.cartoon.constellation_figures]\ngap_points = 1.25\n'
                       '[styles.cartoon.stars.labels]\nplacement = "auto"\n'
                       '[products.default]\naxes_frame = false\nshow_title = false\n[export]\ntransparent = true\n')
    defaults = load_configuration_defaults(overlay)
    assert defaults.geometry_detail.star_constellations == {"Sco", "Lib"}
    assert defaults.style_mode.cartoon.grids.constellation_line_gap_points == 1.25
    assert defaults.style_mode.cartoon.stars.label_placement == "auto"
    assert not defaults.furniture_product_export.product.axes_frame
    assert not defaults.furniture_product_export.product.show_title
    assert defaults.furniture_product_export.export_options.transparent
    import pytest
    for constructor, keyword, value in ((GridStyle, "constellation_line_gap_points", -1),
                                        (GridStyle, "constellation_line_gap_points", float("nan")),
                                        (StellarStyle, "label_placement", "invalid"),
                                        (ChartStyleOverrides, "constellation_line_gap_points", -1)):
        with pytest.raises(ValueError):
            constructor(**{keyword: value})
