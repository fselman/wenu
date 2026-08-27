"""Current legend export contracts."""

# Contracts consolidated from test_milestone40j_automatic_dual_legends.py.
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

# Contracts consolidated from test_milestone40j_dual_legend_coordinator.py.
from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.legend import Legend

import wenu.charts.legend_composition as composition
from wenu import (
    ComposedChartLegends,
    LegendPlacement,
    default_chart_legend_plan,
    draw_planned_chart_legends,
)


class Viewport:
    x_min = -1.0
    x_max = 1.0
    y_min = -1.0
    y_max = 1.0


def star_geometry():
    return (
        SimpleNamespace(
            metadata={"magnitude": np.asarray([-1.0, 0.0, 2.0])}
        ),
        SimpleNamespace(
            x=np.asarray([0.0, 0.2, 0.4]),
            y=np.asarray([0.0, 0.2, 0.4]),
        ),
    )


def fake_object_drawer(
    ax,
    chart,
    sky,
    style,
    *,
    grid=None,
    title=None,
    context_lines=None,
):
    ax.plot([], [], marker="s", label="Galaxy")
    return ax.legend(title=title or "Objects")


def test_coordinator_draws_and_preserves_both_legends(monkeypatch):
    monkeypatch.setattr(
        composition,
        "draw_chart_legend",
        fake_object_drawer,
    )
    figure, ax = plt.subplots()
    spherical, projected = star_geometry()
    result = draw_planned_chart_legends(
        ax,
        object(),
        object(),
        object(),
        default_chart_legend_plan("regional"),
        star_spherical=spherical,
        star_projected=projected,
        viewport=Viewport(),
        effective_limit=3.0,
    )
    assert isinstance(result, ComposedChartLegends)
    assert isinstance(result.objects, Legend)
    assert isinstance(result.stars.artist, Legend)
    assert len(result.artists) == 2
    assert result.objects in ax.get_children()
    assert result.stars.artist in ax.get_children()
    plt.close(figure)


