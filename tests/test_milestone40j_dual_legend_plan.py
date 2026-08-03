import dataclasses

import pytest

from wenu import (
    ChartLegendPlan,
    LegendPlacement,
    default_chart_legend_plan,
)


@pytest.mark.parametrize(
    "chart_type",
    ("regional", "planisphere", "circumpolar", "binocular"),
)
def test_every_public_chart_type_has_a_plan(chart_type):
    plan = default_chart_legend_plan(chart_type)
    assert isinstance(plan, ChartLegendPlan)
    assert plan.chart_type == chart_type
    assert plan.stars.enabled


def test_regional_legends_are_independent():
    plan = default_chart_legend_plan("regional")
    assert plan.objects.location == "upper right"
    assert plan.stars.location == "lower right"
    assert plan.objects is not plan.stars


def test_circumpolar_avoids_putting_both_legends_on_same_side():
    plan = default_chart_legend_plan("circumpolar")
    assert plan.objects.location == "upper right"
    assert plan.stars.location == "lower left"


def test_binocular_defaults_to_a_minimal_object_legend():
    plan = default_chart_legend_plan("binocular")
    assert not plan.objects.enabled
    assert plan.stars.enabled
    assert plan.stars.location == "lower right"
    assert plan.stars.outside


def test_plan_can_be_overridden_without_mutation():
    original = default_chart_legend_plan("planisphere")
    changed = original.with_stars(
        location="upper left",
        outside=True,
        anchor=(1.02, 1.0),
    )
    assert original.stars.location == "lower right"
    assert changed.stars.location == "upper left"
    assert changed.stars.outside
    assert changed.stars.anchor == (1.02, 1.0)


def test_object_and_star_overrides_are_separate():
    original = default_chart_legend_plan("regional")
    changed = original.with_objects(enabled=False)
    assert not changed.objects.enabled
    assert changed.stars == original.stars


def test_contracts_are_immutable():
    plan = default_chart_legend_plan("regional")
    with pytest.raises(dataclasses.FrozenInstanceError):
        plan.chart_type = "binocular"


def test_invalid_chart_type_is_rejected():
    with pytest.raises(ValueError, match="chart_type"):
        default_chart_legend_plan("unknown")


def test_anchor_must_be_a_pair():
    with pytest.raises(ValueError, match="two values"):
        LegendPlacement(anchor=(1.0,))


def test_contract_has_no_rendering_dependency():
    from pathlib import Path
    import wenu.charts.legend_plan as module

    source = Path(module.__file__).read_text(encoding="utf-8").lower()
    assert "matplotlib" not in source
    assert "renderer" not in source
