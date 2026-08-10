"""Current constellation labels contracts."""

# Contracts consolidated from test_milestone41c_cartoon_label_palette_repair.py.
from types import SimpleNamespace

from wenu import cartoon_chart_style


class m41c_cartoon_label_palette_repair_HashableLayer:
    pass


def m41c_cartoon_label_palette_repair_fake_sky():
    labels = m41c_cartoon_label_palette_repair_HashableLayer()
    return SimpleNamespace(
        stars=None,
        nonstellar=None,
        milky_way_isophotes=None,
        magellanic_clouds=None,
        galaxies=None,
        supernova_remnants=None,
        globular_clusters=None,
        planetary_nebulae=None,
        open_clusters=None,
        constellation_lines=None,
        constellation_labels=labels,
        constellation_boundaries=None,
        coordinate_grids=(),
        points=None,
        layers=(labels,),
    )


def test_presentation_uses_brighter_ocean_blue():
    style = cartoon_chart_style("presentation")
    assert style.canvas.sky_color == "#1677A6"
    assert style.grids.constellation_line_color == "#FFE066"
    assert style.grids.constellation_label_color == "#FFE066"


def test_print_remains_white_for_paper():
    style = cartoon_chart_style("print")
    assert style.canvas.sky_color == "white"
    assert style.stars.color == "#000000"


def test_cartoon_labels_receive_clearance_and_matching_halo():
    sky = m41c_cartoon_label_palette_repair_fake_sky()
    style = cartoon_chart_style("presentation")
    render = style.layer_options(sky)[sky.constellation_labels]["render"]
    assert render["label_offset"] == (0.18, 0.14)
    assert render["label_style"]["ha"] == "left"
    assert render["label_style"]["va"] == "bottom"
    bbox = render["label_style"]["bbox"]
    assert bbox["facecolor"] == "#1677A6"
    assert bbox["edgecolor"] == "none"
    assert bbox["alpha"] == 0.78


def test_label_clearance_is_configurable():
    style = cartoon_chart_style("print")
    assert style.constellation_label_offset == (0.18, 0.14)
    assert style.constellation_label_halo_alpha == 0.78

# Contracts consolidated from test_milestone41c_cartoon_label_position_repair.py.
from types import SimpleNamespace

from wenu import cartoon_chart_style


class m41c_cartoon_label_position_repair_HashableLayer:
    pass


def m41c_cartoon_label_position_repair_fake_sky():
    labels = m41c_cartoon_label_position_repair_HashableLayer()
    return SimpleNamespace(
        stars=None,
        nonstellar=None,
        milky_way_isophotes=None,
        magellanic_clouds=None,
        galaxies=None,
        supernova_remnants=None,
        globular_clusters=None,
        planetary_nebulae=None,
        open_clusters=None,
        constellation_lines=None,
        constellation_labels=labels,
        constellation_boundaries=None,
        coordinate_grids=(),
        points=None,
        layers=(labels,),
    )


def test_cartoon_labels_move_clear_of_constellation_figures():
    sky = m41c_cartoon_label_position_repair_fake_sky()
    style = cartoon_chart_style("presentation")
    render = style.layer_options(sky)[sky.constellation_labels]["render"]
    assert render["label_offset"] == (0.18, 0.14)
    assert render["label_style"]["ha"] == "left"
    assert render["label_style"]["va"] == "bottom"


def test_cartoon_label_clearance_is_part_of_reusable_style():
    printed = cartoon_chart_style("print")
    presented = cartoon_chart_style("presentation")
    assert printed.constellation_label_offset == (0.18, 0.14)
    assert presented.constellation_label_offset == (0.18, 0.14)


def test_presentation_palette_remains_unchanged():
    style = cartoon_chart_style("presentation")
    assert style.canvas.sky_color == "#1677A6"
    assert style.canvas.foreground_color == "#FFE066"
    assert style.grids.constellation_line_color == "#FFE066"
    assert style.grids.constellation_label_color == "#FFE066"

# Contracts consolidated from test_milestone41c_composed_label_placement_repair.py.
from types import SimpleNamespace

