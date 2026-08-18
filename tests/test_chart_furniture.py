"""Current chart furniture contracts."""

# Contracts consolidated from test_milestone44b_chart_furniture_contracts.py.
"""Milestone 44B canonical chart-furniture contracts."""

from dataclasses import FrozenInstanceError
from pathlib import Path
from types import SimpleNamespace

import pytest

from wenu import (
    ChartContextOptions,
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


@pytest.mark.parametrize(
    "selection", ["none", "visible", "north", "south", "both"]
)
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
        PoleAnnotations(galactic="east")
    with pytest.raises(ValueError, match="requires a name"):
        FooterOptions(application=True, application_name=" ")


def test_furniture_values_are_immutable():
    options = ChartFurnitureOptions()
    with pytest.raises(FrozenInstanceError):
        options.footer = FooterOptions(application=True)


def test_ecliptic_keypoint_state_is_semantic_and_validated():
    markers = ReferenceAnnotations(ecliptic_keypoints="markers")
    labeled = ReferenceAnnotations(ecliptic_keypoints="labeled")

    assert markers.ecliptic_keypoints_enabled is True
    assert markers.ecliptic_keypoints_labeled is False
    assert labeled.ecliptic_keypoints_labeled is True
    with pytest.raises(ValueError, match="ecliptic_keypoints"):
        ReferenceAnnotations(ecliptic_keypoints="visible")


def test_ecliptic_keypoint_legend_has_four_semantic_names():
    references = ReferenceAnnotations(ecliptic_keypoint_legend=True)

    assert references.ecliptic_keypoint_legend is True
    assert references.ecliptic_keypoint_names == (
        "March equinox",
        "June solstice",
        "September equinox",
        "December solstice",
    )
    with pytest.raises(ValueError, match="four non-empty"):
        ReferenceAnnotations(ecliptic_keypoint_names=("one",) * 3)


def test_stellar_legend_can_request_one_reference_magnitude():
    resolved = LegendOptions(
        stellar_reference_magnitude=3,
        stellar_label_suffix=" mag",
    ).resolve("regional")

    assert resolved.stellar_reference_magnitude == 3
    assert resolved.stellar_label_suffix == " mag"


def test_stellar_legend_can_request_a_range_on_the_sky_background():
    resolved = LegendOptions(
        stellar_reference_range=(0, 5),
        stellar_background="sky",
    ).resolve("regional")

    assert resolved.stellar_reference_range == (0, 5)
    assert resolved.stellar_background == "sky"
    with pytest.raises(ValueError):
        LegendOptions(stellar_reference_range=(5, 0)).resolve("regional")
    with pytest.raises(ValueError):
        LegendOptions(stellar_background="mask").resolve("regional")


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

# Contracts consolidated from test_milestone44d_credits_and_stellar_counts.py.
"""Milestone 44D chart credits and cumulative stellar counts."""

from types import SimpleNamespace

import matplotlib.pyplot as plt
import numpy as np

from wenu import FooterOptions, Viewport
from wenu.charts.footer_furniture import (
    draw_chart_footer,
    resolved_footer_text,
)
from wenu.charts.magnitude_legend import (
    cumulative_visible_star_counts,
    stellar_magnitude_scale,
)
from wenu.charts.magnitude_legend_matplotlib import (
    stellar_magnitude_handles,
)
from wenu.charts.rendered_legend_composition import _resolved_footprint
from wenu import BinocularChart


def geometry(magnitudes, x=None, y=None):
    magnitudes = np.asarray(magnitudes, dtype=float)
    spherical = SimpleNamespace(
        metadata={"magnitude": magnitudes}
    )
    projected = SimpleNamespace(
        x=np.asarray(
            np.zeros(magnitudes.size) if x is None else x,
            dtype=float,
        ),
        y=np.asarray(
            np.zeros(magnitudes.size) if y is None else y,
            dtype=float,
        ),
    )
    return spherical, projected


def test_cumulative_counts_use_only_rendered_geometry():
    spherical, projected = geometry([-1.0, 0.4, 1.8, 2.2])
    counts = cumulative_visible_star_counts(
        spherical,
        projected,
        Viewport(-1.0, 1.0, -1.0, 1.0),
        (-1, 0, 1, 2),
        effective_limit=2.0,
    )

    assert counts == (1, 1, 2, 3)


def test_counts_respect_viewport_and_custom_footprint():
    spherical, projected = geometry(
        [0.0, 0.5, 1.0, 1.5],
        x=[0.0, 0.4, 0.8, 2.0],
        y=[0.0, 0.0, 0.0, 0.0],
    )
    counts = cumulative_visible_star_counts(
        spherical,
        projected,
        Viewport(-1.0, 1.0, -1.0, 1.0),
        (0, 1, 2),
        effective_limit=2.0,
        footprint_contains=lambda x, y: np.hypot(x, y) <= 0.5,
    )

    assert counts == (1, 2, 2)


def test_circular_chart_predicate_excludes_viewport_corners():
    chart = BinocularChart(45.0, 180.0)
    contains = _resolved_footprint(chart, None)
    viewport = chart.chart_context.viewport
    center_x = (viewport.x_min + viewport.x_max) / 2.0
    center_y = (viewport.y_min + viewport.y_max) / 2.0

    assert bool(contains(np.asarray([center_x]), np.asarray([center_y]))[0])
    assert not bool(
        contains(
            np.asarray([viewport.x_max]),
            np.asarray([viewport.y_max]),
        )[0]
    )


def test_explicit_and_vertex_stars_count_when_they_were_rendered():
    # The rendered geometry is intentionally the authority: these two
    # retained stars need no catalogue-global identity lookup here.
    spherical, projected = geometry([1.2, 1.9])
    counts = cumulative_visible_star_counts(
        spherical,
        projected,
        Viewport(-1.0, 1.0, -1.0, 1.0),
        (1, 2),
        effective_limit=2.0,
    )

    assert counts == (0, 2)


def test_count_labels_are_optional_and_keep_signed_magnitudes():
    plain = stellar_magnitude_scale(-1.0, 1.0)
    counted = stellar_magnitude_scale(
        -1.0,
        1.0,
        cumulative_counts=(1, 3, 8),
    )

    assert [handle.get_label() for handle in stellar_magnitude_handles(plain)] == [
        "-1",
        "0",
        "1",
    ]
    assert [
        handle.get_label() for handle in stellar_magnitude_handles(counted)
    ] == ["-1 (1)", "0 (3)", "1 (8)"]


def test_footer_sides_are_independent_and_version_is_resolved():
    left = resolved_footer_text(
        FooterOptions(copyright="© Chart author"),
        package_version="9.8.7",
    )
    right = resolved_footer_text(
        FooterOptions(application=True),
        package_version="9.8.7",
    )

    assert left == ("© Chart author", None)
    assert right == (None, "Wenu 9.8.7")


def test_footer_resolves_version_from_installed_package_metadata(monkeypatch):
    import wenu.charts.footer_furniture as footer_module

    monkeypatch.setattr(footer_module, "version", lambda name: "0.8.0")

    assert footer_module.installed_wenu_version() == "0.8.0"
    assert footer_module.resolved_footer_text(
        FooterOptions(application=True)
    ) == (None, "Wenu 0.8.0")


def test_footer_artists_use_figure_margin_and_reserve_axes_space():
    figure, ax = plt.subplots(figsize=(7.0, 5.0))
    renderer = SimpleNamespace(ax=ax)
    mode = SimpleNamespace(font_scale=1.0)
    result = draw_chart_footer(
        renderer,
        FooterOptions(
            application=True,
            copyright="© Chart author",
        ),
        mode,
        package_version="9.8.7",
    )

    assert [artist.get_ha() for artist in result.artists] == ["left", "right"]
    assert [artist.get_position()[0] for artist in result.artists] == [0.01, 0.99]
    assert all(artist.get_position()[1] < ax.get_position().y0 for artist in result.artists)
    plt.close(figure)


def test_empty_footer_draws_nothing_and_changes_no_layout():
    figure, ax = plt.subplots()
    before = ax.get_position().bounds
    result = draw_chart_footer(
        SimpleNamespace(ax=ax),
        FooterOptions(),
        SimpleNamespace(font_scale=1.0),
    )

    assert result is None
    assert ax.get_position().bounds == before
    plt.close(figure)

# Contracts consolidated from test_milestone43c1_legend_policy.py.
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


def test_context_lines_are_resolved_as_immutable_text():
    resolved = LegendOptions(
        context_lines=("Location", "Date", "Time"),
    ).resolve("planisphere")

    assert resolved.context_lines == ("Location", "Date", "Time")


def test_declarative_chart_context_options_are_typed_and_immutable():
    context = ChartContextOptions(
        center=True,
        grid=False,
        location=True,
        date=True,
        local_time=True,
    )
    furniture = ChartFurnitureOptions(context=context)

    assert furniture.context is context
    assert context.grid is False
    with pytest.raises(TypeError, match="ChartContextOptions"):
        ChartFurnitureOptions(context=object())


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
