"""Milestone 43F contracts for canonical composed chart export."""

from types import SimpleNamespace

import pytest
from astropy import units as u
from astropy.coordinates import AltAz, EarthLocation
from astropy.time import Time

from wenu import (
    BinocularChart,
    ChartExportResult,
    CircumpolarChart,
    FullSkyChart,
    LegendOptions,
    RegionalChart,
    compose_chart,
)


class RecordingFigure:
    def __init__(self):
        self.sizes = []

    def set_size_inches(self, width, height, *, forward):
        self.sizes.append((width, height, forward))


class RecordingExportOptions:
    def __init__(self):
        self.calls = []

    def save(self, figure, path):
        self.calls.append((figure, path))
        return path


def empty_sky():
    return SimpleNamespace(
        stars=None,
        nonstellar=None,
        galaxies=None,
        milky_way_isophotes=None,
        magellanic_clouds=None,
        globular_clusters=None,
        open_clusters=None,
        supernova_remnants=None,
        planetary_nebulae=None,
        constellation_lines=None,
        constellation_labels=None,
        constellation_boundaries=None,
        coordinate_grids=(),
        points=None,
        layers=(),
    )


def charts():
    observer = SimpleNamespace(
        altaz_frame=AltAz(
            obstime=Time("2026-08-02T00:00:00"),
            location=EarthLocation(
                lat=-32.44 * u.deg,
                lon=-71.23 * u.deg,
            ),
        )
    )
    return (
        RegionalChart(35.0, 210.0, 30.0, 20.0),
        FullSkyChart(),
        BinocularChart(45.0, 180.0),
        CircumpolarChart(observer, -30.0),
    )


@pytest.mark.parametrize("chart", charts())
def test_composed_export_renders_legends_and_saves_once(
    chart,
    monkeypatch,
    tmp_path,
):
    import wenu.charts.chart_legend_workflow as legends_module

    composition = compose_chart(
        chart,
        style="atlas",
        mode="presentation",
        legends=LegendOptions(
            objects=False,
            stellar_magnitudes=False,
            context=True,
        ),
    )
    calls = []
    plain_rendering = object()
    decorated_rendering = object()

    def fake_render(self, sky, renderer, **kwargs):
        calls.append(("render", kwargs))
        return plain_rendering

    def fake_legends(*args):
        calls.append(("legends", args))
        assert args[0] is chart
        assert args[4] is plain_rendering
        return decorated_rendering

    monkeypatch.setattr(type(chart), "render", fake_render)
    monkeypatch.setattr(
        legends_module,
        "draw_resolved_chart_legends",
        fake_legends,
    )
    figure = RecordingFigure()
    renderer = SimpleNamespace(ax=SimpleNamespace(figure=figure))
    export_options = RecordingExportOptions()
    path = tmp_path / "chart.png"

    result = chart.export(
        empty_sky(),
        renderer,
        path,
        composition=composition,
        export_options=export_options,
    )

    assert isinstance(result, ChartExportResult)
    rendering, output = result
    assert rendering is decorated_rendering
    assert output == path
    assert result.composition is composition
    assert result.layer_options == {}
    assert result.export_options is export_options
    assert [name for name, _ in calls] == ["render", "legends"]
    render_kwargs = calls[0][1]
    assert render_kwargs["style"] is composition.style
    assert render_kwargs["layer_options"] == {}
    assert figure.sizes == [
        (
            composition.mode.width_inches,
            composition.mode.height_inches,
            True,
        )
    ]
    assert export_options.calls == [(figure, path)]


def test_composition_default_export_options_follow_resolved_mode(monkeypatch):
    from wenu.charts.regional import ExportOptions

    chart = charts()[0]
    composition = compose_chart(
        chart,
        style="atlas",
        mode="presentation",
    )
    captured = {}

    monkeypatch.setattr(
        RegionalChart,
        "render",
        lambda *args, **kwargs: object(),
    )

    def fake_save(self, figure, path):
        captured["options"] = self
        return path

    monkeypatch.setattr(ExportOptions, "save", fake_save)
    figure = RecordingFigure()
    renderer = SimpleNamespace(ax=SimpleNamespace(figure=figure))
    chart.export(
        empty_sky(),
        renderer,
        "chart.png",
        composition=composition,
    )

    options = captured["options"]
    assert options.dpi == composition.mode.dpi
    assert options.transparent == composition.mode.transparent
    assert options.facecolor == composition.style.canvas.sky_color


def test_composition_rejects_wrong_chart_and_ambiguous_legacy_arguments():
    chart = charts()[0]
    other = RegionalChart(35.0, 210.0, 40.0, 20.0)
    composition = compose_chart(other, style="atlas")
    renderer = SimpleNamespace(
        ax=SimpleNamespace(figure=RecordingFigure())
    )
    with pytest.raises(ValueError, match="different chart"):
        chart.export(
            empty_sky(),
            renderer,
            "chart.png",
            composition=composition,
        )
    with pytest.raises(ValueError, match="cannot be combined"):
        chart.export(
            empty_sky(),
            renderer,
            "chart.png",
            composition=compose_chart(chart, style="atlas"),
            style=object(),
        )