from wenu import cartoon_chart_style


class m41c_composed_label_placement_repair_HashableLayer:
    pass


def m41c_composed_label_placement_repair_fake_sky():
    labels = m41c_composed_label_placement_repair_HashableLayer()
    return SimpleNamespace(
        stars=None,
        nonstellar=None,
        milky_way_isophotes=None,
        magellanic_clouds=None,
        galaxies=None,
        supernova_remnants=None,
        globular_clusters=None,
        planetary_nebulae=None,
        open_clusters=None,
        constellation_lines=None,
        constellation_labels=labels,
        constellation_boundaries=None,
        coordinate_grids=(),
        points=None,
        layers=(labels,),
    )


def test_label_placement_survives_publication_style_conversion():
    composed = cartoon_chart_style("presentation")
    publication = composed.as_publication_style()
    assert publication.constellation_label_offset == (0.18, 0.14)
    assert publication.constellation_label_ha == "left"
    assert publication.constellation_label_va == "bottom"


def test_publication_layer_options_use_composed_label_placement():
    sky = m41c_composed_label_placement_repair_fake_sky()
    publication = cartoon_chart_style(
        "presentation"
    ).as_publication_style()
    render = publication.layer_options(
        sky
    )[sky.constellation_labels]["render"]
    assert render["label_offset"]["__default__"] == (0.18, 0.14)
    assert render["label_style"]["ha"] == "left"
    assert render["label_style"]["va"] == "bottom"


def test_print_and_presentation_share_label_clearance():
    printed = cartoon_chart_style("print").as_publication_style()
    presented = cartoon_chart_style(
        "presentation"
    ).as_publication_style()
    assert printed.constellation_label_offset == (0.18, 0.14)
    assert (
        printed.constellation_label_offset
        == presented.constellation_label_offset
    )

# Contracts consolidated from test_milestone41d_manual_constellation_label_offsets.py.
from inspect import signature
from types import SimpleNamespace

import matplotlib.pyplot as plt

from wenu import (
    MatplotlibRenderer,
    cartoon_chart_style,
    compose_cartoon_chart,
)
from wenu.geometry.projected import ProjectedPoints


class m41d_manual_constellation_label_offsets_HashableLayer:
    pass


def m41d_manual_constellation_label_offsets_fake_sky():
    labels = m41d_manual_constellation_label_offsets_HashableLayer()
    return SimpleNamespace(
        stars=None,
        nonstellar=None,
        milky_way_isophotes=None,
        magellanic_clouds=None,
        galaxies=None,
        supernova_remnants=None,
        globular_clusters=None,
        planetary_nebulae=None,
        open_clusters=None,
        constellation_lines=None,
        constellation_labels=labels,
        constellation_boundaries=None,
        coordinate_grids=(),
        points=None,
        layers=(labels,),
    )


def test_manual_offsets_survive_publication_conversion():
    publication = cartoon_chart_style(
        "print",
        constellation_label_offsets={"Lyr": (0.07, 0.05)},
    ).as_publication_style()
    assert publication.constellation_label_offsets == {
        "Lyr": (0.07, 0.05)
    }


def test_label_options_contain_default_and_manual_offsets():
    sky = m41d_manual_constellation_label_offsets_fake_sky()
    publication = cartoon_chart_style(
        "print",
        constellation_label_offsets={"Lyr": (0.07, 0.05)},
    ).as_publication_style()
    offsets = publication.layer_options(
        sky
    )[sky.constellation_labels]["render"]["label_offset"]
    assert offsets["__default__"] == (0.18, 0.14)
    assert offsets["Lyr"] == (0.07, 0.05)


