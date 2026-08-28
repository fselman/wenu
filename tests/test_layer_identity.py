"""Current layer identity contracts."""

# Contracts consolidated from test_milestone40e_constellation_star_identity.py.
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from wenu.sky.constellation_lines import ConstellationLines


def make_lines(tmp_path, *, available=(1, 2, 3, 4, 5)):
    filename = tmp_path / "test.fab"
    filename.write_text(
        "AAA 3 1 2 3\n"
        "BBB 3 3 4 5\n",
        encoding="utf-8",
    )
    stars = SimpleNamespace(
        catalog=pd.DataFrame(index=list(available)),
    )
    return ConstellationLines(stars, filename=filename)


def test_star_ids_are_immutable_and_deduplicated(tmp_path):
    lines = make_lines(tmp_path)
    assert lines.star_ids == frozenset({1, 2, 3, 4, 5})
    with pytest.raises(AttributeError):
        lines.star_ids.add(6)


def test_ids_are_available_by_constellation(tmp_path):
    lines = make_lines(tmp_path)
    assert lines.star_ids_by_constellation["AAA"] == frozenset({1, 2, 3})
    assert lines.star_ids_by_constellation["BBB"] == frozenset({3, 4, 5})
    with pytest.raises(TypeError):
        lines.star_ids_by_constellation["AAA"] = frozenset()


def test_selected_constellation_ids_are_deduplicated(tmp_path):
    lines = make_lines(tmp_path)
    assert lines.star_ids_for(["AAA"]) == frozenset({1, 2, 3})
    assert lines.star_ids_for(["AAA", "BBB"]) == lines.star_ids


def test_unknown_loaded_constellation_is_explicit(tmp_path):
    lines = make_lines(tmp_path)
    with pytest.raises(KeyError, match="CCC"):
        lines.star_ids_for(["CCC"])


def test_missing_catalogue_identifiers_are_reported(tmp_path):
    lines = make_lines(tmp_path, available=(1, 2, 4, 5))
    assert lines.resolvable_star_ids == frozenset({1, 2, 4, 5})
    assert lines.unresolved_star_ids == frozenset({3})
    with pytest.raises(LookupError, match="3"):
        lines.require_resolved_star_ids()


def test_selected_load_exposes_only_requested_figure(tmp_path):
    filename = tmp_path / "test.fab"
    filename.write_text(
        "AAA 3 1 2 3\n"
        "BBB 3 3 4 5\n",
        encoding="utf-8",
    )
    stars = SimpleNamespace(
        catalog=pd.DataFrame(index=[1, 2, 3, 4, 5]),
    )
    lines = ConstellationLines(
        stars,
        filename=filename,
        constellations=["BBB"],
    )
    assert lines.star_ids == frozenset({3, 4, 5})
    assert set(lines.star_ids_by_constellation) == {"BBB"}


def test_source_contains_no_chart_style_or_renderer_dependency():
    import wenu.sky.constellation_lines as module

    source = Path(module.__file__).read_text(encoding="utf-8").lower()
    assert "matplotlib" not in source
    assert "chartstyle" not in source
    assert "cartoon" not in source

# Contracts consolidated from test_milestone41g_layer_alias_identity.py.
from types import SimpleNamespace

from wenu.charts.detail_application import merge_sky_layer_options


class m41g_layer_alias_identity_Layer:
    layer_name = "milky_way_isophotes"


def test_semantic_milky_way_alias_controls_registered_isophote_layer():
    layer = m41g_layer_alias_identity_Layer()
    sky = SimpleNamespace(layers=(layer,))
    merged = merge_sky_layer_options(
        sky,
        {layer: {"enabled": True, "render": {"alpha": 0.2}}},
        {"milky_way": {"enabled": False}},
    )
    assert merged[layer]["enabled"] is False
    assert merged["milky_way"]["enabled"] is False
    assert merged["milky_way_isophotes"]["enabled"] is False
    assert merged[layer]["render"]["alpha"] == 0.2


