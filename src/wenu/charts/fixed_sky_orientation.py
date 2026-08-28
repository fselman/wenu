"""Renderer-neutral orientation for a fixed circumpolar celestial scene."""

from __future__ import annotations

from dataclasses import dataclass

import astropy.units as u
from astropy.coordinates import SkyCoord
import numpy as np

from .regional import target_up_position_angle


def _signed_angle_deg(value: float) -> float:
    """Normalize one angle to the signed half-open degree interval."""
    return float((float(value) + 180.0) % 360.0 - 180.0)


def _pole_declination_deg(pole: str) -> float:
    name = str(pole).strip().lower()
    if name not in {"north", "south"}:
        raise ValueError("pole must be 'north' or 'south'.")
    return 90.0 if name == "north" else -90.0


def circumpolar_pole_coordinate(pole: str) -> SkyCoord:
    """Return the J2000 pole used by the canonical circumpolar chart."""
    return SkyCoord(
        ra=0.0 * u.deg,
        dec=_pole_declination_deg(pole) * u.deg,
        frame="fk5",
        equinox="J2000",
    )


def circumpolar_orientation_reference(pole: str) -> SkyCoord:
    """Return a stable fixed-celestial direction ten degrees from the pole."""
    declination = 80.0 if _pole_declination_deg(pole) > 0.0 else -80.0
    return SkyCoord(
        ra=0.0 * u.deg,
        dec=declination * u.deg,
        frame="fk5",
        equinox="J2000",
    )


def _reference_position_angle_deg(observer, pole: str) -> float:
    center = circumpolar_pole_coordinate(pole).transform_to(
        observer.altaz_frame
    )
    reference = circumpolar_orientation_reference(pole).transform_to(
        observer.altaz_frame
    )
    return target_up_position_angle(
        center_alt_deg=float(center.alt.deg),
        center_az_deg=float(center.az.deg),
        target_alt_deg=float(reference.alt.deg),
        target_az_deg=float(reference.az.deg),
    )


@dataclass(frozen=True)
class FixedSkyCircumpolarOrientation:
    """Astronomical provenance for one anchored projection rotation."""

    pole: str
    anchor_reference_position_angle_deg: float
    frame_reference_position_angle_deg: float
    position_angle_deg: float


def fixed_sky_circumpolar_orientation(
    anchor_observer,
    frame_observer,
    *,
    pole: str,
    anchor_position_angle_deg: float = 0.0,
) -> FixedSkyCircumpolarOrientation:
    """Return the frame rotation that keeps celestial geometry anchored.

    A fixed celestial reference direction is transformed independently at the
    anchor and frame instants. Their signed tangent-plane position-angle
    difference is added to the chart's anchor position angle. The calculation
    therefore follows the actual astronomical coordinate transformation and
    does not assume a uniform 15-degree-per-hour rotation.
    """
    anchor_position_angle_deg = float(anchor_position_angle_deg)
    if not np.isfinite(anchor_position_angle_deg):
        raise ValueError("anchor_position_angle_deg must be finite.")
    name = str(pole).strip().lower()
    _pole_declination_deg(name)
    anchor_angle = _reference_position_angle_deg(anchor_observer, name)
    frame_angle = _reference_position_angle_deg(frame_observer, name)
    position_angle = _signed_angle_deg(
        anchor_position_angle_deg + frame_angle - anchor_angle
    )
    return FixedSkyCircumpolarOrientation(
        pole=name,
        anchor_reference_position_angle_deg=anchor_angle,
        frame_reference_position_angle_deg=frame_angle,
        position_angle_deg=position_angle,
    )
