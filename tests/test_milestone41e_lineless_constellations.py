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
