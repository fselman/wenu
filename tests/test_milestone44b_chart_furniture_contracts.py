"""Milestone 44B canonical chart-furniture contracts."""

from dataclasses import FrozenInstanceError
from pathlib import Path
from types import SimpleNamespace

import pytest

from wenu import (
    ChartFurnitureOptions,
    FooterOptions,
    LegendOptions,
    PoleAnnotations,
    ReferenceAnnotations,
    ReferencePlaneAnnotation,
    RegionalChart,
    ResolvedChartFurnitureOptions,
    compose_chart,
)


def chart():
    return RegionalChart(
        center_alt_deg=35.0,
        center_az_deg=210.0,
        field_width_deg=30.0,
        field_height_deg=20.0,
    )


def test_defaults_preserve_the_v05_composition_contract():
    composition = compose_chart(chart(), style="atlas")

    assert composition.legends is None
    assert composition.furniture is None


def test_no_furniture_keeps_support_for_geometry_only_chart_doubles():
    subject = SimpleNamespace(chart_context=chart().chart_context)
    composition = compose_chart(subject, style="atlas")

    assert composition.context is subject.chart_context
    assert composition.legends is None
    assert composition.furniture is None


def test_furniture_resolves_independent_backend_neutral_concerns():
    options = ChartFurnitureOptions(
        references=ReferenceAnnotations(
            ecliptic=ReferencePlaneAnnotation(
                state="labeled",
                label="Ecliptic",
                anchor=(0.25, -0.5),
            ),
            galactic_plane=ReferencePlaneAnnotation(
                state="line",
                label="Galactic plane",
            ),
        ),
        poles=PoleAnnotations(
            celestial="visible",
            ecliptic="both",
            galactic="none",
            labels=False,
        ),
        footer=FooterOptions(
            application=True,
            include_version=True,
            copyright="Copyright Example",
        ),
        legends=LegendOptions(stellar_counts=True),
    )

    composition = compose_chart(
        chart(),
        style="cartoon",
        mode="presentation",
        furniture=options,
    )

    assert isinstance(composition.furniture, ResolvedChartFurnitureOptions)
    assert composition.furniture.references.ecliptic.labeled is True
    assert composition.furniture.references.ecliptic.anchor == (0.25, -0.5)
    assert composition.furniture.references.galactic_plane.enabled is True
    assert composition.furniture.poles.celestial == "visible"
    assert composition.furniture.poles.ecliptic == "both"
    assert composition.furniture.poles.labels is False
    assert composition.furniture.footer.application_name == "Wenu"
    assert composition.furniture.footer.include_version is True
    assert composition.legends is composition.furniture.legends
    assert composition.legends.stellar_counts is True


def test_reference_states_support_none_line_and_labeled():
    omitted = ReferencePlaneAnnotation(label="Ecliptic")
    line = ReferencePlaneAnnotation(state="line", label="Ecliptic")
    labeled = ReferencePlaneAnnotation(state="labeled", label="Ecliptic")

    assert (omitted.enabled, omitted.labeled) == (False, False)
    assert (line.enabled, line.labeled) == (True, False)
    assert (labeled.enabled, labeled.labeled) == (True, True)


def test_automatic_and_explicit_reference_anchors_are_distinct():
    automatic = ReferencePlaneAnnotation(
        state="labeled",
        label="Galactic plane",
    )
    explicit = ReferencePlaneAnnotation(
        state="labeled",
        label="Galactic plane",
        anchor=[1, 2],
    )

    assert automatic.anchor is None
    assert explicit.anchor == (1.0, 2.0)


@pytest.mark.parametrize("selection", ["none", "visible", "both"])
def test_pole_selection_contract(selection):
    poles = PoleAnnotations(celestial=selection)
    assert poles.celestial == selection


def test_invalid_furniture_values_fail_early():
    with pytest.raises(ValueError, match="state"):
        ReferencePlaneAnnotation(state="labels", label="Ecliptic")
    with pytest.raises(ValueError, match="requires text"):
        ReferencePlaneAnnotation(state="labeled")
    with pytest.raises(ValueError, match="finite"):
        ReferencePlaneAnnotation(
            state="labeled",
            label="Ecliptic",
            anchor=(float("nan"), 0.0),
        )
    with pytest.raises(ValueError, match="pole selection"):
        PoleAnnotations(galactic="north")
    with pytest.raises(ValueError, match="requires a name"):
        FooterOptions(application=True, application_name=" ")


def test_furniture_values_are_immutable():
    options = ChartFurnitureOptions()
    with pytest.raises(FrozenInstanceError):
        options.footer = FooterOptions(application=True)


def test_style_and_mode_do_not_change_chart_geometry():
    request = ChartFurnitureOptions(
        references=ReferenceAnnotations(
            ecliptic=ReferencePlaneAnnotation(
                state="labeled",
                label="Ecliptic",
            )
        ),
        poles=PoleAnnotations(celestial="both"),
    )
    subject = chart()
    atlas = compose_chart(
        subject,
        style="atlas",
        mode="print",
        furniture=request,
    )
    cartoon = compose_chart(
        subject,
        style="cartoon",
        mode="presentation",
        furniture=request,
    )

    assert atlas.context == cartoon.context
    assert atlas.furniture == cartoon.furniture


def test_existing_legends_argument_remains_compatible():
    legends = LegendOptions(
        objects=False,
        stellar_magnitudes=True,
        context=False,
        stellar_counts=True,
    )
    composition = compose_chart(chart(), style="atlas", legends=legends)

    assert composition.furniture is None
    assert composition.legends.plan.objects.enabled is False
    assert composition.legends.plan.stars.enabled is True
    assert composition.legends.context is False
    assert composition.legends.stellar_counts is True


def test_ambiguous_legend_arguments_are_rejected():
    with pytest.raises(ValueError, match="not both"):
        compose_chart(
            chart(),
            style="atlas",
            legends=LegendOptions(),
            furniture=ChartFurnitureOptions(),
        )


def test_policy_modules_do_not_import_matplotlib():
    root = Path(__file__).resolve().parents[1]
    for relative in (
        "src/wenu/charts/furniture.py",
        "src/wenu/charts/legend_plan.py",
    ):
        text = (root / relative).read_text(encoding="utf-8")
        assert "matplotlib" not in text.lower()
