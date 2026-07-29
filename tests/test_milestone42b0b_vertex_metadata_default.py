from types import SimpleNamespace

import numpy as np
import pandas as pd

from wenu.objects.stars import Stars


def stars_with(frame):
    stars = Stars(observer=None)
    stars.hip_df = frame
    stars.compute_altaz = lambda **kwargs: (
        np.asarray((30.0, 40.0)),
        np.asarray((120.0, 130.0)),
    )
    return stars


def test_missing_vertex_column_defaults_to_aligned_false_values():
    stars = stars_with(
        pd.DataFrame(
            {"magnitude": [1.0, 2.0]},
            index=[10, 20],
        )
    )
    geometry = stars.spherical_geometry(SimpleNamespace())
    assert geometry.metadata["is_constellation_vertex"].tolist() == [
        False,
        False,
    ]


def test_existing_vertex_column_is_preserved():
    stars = stars_with(
        pd.DataFrame(
            {
                "magnitude": [1.0, 2.0],
                "is_constellation_vertex": [True, False],
            },
            index=[10, 20],
        )
    )
    geometry = stars.spherical_geometry(SimpleNamespace())
    assert geometry.metadata["is_constellation_vertex"].tolist() == [
        True,
        False,
    ]
