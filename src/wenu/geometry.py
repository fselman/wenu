# geometry functions
import numpy as np

from astropy.coordinates import SkyCoord, AltAz
import astropy.units as u

from skyfield.api import Star


# To draw a constant declination line
def constant_declination_altaz(
    obs,
    t,
    dec_deg,
    npts=720,
):
    """
    Compute the Alt/Az of a constant-declination circle.

    Parameters
    ----------
    obs : Skyfield observer
    t : Skyfield Time
    dec_deg : float
        Declination in degrees.
    npts : int
        Number of points.

    Returns
    -------
    alt_deg, az_deg : ndarray
    """

    ra_hours = np.linspace(0.0, 24.0, npts)

    stars = Star(
        ra_hours=ra_hours,
        dec_degrees=np.full(npts, dec_deg),
    )

    apparent = (
        obs.skyfield.at(obs.t)
        .observe(stars)
        .apparent(deflectors=[])
    )

    alt, az, _ = apparent.altaz()

    return alt.degrees, az.degrees



# =========================================================
# RA/Dec → Alt/Az (tu implementación original, intacta)
# =========================================================
def radec_to_altaz(ra_deg, dec_deg, t, lat_deg, lon_deg):
    """
    Convert Right Ascension / Declination (ICRS) to Altitude / Azimuth.

    Parameters
    ----------
    ra_deg : float or array-like
    dec_deg : float or array-like
    t : skyfield.timelib.Time
    lat_deg : float
    lon_deg : float (East positive)

    Returns
    -------
    alt_deg, az_deg : ndarray
    """

    # Local Sidereal Time
    lst_hours = t.gmst + lon_deg / 15.0
    lst_deg = (lst_hours * 15.0) % 360.0

    # Hour angle
    ha = np.deg2rad(lst_deg - ra_deg)

    dec = np.deg2rad(dec_deg)
    lat = np.deg2rad(lat_deg)

    # Altitude
    alt = np.arcsin(
        np.sin(dec) * np.sin(lat) +
        np.cos(dec) * np.cos(lat) * np.cos(ha)
    )

    # Azimuth
    az = np.arctan2(
        -np.sin(ha) * np.cos(dec),
        np.sin(dec) * np.cos(lat)
        - np.cos(dec) * np.sin(lat) * np.cos(ha)
    )

    alt_deg = np.rad2deg(alt)
    az_deg = (np.rad2deg(az) + 360.0) % 360.0

    return alt_deg, az_deg


# =========================================================
# ECLIPTIC (β = 0)
# =========================================================
def ecliptic_altaz(t, lat_deg, lon_deg, npts=720):
    """
    Alt/Az of the ecliptic.

    Uses same math as your notebook (no astropy dependency here).

    Returns
    -------
    alt, az : ndarray (degrees)
    """

    # LST
    lst_hours = t.gmst + lon_deg / 15.0
    lst_deg = (lst_hours * 15.0) % 360.0

    lat = np.deg2rad(lat_deg)

    # Obliquity
    eps = np.deg2rad(23.439)

    lam = np.linspace(0, 2*np.pi, npts)

    # Ecliptic coordinates
    x_ecl = np.cos(lam)
    y_ecl = np.sin(lam)

    # Rotate to equatorial
    x_eq = x_ecl
    y_eq = y_ecl * np.cos(eps)
    z_eq = y_ecl * np.sin(eps)

    ra = np.arctan2(y_eq, x_eq)
    dec = np.arcsin(z_eq)

    ra_deg = np.rad2deg(ra) % 360.0

    # Hour angle
    ha = np.deg2rad(lst_deg - ra_deg)

    # Alt/Az
    alt = np.arcsin(
        np.sin(dec) * np.sin(lat) +
        np.cos(dec) * np.cos(lat) * np.cos(ha)
    )

    az = np.arctan2(
        -np.sin(ha) * np.cos(dec),
        np.sin(dec) * np.cos(lat)
        - np.cos(dec) * np.sin(lat) * np.cos(ha)
    )

    alt = np.rad2deg(alt)
    az = (np.rad2deg(az) + 360.0) % 360.0

    return alt, az