def test_disabled_object_legend_is_not_called(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("object drawer must not be called")

    monkeypatch.setattr(composition, "draw_chart_legend", fail)
    figure, ax = plt.subplots()
    spherical, projected = star_geometry()
    result = draw_planned_chart_legends(
        ax,
        object(),
        object(),
        object(),
        default_chart_legend_plan("binocular"),
        star_spherical=spherical,
        star_projected=projected,
        viewport=Viewport(),
        effective_limit=3.0,
    )
    assert result.objects is None
    assert result.stars.drawn
    plt.close(figure)


def test_disabled_star_legend_is_not_drawn(monkeypatch):
    monkeypatch.setattr(
        composition,
        "draw_chart_legend",
        fake_object_drawer,
    )
    figure, ax = plt.subplots()
    spherical, projected = star_geometry()
    plan = default_chart_legend_plan("regional").with_stars(
        enabled=False
    )
    result = draw_planned_chart_legends(
        ax,
        object(),
        object(),
        object(),
        plan,
        star_spherical=spherical,
        star_projected=projected,
        viewport=Viewport(),
        effective_limit=3.0,
    )
    assert result.objects is not None
    assert result.stars is None
    assert result.artists == (result.objects,)
    plt.close(figure)


def test_explicit_anchor_is_applied():
    figure, ax = plt.subplots()
    legend = ax.legend([], [], loc="upper right")
    placement = LegendPlacement(
        location="lower left",
        anchor=(0.25, 0.35),
    )
    composition.apply_legend_placement(legend, placement)
    bounds = legend.get_bbox_to_anchor().bounds
    display_anchor = ax.transAxes.transform((0.25, 0.35))
    assert bounds[0] == display_anchor[0]
    assert bounds[1] == display_anchor[1]
    plt.close(figure)


def test_outside_placement_uses_an_automatic_anchor():
    figure, ax = plt.subplots()
    legend = ax.legend([], [], loc="upper right")
    placement = LegendPlacement(
        location="upper right",
        outside=True,
    )
    composition.apply_legend_placement(legend, placement)
    bounds = legend.get_bbox_to_anchor().bounds
    expected = ax.transAxes.transform((1.02, 1.0))
    assert bounds[0] == expected[0]
    assert bounds[1] == expected[1]
    plt.close(figure)


def test_public_api_exports_composition():
    from wenu import draw_planned_chart_legends as exported

    assert exported is draw_planned_chart_legends

# Contracts consolidated from test_milestone40j_dual_legend_plan.py.
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

# Contracts consolidated from test_milestone40j_render_with_legends.py.
from types import SimpleNamespace

from wenu import (
    RenderedChartWithLegends,
    render_chart_with_legends,
)


class m40j_render_with_legends_ComposedStyle:
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
    style = m40j_render_with_legends_ComposedStyle()
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

# Contracts consolidated from test_milestone40j_rendered_star_bridge.py.
from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

import wenu.charts.legend_composition as composition
from wenu import (
    RenderedStarGeometry,
    RenderedStarsNotFoundError,
    default_chart_legend_plan,
    draw_rendered_chart_legends,
    rendered_star_geometry,
)


class Stars:
    pass


class OtherLayer:
    pass


def geometries():
    spherical = SimpleNamespace(
        metadata={"magnitude": np.asarray([-1.0, 1.0, 3.0])}
    )
    projected = SimpleNamespace(
        x=np.asarray([0.0, 0.2, 0.4]),
        y=np.asarray([0.0, 0.2, 0.4]),
    )
    return spherical, projected


def rendering_result(star_layer=None):
    star_layer = Stars() if star_layer is None else star_layer
    spherical, projected = geometries()
    viewport = SimpleNamespace(
        x_min=-1.0,
        x_max=1.0,
        y_min=-1.0,
        y_max=1.0,
    )
    return SimpleNamespace(
        viewport=viewport,
        layers=(
            SimpleNamespace(
                layer=OtherLayer(),
                spherical=object(),
                projected=object(),
            ),
            SimpleNamespace(
                layer=star_layer,
                spherical=spherical,
                projected=projected,
            ),
        ),
    ), star_layer


def test_explicit_layer_identity_extracts_rendered_geometry():
    result, layer = rendering_result()
    resolved = rendered_star_geometry(result, star_layer=layer)
    assert isinstance(resolved, RenderedStarGeometry)
    assert resolved.layer is layer
    assert resolved.spherical is result.layers[1].spherical
    assert resolved.projected is result.layers[1].projected
    assert resolved.viewport is result.viewport


def test_sky_stars_identity_is_preferred():
    result, layer = rendering_result()
    sky = SimpleNamespace(stars=layer)
    resolved = rendered_star_geometry(result, sky=sky)
    assert resolved.layer is layer


def test_class_name_fallback_supports_stored_results():
    result, layer = rendering_result()
    resolved = rendered_star_geometry(result)
    assert resolved.layer is layer


def test_missing_stars_raise_clear_error():
    result, _ = rendering_result()
    result = SimpleNamespace(
        viewport=result.viewport,
        layers=result.layers[:1],
    )
    with pytest.raises(
        RenderedStarsNotFoundError,
        match="no matching Stars",
    ):
        rendered_star_geometry(result)


def test_magnitude_metadata_is_required():
    result, layer = rendering_result()
    bad = SimpleNamespace(
        viewport=result.viewport,
        layers=(
            SimpleNamespace(
                layer=layer,
                spherical=SimpleNamespace(metadata={}),
                projected=result.layers[1].projected,
            ),
        ),
    )
    with pytest.raises(ValueError, match="magnitude"):
        rendered_star_geometry(bad, star_layer=layer)


def test_rendered_coordinator_reuses_geometry(monkeypatch):
    monkeypatch.setattr(
        composition,
        "draw_chart_legend",
        lambda ax, *args, **kwargs: ax.legend([], []),
    )
    result, layer = rendering_result()
    sky = SimpleNamespace(stars=layer)
    figure, ax = plt.subplots()
    legends = draw_rendered_chart_legends(
        ax,
        object(),
        sky,
        object(),
        default_chart_legend_plan("regional"),
        result,
        effective_limit=3.0,
    )
    assert legends.stars.statistics.visible_count == 3
    assert len(legends.artists) == 2
    plt.close(figure)


def test_disabled_stars_do_not_require_a_rendered_star_layer(monkeypatch):
    monkeypatch.setattr(
        composition,
        "draw_chart_legend",
        lambda ax, *args, **kwargs: ax.legend([], []),
    )
    result, _ = rendering_result()
    result = SimpleNamespace(
        viewport=result.viewport,
        layers=result.layers[:1],
    )
    plan = default_chart_legend_plan("regional").with_stars(
        enabled=False
    )
    figure, ax = plt.subplots()
    legends = draw_rendered_chart_legends(
        ax,
        object(),
        SimpleNamespace(stars=None),
        object(),
        plan,
        result,
        effective_limit=3.0,
    )
    assert legends.objects is not None
    assert legends.stars is None
    plt.close(figure)


def test_public_api_exports_rendered_bridge():
    from wenu import draw_rendered_chart_legends as exported

    assert exported is draw_rendered_chart_legends

# Contracts consolidated from test_milestone40j_resolved_legend_inputs.py.
from types import SimpleNamespace

import pytest

from wenu import (
    ResolvedStellarLegendInputs,
    resolve_stellar_legend_inputs,
)


class m40j_resolved_legend_inputs_ComposedStyle:
    stars = SimpleNamespace(area_scale=0.75, color="#123456")

    def as_publication_style(self):
        return SimpleNamespace(
            star_area_scale=self.stars.area_scale,
            star_color=self.stars.color,
        )


def test_inputs_resolve_from_detail_and_composed_style():
    detail = SimpleNamespace(star_magnitude_limit=6.25)
    inputs = resolve_stellar_legend_inputs(detail, m40j_resolved_legend_inputs_ComposedStyle())
    assert inputs == ResolvedStellarLegendInputs(
        effective_limit=6.25,
        area_scale=0.75,
        color="#123456",
        alpha=1.0,
    )


def test_publication_style_is_supported_directly():
    style = SimpleNamespace(
        star_area_scale=1.4,
        star_color="white",
        star_alpha=0.8,
    )
    inputs = resolve_stellar_legend_inputs(
        SimpleNamespace(star_magnitude_limit=4.0),
        style,
    )
    assert inputs.area_scale == pytest.approx(1.4)
    assert inputs.color == "white"
    assert inputs.alpha == pytest.approx(0.8)


def test_explicit_values_override_resolved_sources():
    inputs = resolve_stellar_legend_inputs(
        SimpleNamespace(star_magnitude_limit=6.0),
        m40j_resolved_legend_inputs_ComposedStyle(),
        effective_limit=5.0,
        area_scale=2.0,
        color="red",
        alpha=0.5,
    )
    assert inputs == ResolvedStellarLegendInputs(
        effective_limit=5.0,
        area_scale=2.0,
        color="red",
        alpha=0.5,
    )


def test_missing_resolved_limit_is_rejected():
    with pytest.raises(ValueError, match="no stellar magnitude limit"):
        resolve_stellar_legend_inputs(
            SimpleNamespace(star_magnitude_limit=None),
            m40j_resolved_legend_inputs_ComposedStyle(),
        )


def test_explicit_limit_preserves_legacy_call_pattern():
    inputs = resolve_stellar_legend_inputs(
        None,
        m40j_resolved_legend_inputs_ComposedStyle(),
        effective_limit=3.0,
    )
    assert inputs.effective_limit == pytest.approx(3.0)


def test_invalid_area_scale_is_rejected():
    with pytest.raises(ValueError, match="positive"):
        resolve_stellar_legend_inputs(
            SimpleNamespace(star_magnitude_limit=5.0),
            m40j_resolved_legend_inputs_ComposedStyle(),
            area_scale=0.0,
        )

# Contracts consolidated from test_milestone43c2_canonical_legend_export.py.
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

# Contracts consolidated from test_milestone43f_atlas_legend_example.py.
"""Canonical-workflow contracts for the atlas legend example."""

import ast
from pathlib import Path


EXAMPLE = Path("tests/fixtures/example_regressions/atlas_style.py")


def source():
    return EXAMPLE.read_text(encoding="utf-8")


def calls_named(tree, name):
    return tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and (
            (
                isinstance(node.func, ast.Name)
                and node.func.id == name
            )
            or (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == name
            )
        )
    )