def test_renderer_resolves_offsets_by_label_identity():
    figure, ax = plt.subplots()
    points = ProjectedPoints(
        x=[1.0, 2.0],
        y=[3.0, 4.0],
        labels=["Lyr", "Cyg"],
    )
    artists = MatplotlibRenderer(ax).draw(
        points,
        style={"s": 0.0},
        draw_labels=True,
        label_offset={
            "__default__": (0.18, 0.14),
            "Lyr": (0.07, 0.05),
        },
    )
    positions = {
        artist.get_text(): artist.get_position()
        for artist in artists
        if hasattr(artist, "get_text")
    }
    assert positions["Lyr"] == (1.07, 3.05)
    assert positions["Cyg"] == (2.18, 4.14)
    plt.close(figure)


def test_cartoon_composition_accepts_manual_offsets():
    assert (
        "constellation_label_offsets"
        in signature(compose_cartoon_chart).parameters
    )

# Contracts consolidated from test_milestone41e_finite_label_coordinates.py.
from types import SimpleNamespace

import astropy.units as u
import numpy as np
import pandas as pd
from astropy.coordinates import AltAz, EarthLocation
from astropy.time import Time

from wenu.sky.constellation_labels import ConstellationLabels


def observer():
    return SimpleNamespace(
        altaz_frame=AltAz(
            obstime=Time("2026-07-28T02:00:00"),
            location=EarthLocation(
                lat=-32.45 * u.deg,
                lon=-71.23 * u.deg,
            ),
        )
    )


def test_incomplete_catalogue_rows_are_ignored():
    source = pd.DataFrame(
        {
            "ra_degrees": [0.0, 20.0, 40.0, np.nan, 120.0],
            "dec_degrees": [-85.0, -84.0, -86.0, 10.0, np.nan],
        },
        index=[10, 11, 12, 13, 14],
    )
    stars = SimpleNamespace(
        source_catalog=source,
        hip_df=source.iloc[:1],
    )

    geometry = ConstellationLabels(
        stars,
        selected=["Oct"],
        min_stars=3,
    ).spherical_geometry(observer())

    assert geometry.labels.tolist() == ["Oct"]
    assert np.isfinite(geometry.lon_deg).all()
    assert np.isfinite(geometry.lat_deg).all()


def test_all_incomplete_catalogue_rows_return_empty_geometry():
    source = pd.DataFrame(
        {
            "ra_degrees": [np.nan, 20.0],
            "dec_degrees": [-20.0, np.nan],
        }
    )
    stars = SimpleNamespace(source_catalog=source, hip_df=source)

    geometry = ConstellationLabels(stars).spherical_geometry(observer())

    assert len(geometry) == 0

# Contracts consolidated from test_milestone41e_lineless_constellations.py.
from types import SimpleNamespace

import astropy.units as u
import numpy as np
import pandas as pd
from astropy.coordinates import AltAz, EarthLocation
from astropy.time import Time

from wenu.sky.constellation_labels import ConstellationLabels
from wenu.sky.constellation_lines import ConstellationLines


def test_requested_constellation_without_figure_is_preserved(tmp_path):
    filename = tmp_path / "figures.fab"
    filename.write_text("Cyg 3 1 2 3\n", encoding="utf-8")
    stars = SimpleNamespace(catalog=pd.DataFrame(index=[1, 2, 3]))
    lines = ConstellationLines(
        stars,
        filename=filename,
        constellations=["Cyg", "Oct"],
    )

    assert set(lines.star_ids_by_constellation) == {"Cyg", "Oct"}
    assert lines.star_ids_for(["Oct"]) == frozenset()
    assert lines.star_ids_for(["Cyg"]) == frozenset({1, 2, 3})


def test_label_anchor_uses_unfiltered_source_catalog():
    source = pd.DataFrame(
        {
            "ra_degrees": [0.0, 20.0, 40.0],
            "dec_degrees": [-85.0, -84.0, -86.0],
        },
        index=[10, 11, 12],
    )
    filtered = source.iloc[:1].copy()
    stars = SimpleNamespace(
        source_catalog=source,
        hip_df=filtered,
    )
    observer = SimpleNamespace(
        altaz_frame=AltAz(
            obstime=Time("2026-07-28T02:00:00"),
            location=EarthLocation(
                lat=-32.45 * u.deg,
                lon=-71.23 * u.deg,
            ),
        )
    )

    geometry = ConstellationLabels(
        stars,
        selected=["Oct"],
        min_stars=3,
    ).spherical_geometry(observer)

    assert geometry.labels.tolist() == ["Oct"]
    assert len(geometry.lon_deg) == 1
    assert np.isfinite(geometry.lon_deg[0])
    assert np.isfinite(geometry.lat_deg[0])


