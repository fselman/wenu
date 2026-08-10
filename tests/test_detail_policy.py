"""Current detail policy contracts."""

# Contracts consolidated from test_milestone40c_adaptive_detail.py.
from dataclasses import FrozenInstanceError

import pytest

from wenu import (
    AdaptiveDetailPolicy,
    AtlasChartStyle,
    BinocularChart,
    DetailOverrides,
    FieldDetailLevel,
    FullSkyChart,
    PrintMode,
    RegionalChart,
    compose_chart,
)


def regional(width, height):
    return RegionalChart(
        center_alt_deg=35.0,
        center_az_deg=210.0,
        field_width_deg=width,
        field_height_deg=height,
    )


def resolve(chart, *, width_inches=7.0, policy=None):
    policy = AdaptiveDetailPolicy() if policy is None else policy
    mode = PrintMode(width_inches=width_inches).resolve(
        chart.chart_context
    )
    return policy.resolve(chart.chart_context, mode)


def test_narrower_fields_receive_deeper_stellar_limits():
    full_sky = resolve(FullSkyChart())
    regional_detail = resolve(regional(30.0, 20.0))
    binocular = resolve(
        BinocularChart(
            center_alt_deg=35.0,
            center_az_deg=210.0,
            field_diameter_deg=6.5,
        )
    )
    assert (
        full_sky.star_magnitude_limit
        < regional_detail.star_magnitude_limit
        < binocular.star_magnitude_limit
    )
    assert full_sky.star_magnitude_limit == pytest.approx(
        6.19,
        abs=0.02,
    )
    assert binocular.star_magnitude_limit > 11.0


def test_field_coverage_not_aspect_ratio_drives_detail():
    square = resolve(regional(30.0, 20.0))
    wide = resolve(regional(60.0, 10.0))
    assert wide.star_magnitude_limit == pytest.approx(
        square.star_magnitude_limit
    )
    assert wide.minimum_open_cluster_size_arcmin == pytest.approx(
        square.minimum_open_cluster_size_arcmin
    )


def test_output_size_is_only_a_small_bounded_correction():
    chart = regional(30.0, 20.0)
    small = resolve(chart, width_inches=5.0)
    large = resolve(chart, width_inches=14.0)
    assert large.star_magnitude_limit > small.star_magnitude_limit
    assert (
        large.star_magnitude_limit
        - small.star_magnitude_limit
    ) < 0.6


def test_wide_fields_suppress_only_crowded_specialized_layers():
    detail = resolve(FullSkyChart())
    assert detail.layer_enabled("stars")
    assert detail.layer_enabled("milky_way")
    assert detail.layer_enabled("galaxies")
    assert not detail.layer_enabled("open_clusters")
    assert not detail.layer_enabled("planetary_nebulae")
    assert not detail.layer_enabled("supernova_remnants")


def test_explicit_layer_and_magnitude_overrides_have_final_precedence():
    enabled = frozenset(
        {
            "stars",
            "constellation_lines",
            "constellation_labels",
        }
    )
    composition = compose_chart(
        regional(30.0, 20.0),
        style=AtlasChartStyle(),
        detail=AdaptiveDetailPolicy(),
        detail_overrides=DetailOverrides(
            star_magnitude_limit=4.5,
            enabled_layers=enabled,
        ),
    )
    assert composition.detail.star_magnitude_limit == 4.5
    assert composition.detail.enabled_layers == enabled
    assert not composition.detail.layer_enabled("galaxies")


def test_custom_profile_is_interpolated_in_log_field_span():
    policy = AdaptiveDetailPolicy(
        levels=(
            FieldDetailLevel(
                10.0, 10.0, 12.0, 1.0, 1.0, 1.0, 1.0, 1.0
            ),
            FieldDetailLevel(
                40.0, 6.0, 10.0, 9.0, 9.0, 9.0, 9.0, 0.5
            ),
        ),
        output_magnitude_adjustment_per_octave=0.0,
        adapt_enabled_layers=False,
    )
    detail = resolve(regional(20.0, 20.0), policy=policy)
    assert detail.star_magnitude_limit == pytest.approx(8.0)
    assert detail.minimum_open_cluster_size_arcmin == pytest.approx(5.0)
    assert detail.enabled_layers is None


