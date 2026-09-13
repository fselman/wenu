"""Observer-relative apparent antisolar direction geometry."""

from __future__ import annotations

from math import atan2, cos, degrees, radians, sin


def position_angle_deg(origin, destination):
    """Return destination position angle from origin, east of north."""
    ra1, dec1 = map(radians, origin)
    ra2, dec2 = map(radians, destination)
    delta_ra = ra2 - ra1
    east = cos(dec2) * sin(delta_ra)
    north = (
        cos(dec1) * sin(dec2)
        - sin(dec1) * cos(dec2) * cos(delta_ra)
    )
    return degrees(atan2(east, north)) % 360.0


def antisolar_position_angle_deg(comet, sun):
    """Return apparent comet-tail PA, opposite the apparent Sun."""
    return (position_angle_deg(comet, sun) + 180.0) % 360.0
