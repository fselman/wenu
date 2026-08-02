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


def fake_sky():
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
    assert detail.star_magnitude_limit == pytest.approx(1.5)
    assert detail.constellation_star_mode == "selected"
    assert not detail.layer_enabled("constellation_boundaries")
    assert not detail.layer_enabled("coordinate_grids")
    assert not detail.layer_enabled("galaxies")


def test_constellation_vertices_and_explicit_stars_are_unioned():
    sky = fake_sky()
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
    sky = fake_sky()
    detail = CartoonDetailPolicy(
        constellation_star_mode="none",
        extra_star_ids=frozenset({42}),
    ).resolve(object(), object())
    application = apply_resolved_detail(sky, detail)
    assert sky.stars.include_ids == frozenset()
    assert not sky.stars.include_constellation_vertices
    assert sky.stars.loads == 0
    assert application.layer_options["stars"]["geometry"] == {
        "magnitude_limit": 1.5,
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
