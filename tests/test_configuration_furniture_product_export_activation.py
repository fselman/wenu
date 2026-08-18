"""Runtime authority contracts for packaged furniture/product/export defaults."""

import argparse
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import pytest

from wenu.charts.context import BoundaryKind
from wenu.charts.export_workflow import _composition_export_options
from wenu.charts.footer_furniture import draw_chart_footer
from wenu.charts.legend_plan import default_chart_legend_plan
from wenu.charts.product_options import (
    ChartProduct,
    add_chart_product_arguments,
    chart_product_options,
)
from wenu.charts.regional import ExportOptions
from wenu.configuration import (
    FooterLayoutDefaults,
    load_packaged_defaults,
    packaged_furniture_product_export_defaults,
    translate_furniture_product_export_defaults,
)


def test_packaged_furniture_product_export_authority_is_cached():
    packaged_furniture_product_export_defaults.cache_clear()
    defaults = packaged_furniture_product_export_defaults()

    assert defaults is packaged_furniture_product_export_defaults()
    assert default_chart_legend_plan("regional") is (
        defaults.furniture_by_family["regional"].legends.plan
    )


def test_product_parser_and_extension_consume_packaged_authority(monkeypatch):
    values = load_packaged_defaults()
    values["products"]["default"].update(
        style="cartoon",
        mode="presentation",
        all_products=True,
        extension=".svg",
    )
    configured = translate_furniture_product_export_defaults(values).product
    monkeypatch.setattr(
        "wenu.charts.product_options._packaged_product_defaults",
        lambda: configured,
    )
    parser = add_chart_product_arguments(
        argparse.ArgumentParser(),
        default_output="output/charts",
    )

    options = chart_product_options(parser.parse_args([]))

    assert options.products[0] == ChartProduct("atlas", "print")
    assert options.products[-1] == ChartProduct("cartoon", "presentation")
    assert all(
        path.suffix == ".svg"
        for _, path in options.outputs(stem="sky")
    )


def test_explicit_product_arguments_retain_precedence(monkeypatch):
    configured = replace(
        packaged_furniture_product_export_defaults().product,
        product=ChartProduct("cartoon", "presentation"),
        all_products=False,
    )
    monkeypatch.setattr(
        "wenu.charts.product_options._packaged_product_defaults",
        lambda: configured,
    )
    parser = add_chart_product_arguments(
        argparse.ArgumentParser(),
        default_output="output/chart.png",
    )

    options = chart_product_options(parser.parse_args([
        "--style", "atlas", "--mode", "print", "--output", "chosen.png",
    ]))

    assert options.products == (ChartProduct("atlas", "print"),)
    assert options.output == Path("chosen.png")


def test_footer_layout_uses_packaged_coordinates(monkeypatch):
    layout = FooterLayoutDefaults(
        font_size=9.0,
        y=0.025,
        left_x=0.02,
        right_x=0.98,
    )
    defaults = replace(
        packaged_furniture_product_export_defaults(),
        footer_layout=layout,
    )
    monkeypatch.setattr(
        "wenu.configuration.packaged_furniture_product_export_defaults",
        lambda: defaults,
    )
    calls = []
    figure = SimpleNamespace(
        text=lambda x, **kwargs: calls.append((x, kwargs)) or object(),
        get_size_inches=lambda: (7.0, 5.0),
    )
    position = SimpleNamespace(y0=0.1, y1=0.9, x0=0.1, width=0.8)
    ax = SimpleNamespace(
        figure=figure,
        get_position=lambda: position,
        set_position=lambda value: None,
    )
    renderer = SimpleNamespace(ax=ax)
    footer = replace(
        defaults.furniture_by_family["regional"].footer,
        application=True,
    )

    draw_chart_footer(
        renderer,
        footer,
        SimpleNamespace(font_scale=2.0),
        package_version="1.2.3",
    )

    assert calls[0][0] == 0.9
    assert calls[0][1]["y"] == pytest.approx(0.0325)
    assert calls[0][1]["fontsize"] == 18.0


def test_export_defaults_are_base_and_mode_canvas_values_remain_derived(
    monkeypatch,
):
    configured = ExportOptions(
        dpi=999,
        bbox_inches=None,
        transparent=False,
        facecolor="pink",
        metadata={"Creator": "Wenu"},
        padding=0.25,
    )
    defaults = replace(
        packaged_furniture_product_export_defaults(),
        export_options=configured,
    )
    monkeypatch.setattr(
        "wenu.configuration.packaged_furniture_product_export_defaults",
        lambda: defaults,
    )
    composition = SimpleNamespace(
        mode=SimpleNamespace(dpi=160, transparent=True),
        context=SimpleNamespace(boundary_kind=BoundaryKind.RECTANGULAR),
        style=SimpleNamespace(canvas=SimpleNamespace(sky_color="#123456")),
    )

    resolved = _composition_export_options(composition)

    assert resolved.dpi == 160
    assert resolved.transparent is True
    assert resolved.facecolor == "#123456"
    assert resolved.bbox_inches is None
    assert resolved.metadata == {"Creator": "Wenu"}
    assert resolved.padding == 0.25


def test_export_padding_is_only_forwarded_when_nonzero():
    calls = []
    figure = SimpleNamespace(savefig=lambda path, **kwargs: calls.append(kwargs))

    ExportOptions(padding=0.0).save(figure, "zero.png")
    ExportOptions(padding=0.2).save(figure, "padded.png")

    assert "pad_inches" not in calls[0]
    assert calls[1]["pad_inches"] == 0.2
