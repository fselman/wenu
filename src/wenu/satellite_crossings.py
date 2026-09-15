"""Provider-neutral artificial-satellite crossing contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import isfinite

from wenu.coordinates import CoordinateSpec


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


def _finite_float(value, *, name):
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a finite number.")
    try:
        normalized = float(value)
    except (TypeError, ValueError) as error:
        raise TypeError(f"{name} must be a finite number.") from error
    if not isfinite(normalized):
        raise ValueError(f"{name} must be finite.")
    return normalized


def _utc_instant(value, *, name):
    value = _text(value, name=name)
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as error:
        raise ValueError(f"{name} must be an ISO-8601 UTC instant.") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError(f"{name} must be an ISO-8601 UTC instant.")
    normalized = parsed.astimezone(timezone.utc).isoformat(timespec="microseconds")
    return normalized.replace("+00:00", "Z")


def _instant_datetime(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _string_tuple(value, *, name):
    if isinstance(value, (str, bytes)):
        raise TypeError(f"{name} must be an iterable of strings.")
    try:
        return tuple(_text(item, name=f"{name} entry") for item in value)
    except TypeError as error:
        raise TypeError(f"{name} must be an iterable of strings.") from error


@dataclass(frozen=True)
class SatelliteIdentity:
    """Provider-neutral identity of one artificial satellite."""

    norad_catalog_id: int
    object_name: str | None = None
    international_designator: str | None = None
    classification: str | None = None

    def __post_init__(self):
        if isinstance(self.norad_catalog_id, bool) or not isinstance(
            self.norad_catalog_id, int
        ):
            raise TypeError("norad_catalog_id must be a positive integer.")
        if self.norad_catalog_id <= 0:
            raise ValueError("norad_catalog_id must be a positive integer.")
        for name in (
            "object_name",
            "international_designator",
            "classification",
        ):
            object.__setattr__(
                self,
                name,
                _optional_text(getattr(self, name), name=name),
            )


@dataclass(frozen=True)
class SatelliteObserver:
    """Immutable terrestrial site and coordinate-policy identity."""

    observer_id: str
    longitude_deg: float
    latitude_deg: float
    elevation_m: float
    refraction_policy: str = "vacuum"
    earth_orientation_policy: str = "astropy"

    def __post_init__(self):
        object.__setattr__(
            self, "observer_id", _text(self.observer_id, name="observer_id")
        )
        for name in ("longitude_deg", "latitude_deg", "elevation_m"):
            object.__setattr__(
                self,
                name,
                _finite_float(getattr(self, name), name=name),
            )
        if not -90.0 <= self.latitude_deg <= 90.0:
            raise ValueError("latitude_deg must be between -90 and 90.")
        object.__setattr__(
            self,
            "longitude_deg",
            (self.longitude_deg + 180.0) % 360.0 - 180.0,
        )
        for name in ("refraction_policy", "earth_orientation_policy"):
            object.__setattr__(
                self,
                name,
                _text(getattr(self, name), name=name).lower(),
            )


@dataclass(frozen=True)
class SatelliteFieldOfView:
    """One closed circular field in declared spherical coordinates."""

    field_id: str
    center_longitude_deg: float
    center_latitude_deg: float
    angular_radius_deg: float
    coordinate_spec: CoordinateSpec
    boundary: str = "closed"

    def __post_init__(self):
        object.__setattr__(self, "field_id", _text(self.field_id, name="field_id"))
        if not isinstance(self.coordinate_spec, CoordinateSpec):
            raise TypeError("coordinate_spec must be a CoordinateSpec.")
        for name in (
            "center_longitude_deg",
            "center_latitude_deg",
            "angular_radius_deg",
        ):
            object.__setattr__(
                self,
                name,
                _finite_float(getattr(self, name), name=name),
            )
        object.__setattr__(
            self,
            "center_longitude_deg",
            self.center_longitude_deg % 360.0,
        )
        if not -90.0 <= self.center_latitude_deg <= 90.0:
            raise ValueError("center_latitude_deg must be between -90 and 90.")
        if not 0.0 < self.angular_radius_deg <= 180.0:
            raise ValueError("angular_radius_deg must be in the interval (0, 180].")
        boundary = _text(self.boundary, name="boundary").lower()
        if boundary != "closed":
            raise ValueError("boundary must be 'closed'.")
        object.__setattr__(self, "boundary", boundary)


@dataclass(frozen=True)
class InclusiveTimeInterval:
    """One closed UTC query interval."""

    start: str
    stop: str
    time_scale: str = "utc"
    boundary: str = "inclusive"

    def __post_init__(self):
        start = _utc_instant(self.start, name="start")
        stop = _utc_instant(self.stop, name="stop")
        if _instant_datetime(stop) < _instant_datetime(start):
            raise ValueError("stop must not precede start.")
        object.__setattr__(self, "start", start)
        object.__setattr__(self, "stop", stop)
        time_scale = _text(self.time_scale, name="time_scale").lower()
        if time_scale != "utc":
            raise ValueError("time_scale must be 'utc'.")
        object.__setattr__(self, "time_scale", time_scale)
        boundary = _text(self.boundary, name="boundary").lower()
        if boundary != "inclusive":
            raise ValueError("boundary must be 'inclusive'.")
        object.__setattr__(self, "boundary", boundary)

    def contains(self, instant):
        """Return whether an instant lies in this inclusive interval."""
        instant = _utc_instant(instant, name="instant")
        value = _instant_datetime(instant)
        return (
            _instant_datetime(self.start)
            <= value
            <= _instant_datetime(self.stop)
        )


@dataclass(frozen=True)
class SatelliteCrossingCandidate:
    """One provider-neutral candidate awaiting or surviving exact refinement."""

    satellite: SatelliteIdentity
    observer: SatelliteObserver
    field_of_view: SatelliteFieldOfView
    interval: InclusiveTimeInterval
    source_provider: str
    orbit_solution_id: str | None = None
    snapshot_sha256: str | None = None
    element_epoch: str | None = None
    provenance: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        expected = (
            ("satellite", SatelliteIdentity),
            ("observer", SatelliteObserver),
            ("field_of_view", SatelliteFieldOfView),
            ("interval", InclusiveTimeInterval),
        )
        for name, type_ in expected:
            if not isinstance(getattr(self, name), type_):
                raise TypeError(f"{name} must be a {type_.__name__}.")
        object.__setattr__(
            self,
            "source_provider",
            _text(self.source_provider, name="source_provider"),
        )
        for name in ("orbit_solution_id", "element_epoch"):
            object.__setattr__(
                self,
                name,
                _optional_text(getattr(self, name), name=name),
            )
        if self.snapshot_sha256 is not None:
            digest = _text(self.snapshot_sha256, name="snapshot_sha256").lower()
            if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                raise ValueError(
                    "snapshot_sha256 must contain exactly 64 hexadecimal characters."
                )
            object.__setattr__(self, "snapshot_sha256", digest)
        if self.element_epoch is not None:
            object.__setattr__(
                self,
                "element_epoch",
                _utc_instant(self.element_epoch, name="element_epoch"),
            )
        object.__setattr__(
            self,
            "provenance",
            _string_tuple(self.provenance, name="provenance"),
        )
        object.__setattr__(
            self,
            "warnings",
            _string_tuple(self.warnings, name="warnings"),
        )


@dataclass(frozen=True)
class SatelliteCrossingResult:
    """One normalized connected visit through a closed spherical field."""

    candidate: SatelliteCrossingCandidate
    entry_instant: str
    exit_instant: str
    closest_approach_instant: str
    closest_approach_deg: float
    range_km: float | None = None
    angular_rate_deg_per_s: float | None = None
    illumination: str | None = None
    provider_event_id: str | None = None
    provenance: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if not isinstance(self.candidate, SatelliteCrossingCandidate):
            raise TypeError("candidate must be a SatelliteCrossingCandidate.")
        for name in (
            "entry_instant",
            "exit_instant",
            "closest_approach_instant",
        ):
            object.__setattr__(
                self,
                name,
                _utc_instant(getattr(self, name), name=name),
            )
        entry = _instant_datetime(self.entry_instant)
        closest = _instant_datetime(self.closest_approach_instant)
        exit_ = _instant_datetime(self.exit_instant)
        if not entry <= closest <= exit_:
            raise ValueError(
                "entry, closest approach, and exit instants must be ordered."
            )
        if not self.candidate.interval.contains(self.entry_instant) or not (
            self.candidate.interval.contains(self.exit_instant)
        ):
            raise ValueError("crossing instants must lie within the query interval.")
        separation = _finite_float(
            self.closest_approach_deg,
            name="closest_approach_deg",
        )
        if separation < 0.0:
            raise ValueError("closest_approach_deg must be non-negative.")
        if separation > self.candidate.field_of_view.angular_radius_deg:
            raise ValueError("closest approach must lie within the closed field.")
        object.__setattr__(self, "closest_approach_deg", separation)
        for name in ("range_km", "angular_rate_deg_per_s"):
            value = getattr(self, name)
            if value is None:
                continue
            value = _finite_float(value, name=name)
            if value < 0.0 or (name == "range_km" and value == 0.0):
                qualifier = "positive" if name == "range_km" else "non-negative"
                raise ValueError(f"{name} must be {qualifier}.")
            object.__setattr__(self, name, value)
        for name in ("illumination", "provider_event_id"):
            object.__setattr__(
                self,
                name,
                _optional_text(getattr(self, name), name=name),
            )
        object.__setattr__(
            self,
            "provenance",
            _string_tuple(self.provenance, name="provenance"),
        )
        object.__setattr__(
            self,
            "warnings",
            _string_tuple(self.warnings, name="warnings"),
        )

    @property
    def time_in_field_seconds(self):
        """Return elapsed time between entry and exit, including endpoints."""
        return (
            _instant_datetime(self.exit_instant)
            - _instant_datetime(self.entry_instant)
        ).total_seconds()
