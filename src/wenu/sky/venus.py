"""Configured symbolic-point specialization for apparent Venus."""

from __future__ import annotations

from wenu.sky.solar_system_points import (
    SolarSystemPointDescriptor,
    SolarSystemPointLayer,
)


VENUS_POINT = SolarSystemPointDescriptor(
    target="venus",
    entity_key="venus",
    display_name="Venus",
    selection_key="venus",
)


class VenusLayer(SolarSystemPointLayer):
    """Realize apparent Venus through shared Solar-System orchestration."""

    layer_name = "venus"

    def __init__(self, **dependencies):
        super().__init__(VENUS_POINT, **dependencies)
