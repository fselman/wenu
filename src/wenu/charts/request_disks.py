"""Resolved Solar-System disk request and dynamic layer installation."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from wenu.sky.venus_disk import venus_disk_layers


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


def configure_chart_request_disks(sky, request):
    """Replace request-owned disk layers with the current request selection."""
    for layer in tuple(sky.layers):
        if getattr(layer, "layer_name", "").startswith("venus_disk_"):
            sky.remove(layer)

    for name in (
        "venus_disk_illuminated",
        "venus_disk_limb",
        "venus_disk_terminator",
    ):
        setattr(sky, name, None)

    for disk in request.solar_system_disks:
        if disk.target != "venus":
            raise ValueError(f"unsupported resolved disk: {disk.target!r}.")
        layers = venus_disk_layers(magnification=disk.magnification)
        for layer in layers:
            setattr(sky, layer.layer_name, layer)
            sky.add(layer)
