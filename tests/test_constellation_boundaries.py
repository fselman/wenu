"""Current constellation boundaries contracts."""

# Contracts consolidated from test_milestone8_boundaries.py.
"""Milestone 8 tests for geometry-only constellation boundaries."""

from collections import OrderedDict
from types import SimpleNamespace

import numpy as np
import pytest
from astropy.time import Time

from wenu.sky.geometrical_object import GeometricalObject
from wenu.sky.constellation_boundaries import ConstellationBoundaries
from wenu.geometry.spherical import SphericalPolygons


def make_boundaries(*, sampling_step_deg=1.0):
    boundaries = object.__new__(ConstellationBoundaries)
    boundaries.observer = None
    boundaries.boundaries_name = "iau"
    boundaries.filename = None
    boundaries.constellations = None
    boundaries.sampling_step_deg = sampling_step_deg
    boundaries.vertices = OrderedDict(
        {
            "TST": np.asarray(
                [
                    [1.0, -20.0],
                    [2.0, -20.0],
                    [2.0, -10.0],
                    [1.0, -10.0],
                ]
            )
        }
    )
    boundaries.sampled_vertices = OrderedDict()
    return boundaries


def make_observer():
    return SimpleNamespace(
        t_astropy=Time("2026-08-16T01:00:00"),
        lat_deg=-33.0,
        lon_deg=-71.5,
        elevation_m=52.0,
    )


def test_boundaries_are_geometrical_objects():
    assert issubclass(
        ConstellationBoundaries,
        GeometricalObject,
    )


def test_native_b1875_segments_are_sampled_before_transformation():
    boundaries = make_boundaries(sampling_step_deg=1.0)

    geometry = boundaries.spherical_geometry(make_observer())

    assert isinstance(geometry, SphericalPolygons)
    assert len(boundaries.vertices["TST"]) == 4
    assert len(boundaries.sampled_vertices["TST"]) > 4
    assert len(geometry.lon_deg[0]) == len(
        boundaries.sampled_vertices["TST"]
    )
    assert geometry.metadata["source_frame"] == "fk4"
    assert geometry.metadata["source_equinox"] == "B1875.0"


def test_spherical_geometry_preserves_boundary_identity():
    geometry = make_boundaries().spherical_geometry(
        make_observer()
    )

    np.testing.assert_array_equal(geometry.ids, ["TST"])
    np.testing.assert_array_equal(geometry.names, ["TST"])
    assert geometry.metadata["boundaries"] == "iau"


def test_serpens_selection_expands_to_native_polygons():
    assert ConstellationBoundaries._expand_constellation_names(
        ["Ser"]
    ) == {"SER1", "SER2"}


def test_boundary_selection_is_render_local_and_expands_serpens():
    boundaries = make_boundaries()
    boundaries.vertices["SER1"] = boundaries.vertices["TST"].copy()
    boundaries.vertices["SER2"] = boundaries.vertices["TST"].copy()

    selected = boundaries.spherical_geometry(
        make_observer(), selected={"Ser"}
    )
    complete = boundaries.spherical_geometry(make_observer())

    assert selected.ids.tolist() == ["SER1", "SER2"]
    assert complete.ids.tolist() == ["TST", "SER1", "SER2"]
    assert tuple(boundaries.vertices) == ("TST", "SER1", "SER2")


def test_unknown_boundary_selection_is_rejected():
    with pytest.raises(KeyError, match="Unknown loaded constellation"):
        make_boundaries().spherical_geometry(
            make_observer(), selected={"Cru"}
        )
    assert ConstellationBoundaries._expand_constellation_names(
        ["SerCap", "SerCau"]
    ) == {"SER1", "SER2"}


def test_native_containment_handles_ra_seam_without_matplotlib():
    vertices = np.asarray(
        [
            [23.0, -10.0],
            [1.0, -10.0],
            [1.0, 10.0],
            [23.0, 10.0],
        ]
    )

    assert ConstellationBoundaries._contains_b1875_point(
        vertices,
        ra_hours=0.0,
        dec_degrees=0.0,
    )
    assert not ConstellationBoundaries._contains_b1875_point(
        vertices,
        ra_hours=12.0,
        dec_degrees=0.0,
    )


def test_vectorized_region_lookup_preserves_shape_and_nonfinite_values():
    boundaries = make_boundaries()
    ra = np.asarray([[15.0, np.nan], [30.0, 45.0]])
    dec = np.asarray([[-15.0, 0.0], [-15.0, -15.0]])

    regions = boundaries.regions_of(
        ra,
        dec,
        candidates={"TST"},
    )

    assert regions.shape == ra.shape
    assert regions[0, 1] is None
    assert regions[0, 0] == boundaries.region_of(
        ra[0, 0], dec[0, 0], candidates={"TST"}
    )


def test_domain_layer_contains_no_projection_or_rendering_api():
    boundaries = make_boundaries()

    for name in (
        "project",
        "draw",
        "projected",
        "artists",
        "color",
        "linewidth",
        "alpha",
        "zorder",
        "horizon_altitude",
    ):
        assert not hasattr(boundaries, name)