def test_presentation_alias_can_enable_registered_isophote_layer():
    layer = m41g_layer_alias_identity_Layer()
    sky = SimpleNamespace(layers=(layer,))
    merged = merge_sky_layer_options(
        sky,
        {layer: {"enabled": False}},
        {"milky_way": {"enabled": True}},
    )
    assert merged[layer]["enabled"] is True


def test_unhashable_synthetic_layer_is_supported():
    layer = SimpleNamespace(layer_name="constellation_lines")
    sky = SimpleNamespace(layers=(layer,))
    merged = merge_sky_layer_options(
        sky,
        {"constellation_lines": {"enabled": True}},
    )
    assert merged["constellation_lines"]["enabled"] is True


# Contracts consolidated from test_milestone41g_layer_option_identity.py.
from types import SimpleNamespace

from wenu.charts.detail import ResolvedDetail
from wenu.charts.detail_application import apply_resolved_detail


class m41g_layer_option_identity_Layer:
    def __init__(self, name):
        self.layer_name = name


def test_named_disabled_option_overrides_object_keyed_style():
    milky_way = m41g_layer_option_identity_Layer("milky_way")
    sky = SimpleNamespace(
        layers=(milky_way,),
        stars=None,
        galaxies=None,
    )
    detail = ResolvedDetail(
        enabled_layers=frozenset({"stars"}),
    )
    applied = apply_resolved_detail(
        sky,
        detail,
        base_layer_options={
            milky_way: {
                "prepare": object(),
                "render": {"style": {"color": "blue"}},
            }
        },
        reload_catalogues=False,
    )
    by_object = applied.layer_options[milky_way]
    by_name = applied.layer_options["milky_way"]
    assert by_object is by_name
    assert by_object["enabled"] is False
    assert by_object["render"]["style"]["color"] == "blue"


def test_explicit_named_option_has_final_precedence_for_object_key():
    layer = m41g_layer_option_identity_Layer("milky_way")
    sky = SimpleNamespace(
        layers=(layer,),
        stars=None,
        galaxies=None,
    )
    applied = apply_resolved_detail(
        sky,
        ResolvedDetail(enabled_layers=frozenset({"stars"})),
        base_layer_options={layer: {"enabled": True}},
        explicit_layer_options={"milky_way": {"enabled": True}},
        reload_catalogues=False,
    )
    assert applied.layer_options[layer]["enabled"] is True


def test_object_key_is_more_specific_within_one_source():
    layer = m41g_layer_option_identity_Layer("milky_way")
    sky = SimpleNamespace(
        layers=(layer,),
        stars=None,
        galaxies=None,
    )
    applied = apply_resolved_detail(
        sky,
        ResolvedDetail(enabled_layers=None),
        explicit_layer_options={
            "milky_way": {"render": {"style": {"alpha": 0.2}}},
            layer: {"render": {"style": {"alpha": 0.7}}},
        },
        reload_catalogues=False,
    )
    assert (
        applied.layer_options[layer]["render"]["style"]["alpha"]
        == 0.7
    )

# Contracts consolidated from test_milestone42b0_constellation_vertex_metadata.py.
from types import SimpleNamespace

import numpy as np
import pandas as pd

from wenu.charts.detail import ResolvedDetail
from wenu.charts.detail_application import apply_resolved_detail
from wenu.objects.stars import Stars


def bare_stars():
    stars = Stars.__new__(Stars)
    stars.include_ids = frozenset()
    stars.constellation_vertex_ids = frozenset()
    stars.include_constellation_vertices = False
    stars.load_calls = 0
    stars.load = lambda: setattr(
        stars,
        "load_calls",
        stars.load_calls + 1,
    )
    return stars


def test_vertex_identifiers_are_stored_immutably():
    stars = bare_stars()
    assert stars.set_constellation_vertices({5, 2, 5})
    assert stars.constellation_vertex_ids == frozenset({2, 5})
    assert stars.load_calls == 1
    assert not stars.set_constellation_vertices({2, 5})
    assert stars.load_calls == 1


