"""Ring interior under the explicit native north-pole outline convention.

The source adapter supplies the winding interpretation. No catalogue,
projection, observer or rendering dependencies are required.
"""

import numpy as np


def ring_interior(coordinates, pole_winding):
    """Resolve the catalogue's filled side and its spherical area.

    Longitude-winding rings enclose the opposite side of their bounded
    north-pole planar outline. Ordinary catalogue rings enclose that outline.
    These are intrinsic ring properties, independent of the chart pole.
    """
    lon, lat = np.radians(coordinates).T
    cosine = np.cos(lat)
    vectors = np.column_stack((
        cosine * np.cos(lon), cosine * np.sin(lon), np.sin(lat)
    ))
    x = -vectors[:, 1] / (1.0 + vectors[:, 2])
    y = vectors[:, 0] / (1.0 + vectors[:, 2])
    signed_outline = np.sum(x * np.roll(y, -1) - y * np.roll(x, -1))
    left = bool(signed_outline > 0.0) != bool(pole_winding)
    following = np.roll(vectors, -1, axis=0)
    # Oriented triangle solid angles with the native north pole.
    left_area = np.sum(2.0 * np.arctan2(
        np.cross(vectors, following)[:, 2],
        1.0 + vectors[:, 2] + following[:, 2]
        + np.sum(vectors * following, axis=1),
    )) % (4.0 * np.pi)
    return left, float(left_area if left else 4.0 * np.pi - left_area)
