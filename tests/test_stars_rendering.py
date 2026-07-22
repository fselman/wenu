import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import PathCollection

from wenu.objects.stars import Stars
from wenu.renderers import layers


class DummyObserver:
    pass


class DummyProjection:
    def project(
        self,
        alt,
        az,
    ):
        return (
            np.asarray(az, dtype=float),
            np.asarray(alt, dtype=float),
        )


def test_stars_draw_returns_scatter_artist(monkeypatch):
    stars = Stars(
        observer=DummyObserver(),
    )

    stars.hip_df = pd.DataFrame(
        {
            "magnitude": [
                1.0,
                2.0,
            ],
        },
        index=[
            100,
            200,
        ],
    )

    def fake_compute_altaz(alt_min=-10.0):
        stars.alt = np.array(
            [30.0, 40.0]
        )
        stars.az = np.array(
            [10.0, 20.0]
        )
        return stars.alt, stars.az

    monkeypatch.setattr(
        stars,
        "compute_altaz",
        fake_compute_altaz,
    )

    fig, ax = plt.subplots()

    artist = stars.draw(
        ax,
        projection=DummyProjection(),
    )

    assert isinstance(
        artist,
        PathCollection,
    )

    assert artist.get_zorder() == layers.STARS

    np.testing.assert_allclose(
        artist.get_offsets(),
        [
            [10.0, 30.0],
            [20.0, 40.0],
        ],
    )

    assert stars.artist is artist

    plt.close(fig)