def test_active_star_filter_does_not_define_label_identity():
    source = pd.DataFrame(
        {
            "ra_degrees": [0.0, 20.0, 40.0],
            "dec_degrees": [-85.0, -84.0, -86.0],
        },
        index=[10, 11, 12],
    )
    stars = SimpleNamespace(
        source_catalog=source,
        hip_df=source.iloc[0:0],
    )
    labels = ConstellationLabels(stars, selected=["Oct"])
    assert labels.selected == {"Oct"}
    assert len(stars.hip_df) == 0
    assert len(stars.source_catalog) == 3

# Contracts consolidated from test_milestone41f_constellation_label_positions.py.
from inspect import signature
from types import SimpleNamespace

import pytest

from wenu import cartoon_chart_style, compose_cartoon_chart
from wenu.charts.label_placement import (
    LABEL_POSITION_VECTORS,
    resolve_constellation_label_offsets,
)


class m41f_constellation_label_positions_HashableLayer:
    pass


def m41f_constellation_label_positions_fake_sky():
    labels = m41f_constellation_label_positions_HashableLayer()
    return SimpleNamespace(
        stars=None,
        nonstellar=None,
        milky_way_isophotes=None,
        magellanic_clouds=None,
        galaxies=None,
        supernova_remnants=None,
        globular_clusters=None,
        planetary_nebulae=None,
        open_clusters=None,
        constellation_lines=None,
        constellation_labels=labels,
        constellation_boundaries=None,
        coordinate_grids=(),
        points=None,
        layers=(labels,),
    )


def test_nine_position_vocabulary_is_complete():
    assert set(LABEL_POSITION_VECTORS) == {
        "c", "ul", "u", "ur", "cl", "cr", "ll", "lc", "lr"
    }


def test_unspecified_labels_default_to_center():
    resolved = resolve_constellation_label_offsets(
        {"Cyg": "cl"},
        clearance=(0.2, 0.1),
    )
    assert resolved["__default__"] == (0.0, 0.0)
    assert resolved["Cyg"] == pytest.approx((-0.2, 0.0))


def test_manual_offset_is_added_after_discrete_position():
    resolved = resolve_constellation_label_offsets(
        {"Lyr": "ur"},
        {"Lyr": (-0.03, 0.02)},
        clearance=(0.2, 0.1),
    )
    assert resolved["Lyr"] == pytest.approx((0.17, 0.12))


def test_unknown_position_is_rejected():
    with pytest.raises(ValueError, match="sideways"):
        resolve_constellation_label_offsets({"Lyr": "sideways"})


def test_cartoon_style_emits_resolved_per_label_offsets():
    sky = m41f_constellation_label_positions_fake_sky()
    style = cartoon_chart_style(
        "print",
        constellation_label_positions={
            "Cyg": "cl",
            "Lyr": "ur",
        },
        constellation_label_offsets={
            "Lyr": (-0.03, 0.02),
        },
        constellation_label_clearance=(0.2, 0.1),
    ).as_publication_style()
    render = style.layer_options(
        sky
    )[sky.constellation_labels]["render"]
    assert render["label_offset"]["__default__"] == (0.0, 0.0)
    assert render["label_offset"]["Cyg"] == pytest.approx((-0.2, 0.0))
    assert render["label_offset"]["Lyr"] == pytest.approx((0.17, 0.12))
    assert render["label_style"]["ha"] == "center"
    assert render["label_style"]["va"] == "center"


def test_composition_exposes_position_and_clearance_controls():
    parameters = signature(compose_cartoon_chart).parameters
    assert "constellation_label_positions" in parameters
    assert "constellation_label_offsets" in parameters
    assert "constellation_label_clearance" in parameters