def test_adaptive_results_are_immutable():
    detail = resolve(regional(30.0, 20.0))
    with pytest.raises(FrozenInstanceError):
        detail.star_magnitude_limit = 12.0


def test_adaptive_detail_contract_has_no_backend_dependency():
    from pathlib import Path
    import wenu.charts.detail as detail_module

    source = Path(detail_module.__file__).read_text().lower()
    assert "matplotlib" not in source

# Contracts consolidated from test_milestone40d_detail_application.py.
from types import SimpleNamespace

from wenu.charts.detail import ResolvedDetail
from wenu.charts.detail_application import (
    apply_resolved_detail,
    merge_layer_options,
)


class m40d_detail_application_Layer:
    def __init__(self, name, magnitude_limit=None):
        self.layer_name = name
        self.magnitude_limit = magnitude_limit
        self.loads = 0

    def load(self):
        self.loads += 1


def m40d_detail_application_fake_sky():
    stars = m40d_detail_application_Layer("stars", 6.0)
    galaxies = m40d_detail_application_Layer("galaxies", 10.0)
    open_clusters = m40d_detail_application_Layer("open_clusters")
    planetary = m40d_detail_application_Layer("planetary_nebulae")
    labels = m40d_detail_application_Layer("constellation_labels")
    return SimpleNamespace(
        stars=stars,
        galaxies=galaxies,
        layers=(
            stars,
            galaxies,
            open_clusters,
            planetary,
            labels,
        ),
    )


def test_detail_applies_catalogue_limits_and_geometry_thresholds():
    sky = m40d_detail_application_fake_sky()
    detail = ResolvedDetail(
        star_magnitude_limit=8.5,
        galaxy_magnitude_limit=11.0,
        minimum_open_cluster_size_arcmin=4.0,
        minimum_planetary_nebula_size_arcmin=1.0,
    )
    applied = apply_resolved_detail(sky, detail)
    assert sky.stars.magnitude_limit == 6.0
    assert sky.galaxies.magnitude_limit == 10.0
    assert sky.stars.loads == sky.galaxies.loads == 0
    assert applied.reloaded_layers == ()
    assert applied.layer_options["stars"]["geometry"] == {
        "magnitude_limit": 8.5,
    }
    assert applied.layer_options["galaxies"]["geometry"] == {
        "magnitude_limit": 11.0,
    }
    assert applied.layer_options["open_clusters"]["geometry"] == {
        "minimum_size_arcmin": 4.0,
    }
    assert applied.layer_options["planetary_nebulae"]["geometry"] == {
        "minimum_size_arcmin": 1.0,
    }


def test_disabled_layers_are_expressed_without_mutating_registry():
    sky = m40d_detail_application_fake_sky()
    detail = ResolvedDetail(
        enabled_layers=frozenset({"stars", "constellation_labels"})
    )
    before = sky.layers
    applied = apply_resolved_detail(
        sky,
        detail,
        reload_catalogues=False,
    )
    assert applied.layer_options["stars"]["enabled"] is True
    assert applied.layer_options["galaxies"]["enabled"] is False
    assert applied.layer_options["open_clusters"]["enabled"] is False
    assert sky.layers is before


def test_explicit_layer_options_have_final_precedence():
    sky = m40d_detail_application_fake_sky()
    detail = ResolvedDetail(
        enabled_layers=frozenset({"stars"}),
        minimum_open_cluster_size_arcmin=8.0,
    )
    applied = apply_resolved_detail(
        sky,
        detail,
        base_layer_options={
            "open_clusters": {
                "render": {"style": {"color": "gold"}},
            }
        },
        explicit_layer_options={
            "open_clusters": {
                "enabled": True,
                "geometry": {"minimum_size_arcmin": 2.0},
            }
        },
        reload_catalogues=False,
    )
    options = applied.layer_options["open_clusters"]
    assert options["enabled"] is True
    assert options["geometry"]["minimum_size_arcmin"] == 2.0
    assert options["render"]["style"]["color"] == "gold"