def test_selection_flag_extends_existing_configuration():
    stars = bare_stars()
    assert stars.configure_selection(
        include_ids={11},
        include_constellation_vertices=True,
    )
    assert stars.include_ids == frozenset({11})
    assert stars.include_constellation_vertices
    assert stars.load_calls == 1

    assert not stars.configure_selection(
        include_ids={11},
        include_constellation_vertices=True,
    )
    assert stars.load_calls == 1


def test_legacy_selection_call_preserves_vertex_flag():
    stars = bare_stars()
    stars.include_constellation_vertices = True
    assert stars.configure_selection(include_ids={7})
    assert stars.include_constellation_vertices


def test_spherical_geometry_propagates_vertex_metadata():
    stars = Stars.__new__(Stars)
    stars.catalog_name = "test"
    stars.hip_df = pd.DataFrame(
        {
            "magnitude": [1.0, 4.0],
            "is_constellation_vertex": [False, True],
        },
        index=[10, 20],
    )
    stars.compute_altaz = lambda **kwargs: (
        np.asarray([30.0, 40.0]),
        np.asarray([100.0, 110.0]),
    )
    geometry = stars.spherical_geometry(
        SimpleNamespace(
            t_astropy=SimpleNamespace(
                isot="2026-08-28T00:00:00.000", scale="utc"
            )
        )
    )
    assert geometry.ids.tolist() == [10, 20]
    assert geometry.metadata["is_constellation_vertex"].tolist() == [
        False,
        True,
    ]


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
        include_ids = frozenset(include_ids)
        include_vertices = (
            self.include_constellation_vertices
            if include_constellation_vertices is None
            else bool(include_constellation_vertices)
        )
        changed = (
            include_ids != self.include_ids
            or include_vertices != self.include_constellation_vertices
        )
        self.include_ids = include_ids
        self.include_constellation_vertices = include_vertices
        if changed and reload:
            self.load()
        return changed


def test_detail_application_uses_vertex_flag_and_keeps_extra_ids():
    stars = FakeStars()
    lines = SimpleNamespace(
        layer_name="constellation_lines",
        star_ids=frozenset({1, 2, 3}),
    )
    sky = SimpleNamespace(
        stars=stars,
        galaxies=None,
        constellation_lines=lines,
        layers=(stars, lines),
    )
    detail = ResolvedDetail(
        star_magnitude_limit=2.0,
        constellation_star_mode="selected",
        extra_star_ids=frozenset({99}),
        enabled_layers=frozenset({"stars", "constellation_lines"}),
    )
    applied = apply_resolved_detail(sky, detail)
    assert stars.include_ids == frozenset()
    assert not stars.include_constellation_vertices
    assert applied.layer_options["stars"]["geometry"] == {
        "magnitude_limit": 2.0,
        "include_ids": frozenset({99}),
        "include_constellation_vertices": True,
    }


def test_none_mode_disables_vertex_inclusion():
    stars = FakeStars()
    stars.include_constellation_vertices = True
    lines = SimpleNamespace(
        layer_name="constellation_lines",
        star_ids=frozenset({1, 2, 3}),
    )
    sky = SimpleNamespace(
        stars=stars,
        galaxies=None,
        constellation_lines=lines,
        layers=(stars, lines),
    )
    detail = ResolvedDetail(
        constellation_star_mode="none",
        extra_star_ids=frozenset({42}),
        enabled_layers=frozenset({"stars", "constellation_lines"}),
    )
    applied = apply_resolved_detail(sky, detail)
    assert stars.include_ids == frozenset()
    assert stars.include_constellation_vertices
    assert applied.layer_options["stars"]["geometry"] == {
        "include_ids": frozenset({42}),
        "include_constellation_vertices": False,
    }

# Contracts consolidated from test_milestone42b0b_vertex_metadata_default.py.
from types import SimpleNamespace

