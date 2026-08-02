"""Milestone 43E contracts for render-local detail resolution."""

from types import SimpleNamespace

import pandas as pd
from astropy.table import Table

from wenu import (
    AdaptiveDetailPolicy,
    CartoonDetailPolicy,
    FixedDetailPolicy,
    FullSkyChart,
    RegionalChart,
    ResolvedDetail,
    compose_chart,
)
from wenu.objects.nonstellar import NonStellar
from wenu.objects.stars import Stars


class RecordingLayer:
    def __init__(self, name, magnitude_limit=None):
        self.layer_name = name
        self.magnitude_limit = magnitude_limit
        self.loads = 0
        self.include_ids = frozenset({7})
        self.include_constellation_vertices = False
        self.constellation_vertex_ids = frozenset({1, 2, 3})

    def load(self):
        self.loads += 1


def fake_sky():
    stars = RecordingLayer("stars", 5.5)
    galaxies = RecordingLayer("galaxies", 10.0)
    return SimpleNamespace(
        stars=stars,
        nonstellar=None,
        galaxies=galaxies,
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
        layers=(stars, galaxies),
    )


def regional_chart():
    return RegionalChart(
        center_alt_deg=35.0,
        center_az_deg=210.0,
        field_width_deg=30.0,
        field_height_deg=20.0,
    )


def snapshot(sky):
    return (
        sky.stars.magnitude_limit,
        sky.stars.include_ids,
        sky.stars.include_constellation_vertices,
        sky.stars.constellation_vertex_ids,
        sky.stars.loads,
        sky.galaxies.magnitude_limit,
        sky.galaxies.loads,
    )


def test_print_presentation_print_does_not_change_sky_state():
    sky = fake_sky()
    before = snapshot(sky)
    detail = FixedDetailPolicy(
        ResolvedDetail(
            star_magnitude_limit=7.0,
            galaxy_magnitude_limit=11.0,
        )
    )

    first = compose_chart(
        regional_chart(), style="atlas", mode="print", detail=detail
    ).layer_options(sky)
    presented = compose_chart(
        regional_chart(),
        style="atlas",
        mode="presentation",
        detail=detail,
    ).layer_options(sky)
    second = compose_chart(
        regional_chart(), style="atlas", mode="print", detail=detail
    ).layer_options(sky)

    assert snapshot(sky) == before
    assert first.layer_options["stars"]["geometry"] == (
        second.layer_options["stars"]["geometry"]
    )
    assert presented.layer_options["stars"]["geometry"] == (
        first.layer_options["stars"]["geometry"]
    )


def test_atlas_cartoon_atlas_keeps_vertex_metadata_and_selection():
    sky = fake_sky()
    before = snapshot(sky)
    atlas = compose_chart(
        regional_chart(),
        style="atlas",
        detail=FixedDetailPolicy(ResolvedDetail(star_magnitude_limit=6.0)),
    )
    cartoon = compose_chart(
        regional_chart(),
        style="atlas",
        detail=CartoonDetailPolicy(
            bright_star_magnitude_limit=1.5,
            extra_star_ids=frozenset({42}),
        ),
    )

    first = atlas.layer_options(sky)
    sparse = cartoon.layer_options(sky)
    second = atlas.layer_options(sky)

    assert snapshot(sky) == before
    for name in ("stars", "galaxies"):
        assert first.layer_options[name]["enabled"] == (
            second.layer_options[name]["enabled"]
        )
        assert first.layer_options[name].get("geometry") == (
            second.layer_options[name].get("geometry")
        )
    sparse_geometry = sparse.layer_options["stars"]["geometry"]
    assert sparse_geometry["magnitude_limit"] == 1.5
    assert sparse_geometry["include_ids"] == frozenset({42})
    assert sparse_geometry["include_constellation_vertices"] is True


def test_regional_then_full_sky_uses_field_local_limits():
    sky = fake_sky()
    before = snapshot(sky)
    detail = AdaptiveDetailPolicy()
    regional = compose_chart(
        regional_chart(), style="atlas", detail=detail
    )
    planisphere = compose_chart(
        FullSkyChart(), style="atlas", detail=detail
    )

    regional_options = regional.layer_options(sky)
    full_sky_options = planisphere.layer_options(sky)

    assert snapshot(sky) == before
    assert regional_options.layer_options is not full_sky_options.layer_options
    assert (
        regional_options.layer_options["stars"]["geometry"][
            "magnitude_limit"
        ]
        != full_sky_options.layer_options["stars"]["geometry"][
            "magnitude_limit"
        ]
    )


def test_stellar_union_is_selected_without_changing_loaded_catalogue():
    stars = Stars.__new__(Stars)
    source = pd.DataFrame(
        {
            "magnitude": [1.0, 4.0, 8.0, 9.0],
            "is_constellation_vertex": [False, True, False, False],
        },
        index=[10, 20, 30, 40],
    )
    stars.source_catalog = source
    stars.catalog = source.iloc[[0]].copy()
    stars.magnitude_limit = 1.0
    stars.include_ids = frozenset()
    stars.include_constellation_vertices = False
    stars.constellation_vertex_ids = frozenset({20})
    before = stars.catalog.copy()

    selected = stars._render_catalog(
        magnitude_limit=2.0,
        include_ids=frozenset({30}),
        include_constellation_vertices=True,
    )

    assert selected.index.tolist() == [10, 20, 30]
    pd.testing.assert_frame_equal(stars.catalog, before)
    assert stars.constellation_vertex_ids == frozenset({20})


def test_nonstellar_magnitude_filter_uses_source_catalogue_locally():
    layer = NonStellar.__new__(NonStellar)
    source = Table(
        {
            "identifier": ["bright", "faint", "unknown"],
            "magnitude": [8.0, 12.0, float("nan")],
        }
    )
    layer.source_catalog = source
    layer.catalog = source[:1].copy()
    before = layer.catalog.copy()

    selected = layer._geometry_table(magnitude_limit=10.0)

    assert list(selected["identifier"]) == ["bright", "unknown"]
    assert list(layer.catalog["identifier"]) == list(before["identifier"])
