"""Milestone 11 domain regression retained after legacy renderer removal."""

from collections import OrderedDict
from types import SimpleNamespace

import numpy as np
from astropy.time import Time

from wenu.sky.constellation_boundaries import ConstellationBoundaries


def make_boundaries():
    boundaries = object.__new__(ConstellationBoundaries)
    boundaries.observer = None
    boundaries.boundaries_name = "iau"
    boundaries.filename = None
    boundaries.constellations = None
    boundaries.sampling_step_deg = 2.0
    boundaries.vertices = OrderedDict(
        {
            "TST": np.asarray(
                [
                    [1.0, -20.0],
                    [2.0, -20.0],
                    [2.0, -10.0],
                    [1.0, -10.0],
                ],
                dtype=float,
            )
        }
    )
    boundaries.sampled_vertices = OrderedDict()
    return boundaries


def make_observer(time):
    return SimpleNamespace(
        t_astropy=Time(time),
        lat_deg=-33.0,
        lon_deg=-71.5,
        elevation_m=52.0,
    )


def test_boundary_geometry_is_evaluated_at_observer_time():
    boundaries = make_boundaries()

    first = boundaries.spherical_geometry(
        make_observer("2026-08-16T01:00:00")
    )
    second = boundaries.spherical_geometry(
        make_observer("2026-08-16T07:00:00")
    )

    # Native B1875 sampling is stable, but its observer-time Alt/Az
    # realization must change with time.
    assert not np.allclose(first.lon_deg[0], second.lon_deg[0])
    assert not np.allclose(first.lat_deg[0], second.lat_deg[0])
    assert first.metadata["source_equinox"] == "B1875.0"
    assert second.metadata["source_equinox"] == "B1875.0"
