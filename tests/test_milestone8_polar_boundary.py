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
