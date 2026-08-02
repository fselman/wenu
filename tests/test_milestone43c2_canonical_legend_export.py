"""Milestone 43C.2 contracts for legends before one chart save."""

from types import SimpleNamespace

import pytest

from wenu import (
    AtlasChartStyle,
    ExportOptions,
    LegendOptions,
    RegionalChart,
    RenderedChartWithLegends,
    compose_chart,
    draw_resolved_chart_legends,
    legend_symbol_descriptors,
)


def regional_chart():
    return RegionalChart(
        center_alt_deg=35.0,
        center_az_deg=210.0,
        field_width_deg=30.0,
        field_height_deg=20.0,
    )


def test_resolved_legends_are_drawn_from_composition(monkeypatch):
    import wenu.charts.chart_legend_workflow as module

    composition = compose_chart(
        regional_chart(),
        style="atlas",
        legends=LegendOptions(
            objects=False,
            stellar_magnitudes=False,
            context=True,
        ),
    )
    captured = {}
    automatic = SimpleNamespace(artists=("context",))

    def fake_draw(*args, **kwargs):
        captured.update(kwargs)
        return automatic

    monkeypatch.setattr(module, "draw_automatic_chart_legends", fake_draw)
    rendering = object()
    result = draw_resolved_chart_legends(
        regional_chart(),
        object(),
        SimpleNamespace(ax=object()),
        composition.style,
        rendering,
        composition.detail,
        composition.legends,
    )
    assert isinstance(result, RenderedChartWithLegends)
    assert result.rendering is rendering
    assert captured["plan"] is composition.legends.plan
    assert captured["include_objects"] is False
    assert captured["include_context"] is True


def test_no_policy_preserves_plain_rendering_result():
    rendering = object()
    result = draw_resolved_chart_legends(
        regional_chart(),
        object(),
        SimpleNamespace(ax=object()),
        object(),
        rendering,
        object(),
        None,
    )
    assert result is rendering


def test_canonical_legends_require_composed_style():
    composition = compose_chart(
        regional_chart(),
        style="atlas",
        legends=LegendOptions(),
    )
    with pytest.raises(TypeError, match="composed chart style"):
        draw_resolved_chart_legends(
            regional_chart(),
            object(),
            SimpleNamespace(ax=object()),
            object(),
            object(),
            composition.detail,
            composition.legends,
        )


def test_export_draws_legends_before_its_single_save(monkeypatch, tmp_path):
    import wenu.charts.chart_legend_workflow as workflow

    chart = regional_chart()
    composition = compose_chart(
        chart,
        style="atlas",
        legends=LegendOptions(
            objects=False,
            stellar_magnitudes=False,
            context=True,
        ),
    )
    calls = []
    rendering = object()
    rendered_with_legends = object()

    def fake_render(self, sky, renderer, **kwargs):
        calls.append("render")
        return rendering

    def fake_legends(*args):
        calls.append("legends")
        assert args[4] is rendering
        return rendered_with_legends

    def fake_save(self, figure, path):
        calls.append("save")
        return path

    monkeypatch.setattr(RegionalChart, "render", fake_render)
    monkeypatch.setattr(workflow, "draw_resolved_chart_legends", fake_legends)
    monkeypatch.setattr(ExportOptions, "save", fake_save)
    renderer = SimpleNamespace(ax=SimpleNamespace(figure=object()))
    result, output = chart.export(
        object(),
        renderer,
        tmp_path / "chart.png",
        style=composition.style,
        legends=composition.legends,
        resolved_detail=composition.detail,
    )
    assert result is rendered_with_legends
    assert output == tmp_path / "chart.png"
    assert calls == ["render", "legends", "save"]


def test_object_symbols_follow_resolved_enabled_layers():
    style = AtlasChartStyle()
    sky = SimpleNamespace(
        open_clusters=object(),
        globular_clusters=object(),
        planetary_nebulae=None,
        supernova_remnants=None,
        galaxies=None,
        milky_way_isophotes=None,
    )
    detail = SimpleNamespace(
        layer_enabled=lambda name: name == "open_clusters"
    )
    descriptors = legend_symbol_descriptors(
        sky,
        style,
        resolved_detail=detail,
    )
    assert tuple(item.key for item in descriptors) == ("open_cluster",)
