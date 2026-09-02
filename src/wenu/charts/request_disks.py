"""Resolved Solar-System disk request and dynamic layer installation."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from wenu.sky.solar_system_bodies import (
    FROZEN_EARTH_DISK_SEQUENCE,
    OBSERVED_DISK_SEQUENCE,
    RESOLVED_SPHERICAL_DISK,
    SolarSystemBodyDescriptor,
)
from wenu.sky.solar_system_catalog import SOLAR_SYSTEM_BODY_CATALOG
from wenu.sky.venus_disk import solar_system_disk_layers
from wenu.sky.solar_system_disk_sequences import (
    ObservedSolarSystemDiskSequenceRequest,
)
from wenu.sky.venus_disk_sequence import (
    observed_solar_system_disk_sequence_layers,
)
from wenu.sky.frozen_earth_disk_sequences import FrozenEarthDiskSequenceRequest
from wenu.sky.frozen_earth_venus_disk_sequence import (
    frozen_earth_solar_system_disk_sequence_layers,
)


@dataclass(frozen=True)
class SolarSystemDiskDisplayRequest:
    """One descriptor-driven opt-in resolved disk display."""

    descriptor: SolarSystemBodyDescriptor | str
    magnification: float = 1.0

    def __post_init__(self):
        descriptor = self.descriptor
        if not isinstance(descriptor, SolarSystemBodyDescriptor):
            try:
                descriptor = SOLAR_SYSTEM_BODY_CATALOG.resolve(descriptor)
            except KeyError as error:
                raise ValueError(str(error)) from error
        if not descriptor.supports(RESOLVED_SPHERICAL_DISK):
            raise ValueError(
                f"{descriptor.display_name} does not support resolved disks."
            )
        magnification = float(self.magnification)
        if not isfinite(magnification) or not 1.0 <= magnification <= 1000.0:
            raise ValueError(
                "disk magnification must be finite and between 1 and 1000."
            )
        object.__setattr__(self, "descriptor", descriptor)
        object.__setattr__(self, "magnification", magnification)

    @property
    def target(self):
        return self.descriptor.target


@dataclass(frozen=True)
class ObservedSolarSystemDiskSequenceDisplayRequest:
    """Drawable observed major-step disk sequence."""

    sequence: ObservedSolarSystemDiskSequenceRequest
    magnification: float = 1.0
    label_dates: bool = False

    def __post_init__(self):
        if not isinstance(self.sequence, ObservedSolarSystemDiskSequenceRequest):
            raise TypeError(
                "sequence must be an ObservedSolarSystemDiskSequenceRequest."
            )
        descriptor = self.sequence.descriptor
        if (
            isinstance(descriptor, SolarSystemBodyDescriptor)
            and not descriptor.supports(OBSERVED_DISK_SEQUENCE)
        ):
            raise ValueError(
                f"{descriptor.display_name} does not support observed "
                "disk sequences."
            )
        magnification = float(self.magnification)
        if not isfinite(magnification) or not 1.0 <= magnification <= 1000.0:
            raise ValueError(
                "disk magnification must be finite and between 1 and 1000."
            )
        object.__setattr__(self, "magnification", magnification)
        object.__setattr__(self, "label_dates", bool(self.label_dates))

    @property
    def target(self):
        return self.sequence.descriptor.target

    @property
    def model(self):
        return "observed"

    def supports_chart_family(self, family):
        return self.sequence.descriptor.supports_observed_disk_sequence_in(
            family
        )


@dataclass(frozen=True)
class FrozenEarthSolarSystemDiskSequenceDisplayRequest:
    """Drawable frozen-Earth sequence in fixed J2000 ecliptic axes."""

    sequence: FrozenEarthDiskSequenceRequest
    magnification: float = 1.0
    label_dates: bool = False

    def __post_init__(self):
        if not isinstance(self.sequence, FrozenEarthDiskSequenceRequest):
            raise TypeError(
                "sequence must be a FrozenEarthDiskSequenceRequest."
            )
        descriptor = self.sequence.descriptor
        if (
            isinstance(descriptor, SolarSystemBodyDescriptor)
            and not descriptor.supports(FROZEN_EARTH_DISK_SEQUENCE)
        ):
            raise ValueError(
                f"{descriptor.display_name} does not support frozen-Earth "
                "disk sequences."
            )
        magnification = float(self.magnification)
        if not isfinite(magnification) or not 1.0 <= magnification <= 1000.0:
            raise ValueError(
                "disk magnification must be finite and between 1 and 1000."
            )
        object.__setattr__(self, "magnification", magnification)
        object.__setattr__(self, "label_dates", bool(self.label_dates))

    @property
    def target(self):
        return self.sequence.descriptor.target

    @property
    def model(self):
        return "frozen-earth-ecliptic"

    def supports_chart_family(self, family):
        return str(family).strip().lower() == "regional"


def configure_chart_request_disks(sky, request):
    """Replace request-owned disk layers with the current request selection."""
    for layer in tuple(sky.layers):
        name = getattr(layer, "layer_name", "")
        if (
            getattr(layer, "display_kind", None) in {
                "resolved_disk",
                "observed_disk_sequence",
                "frozen_earth_disk_sequence",
            }
            or name == "frozen_earth_sun"
        ):
            sky.remove(layer)
            if name:
                setattr(sky, name, None)

    for name in (
        "venus_disk_illuminated",
        "venus_disk_limb",
        "venus_disk_terminator",
        "venus_disk_sequence_illuminated",
        "venus_disk_sequence_limb",
        "venus_disk_sequence_terminator",
        "venus_disk_sequence_labels",
        "venus_disk_sequence_frozen_illuminated",
        "venus_disk_sequence_frozen_limb",
        "venus_disk_sequence_frozen_terminator",
        "venus_disk_sequence_frozen_labels",
        "frozen_earth_sun",
    ):
        setattr(sky, name, None)

    for disk in request.solar_system_disks:
        layers = solar_system_disk_layers(
            disk.descriptor,
            magnification=disk.magnification,
        )
        for layer in layers:
            setattr(sky, layer.layer_name, layer)
            sky.add(layer)

    sequence = getattr(request, "solar_system_disk_sequence", None)
    if sequence is not None:
        factory = (
            frozen_earth_solar_system_disk_sequence_layers
            if isinstance(
                sequence,
                FrozenEarthSolarSystemDiskSequenceDisplayRequest,
            )
            else observed_solar_system_disk_sequence_layers
        )
        layers = factory(
            sequence.sequence,
            magnification=sequence.magnification,
            label_dates=sequence.label_dates,
        )
        for layer in layers:
            setattr(sky, layer.layer_name, layer)
            sky.add(layer)
