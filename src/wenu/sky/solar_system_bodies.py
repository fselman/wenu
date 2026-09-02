"""Typed identities and capabilities for moving Solar-System bodies."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from types import MappingProxyType

from wenu.sky.solar_system_points import SolarSystemPointDescriptor


SYMBOLIC_POINT = "symbolic_point"
APPARENT_TRACK = "apparent_track"
SPHERICAL_PHYSICAL_APPEARANCE = "spherical_physical_appearance"
RESOLVED_SPHERICAL_DISK = "resolved_spherical_disk"
OBSERVED_DISK_SEQUENCE = "observed_disk_sequence"
FROZEN_EARTH_DISK_SEQUENCE = "frozen_earth_disk_sequence"


def _optional_text(value, *, name):
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be None or a non-empty string.")
    return value.strip()


@dataclass(frozen=True)
class SolarSystemBodyDescriptor(SolarSystemPointDescriptor):
    """Stable identity, relationships, physics, and display capabilities."""

    body_class: str = "solar_system_body"
    physical_body_id: str | None = None
    parent_body_key: str | None = None
    classifications: frozenset[str] = field(default_factory=frozenset)
    physical_radius_km: float | None = None
    radius_model: str | None = None
    capabilities: frozenset[str] = field(default_factory=frozenset)
    resolved_disk_chart_families: frozenset[str] | None = None
    observed_disk_sequence_chart_families: frozenset[str] | None = None
    localized_display_names: tuple[tuple[str, str], ...] = ()
    astronomical_symbol: str | None = None

    def __post_init__(self):
        super().__post_init__()
        for name in ("body_class",):
            value = _optional_text(getattr(self, name), name=name)
            object.__setattr__(self, name, value)
        for name in (
            "physical_body_id",
            "parent_body_key",
            "radius_model",
            "astronomical_symbol",
        ):
            object.__setattr__(
                self, name, _optional_text(getattr(self, name), name=name)
            )
        classifications = frozenset(
            _optional_text(value, name="classification")
            for value in self.classifications
        )
        capabilities = frozenset(
            _optional_text(value, name="capability")
            for value in self.capabilities
        )
        object.__setattr__(self, "classifications", classifications)
        object.__setattr__(self, "capabilities", capabilities)
        families = self.resolved_disk_chart_families
        if families is None:
            families = (
                frozenset(("regional", "binocular"))
                if RESOLVED_SPHERICAL_DISK in capabilities
                else frozenset()
            )
        else:
            families = frozenset(
                _optional_text(value, name="resolved disk chart family").lower()
                for value in families
            )
        allowed_families = frozenset({
            "regional", "binocular", "circumpolar", "planisphere", "all_sky",
        })
        unknown_families = families - allowed_families
        if unknown_families:
            raise ValueError(
                "unknown resolved disk chart families: "
                + ", ".join(sorted(unknown_families))
            )
        if families and RESOLVED_SPHERICAL_DISK not in capabilities:
            raise ValueError(
                "resolved_disk_chart_families requires resolved disk capability."
            )
        object.__setattr__(self, "resolved_disk_chart_families", families)
        sequence_families = self.observed_disk_sequence_chart_families
        if sequence_families is None:
            sequence_families = (
                frozenset(("regional", "binocular"))
                if OBSERVED_DISK_SEQUENCE in capabilities
                else frozenset()
            )
        else:
            sequence_families = frozenset(
                _optional_text(
                    value, name="observed disk sequence chart family"
                ).lower()
                for value in sequence_families
            )
        unknown_families = sequence_families - allowed_families
        if unknown_families:
            raise ValueError(
                "unknown observed disk sequence chart families: "
                + ", ".join(sorted(unknown_families))
            )
        if sequence_families and OBSERVED_DISK_SEQUENCE not in capabilities:
            raise ValueError(
                "observed_disk_sequence_chart_families requires observed "
                "disk sequence capability."
            )
        object.__setattr__(
            self,
            "observed_disk_sequence_chart_families",
            sequence_families,
        )
        localized = []
        languages = set()
        for language, display_name in self.localized_display_names:
            language = _optional_text(language, name="display language").lower()
            display_name = _optional_text(
                display_name, name="localized display name"
            )
            if language in languages:
                raise ValueError(
                    f"duplicate localized display language: {language!r}."
                )
            languages.add(language)
            localized.append((language, display_name))
        object.__setattr__(self, "localized_display_names", tuple(localized))
        radius = self.physical_radius_km
        if radius is not None:
            radius = float(radius)
            if not isfinite(radius) or radius <= 0.0:
                raise ValueError(
                    "physical_radius_km must be positive and finite."
                )
        if (radius is None) != (self.radius_model is None):
            raise ValueError(
                "physical_radius_km and radius_model must be supplied together."
            )
        object.__setattr__(self, "physical_radius_km", radius)

    def supports(self, capability):
        return capability in self.capabilities

    def supports_resolved_disk_in(self, family):
        return str(family).strip().lower() in self.resolved_disk_chart_families

    def supports_observed_disk_sequence_in(self, family):
        return (
            str(family).strip().lower()
            in self.observed_disk_sequence_chart_families
        )

    def display_name_for(self, language):
        """Return catalog-owned localized display text with stable fallback."""
        names = dict(self.localized_display_names)
        return names.get(str(language).strip().lower(), self.display_name)


class SolarSystemBodyCatalog:
    """Immutable lookup of independent bodies and their relationships."""

    def __init__(self, descriptors=()):
        values = {}
        for descriptor in descriptors:
            if not isinstance(descriptor, SolarSystemBodyDescriptor):
                raise TypeError(
                    "catalog entries must be SolarSystemBodyDescriptor values."
                )
            if descriptor.selection_key in values:
                raise ValueError(
                    f"duplicate body key: {descriptor.selection_key!r}."
                )
            values[descriptor.selection_key] = descriptor
        self._descriptors = MappingProxyType(values)

    def resolve(self, key):
        normalized = str(key).strip().lower()
        try:
            return self._descriptors[normalized]
        except KeyError as error:
            raise KeyError(f"unknown Solar-System body: {normalized!r}.") from error

    def children_of(self, key):
        parent = self.resolve(key).selection_key
        return tuple(
            descriptor for descriptor in self._descriptors.values()
            if descriptor.parent_body_key == parent
        )

    def supporting(self, capability):
        return tuple(
            descriptor for descriptor in self._descriptors.values()
            if descriptor.supports(capability)
        )

    def with_descriptors(self, *descriptors):
        return type(self)((*self._descriptors.values(), *descriptors))
