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
