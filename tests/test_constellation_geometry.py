"""Current constellation geometry contracts."""

# Contracts consolidated from test_milestone8_geometrical_object.py.
"""Milestone 8 tests for the GeometricalObject hierarchy."""

import pytest

from wenu.objects.astronomical_object import AstronomicalObject
from wenu.sky import GeometricalObject, SkyLayer
from wenu.sky.constellation_boundaries import ConstellationBoundaries


def test_geometrical_object_is_abstract_sky_layer():
    assert issubclass(GeometricalObject, SkyLayer)

    with pytest.raises(TypeError):
        GeometricalObject()


def test_geometrical_and_astronomical_branches_are_distinct():
    assert not issubclass(GeometricalObject, AstronomicalObject)
    assert not issubclass(AstronomicalObject, GeometricalObject)


def test_constellation_boundaries_are_geometrical_objects():
    assert issubclass(
        ConstellationBoundaries,
        GeometricalObject,
    )
    assert not issubclass(
        ConstellationBoundaries,
        AstronomicalObject,
    )


# Contracts consolidated from test_milestone8_polar_boundary.py.
"""Regression test for polar boundary closure artifacts."""

from collections import OrderedDict

import numpy as np

from wenu.sky.constellation_boundaries import ConstellationBoundaries


def test_polar_closure_vertices_are_not_rendered():
    boundaries = object.__new__(ConstellationBoundaries)
    boundaries.sampling_step_deg = 0.5
    boundaries.vertices = OrderedDict(
        {
            "OCT": np.asarray(
                [
                    [0.0, -90.0],
                    [0.0, -82.5],
                    [3.5, -82.5],
                    [3.5, -85.0],
                    [7.66667, -85.0],
                    [7.66667, -82.5],
                    [13.66667, -82.5],
                    [18.0, -82.5],
                    [18.0, -75.0],
                    [21.33333, -75.0],
                    [23.33333, -75.0],
                    [24.0, -75.0],
                    [24.0, -90.0],
                    [12.0, -90.0],
                ]
            )
        }
    )
    boundaries.sampled_vertices = OrderedDict()

    sampled = boundaries.sample()["OCT"]

    # Source data remain authoritative and unchanged.
    assert np.count_nonzero(
        np.isclose(boundaries.vertices["OCT"][:, 1], -90.0)
    ) == 3

    # Rendering geometry contains no artificial radial edge to the pole.
    assert not np.any(np.isclose(sampled[:, 1], -90.0))

    # The 24h-to-0h closure is treated as one native meridian.
    assert np.isclose(sampled[-1, 0] % 24.0, 0.0)
    assert np.isclose(sampled[-1, 1], -82.5)

# Contracts consolidated from test_milestone10_constellation_lines.py.
"""Milestone 10 domain tests for constellation-line geometry."""

from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

from wenu.sky.constellation_lines import ConstellationLines
from wenu.sky.geometrical_object import GeometricalObject
from wenu.geometry.spherical import SphericalCurves


class Angle:
    def __init__(self, degrees):
        self.degrees = np.asarray(degrees, dtype=float)


class Apparent:
    def __init__(self, shift):
        self.shift = shift

    def observe(self, stars):
        return self

    def apparent(self, deflectors):
        assert deflectors == []
        return self

    def altaz(self):
        return (
            Angle([10.0 + self.shift, 20.0 + self.shift, -5.0]),
            Angle([30.0 + self.shift, 40.0 + self.shift, 50.0]),
            None,
        )


class ObserverVector:
    def at(self, time):
        return Apparent(float(time))


def make_lines(tmp_path):
    filename = Path(tmp_path) / "test.fab"
    filename.write_text("Cru 3 100 200 300\n", encoding="utf-8")
    stars = SimpleNamespace(
        catalog=pd.DataFrame(index=[100, 200, 300]),
        skyfield_stars=object(),
    )
    observer = SimpleNamespace(
        skyfield=ObserverVector(),
        t=0.0,
    )
    return ConstellationLines(
        stars=stars,
        filename=filename,
    ), observer


def test_constellation_lines_are_geometrical_objects(tmp_path):
    lines, _ = make_lines(tmp_path)
    assert isinstance(lines, GeometricalObject)


def test_lines_return_one_spherical_curve_per_hip_edge(tmp_path):
    lines, observer = make_lines(tmp_path)
    geometry = lines.spherical_geometry(observer)

    assert isinstance(geometry, SphericalCurves)
    assert len(geometry) == 2
    assert geometry.names.tolist() == ["Cru", "Cru"]
    assert geometry.metadata["hip_edges"] == ((100, 200), (200, 300))
    np.testing.assert_allclose(geometry.lon_deg[0], [30.0, 40.0])
    np.testing.assert_allclose(geometry.lat_deg[0], [10.0, 20.0])


