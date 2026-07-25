"""Shared coordinate-conversion functions."""

from __future__ import annotations

import numpy as np


def radec_to_altaz(ra_deg, dec_deg, t, lat_deg, lon_deg):
    """Convert ICRS right ascension and declination to Alt/Az."""
    lst_hours = t.gmst + lon_deg / 15.0
    lst_deg = (lst_hours * 15.0) % 360.0
    ha = np.deg2rad(lst_deg - np.asarray(ra_deg, dtype=float))
    dec = np.deg2rad(np.asarray(dec_deg, dtype=float))
    lat = np.deg2rad(float(lat_deg))

    altitude = np.arcsin(
        np.sin(dec) * np.sin(lat)
        + np.cos(dec) * np.cos(lat) * np.cos(ha)
    )
    azimuth = np.arctan2(
        -np.sin(ha) * np.cos(dec),
        np.sin(dec) * np.cos(lat)
        - np.cos(dec) * np.sin(lat) * np.cos(ha),
    )
    return (
        np.rad2deg(altitude),
        (np.rad2deg(azimuth) + 360.0) % 360.0,
    )