def test_example_requests_all_canonical_atlas_legends():
    text = source()
    assert 'style="atlas"' in text
    assert "mode=PrintMode(width_inches=10.0, dpi=600)" in text
    assert "objects=True" in text
    assert "stellar_magnitudes=True" in text
    assert "context=True" in text


def test_example_exports_composition_and_saves_only_once():
    tree = ast.parse(source(), filename=str(EXAMPLE))
    exports = calls_named(tree, "export")

    assert len(exports) == 1
    assert any(
        keyword.arg == "composition"
        for keyword in exports[0].keywords
    )
    assert calls_named(tree, "savefig") == ()
    assert calls_named(tree, "draw_chart_legend") == ()


def test_example_has_no_legacy_legend_or_export_coordination_imports():
    tree = ast.parse(source(), filename=str(EXAMPLE))
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    assert "draw_chart_legend" not in imported
    assert "ExportOptions" not in imported

# Contracts consolidated from test_milestone43f_composed_chart_export.py.
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



def test_regional_furniture_declares_title_and_legend_hierarchy():
    from wenu.chart_document import assign_furniture_semantics

    assigned = []
    title = SimpleNamespace(get_text=lambda: "Chart title")
    renderer = SimpleNamespace(
        ax=SimpleNamespace(title=title),
        assign_semantic_identity=lambda artists, identity: assigned.append(
            (artists, identity)
        ),
    )
    class Legend:
        legend_handles = ()

        def __init__(self):
            self.frame = SimpleNamespace(set_gid=lambda value: None)
            self.title = SimpleNamespace(
                get_text=lambda: "",
                set_gid=lambda value: None,
            )

        def get_frame(self):
            return self.frame

        def get_title(self):
            return self.title

        def get_texts(self):
            return ()

    object_legend = Legend()
    stellar_legend = Legend()
    rendering = SimpleNamespace(
        legends=SimpleNamespace(
            legends=SimpleNamespace(
                objects=object_legend,
                stars=SimpleNamespace(artist=stellar_legend),
            )
        )
    )

    assign_furniture_semantics(renderer, rendering)

    assert [identity.semantic_path for _, identity in assigned] == [
        ("furniture", "title"),
        (
            "furniture",
            "legends",
            "chart_information_and_object_key",
        ),
        ("furniture", "legends", "stellar_magnitude_scale"),
    ]
    assert [artists[0] for artists, _ in assigned] == [
        title,
        object_legend,
        stellar_legend,
    ]
    assert all(
        identity.edit_policy.value == "layout"
        for _, identity in assigned
    )



