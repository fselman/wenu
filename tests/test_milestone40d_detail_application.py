from types import SimpleNamespace

from wenu.charts.detail import ResolvedDetail
from wenu.charts.detail_application import (
    apply_resolved_detail,
    merge_layer_options,
)


class Layer:
    def __init__(self, name, magnitude_limit=None):
        self.layer_name = name
        self.magnitude_limit = magnitude_limit
        self.loads = 0

    def load(self):
        self.loads += 1


def fake_sky():
    stars = Layer("stars", 6.0)
    galaxies = Layer("galaxies", 10.0)
    open_clusters = Layer("open_clusters")
    planetary = Layer("planetary_nebulae")
    labels = Layer("constellation_labels")
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
    sky = fake_sky()
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
    sky = fake_sky()
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
    sky = fake_sky()
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
    sky = fake_sky()
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
