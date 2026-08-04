"""Milestone 45B contracts for independent grid detail identity."""

from types import SimpleNamespace

from wenu.charts.detail import (
    AdaptiveDetailPolicy,
    CartoonDetailPolicy,
    ResolvedDetail,
)
from wenu.charts.detail_application import apply_resolved_detail


class Grid:
    layer_name = "coordinates_grid"

    def __init__(self, coordinate_system):
        self.coordinate_system = coordinate_system


class Layer:
    def __init__(self, name):
        self.layer_name = name


def grid_sky():
    grids = tuple(
        Grid(name) for name in ("equatorial", "ecliptic", "galactic")
    )
    return SimpleNamespace(layers=grids), grids


def enabled(application, grids):
    return tuple(
        application.layer_options[grid]["enabled"] for grid in grids
    )


def test_each_grid_can_be_enabled_without_enabling_another():
    sky, grids = grid_sky()
    for index, name in enumerate(
        ("equatorial_grid", "ecliptic_grid", "galactic_grid")
    ):
        application = apply_resolved_detail(
            sky,
            ResolvedDetail(enabled_layers=frozenset({name})),
        )
        assert enabled(application, grids) == tuple(
            position == index for position in range(3)
        )


def test_grid_options_are_available_by_object_and_semantic_name():
    sky, grids = grid_sky()
    application = apply_resolved_detail(
        sky,
        ResolvedDetail(enabled_layers=frozenset({"ecliptic_grid"})),
    )

    for grid, name in zip(
        grids,
        ("equatorial_grid", "ecliptic_grid", "galactic_grid"),
    ):
        assert application.layer_options[grid] is application.layer_options[name]


def test_legacy_group_name_still_enables_all_grids():
    sky, grids = grid_sky()
    application = apply_resolved_detail(
        sky,
        ResolvedDetail(enabled_layers=frozenset({"coordinate_grids"})),
    )
    assert enabled(application, grids) == (True, True, True)


def test_sequential_grid_selection_does_not_leak():
    sky, grids = grid_sky()
    equatorial = ResolvedDetail(
        enabled_layers=frozenset({"equatorial_grid"})
    )
    galactic = ResolvedDetail(enabled_layers=frozenset({"galactic_grid"}))

    first = apply_resolved_detail(sky, equatorial)
    second = apply_resolved_detail(sky, galactic)
    repeated = apply_resolved_detail(sky, equatorial)

    assert enabled(first, grids) == (True, False, False)
    assert enabled(second, grids) == (False, False, True)
    assert enabled(repeated, grids) == (True, False, False)


def test_policy_contracts_use_system_specific_grid_names():
    adaptive = AdaptiveDetailPolicy().resolve(
        SimpleNamespace(
            visible_solid_angle_sq_deg=400.0,
            angular_area_deg2=400.0,
        ),
        SimpleNamespace(width_inches=7.0, font_scale=1.0, symbol_scale=1.0),
    )
    deep_cartoon = CartoonDetailPolicy(include_deep_sky=True).resolve(
        object(), object()
    )

    for detail in (adaptive, deep_cartoon):
        assert detail.layer_enabled("equatorial_grid")
        assert detail.layer_enabled("ecliptic_grid")
        assert detail.layer_enabled("galactic_grid")
        assert detail.layer_enabled("coordinate_grids")


def test_non_grid_alias_behavior_is_unchanged():
    milky_way = Layer("milky_way_isophotes")
    sky = SimpleNamespace(layers=(milky_way,))
    application = apply_resolved_detail(
        sky,
        ResolvedDetail(enabled_layers=frozenset({"milky_way"})),
    )

    assert application.layer_options[milky_way]["enabled"] is True
    assert (
        application.layer_options[milky_way]
        is application.layer_options["milky_way"]
        is application.layer_options["milky_way_isophotes"]
    )