def test_legacy_manual_offset_calls_remain_unchanged():
    style = cartoon_chart_style(
        "print",
        constellation_label_offsets={"Lyr": (0.07, 0.05)},
    ).as_publication_style()
    assert style.constellation_label_offsets == {
        "Lyr": (0.07, 0.05)
    }

# Contracts consolidated from test_milestone41f_editable_label_example.py.
from pathlib import Path
import runpy


EXAMPLE = (
    Path(__file__).parents[1]
    / "tests/fixtures/example_regressions/cartoon_modes_explicit_labels.py"
)


def namespace():
    return runpy.run_path(str(EXAMPLE))


def test_example_exposes_all_requested_label_positions():
    values = namespace()
    assert values["CONSTELLATION_LABEL_POSITIONS"] == {
        "Cyg": "cl",
        "Lyr": "ur",
        "Vul": "ll",
        "Sge": "lr",
        "Aql": "ur",
    }
    assert set(values["CONSTELLATION_LABEL_OFFSETS"]) == {
        "Cyg", "Lyr", "Vul", "Sge", "Aql"
    }
    assert values["LABEL_CLEARANCE"] == (0.32, 0.36)


def test_only_presentation_enables_milky_way():
    values = namespace()
    assert "milky_way" not in values["content_layers"]("print")
    assert (
        "milky_way"
        in values["content_layers"]("presentation")
    )


def test_example_loads_milky_way_isophotes():
    source = EXAMPLE.read_text(encoding="utf-8")
    assert "sky.add_milky_way_isophotes()" in source

# Contracts consolidated from test_milestone41f_legacy_alignment_repair.py.
from types import SimpleNamespace

from wenu import cartoon_chart_style


class m41f_legacy_alignment_repair_HashableLayer:
    pass


def m41f_legacy_alignment_repair_fake_sky():
    labels = m41f_legacy_alignment_repair_HashableLayer()
    return SimpleNamespace(
        stars=None,
        nonstellar=None,
        milky_way_isophotes=None,
        magellanic_clouds=None,
        galaxies=None,
        supernova_remnants=None,
        globular_clusters=None,
        planetary_nebulae=None,
        open_clusters=None,
        constellation_lines=None,
        constellation_labels=labels,
        constellation_boundaries=None,
        coordinate_grids=(),
        points=None,
        layers=(labels,),
    )


def test_legacy_mode_retains_left_bottom_alignment():
    publication = cartoon_chart_style(
        "presentation"
    ).as_publication_style()
    assert publication.constellation_label_ha == "left"
    assert publication.constellation_label_va == "bottom"


def test_discrete_position_mode_uses_center_alignment():
    sky = m41f_legacy_alignment_repair_fake_sky()
    publication = cartoon_chart_style(
        "presentation",
        constellation_label_positions={"Lyr": "ur"},
    ).as_publication_style()
    render = publication.layer_options(
        sky
    )[sky.constellation_labels]["render"]
    assert render["label_style"]["ha"] == "center"
    assert render["label_style"]["va"] == "center"

# Contracts consolidated from test_milestone43h_visible_constellation_labels.py.
"""Milestone 43H chart-visible constellation-label contracts."""

from types import SimpleNamespace

import numpy as np
import wenu.geometry.clipping as clipping_module

from wenu.charts.boundaries import circular_boundary
from wenu.charts.constellation_label_placement import (
    apply_visible_constellation_label_anchors,
)
from wenu.geometry.clipping import (
    clip_polygon_to_convex_boundary,
    polygon_centroid,
)
from wenu.geometry.projected import (
    ProjectedCurve,
    ProjectedPoints,
    ProjectedPolygon,
    ProjectedPolygons,
)
from wenu.geometry.viewport import Viewport


