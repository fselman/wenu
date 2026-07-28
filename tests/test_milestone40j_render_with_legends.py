from types import SimpleNamespace

from wenu import (
    RenderedChartWithLegends,
    render_chart_with_legends,
)


class ComposedStyle:
    def __init__(self):
        self.publication = object()

    def as_publication_style(self):
        return self.publication


class Chart:
    def __init__(self):
        self.calls = []

    def render(self, sky, renderer, **kwargs):
        self.calls.append((sky, renderer, kwargs))
        return "rendering-result"


def test_workflow_renders_with_publication_style(monkeypatch):
    import wenu.charts.chart_legend_workflow as module

    chart = Chart()
    sky = object()
    renderer = SimpleNamespace(ax=object())
    style = ComposedStyle()
    detail = object()
    automatic = SimpleNamespace(artists=("one", "two"))
    captured = {}

    def fake_legends(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return automatic

    monkeypatch.setattr(
        module,
        "draw_automatic_chart_legends",
        fake_legends,
    )
    result = render_chart_with_legends(
        chart,
        sky,
        renderer,
        style,
        detail,
    )
    assert chart.calls[0][2]["style"] is style.publication
    assert result.rendering == "rendering-result"
    assert result.legends is automatic
    assert result.artists == ("one", "two")
    assert captured["args"][0] is renderer.ax
    assert captured["kwargs"]["resolved_detail"] is detail


def test_publication_style_passes_through_unchanged(monkeypatch):
    import wenu.charts.chart_legend_workflow as module

    chart = Chart()
    publication = object()
    monkeypatch.setattr(
        module,
        "draw_automatic_chart_legends",
        lambda *args, **kwargs: SimpleNamespace(artists=()),
    )
    render_chart_with_legends(
        chart,
        object(),
        SimpleNamespace(ax=object()),
        publication,
        object(),
    )
    assert chart.calls[0][2]["style"] is publication


def test_layer_and_render_options_are_forwarded(monkeypatch):
    import wenu.charts.chart_legend_workflow as module

    chart = Chart()
    layer_options = {object(): {"render": {}}}
    monkeypatch.setattr(
        module,
        "draw_automatic_chart_legends",
        lambda *args, **kwargs: SimpleNamespace(artists=()),
    )
    render_chart_with_legends(
        chart,
        object(),
        SimpleNamespace(ax=object()),
        object(),
        object(),
        layer_options=layer_options,
        render_options={"boundary_style": {"edgecolor": "black"}},
    )
    kwargs = chart.calls[0][2]
    assert kwargs["layer_options"] is layer_options
    assert kwargs["boundary_style"] == {"edgecolor": "black"}


def test_legend_configuration_is_forwarded(monkeypatch):
    import wenu.charts.chart_legend_workflow as module

    chart = Chart()
    captured = {}

    def fake_legends(*args, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(artists=())

    monkeypatch.setattr(
        module,
        "draw_automatic_chart_legends",
        fake_legends,
    )
    plan = object()
    footprint = object()
    grid = object()
    render_chart_with_legends(
        chart,
        object(),
        SimpleNamespace(ax=object()),
        object(),
        object(),
        plan=plan,
        footprint_contains=footprint,
        grid=grid,
        object_title="Objects",
        context_lines=("La Ligua",),
    )
    assert captured["plan"] is plan
    assert captured["footprint_contains"] is footprint
    assert captured["grid"] is grid
    assert captured["object_title"] == "Objects"
    assert captured["context_lines"] == ("La Ligua",)


def test_result_contract_does_not_merge_artist_families():
    rendering = SimpleNamespace(artists=("chart",))
    legends = SimpleNamespace(artists=("objects", "stars"))
    result = RenderedChartWithLegends(rendering, legends)
    assert result.rendering.artists == ("chart",)
    assert result.artists == ("objects", "stars")
