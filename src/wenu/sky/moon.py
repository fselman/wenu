"""Configured symbolic-point specialization for the apparent Moon."""

from __future__ import annotations

from wenu.sky.solar_system_points import (
    SolarSystemPointDescriptor,
    SolarSystemPointLayer,
)


MOON_POINT = SolarSystemPointDescriptor(
    target="moon",
    entity_key="moon",
    display_name="Moon",
    selection_key="moon",
)


class MoonLayer(SolarSystemPointLayer):
    """Realize the apparent Moon through shared Solar-System orchestration."""

    layer_name = "moon"

    def __init__(self, **dependencies):
        super().__init__(MOON_POINT, **dependencies)
