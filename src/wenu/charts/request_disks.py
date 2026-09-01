"""Resolved Solar-System disk request and dynamic layer installation."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from wenu.sky.venus_disk import venus_disk_layers
from wenu.sky.solar_system_disk_sequences import (
    ObservedSolarSystemDiskSequenceRequest,
)
from wenu.sky.venus_disk_sequence import observed_venus_disk_sequence_layers


SUPPORTED_RESOLVED_DISKS = frozenset({"venus"})


@dataclass(frozen=True)
class SolarSystemDiskDisplayRequest:
    """One object-specific opt-in resolved disk display."""

    target: str
    magnification: float = 1.0

    def __post_init__(self):
        target = str(self.target).strip().lower()
        if target not in SUPPORTED_RESOLVED_DISKS:
            raise ValueError("resolved disks currently support only venus.")
        magnification = float(self.magnification)
        if not isfinite(magnification) or not 1.0 <= magnification <= 1000.0:
            raise ValueError(
                "disk magnification must be finite and between 1 and 1000."
            )
        object.__setattr__(self, "target", target)
        object.__setattr__(self, "magnification", magnification)


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
        if self.sequence.descriptor.target != "venus":
            raise ValueError(
                "drawable observed sequences currently support only venus."
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


def configure_chart_request_disks(sky, request):
    """Replace request-owned disk layers with the current request selection."""
    for layer in tuple(sky.layers):
        if getattr(layer, "layer_name", "").startswith("venus_disk_"):
            sky.remove(layer)

    for name in (
        "venus_disk_illuminated",
        "venus_disk_limb",
        "venus_disk_terminator",
        "venus_disk_sequence_illuminated",
        "venus_disk_sequence_limb",
        "venus_disk_sequence_terminator",
        "venus_disk_sequence_labels",
    ):
        setattr(sky, name, None)

    for disk in request.solar_system_disks:
        if disk.target != "venus":
            raise ValueError(f"unsupported resolved disk: {disk.target!r}.")
        layers = venus_disk_layers(magnification=disk.magnification)
        for layer in layers:
            setattr(sky, layer.layer_name, layer)
            sky.add(layer)

    sequence = getattr(request, "solar_system_disk_sequence", None)
    if sequence is not None:
        layers = observed_venus_disk_sequence_layers(
            sequence.sequence,
            magnification=sequence.magnification,
            label_dates=sequence.label_dates,
        )
        for layer in layers:
            setattr(sky, layer.layer_name, layer)
            sky.add(layer)