def test_merge_layer_options_preserves_nested_style_options():
    merged = merge_layer_options(
        {"stars": {"render": {"style": {"color": "black", "s": 2}}}},
        {"stars": {"enabled": True}},
        {"stars": {"render": {"style": {"s": 4}}}},
    )
    assert merged["stars"] == {
        "enabled": True,
        "render": {"style": {"color": "black", "s": 4}},
    }


def test_legacy_reload_flag_does_not_restore_mutation():
    sky = m40d_detail_application_fake_sky()
    apply_resolved_detail(
        sky,
        ResolvedDetail(
            star_magnitude_limit=9.0,
            galaxy_magnitude_limit=12.0,
        ),
        reload_catalogues=False,
    )
    assert sky.stars.magnitude_limit == 6.0
    assert sky.galaxies.magnitude_limit == 10.0
    assert sky.stars.loads == sky.galaxies.loads == 0

# Contracts consolidated from test_milestone40f_cartoon_detail_policy.py.
from types import SimpleNamespace

import pytest

from wenu import CartoonDetailPolicy
from wenu.charts.detail import CARTOON_CONTENT_LAYERS
from wenu.charts.detail_application import apply_resolved_detail
from wenu.objects.stars import Stars


class FakeStars:
    layer_name = "stars"

    def __init__(self):
        self.magnitude_limit = 5.5
        self.include_ids = frozenset()
        self.include_constellation_vertices = False
        self.loads = 0

    def load(self):
        self.loads += 1

    def configure_selection(
        self,
        *,
        include_ids=(),
        include_constellation_vertices=None,
        reload=True,
    ):
        identifiers = frozenset(int(value) for value in include_ids)
        include_vertices = (
            self.include_constellation_vertices
            if include_constellation_vertices is None
            else bool(include_constellation_vertices)
        )
        changed = (
            identifiers != self.include_ids
            or include_vertices != self.include_constellation_vertices
        )
        self.include_ids = identifiers
        self.include_constellation_vertices = include_vertices
        if changed and reload:
            self.load()
        return changed


class FakeLayer:
    def __init__(self, name):
        self.layer_name = name


def m40f_cartoon_detail_policy_fake_sky():
    stars = FakeStars()
    lines = SimpleNamespace(
        layer_name="constellation_lines",
        star_ids=frozenset({1, 2, 3}),
        resolvable_star_ids=frozenset({1, 2, 3}),
    )
    labels = FakeLayer("constellation_labels")
    galaxies = FakeLayer("galaxies")
    return SimpleNamespace(
        stars=stars,
        galaxies=None,
        constellation_lines=lines,
        layers=(stars, lines, labels, galaxies),
    )


def test_default_policy_is_sparse_and_style_independent():
    detail = CartoonDetailPolicy().resolve(object(), object())
    assert detail.enabled_layers == CARTOON_CONTENT_LAYERS
    assert detail.star_magnitude_limit == pytest.approx(3.0)
    assert detail.constellation_star_mode == "selected"
    assert not detail.layer_enabled("constellation_boundaries")
    assert not detail.layer_enabled("coordinate_grids")
    assert not detail.layer_enabled("galaxies")


def test_constellation_vertices_and_explicit_stars_are_unioned():
    sky = m40f_cartoon_detail_policy_fake_sky()
    detail = CartoonDetailPolicy(
        bright_star_magnitude_limit=2.0,
        extra_star_ids=frozenset({3, 99}),
    ).resolve(object(), object())
    application = apply_resolved_detail(sky, detail)
    assert sky.stars.magnitude_limit == pytest.approx(5.5)
    assert sky.stars.include_ids == frozenset()
    assert not sky.stars.include_constellation_vertices
    assert sky.stars.loads == 0
    assert application.reloaded_layers == ()
    assert application.layer_options["stars"]["geometry"] == {
        "magnitude_limit": 2.0,
        "include_ids": frozenset({3, 99}),
        "include_constellation_vertices": True,
    }