def test_convex_boundary_intersection_has_area_centroid():
    polygon = ProjectedPolygon(
        x=np.asarray([0.0, 2.0, 2.0, 0.0]),
        y=np.asarray([-0.5, -0.5, 0.5, 0.5]),
        name="TST",
    )
    boundary = ProjectedCurve(
        x=np.asarray([-1.0, 1.0, 1.0, -1.0]),
        y=np.asarray([-1.0, -1.0, 1.0, 1.0]),
        closed=True,
    )

    clipped = clip_polygon_to_convex_boundary(polygon, boundary)

    assert clipped is not None
    np.testing.assert_allclose(
        polygon_centroid(clipped), (0.5, 0.0)
    )


def test_convex_clipping_cleans_vertices_once(monkeypatch):
    calls = []
    original = clipping_module._remove_consecutive_duplicate_vertices

    def recording(vertices):
        calls.append(len(vertices))
        return original(vertices)

    monkeypatch.setattr(
        clipping_module,
        "_remove_consecutive_duplicate_vertices",
        recording,
    )
    polygon = ProjectedPolygon(
        x=np.asarray([-2.0, 2.0, 2.0, -2.0]),
        y=np.asarray([-2.0, -2.0, 2.0, 2.0]),
    )

    clipped = clip_polygon_to_convex_boundary(
        polygon, circular_boundary(1.0, samples=73)
    )

    assert clipped is not None
    assert len(calls) == 1


def test_partial_constellation_uses_visible_region_anchor():
    label_layer = object()
    region_layer = SimpleNamespace()
    region_geometry = object()
    region_layer.spherical_geometry = lambda observer: region_geometry
    projected_regions = ProjectedPolygons(
        items=[
            ProjectedPolygon(
                x=np.asarray([0.5, 1.5, 1.5, 0.5]),
                y=np.asarray([-0.25, -0.25, 0.25, 0.25]),
                name="TST",
            )
        ]
    )

    class Projection:
        def project_geometry(self, geometry):
            assert geometry is region_geometry
            return projected_regions

    sky = SimpleNamespace(
        constellation_labels=label_layer,
        constellation_boundaries=region_layer,
        observer=object(),
    )
    options = apply_visible_constellation_label_anchors(
        {label_layer: {"render": {"draw_labels": True}}},
        sky=sky,
        projection=Projection(),
        viewport=Viewport.centered(width=2.0, height=2.0),
        boundary=circular_boundary(1.0, samples=73),
    )
    projected_labels = ProjectedPoints(
        x=np.asarray([1.2]),
        y=np.asarray([0.0]),
        labels=np.asarray(["Tst"], dtype=object),
    )

    prepared = options[label_layer]["prepare"](
        object(), projected_labels
    )

    assert prepared.metadata["visible_region_anchors"] is True
    assert prepared.metadata["visible_region_anchor_inset"] == 0.94
    assert np.hypot(prepared.x[0], prepared.y[0]) < 0.94
    assert prepared.x[0] < projected_labels.x[0]


def test_complete_constellation_keeps_existing_anchor():
    label_layer = object()
    region_layer = SimpleNamespace()
    region_geometry = object()
    region_layer.spherical_geometry = lambda observer: region_geometry
    projected_regions = ProjectedPolygons(
        items=[
            ProjectedPolygon(
                x=np.asarray([-0.2, 0.2, 0.2, -0.2]),
                y=np.asarray([-0.2, -0.2, 0.2, 0.2]),
                name="TST",
            )
        ]
    )

    class Projection:
        def project_geometry(self, geometry):
            return projected_regions

    sky = SimpleNamespace(
        constellation_labels=label_layer,
        constellation_boundaries=region_layer,
        observer=object(),
    )
    options = apply_visible_constellation_label_anchors(
        {label_layer: {}},
        sky=sky,
        projection=Projection(),
        viewport=Viewport.centered(width=2.0, height=2.0),
        boundary=circular_boundary(1.0, samples=73),
    )
    labels = ProjectedPoints(
        x=np.asarray([0.1]),
        y=np.asarray([0.05]),
        labels=np.asarray(["Tst"], dtype=object),
    )

    prepared = options[label_layer]["prepare"](object(), labels)

    np.testing.assert_array_equal(prepared.x, labels.x)
    np.testing.assert_array_equal(prepared.y, labels.y)
