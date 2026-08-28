"""Astronomical coordinate vocabulary and legacy conversion functions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import isfinite

import numpy as np


def _identifier(value, *, name):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string.")
    normalized = value.strip().lower()
    if not normalized:
        raise ValueError(f"{name} must be non-empty.")
    return normalized


def _text(value, *, name):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{name} must be non-empty.")
    return normalized


def _optional_text(value, *, name):
    if value is None:
        return None
    return _text(value, name=name)


class PositionStatus(str, Enum):
    """Scientific status of one represented astronomical position."""

    GEOMETRIC = "geometric"
    ASTROMETRIC = "astrometric"
    APPARENT = "apparent"
    TOPOCENTRIC = "topocentric"
    OBSERVED = "observed"


@dataclass(frozen=True)
class CoordinateSpec:
    """Immutable scientific identity of spherical astronomical coordinates."""

    frame: str
    origin: str
    position_status: PositionStatus = PositionStatus.GEOMETRIC
    epoch: str | None = None
    equinox: str | None = None
    instant: str | None = None
    time_scale: str | None = None
    longitude_unit: str = "deg"
    latitude_unit: str = "deg"
    representation: str = "spherical"
    provider: str | None = None
    model: str | None = None
    provenance: tuple[str, ...] = ()
    corrections: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self):
        object.__setattr__(
            self,
            "frame",
            _identifier(self.frame, name="frame"),
        )
        object.__setattr__(
            self,
            "origin",
            _identifier(self.origin, name="origin"),
        )
        try:
            status = PositionStatus(self.position_status)
        except ValueError as error:
            raise ValueError(
                f"Unsupported position status: {self.position_status!r}."
            ) from error
        object.__setattr__(self, "position_status", status)

        for name in ("epoch", "equinox", "instant", "provider", "model"):
            object.__setattr__(
                self,
                name,
                _optional_text(getattr(self, name), name=name),
            )

        time_scale = (
            None
            if self.time_scale is None
            else _identifier(self.time_scale, name="time_scale")
        )
        if (self.instant is None) != (time_scale is None):
            raise ValueError(
                "instant and time_scale must be supplied together."
            )
        object.__setattr__(self, "time_scale", time_scale)

        for name in (
            "longitude_unit",
            "latitude_unit",
            "representation",
        ):
            object.__setattr__(
                self,
                name,
                _identifier(getattr(self, name), name=name),
            )

        provenance = tuple(
            _text(value, name="provenance entry")
            for value in self.provenance
        )
        object.__setattr__(self, "provenance", provenance)

        corrections = frozenset(
            _identifier(value, name="correction")
            for value in self.corrections
        )
        object.__setattr__(self, "corrections", corrections)


GENERIC_SPHERICAL_SPEC = CoordinateSpec(
    frame="generic-spherical",
    origin="unit-sphere",
    provider="wenu synthetic geometry",
)


ICRS_ASTROMETRIC_SPEC = CoordinateSpec(
    frame="icrs",
    origin="solar-system-barycenter",
    position_status=PositionStatus.ASTROMETRIC,
    epoch="J2000.0",
    provider="catalogue",
)


def icrs_catalogue_spec(provider, *, epoch="J2000.0", provenance=()):
    """Describe static native catalogue positions in ICRS."""
    return CoordinateSpec(
        frame="icrs",
        origin="solar-system-barycenter",
        position_status=PositionStatus.ASTROMETRIC,
        epoch=epoch,
        provider=provider,
        provenance=provenance,
    )


def observer_altaz_spec(
    observer,
    *,
    position_status=PositionStatus.TOPOCENTRIC,
    provider=None,
    model=None,
    provenance=(),
    corrections=frozenset(),
):
    """Describe observer-local AltAz geometry at the observer instant."""
    instant, time_scale = _observer_instant(observer)
    return CoordinateSpec(
        frame="altaz",
        origin="observer",
        position_status=position_status,
        instant=instant,
        time_scale=time_scale,
        provider=provider,
        model=model,
        provenance=provenance,
        corrections=corrections,
    )


def observer_celestial_spec(
    observer,
    frame,
    *,
    provider="astropy",
    model=None,
    provenance=(),
    corrections=frozenset(),
):
    """Describe an observer-instant direction expressed in a celestial frame."""
    instant, time_scale = _observer_instant(observer)
    return CoordinateSpec(
        frame=frame,
        origin="topocentric-direction",
        position_status=PositionStatus.ASTROMETRIC,
        instant=instant,
        time_scale=time_scale,
        provider=provider,
        model=model,
        provenance=provenance,
        corrections=corrections,
    )


def _observer_instant(observer):
    time = getattr(observer, "t_astropy", None)
    if time is None:
        frame = getattr(observer, "altaz_frame", None)
        time = getattr(frame, "obstime", None)
    if time is None:
        raise TypeError("observer must provide t_astropy or AltAz obstime.")
    instant = getattr(time, "isot", None) or str(time)
    time_scale = getattr(time, "scale", None) or "utc"
    return str(instant), str(time_scale)


@dataclass(frozen=True)
class ObservationContext:
    """Immutable observer-local input to an astronomical transformation."""

    longitude_deg: float
    latitude_deg: float
    elevation_m: float
    instant: str
    time_scale: str = "utc"
    refraction_policy: str = "vacuum"
    earth_orientation_policy: str = "astropy"

    def __post_init__(self):
        for name in ("longitude_deg", "latitude_deg", "elevation_m"):
            value = getattr(self, name)
            if isinstance(value, bool):
                raise TypeError(f"{name} must be a finite number.")
            try:
                value = float(value)
            except (TypeError, ValueError) as error:
                raise TypeError(
                    f"{name} must be a finite number."
                ) from error
            if not isfinite(value):
                raise ValueError(f"{name} must be finite.")
            object.__setattr__(self, name, value)

        if not -90.0 <= self.latitude_deg <= 90.0:
            raise ValueError("latitude_deg must be between -90 and 90.")
        longitude = (self.longitude_deg + 180.0) % 360.0 - 180.0
        object.__setattr__(self, "longitude_deg", longitude)
        object.__setattr__(
            self,
            "instant",
            _text(self.instant, name="instant"),
        )
        for name in (
            "time_scale",
            "refraction_policy",
            "earth_orientation_policy",
        ):
            object.__setattr__(
                self,
                name,
                _identifier(getattr(self, name), name=name),
            )


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