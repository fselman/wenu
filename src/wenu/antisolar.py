"""Observer-relative apparent antisolar direction geometry."""

from __future__ import annotations

from math import acos, asin, atan2, cos, degrees, radians, sin


MINIMUM_ANTISOLAR_SEPARATION_DEG = 0.1
ANTISOLAR_TANGENT_OFFSET_DEG = 1.0 / 60.0


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


def angular_separation_deg(first, second):
    """Return the great-circle separation between two directions."""
    ra1, dec1 = map(radians, first)
    ra2, dec2 = map(radians, second)
    cosine = (
        sin(dec1) * sin(dec2)
        + cos(dec1) * cos(dec2) * cos(ra2 - ra1)
    )
    return degrees(acos(max(-1.0, min(1.0, cosine))))


def offset_direction_deg(origin, position_angle, distance_deg):
    """Move from ``origin`` along a spherical position angle."""
    ra1, dec1 = map(radians, origin)
    bearing = radians(position_angle)
    distance = radians(distance_deg)
    dec2 = asin(
        sin(dec1) * cos(distance)
        + cos(dec1) * sin(distance) * cos(bearing)
    )
    delta_ra = atan2(
        sin(bearing) * sin(distance) * cos(dec1),
        cos(distance) - sin(dec1) * sin(dec2),
    )
    return (degrees(ra1 + delta_ra) % 360.0, degrees(dec2))


def antisolar_reference_direction(
    comet,
    sun,
    *,
    minimum_separation_deg=MINIMUM_ANTISOLAR_SEPARATION_DEG,
    offset_deg=ANTISOLAR_TANGENT_OFFSET_DEG,
):
    """Return a nearby tail-axis point, failing closed near conjunction."""
    separation = angular_separation_deg(comet, sun)
    if separation < minimum_separation_deg:
        raise ValueError(
            "Apparent comet-Sun separation is below the antisolar "
            f"orientation threshold of {minimum_separation_deg:g} degrees."
        )
    angle = antisolar_position_angle_deg(comet, sun)
    return offset_direction_deg(comet, angle, offset_deg)
