"""Milestone 43C.1 contracts for canonical legend policy."""

import pytest

from wenu import (
    ChartLegendPlan,
    LegendOptions,
    LegendPlacement,
    RegionalChart,
    ResolvedLegendOptions,
    compose_chart,
)


def regional_chart():
    return RegionalChart(
        center_alt_deg=35.0,
        center_az_deg=210.0,
        field_width_deg=30.0,
        field_height_deg=20.0,
    )


def test_legends_are_opt_in_during_migration():
    composition = compose_chart(regional_chart(), style="atlas")
    assert composition.legends is None


def test_legend_families_resolve_independently():
    composition = compose_chart(
        regional_chart(),
        style="atlas",
        legends=LegendOptions(
            objects=False,
            stellar_magnitudes=True,
            context=False,
        ),
    )
    assert isinstance(composition.legends, ResolvedLegendOptions)
    assert composition.legends.plan.chart_type == "regional"
    assert composition.legends.plan.objects.enabled is False
    assert composition.legends.plan.stars.enabled is True
    assert composition.legends.context is False


def test_existing_plan_is_reused_with_family_switches():
    plan = ChartLegendPlan(
        chart_type="regional",
        objects=LegendPlacement(location="lower left"),
        stars=LegendPlacement(location="upper left"),
    )
    resolved = LegendOptions(
        objects=True,
        stellar_magnitudes=False,
        context=True,
        plan=plan,
    ).resolve("regional")
    assert resolved.plan.objects.location == "lower left"
    assert resolved.plan.objects.enabled is True
    assert resolved.plan.stars.location == "upper left"
    assert resolved.plan.stars.enabled is False
    assert resolved.context is True


def test_direct_plan_remains_a_composition_shortcut():
    plan = ChartLegendPlan(
        chart_type="regional",
        objects=LegendPlacement(),
        stars=LegendPlacement(),
    )
    composition = compose_chart(
        regional_chart(),
        style="atlas",
        legends=plan,
    )
    assert composition.legends.plan == plan


def test_plan_for_wrong_chart_type_is_rejected():
    plan = ChartLegendPlan(
        chart_type="planisphere",
        objects=LegendPlacement(),
        stars=LegendPlacement(),
    )
    with pytest.raises(ValueError, match="does not match"):
        LegendOptions(plan=plan).resolve("regional")
