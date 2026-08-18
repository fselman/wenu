"""Reviewed label clearances for the physical polar planisphere."""

import numpy as np
from matplotlib.path import Path


def _light_dashed_circle():
    """Return a sparse open circle suitable for the broad Hyades region."""
    vertices = []
    codes = []
    for start_deg in np.arange(0.0, 360.0, 30.0):
        angles = np.radians(np.linspace(start_deg, start_deg + 20.0, 5))
        vertices.extend(zip(np.cos(angles), np.sin(angles), strict=True))
        codes.extend((Path.MOVETO, *(Path.LINETO for _ in angles[1:])))
    return Path(np.asarray(vertices, dtype=float), np.asarray(codes))

SOUTH_CONSTELLATION_LABEL_OFFSETS = {
    "Mus": (-0.018, 0.1125),
    "Cir": (0.0, 0.135),
    "Cen": (0.045, -0.15),
    "TrA": (0.06, 0.105),
    "Ara": (0.03, 0.15),
    "Crv": (0.12, 0.0),
    "Crt": (0.12, 0.0),
    "Gru": (0.0, 0.12),
    "PsA": (0.0, 0.12),
    "Phe": (0.0, -0.12),
    "For": (0.0, 0.12),
    "Sgr": (0.0, 0.12),
    "CMa": (0.0, 0.12),
}

SOUTH_DEEP_SKY_LABEL_OFFSETS = {
    "open_clusters": {"Híades": (0.075, 0.15)},
    "globular_clusters": {
        "47 Tuc": (0.12, 0.0225),
        "ω": (0.04, 0.01),
    },
}

# The Hyades is extended, but its boundary should remain quiet on paper.
SOUTH_OPEN_CLUSTER_SYMBOL_STYLES = {
    "Melotte 25": {
        "marker": _light_dashed_circle(),
        "s": 600.0,
        "facecolors": "none",
        "linewidths": 0.45,
    }
}

SOUTH_GLOBULAR_MINIMUM_SIZE_ARCMIN = 120.0
SOUTH_GLOBULAR_LABEL_FONTSIZE = 5.5