def test_geometry_is_recomputed_at_observer_time(tmp_path):
    lines, observer = make_lines(tmp_path)
    first = lines.spherical_geometry(observer)
    observer.t = 5.0
    second = lines.spherical_geometry(observer)

    np.testing.assert_allclose(
        second.lon_deg[0] - first.lon_deg[0],
        [5.0, 5.0],
    )
    np.testing.assert_allclose(
        second.lat_deg[0] - first.lat_deg[0],
        [5.0, 5.0],
    )


def test_geometry_does_not_mutate_active_star_selection(tmp_path):
    lines, observer = make_lines(tmp_path)
    active = pd.DataFrame(index=[100])
    lines.stars.hip_df = active

    lines.spherical_geometry(observer)

    assert lines.stars.hip_df is active


def test_line_selection_is_render_local_and_ordered(tmp_path):
    lines, observer = make_lines(tmp_path)
    lines.edges_by_constellation["Cen"] = [(100, 300)]
    lines.edges.append((100, 300))

    selected = lines.spherical_geometry(observer, selected={"Cen"})
    complete = lines.spherical_geometry(observer)

    assert selected.names.tolist() == ["Cen"]
    assert complete.names.tolist() == ["Cru", "Cru", "Cen"]
    assert tuple(lines.edges_by_constellation) == ("Cru", "Cen")


def test_unknown_line_selection_is_rejected(tmp_path):
    lines, observer = make_lines(tmp_path)

    with pytest.raises(KeyError, match="Unknown loaded constellation"):
        lines.spherical_geometry(observer, selected={"Lyr"})

# Contracts consolidated from test_milestone12_coordinate_grids.py.
"""Milestone 12 domain tests for coordinate grids."""

from types import SimpleNamespace

import numpy as np

from wenu.sky.coordinate_grids import (
    CoordinatesGrid,
    SphericalCoordinatesGrid,
)
from wenu.sky.geometrical_object import GeometricalObject
from wenu.geometry.spherical import SphericalCurves, SphericalGrid


class StubGrid(CoordinatesGrid):
    coordinate_system = "test"

    def _native_to_icrs(self, longitude_deg, latitude_deg):
        return (
            np.asarray(longitude_deg) + 10.0,
            np.asarray(latitude_deg) - 5.0,
        )


def observer(time):
    return SimpleNamespace(
        t=time,
        lat_deg=-33.0,
        lon_deg=-71.5,
    )


def test_grid_hierarchy_and_compatibility_alias():
    assert issubclass(CoordinatesGrid, GeometricalObject)
    assert SphericalCoordinatesGrid is CoordinatesGrid


def test_parallel_and_meridian_return_spherical_collections(monkeypatch):
    grid = StubGrid(observer(1.0), samples=5)

    def fake_transform(ra, dec, time, lat, lon):
        return np.asarray(dec) + time, np.asarray(ra) + time

    monkeypatch.setattr(
        "wenu.sky.coordinate_grids.radec_to_altaz",
        fake_transform,
    )
    parallel = grid.parallel(20.0, style={"linewidth": 1.5})
    meridian = grid.meridian(30.0)

    assert isinstance(parallel, SphericalCurves)
    assert isinstance(meridian, SphericalCurves)
    assert len(parallel) == len(meridian) == 1
    assert parallel.closed.tolist() == [True]
    assert meridian.closed.tolist() == [False]
    assert parallel.metadata["styles"] == ({"linewidth": 1.5},)


def test_complete_grid_preserves_component_groups(monkeypatch):
    monkeypatch.setattr(
        "wenu.sky.coordinate_grids.radec_to_altaz",
        lambda ra, dec, *args: (np.asarray(dec), np.asarray(ra)),
    )
    geometry = StubGrid(observer(0.0), samples=5).grid(
        longitudes=[0.0, 90.0],
        latitudes=[-30.0, 30.0],
    )

    assert isinstance(geometry, SphericalGrid)
    assert set(geometry.components) == {"meridians", "parallels"}
    assert len(geometry["meridians"]) == 2
    assert len(geometry["parallels"]) == 2
    assert geometry.metadata["coordinate_system"] == "test"


def test_coordinate_geometry_uses_observer_time(monkeypatch):
    def fake_transform(ra, dec, time, lat, lon):
        return np.asarray(dec) + time, np.asarray(ra) + time

    monkeypatch.setattr(
        "wenu.sky.coordinate_grids.radec_to_altaz",
        fake_transform,
    )
    first = StubGrid(observer(1.0), samples=5).parallel(0.0)
    second = StubGrid(observer(4.0), samples=5).parallel(0.0)

    np.testing.assert_allclose(
        second.lon_deg[0] - first.lon_deg[0],
        3.0,
    )
    np.testing.assert_allclose(
        second.lat_deg[0] - first.lat_deg[0],
        3.0,
    )
