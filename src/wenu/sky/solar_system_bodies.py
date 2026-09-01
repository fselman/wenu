"""Typed identities and capabilities for moving Solar-System bodies."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from types import MappingProxyType

from wenu.sky.solar_system_points import SolarSystemPointDescriptor


SYMBOLIC_POINT = "symbolic_point"
APPARENT_TRACK = "apparent_track"
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

    def __post_init__(self):
        super().__post_init__()
        for name in ("body_class",):
            value = _optional_text(getattr(self, name), name=name)
            object.__setattr__(self, name, value)
        for name in ("physical_body_id", "parent_body_key", "radius_model"):
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
