"""Immutable user-facing chart-request contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from pathlib import Path

from .detail import DetailOverrides, SkyContentSelection
from .furniture import ChartFurnitureOptions
from .product_options import ChartProductOptions


CHART_FAMILIES = frozenset(
    {"planisphere", "regional", "circumpolar", "binocular"}
)
CHART_LANGUAGES = frozenset({"en", "es"})
EXCLUDABLE_CATALOGUE_FAMILIES = (
    "nonstellar_objects",
    "galaxies",
    "open_clusters",
    "globular_clusters",
    "planetary_nebulae",
    "supernova_remnants",
)


def _optional_text(value, *, field_name):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} cannot be empty.")
    return text


def _identifier_set(values, *, field_name):
    if values is None:
        return frozenset()
    normalized = frozenset(str(value).strip() for value in values)
    if "" in normalized:
        raise ValueError(f"{field_name} cannot contain an empty identifier.")
    return normalized


@dataclass(frozen=True)
class ChartContentExclusions:
    """Catalogue identifiers explicitly omitted from one chart request."""

    nonstellar_objects: frozenset[str] = frozenset()
    galaxies: frozenset[str] = frozenset()
    open_clusters: frozenset[str] = frozenset()
    globular_clusters: frozenset[str] = frozenset()
    planetary_nebulae: frozenset[str] = frozenset()
    supernova_remnants: frozenset[str] = frozenset()

    def __post_init__(self):
        for name in EXCLUDABLE_CATALOGUE_FAMILIES:
            object.__setattr__(
                self,
                name,
                _identifier_set(getattr(self, name), field_name=name),
            )


@dataclass(frozen=True)
class ChartObserverRequest:
    """Location and instant that scientifically define an observation."""

    time: str | datetime
    location: str | None = None
    lat_deg: float | None = None
    lon_deg: float | None = None
    elevation_m: float | None = None
    timezone_name: str | None = None

    def __post_init__(self):
        location = _optional_text(self.location, field_name="location")
        timezone_name = _optional_text(
            self.timezone_name,
            field_name="timezone_name",
        )
        if location is not None:
            if any(
                value is not None
                for value in (
                    self.lat_deg,
                    self.lon_deg,
                    self.elevation_m,
                    timezone_name,
                )
            ):
                raise ValueError(
                    "Specify either a named location or explicit observer "
                    "coordinates, not both."
                )
        elif self.lat_deg is None or self.lon_deg is None:
            raise ValueError(
                "An observer requires a named location or latitude and "
                "longitude."
            )
        else:
            latitude = float(self.lat_deg)
            longitude = float(self.lon_deg)
            elevation = float(self.elevation_m or 0.0)
            if not all(isfinite(value) for value in (
                latitude, longitude, elevation
            )):
                raise ValueError("Observer coordinates must be finite.")
            if not -90.0 <= latitude <= 90.0:
                raise ValueError("lat_deg must be between -90 and 90.")
            if not -180.0 <= longitude <= 180.0:
                raise ValueError("lon_deg must be between -180 and 180.")
            object.__setattr__(self, "lat_deg", latitude)
            object.__setattr__(self, "lon_deg", longitude)
            object.__setattr__(self, "elevation_m", elevation)
        if isinstance(self.time, str) and not self.time.strip():
            raise ValueError("time cannot be empty.")
        if not isinstance(self.time, (str, datetime)):
            raise TypeError("time must be an ISO string or datetime.")
        object.__setattr__(self, "location", location)
        object.__setattr__(self, "timezone_name", timezone_name)

    def observer_kwargs(self):
        """Return constructor arguments for the established Observer API."""
        return {
            "time": self.time,
            "location": self.location,
            "lat_deg": self.lat_deg,
            "lon_deg": self.lon_deg,
            "elevation_m": self.elevation_m,
            "timezone_name": self.timezone_name,
        }

    def scientific_identity(self):
        """Return the normalized location and UTC instant of this request."""
        from wenu.observer import Observer

        return Observer.resolve_scientific_identity(
            **self.observer_kwargs()
        )

    def matches(self, observer):
        """Return whether an existing observer realizes this request."""
        latitude, longitude, elevation, instant = self.scientific_identity()
        return (
            getattr(observer, "lat_deg", None) == latitude
            and getattr(observer, "lon_deg", None) == longitude
            and getattr(observer, "elevation_m", None) == elevation
            and getattr(observer, "utc_datetime", None) == instant
        )


@dataclass(frozen=True)
class ChartSubjectRequest:
    """One named, coordinate, constellation, or group chart subject."""

    target: str | None = None
    ra_deg: float | None = None
    dec_deg: float | None = None
    constellations: tuple[str, ...] | None = None
    group: str | None = None
    display_name: str | None = None

    def __post_init__(self):
        target = _optional_text(self.target, field_name="target")
        group = _optional_text(self.group, field_name="group")
        display_name = _optional_text(
            self.display_name,
            field_name="display_name",
        )
        coordinate_supplied = self.ra_deg is not None or self.dec_deg is not None
        if coordinate_supplied and (
            self.ra_deg is None or self.dec_deg is None
        ):
            raise ValueError("ra_deg and dec_deg must be supplied together.")
        coordinates = None
        if coordinate_supplied:
            right_ascension = float(self.ra_deg)
            declination = float(self.dec_deg)
            if not isfinite(right_ascension) or not isfinite(declination):
                raise ValueError("Target coordinates must be finite.")
            if not -90.0 <= declination <= 90.0:
                raise ValueError("dec_deg must be between -90 and 90.")
            coordinates = (right_ascension % 360.0, declination)
        constellations = None
        if self.constellations is not None:
            constellations = tuple(
                str(value).strip().upper()
                for value in self.constellations
            )
            if not constellations or any(not value for value in constellations):
                raise ValueError("constellations must contain IAU names.")
            if len(set(constellations)) != len(constellations):
                raise ValueError("constellations must be unique.")
        forms = sum(
            value is not None
            for value in (target, coordinates, constellations, group)
        )
        if forms > 1:
            raise ValueError("A chart request accepts only one subject form.")
        object.__setattr__(self, "target", target)
        object.__setattr__(self, "group", group)
        object.__setattr__(self, "display_name", display_name)
        object.__setattr__(self, "constellations", constellations)
        if coordinates is not None:
            object.__setattr__(self, "ra_deg", coordinates[0])
            object.__setattr__(self, "dec_deg", coordinates[1])

    @property
    def is_empty(self):
        return all(
            value is None
            for value in (
                self.target,
                self.ra_deg,
                self.constellations,
                self.group,
            )
        )


@dataclass(frozen=True)
class ChartFrameRequest:
    """Optional explicit overrides for otherwise automatic chart framing."""

    field_diameter_deg: float | None = None
    field_width_deg: float | None = None
    field_height_deg: float | None = None
    position_angle_deg: float = 0.0
    pole: str = "south"
    limiting_declination_deg: float | None = None

    def __post_init__(self):
        width_pair = (
            self.field_width_deg is not None,
            self.field_height_deg is not None,
        )
        if width_pair[0] != width_pair[1]:
            raise ValueError(
                "field_width_deg and field_height_deg must be supplied "
                "together."
            )
        if self.field_diameter_deg is not None and any(width_pair):
            raise ValueError(
                "Specify either field diameter or width and height."
            )
        for name in (
            "field_diameter_deg",
            "field_width_deg",
            "field_height_deg",
        ):
            value = getattr(self, name)
            if value is None:
                continue
            value = float(value)
            upper = 180.0 if name == "field_diameter_deg" else 360.0
            if not isfinite(value) or not 0.0 < value < upper:
                raise ValueError(
                    f"{name} must be between 0 and {upper:g}."
                )
            object.__setattr__(self, name, value)
        angle = float(self.position_angle_deg)
        if not isfinite(angle):
            raise ValueError("position_angle_deg must be finite.")
        pole = str(self.pole).strip().lower()
        if pole not in {"north", "south"}:
            raise ValueError("pole must be 'north' or 'south'.")
        limit = self.limiting_declination_deg
        if limit is not None:
            limit = float(limit)
            if not isfinite(limit) or not -90.0 < limit < 90.0:
                raise ValueError(
                    "limiting_declination_deg must be between -90 and 90."
                )
            if (pole == "south" and limit >= 0.0) or (
                pole == "north" and limit <= 0.0
            ):
                raise ValueError(
                    "limiting_declination_deg must agree with pole."
                )
        object.__setattr__(self, "position_angle_deg", angle)
        object.__setattr__(self, "pole", pole)
        object.__setattr__(self, "limiting_declination_deg", limit)


@dataclass(frozen=True)
class ChartRequest:
    """Complete immutable request shared by Python and future CLI adapters."""

    observer: ChartObserverRequest
    family: str
    product: ChartProductOptions
    subject: ChartSubjectRequest = ChartSubjectRequest()
    frame: ChartFrameRequest = ChartFrameRequest()
    mask: bool = False
    content: SkyContentSelection = SkyContentSelection()
    exclusions: ChartContentExclusions = ChartContentExclusions()
    detail: DetailOverrides = DetailOverrides()
    furniture: ChartFurnitureOptions = ChartFurnitureOptions()
    language: str = "en"
    title: str | None = None

    def __post_init__(self):
        family = str(self.family).strip().lower()
        if family not in CHART_FAMILIES:
            raise ValueError(
                "family must be planisphere, regional, circumpolar, or "
                "binocular."
            )
        expected = (
            ("observer", self.observer, ChartObserverRequest),
            ("product", self.product, ChartProductOptions),
            ("subject", self.subject, ChartSubjectRequest),
            ("frame", self.frame, ChartFrameRequest),
            ("content", self.content, SkyContentSelection),
            ("exclusions", self.exclusions, ChartContentExclusions),
            ("detail", self.detail, DetailOverrides),
            ("furniture", self.furniture, ChartFurnitureOptions),
        )
        for name, value, kind in expected:
            if not isinstance(value, kind):
                raise TypeError(f"{name} must be a {kind.__name__} value.")
        if family == "binocular" and (
            self.subject.target is None and self.subject.ra_deg is None
        ):
            raise ValueError(
                "A binocular request requires a target or coordinates."
            )
        if family == "regional" and self.subject.is_empty:
            raise ValueError("A regional request requires a subject.")
        if family == "circumpolar" and self.frame.limiting_declination_deg is None:
            raise ValueError(
                "A circumpolar request requires limiting_declination_deg."
            )
        if family == "circumpolar" and not self.subject.is_empty:
            raise ValueError("A circumpolar request does not take a subject.")
        if family == "planisphere" and not self.subject.is_empty:
            allowed_mask = self.mask and (
                self.subject.constellations is not None
                or self.subject.group is not None
            )
            if not allowed_mask:
                raise ValueError(
                    "A planisphere subject is allowed only as a mask."
                )
        language = str(self.language).strip().lower()
        if language not in CHART_LANGUAGES:
            raise ValueError("language must be 'en' or 'es'.")
        if self.detail.content_selection is not None:
            raise ValueError(
                "Specify chart content through ChartRequest.content, not "
                "DetailOverrides.content_selection."
            )
        object.__setattr__(self, "family", family)
        object.__setattr__(self, "mask", bool(self.mask))
        object.__setattr__(self, "language", language)
        object.__setattr__(
            self,
            "title",
            _optional_text(self.title, field_name="title"),
        )
