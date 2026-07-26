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