def test_legend_symbols_and_labels_receive_matching_semantic_names():
    from wenu.chart_document import _name_legend_contents

    class Item:
        def __init__(self, text=""):
            self.text = text
            self.gid = None

        def get_text(self):
            return self.text

        def set_gid(self, value):
            self.gid = value

    frame = Item()
    title = Item("Stars")
    handles = (Item(), Item())
    labels = (Item("Open cluster"), Item("3"))
    legend = SimpleNamespace(
        legend_handles=handles,
        get_frame=lambda: frame,
        get_title=lambda: title,
        get_texts=lambda: labels,
    )

    _name_legend_contents(legend, "key")

    assert frame.gid == "key-frame"
    assert title.gid == "key-title"
    assert [item.gid for item in handles] == [
        "open-cluster-symbol",
        "3-symbol",
    ]
    assert [item.gid for item in labels] == [
        "open-cluster-label",
        "3-label",
    ]

    magnitude_handle = Item()
    magnitude_label = Item("3")
    magnitude = SimpleNamespace(
        legend_handles=(magnitude_handle,),
        get_frame=lambda: Item(),
        get_title=lambda: Item(),
        get_texts=lambda: (magnitude_label,),
    )
    _name_legend_contents(
        magnitude,
        "magnitude-scale",
        entry_prefix="mag",
    )
    assert magnitude_handle.gid == "mag-3-symbol"
    assert magnitude_label.gid == "mag-3-label"
