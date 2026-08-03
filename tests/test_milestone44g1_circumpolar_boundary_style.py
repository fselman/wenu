"""Milestone 44G.1 circumpolar boundary-style ownership."""

from wenu import CircumpolarChart, cartoon_chart_style
from wenu.charts.presets import AtlasChartStyle


class Delegate:
    def __init__(self):
        self.options = None

    def render(self, *args, **kwargs):
        self.options = kwargs
        return "rendered"


def chart_with_delegate(monkeypatch):
    delegate = Delegate()
    monkeypatch.setattr(
        CircumpolarChart,
        "binocular_chart",
        property(lambda self: delegate),
    )
    return CircumpolarChart(object(), -69.75), delegate


def test_atlas_boundary_uses_resolved_grid_appearance(monkeypatch):
    chart, delegate = chart_with_delegate(monkeypatch)
    style = AtlasChartStyle()

    result = chart.render(
        object(),
        object(),
        style=style,
        coordinate_label_anchor=object(),
    )

    boundary = delegate.options["boundary_style"]
    assert result == "rendered"
    assert boundary["edgecolor"] == style.grids.boundary_color
    assert boundary["linewidth"] == style.grids.boundary_linewidth
    assert boundary["linestyle"] == style.grids.boundary_linestyle
    assert boundary["alpha"] == style.grids.boundary_alpha
    assert boundary["facecolor"] == "none"


def test_cartoon_boundary_uses_mode_specific_contract(monkeypatch):
    chart, delegate = chart_with_delegate(monkeypatch)
    style = cartoon_chart_style("presentation")

    chart.render(
        object(),
        object(),
        style=style,
        coordinate_label_anchor=object(),
    )

    boundary = delegate.options["boundary_style"]
    assert boundary["edgecolor"] == "#FFE066"
    assert boundary["linewidth"] == style.grids.constellation_linewidth


def test_explicit_boundary_style_retains_precedence(monkeypatch):
    chart, delegate = chart_with_delegate(monkeypatch)
    explicit = {"edgecolor": "magenta", "linewidth": 3.0}

    chart.render(
        object(),
        object(),
        style=AtlasChartStyle(),
        boundary_style=explicit,
        coordinate_label_anchor=object(),
    )

    assert delegate.options["boundary_style"] is explicit
