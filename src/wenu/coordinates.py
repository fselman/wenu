"""Shared coordinate vocabulary aliases and Wenu source/observer factories."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from wenu_kernel.coordinates import (
    CoordinateSpec, PositionStatus, GENERIC_SPHERICAL_SPEC,
    _identifier, _text, _optional_text,
)


ICRS_ASTROMETRIC_SPEC = CoordinateSpec(
    frame="icrs",
    origin="solar-system-barycenter",
    position_status=PositionStatus.ASTROMETRIC,
    epoch=None,
    provider="catalogue",
)


def icrs_catalogue_spec(provider, *, epoch=None, provenance=()):
    """Describe ICRS positions without inferring a measurement epoch.

    Callers with an admitted source epoch supply it explicitly. ICRS axes
    alone do not establish when a catalogue position was measured.
    """
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
    position_status,
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


def observation_context(observer):
    """Build the immutable transformation context for an Observer-like value."""
    instant, time_scale = _observer_instant(observer)
    longitude = getattr(observer, "lon_deg", None)
    latitude = getattr(observer, "lat_deg", None)
    elevation = getattr(observer, "elevation_m", None)
    if longitude is None or latitude is None:
        frame = getattr(observer, "altaz_frame", None)
        location = getattr(frame, "location", None)
        if location is None:
            raise TypeError(
                "observer must provide longitude/latitude attributes "
                "or an AltAz frame with a location."
            )
        geodetic = location.to_geodetic()
        longitude = geodetic.lon.deg
        latitude = geodetic.lat.deg
        if elevation is None:
            elevation = geodetic.height.to_value("m")
    return ObservationContext(
        longitude_deg=longitude,
        latitude_deg=latitude,
        elevation_m=0.0 if elevation is None else elevation,
        instant=instant,
        time_scale=time_scale,
    )


def _observer_instant(observer):
    time = getattr(observer, "t_astropy", None)
    if time is None:
        frame = getattr(observer, "altaz_frame", None)
        time = getattr(frame, "obstime", None)
    if time is None:
        utc_datetime = getattr(observer, "utc_datetime", None)
        if utc_datetime is not None:
            from astropy.time import Time

            time = Time(utc_datetime, scale="utc")
    if time is None:
        raise TypeError(
            "observer must provide t_astropy, AltAz obstime, or "
            "utc_datetime."
        )
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