def test_none_mode_keeps_only_explicit_ids_beyond_bright_limit():
    sky = m40f_cartoon_detail_policy_fake_sky()
    detail = CartoonDetailPolicy(
        constellation_star_mode="none",
        extra_star_ids=frozenset({42}),
    ).resolve(object(), object())
    application = apply_resolved_detail(sky, detail)
    assert sky.stars.include_ids == frozenset()
    assert not sky.stars.include_constellation_vertices
    assert sky.stars.loads == 0
    assert application.layer_options["stars"]["geometry"] == {
        "magnitude_limit": 3.0,
        "include_ids": frozenset({42}),
        "include_constellation_vertices": False,
    }


def test_deep_sky_can_be_enabled_without_changing_visual_style():
    detail = CartoonDetailPolicy(include_deep_sky=True).resolve(
        object(),
        object(),
    )
    assert detail.layer_enabled("galaxies")
    assert detail.layer_enabled("milky_way")
    assert detail.layer_enabled("coordinate_grids")


def test_invalid_constellation_mode_is_rejected():
    with pytest.raises(ValueError, match="constellation_star_mode"):
        CartoonDetailPolicy(constellation_star_mode="nearby")


def test_stars_selection_configuration_is_stable():
    stars = Stars.__new__(Stars)
    stars.include_ids = frozenset()
    calls = []
    stars.load = lambda: calls.append("load")
    assert stars.configure_selection(include_ids={5, 2, 5})
    assert stars.include_ids == frozenset({2, 5})
    assert calls == ["load"]
    assert not stars.configure_selection(include_ids={2, 5})
    assert calls == ["load"]


def test_cartoon_policy_has_no_visual_parameters():
    fields = CartoonDetailPolicy.__dataclass_fields__
    forbidden = {
        "sky_color",
        "star_color",
        "line_color",
        "font_size",
        "linewidth",
    }
    assert forbidden.isdisjoint(fields)

# Contracts consolidated from test_milestone41g_milky_way_detail_resolution.py.
from types import SimpleNamespace

from wenu.charts.detail import ResolvedDetail
from wenu.charts.detail_application import apply_resolved_detail


class MilkyWayLayer:
    layer_name = "milky_way_isophotes"


def sky_with_milky_way():
    layer = MilkyWayLayer()
    return SimpleNamespace(
        layers=(layer,),
        stars=None,
        galaxies=None,
    ), layer


def resolved_detail(enabled_layers):
    return ResolvedDetail(
        star_magnitude_limit=3.0,
        enabled_layers=frozenset(enabled_layers),
    )


def test_semantic_content_name_enables_registered_milky_way_layer():
    sky, layer = sky_with_milky_way()
    application = apply_resolved_detail(
        sky,
        resolved_detail({"milky_way"}),
        reload_catalogues=False,
    )
    assert application.layer_options[layer]["enabled"] is True
    assert (
        application.layer_options["milky_way_isophotes"]["enabled"]
        is True
    )


def test_absent_semantic_content_name_disables_milky_way_layer():
    sky, layer = sky_with_milky_way()
    application = apply_resolved_detail(
        sky,
        resolved_detail({"stars"}),
        reload_catalogues=False,
    )
    assert application.layer_options[layer]["enabled"] is False


# Contracts consolidated from test_milestone45c_opt_in_content.py.
"""Milestone 45C contracts for explicit celestial reference content."""

import argparse
from types import SimpleNamespace

import pytest

from wenu import (
    AdaptiveDetailPolicy,
    CartoonDetailPolicy,
    add_chart_arguments,
    chart_detail_overrides,
)
from wenu.charts.detail import apply_detail_overrides
from wenu.charts.detail_application import apply_resolved_detail