import numpy as np
import pandas as pd

from wenu.objects.stars import Stars


def stars_with(frame):
    stars = Stars(observer=None)
    stars.hip_df = frame
    stars.compute_altaz = lambda **kwargs: (
        np.asarray((30.0, 40.0)),
        np.asarray((120.0, 130.0)),
    )
    return stars


def test_missing_vertex_column_defaults_to_aligned_false_values():
    stars = stars_with(
        pd.DataFrame(
            {"magnitude": [1.0, 2.0]},
            index=[10, 20],
        )
    )
    geometry = stars.spherical_geometry(
        SimpleNamespace(
            t_astropy=SimpleNamespace(
                isot="2026-08-28T00:00:00.000", scale="utc"
            )
        )
    )
    assert geometry.metadata["is_constellation_vertex"].tolist() == [
        False,
        False,
    ]


def test_existing_vertex_column_is_preserved():
    stars = stars_with(
        pd.DataFrame(
            {
                "magnitude": [1.0, 2.0],
                "is_constellation_vertex": [True, False],
            },
            index=[10, 20],
        )
    )
    geometry = stars.spherical_geometry(
        SimpleNamespace(
            t_astropy=SimpleNamespace(
                isot="2026-08-28T00:00:00.000", scale="utc"
            )
        )
    )
    assert geometry.metadata["is_constellation_vertex"].tolist() == [
        True,
        False,
    ]

# Contracts consolidated from test_milestone45b_grid_detail_identity.py.
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


class m45b_grid_detail_identity_Layer:
    def __init__(self, name):
        self.layer_name = name


def grid_sky():
    grids = tuple(
        Grid(name)
        for name in ("altaz", "equatorial", "ecliptic", "galactic")
    )
    return SimpleNamespace(layers=grids), grids


def enabled(application, grids):
    return tuple(
        application.layer_options[grid]["enabled"] for grid in grids
    )


def test_each_grid_can_be_enabled_without_enabling_another():
    sky, grids = grid_sky()
    for index, name in enumerate(
        ("altaz_grid", "equatorial_grid", "ecliptic_grid", "galactic_grid")
    ):
        application = apply_resolved_detail(
            sky,
            ResolvedDetail(enabled_layers=frozenset({name})),
        )
        assert enabled(application, grids) == tuple(
            position == index for position in range(4)
        )


def test_grid_options_are_available_by_object_and_semantic_name():
    sky, grids = grid_sky()
    application = apply_resolved_detail(
        sky,
        ResolvedDetail(enabled_layers=frozenset({"ecliptic_grid"})),
    )

    for grid, name in zip(
        grids,
        ("altaz_grid", "equatorial_grid", "ecliptic_grid", "galactic_grid"),
    ):
        assert application.layer_options[grid] is application.layer_options[name]


def test_legacy_group_name_still_enables_all_grids():
    sky, grids = grid_sky()
    application = apply_resolved_detail(
        sky,
        ResolvedDetail(enabled_layers=frozenset({"coordinate_grids"})),
    )
    assert enabled(application, grids) == (True, True, True, True)


def test_sequential_grid_selection_does_not_leak():
    sky, grids = grid_sky()
    equatorial = ResolvedDetail(
        enabled_layers=frozenset({"equatorial_grid"})
    )
    galactic = ResolvedDetail(enabled_layers=frozenset({"galactic_grid"}))

    first = apply_resolved_detail(sky, equatorial)
    second = apply_resolved_detail(sky, galactic)
    repeated = apply_resolved_detail(sky, equatorial)

    assert enabled(first, grids) == (False, True, False, False)
    assert enabled(second, grids) == (False, False, False, True)
    assert enabled(repeated, grids) == (False, True, False, False)


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
        assert detail.layer_enabled("altaz_grid")
        assert detail.layer_enabled("coordinate_grids")


def test_non_grid_alias_behavior_is_unchanged():
    milky_way = m45b_grid_detail_identity_Layer("milky_way_isophotes")
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