# =========================================================
# ECLIPTIC KEY POINTS (Equinoxes / Solstices)
# =========================================================
def ecliptic_keypoints_altaz(t, lat_deg, lon_deg):
    """
    Return Alt/Az of equinoxes and solstices.

    Returns
    -------
    dict:
        {
            "vernal": (alt, az),
            "summer": (alt, az),
            "autumnal": (alt, az),
            "winter": (alt, az),
        }
    """

    lst_hours = t.gmst + lon_deg / 15.0
    lst_deg = (lst_hours * 15.0) % 360.0

    lat = np.deg2rad(lat_deg)
    eps = np.deg2rad(23.439)

    lam_deg = {
        "vernal": 0,
        "summer": 90,
        "autumnal": 180,
        "winter": 270,
    }

    results = {}

    for key, lam_d in lam_deg.items():
        lam = np.deg2rad(lam_d)

        x = np.cos(lam)
        y = np.sin(lam)

        x_eq = x
        y_eq = y * np.cos(eps)
        z_eq = y * np.sin(eps)

        ra = np.arctan2(y_eq, x_eq)
        dec = np.arcsin(z_eq)

        ra_deg = np.rad2deg(ra) % 360.0

        ha = np.deg2rad(lst_deg - ra_deg)

        alt = np.arcsin(
            np.sin(dec) * np.sin(lat) +
            np.cos(dec) * np.cos(lat) * np.cos(ha)
        )

        az = np.arctan2(
            -np.sin(ha) * np.cos(dec),
            np.sin(dec) * np.cos(lat)
            - np.cos(dec) * np.sin(lat) * np.cos(ha)
        )

        alt = np.rad2deg(alt)
        az = (np.rad2deg(az) + 360.0) % 360.0

        results[key] = (alt, az)

    return results


# =========================================================
# GALACTIC PLANE (b = 0)
# =========================================================
def galactic_plane_altaz(t, location, npts=720):
    """
    Galactic plane (b = 0) using Astropy transform pipeline.

    Parameters
    ----------
    t : skyfield.timelib.Time
    location : astropy.coordinates.EarthLocation

    Returns
    -------
    alt, az : ndarray (degrees)
    """

    # Avoid discontinuity at edges
    lon = np.linspace(-180.0, 180.0, npts) * u.deg
    b = np.zeros(npts) * u.deg

    # Galactic frame
    gal = SkyCoord(l=lon, b=b, frame='galactic')

    # Convert to ICRS
    icrs = gal.icrs

    # Convert to AltAz
    altaz = icrs.transform_to(
        AltAz(
            obstime=t.to_astropy(),
            location=location
        )
    )

    return altaz.alt.deg, altaz.az.deg

def equator_altaz(obs, t, npts=1000):
    """
    Celestial equator in Alt/Az using Skyfield.

    Parameters
    ----------
    obs : Skyfield observer (earth + wgs84.latlon)
    t   : Skyfield Time

    Returns
    -------
    alt, az : ndarray (degrees)
    """

    # RA from 0 to 24h, Dec = 0
    ra_hours = np.linspace(0.0, 24.0, npts)
    dec_deg = np.zeros_like(ra_hours)

    stars = Star(ra_hours=ra_hours, dec_degrees=dec_deg)

    apparent = obs.at(t).observe(stars).apparent(deflectors=[])

    alt, az, _ = apparent.altaz()

    return alt.degrees, az.degrees

def galactic_center_altaz(t, location):
    """
    Galactic center (l=0, b=0) in Alt/Az.

    Parameters
    ----------
    t : Skyfield Time
    location : astropy.coordinates.EarthLocation

    Returns
    -------
    alt, az : floats (degrees)
    """

    # Galactic center
    gc = SkyCoord(
        l=0 * u.deg,
        b=0 * u.deg,
        frame='galactic'
    )

    # Convert to ICRS
    gc_icrs = gc.icrs

    # Convert to AltAz
    altaz = gc_icrs.transform_to(
        AltAz(
            obstime=t.to_astropy(),
            location=location
        )
    )

    return altaz.alt.deg, altaz.az.deg