OPTIONAL_LAYERS = frozenset(
    {
        "constellation_lines",
        "constellation_labels",
        "constellation_boundaries",
        "altaz_grid",
        "equatorial_grid",
        "ecliptic_grid",
        "galactic_grid",
    }
)


class m45c_opt_in_content_Layer:
    def __init__(self, name, coordinate_system=None):
        self.layer_name = name
        if coordinate_system is not None:
            self.coordinate_system = coordinate_system


def parser():
    value = argparse.ArgumentParser()
    return add_chart_arguments(value, default_output="output/test.png")


def adaptive_detail():
    return AdaptiveDetailPolicy().resolve(
        SimpleNamespace(
            visible_solid_angle_sq_deg=400.0,
            angular_area_deg2=400.0,
        ),
        SimpleNamespace(width_inches=7.0, font_scale=1.0, symbol_scale=1.0),
    )


def test_default_arguments_disable_all_optional_content():
    overrides = chart_detail_overrides(parser().parse_args([]))

    for base in (
        adaptive_detail(),
        CartoonDetailPolicy().resolve(object(), object()),
    ):
        detail = apply_detail_overrides(base, overrides)
        assert all(not detail.layer_enabled(name) for name in OPTIONAL_LAYERS)
        assert detail.grid_label_layers == frozenset()
        assert detail.constellation_star_mode == "none"


@pytest.mark.parametrize(
    ("option", "layer"),
    (
        ("--constellation-lines", "constellation_lines"),
        ("--constellation-labels", "constellation_labels"),
        ("--constellation-boundaries", "constellation_boundaries"),
        ("--altaz-grid", "altaz_grid"),
        ("--equatorial-grid", "equatorial_grid"),
        ("--ecliptic-grid", "ecliptic_grid"),
        ("--galactic-grid", "galactic_grid"),
    ),
)
def test_each_content_switch_enables_only_its_layer(option, layer):
    overrides = chart_detail_overrides(parser().parse_args([option]))
    detail = apply_detail_overrides(adaptive_detail(), overrides)

    assert detail.layer_enabled(layer)
    assert all(
        not detail.layer_enabled(other)
        for other in OPTIONAL_LAYERS - {layer}
    )
    assert detail.constellation_star_mode == (
        "selected" if layer == "constellation_lines" else "none"
    )


@pytest.mark.parametrize(
    ("option", "layer"),
    (
        ("--altaz-grid-labels", "altaz_grid"),
        ("--equatorial-grid-labels", "equatorial_grid"),
        ("--ecliptic-grid-labels", "ecliptic_grid"),
        ("--galactic-grid-labels", "galactic_grid"),
    ),
)
def test_grid_label_switch_enables_only_matching_grid(option, layer):
    overrides = chart_detail_overrides(parser().parse_args([option]))
    detail = apply_detail_overrides(adaptive_detail(), overrides)

    assert detail.grid_label_layers == frozenset({layer})
    assert detail.layer_enabled(layer)
    assert all(
        not detail.layer_enabled(other)
        for other in OPTIONAL_LAYERS - {layer}
    )


def test_grid_labels_are_applied_per_grid_object_not_global_style():
    grids = tuple(
        m45c_opt_in_content_Layer("coordinates_grid", name)
        for name in ("altaz", "equatorial", "ecliptic", "galactic")
    )
    sky = SimpleNamespace(layers=grids)
    overrides = chart_detail_overrides(
        parser().parse_args(["--ecliptic-grid-labels"])
    )
    detail = apply_detail_overrides(adaptive_detail(), overrides)
    application = apply_resolved_detail(
        sky,
        detail,
        base_layer_options={
            grid: {"render": {"draw_labels": True}} for grid in grids
        },
    )

    assert tuple(
        application.layer_options[grid]["render"]["draw_labels"]
        for grid in grids
    ) == (False, False, True, False)


def test_removed_generic_grid_switches_are_rejected():
    with pytest.raises(SystemExit):
        parser().parse_args(["--coordinate-grid"])
    with pytest.raises(SystemExit):
        parser().parse_args(["--coordinate-grid-labels"])
