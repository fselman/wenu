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
    geometry = stars.spherical_geometry(object())
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
