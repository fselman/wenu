"""Observer-local altitude-zero reference geometry."""

from __future__ import annotations

from wenu.sky.coordinate_grids import AltAzGrid
from wenu.sky.geometrical_object import GeometricalObject


class HorizonReference(GeometricalObject):
    """The observer horizon as one semantic spherical reference curve."""

    layer_name = "horizon"

    def __init__(self, observer=None, *, samples=721):
        if int(samples) < 4:
            raise ValueError("samples must be at least 4.")
        self.observer = observer
        self.samples = int(samples)

    def spherical_geometry(self, observer):
        """Return the closed altitude-zero curve for ``observer``."""
        resolved = self.observer if observer is None else observer
        if resolved is None:
            raise RuntimeError(
                "An Observer is required for horizon geometry."
            )
        geometry = AltAzGrid(
            resolved,
            samples=self.samples,
        ).horizon()
        geometry.metadata["reference"] = "horizon"
        return geometry
