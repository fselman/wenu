from types import SimpleNamespace

import pytest

from wenu import (
    AutomaticChartLegends,
    ChartLegendPlan,
    LegendPlacement,
    chart_type_name,
)


@pytest.mark.parametrize(
    ("class_name", "expected"),
    (
        ("RegionalChart", "regional"),
        ("FullSkyChart", "planisphere"),
        ("CircumpolarChart", "circumpolar"),
        ("BinocularChart", "binocular"),
    ),
)
def test_public_chart_classes_map_to_semantic_types(
    class_name,
    expected,
):
    chart_class = type(class_name, (), {})
    assert chart_type_name(chart_class()) == expected


def test_explicit_chart_type_protocol_is_supported():
    chart = SimpleNamespace(chart_type="circumpolar")
    assert chart_type_name(chart) == "circumpolar"


def test_unknown_chart_requires_explicit_plan():
    with pytest.raises(ValueError, match="pass plan explicitly"):
        chart_type_name(object())


def test_result_exposes_nested_artists():
    nested = SimpleNamespace(artists=("objects", "stars"))
    plan = ChartLegendPlan(
        chart_type="regional",
        objects=LegendPlacement(),
        stars=LegendPlacement(),
    )
    result = AutomaticChartLegends(
        chart_type="regional",
        plan=plan,
        legends=nested,
    )
    assert result.artists == ("objects", "stars")


def test_custom_plan_can_describe_unknown_chart(monkeypatch):
    import wenu.charts.automatic_legends as module

    plan = ChartLegendPlan(
        chart_type="regional",
        objects=LegendPlacement(enabled=False),
        stars=LegendPlacement(enabled=False),
    )
    sentinel = SimpleNamespace(artists=())
    captured = {}

    def fake_draw(*args, **kwargs):
        captured.update(kwargs)
        return sentinel

    monkeypatch.setattr(module, "draw_rendered_chart_legends", fake_draw)
    result = module.draw_automatic_chart_legends(
        object(),
        object(),
        object(),
        object(),
        SimpleNamespace(viewport=object()),
        resolved_detail=object(),
        plan=plan,
    )
    assert result.chart_type == "regional"
    assert result.plan is plan
    assert result.legends is sentinel
    assert captured["resolved_detail"] is not None


def test_default_plan_is_inferred_and_inputs_are_forwarded(monkeypatch):
    import wenu.charts.automatic_legends as module

    chart = type("BinocularChart", (), {})()
    detail = object()
    sentinel = SimpleNamespace(artists=("stars",))
    captured = {}

    def fake_draw(
        ax,
        actual_chart,
        sky,
        style,
        plan,
        rendering_result,
        **kwargs,
    ):
        captured["plan"] = plan
        captured.update(kwargs)
        return sentinel

    monkeypatch.setattr(module, "draw_rendered_chart_legends", fake_draw)
    result = module.draw_automatic_chart_legends(
        object(),
        chart,
        object(),
        object(),
        object(),
        resolved_detail=detail,
    )
    assert result.chart_type == "binocular"
    assert result.plan.chart_type == "binocular"
    assert not result.plan.objects.enabled
    assert result.plan.stars.enabled
    assert captured["resolved_detail"] is detail
