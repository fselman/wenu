"""Shared visibility policy for start-inclusive temporal components."""

from __future__ import annotations

from dataclasses import dataclass

from wenu.geometry.spherical import SphericalCurves, SphericalPoints


TEMPORAL_CADENCES = frozenset({"none", "start", "major"})


def _cadence(value, *, name):
    normalized = str(value).strip().lower()
    if normalized not in TEMPORAL_CADENCES:
        raise ValueError(f"{name} must be 'none', 'start', or 'major'.")
    return normalized


@dataclass(frozen=True)
class TemporalComponentPolicy:
    """Independent visibility choices over exact start-inclusive anchors."""

    path: bool = True
    ticks: bool = True
    symbols: str = "none"
    labels: str = "none"

    def __post_init__(self):
        object.__setattr__(self, "path", bool(self.path))
        object.__setattr__(self, "ticks", bool(self.ticks))
        object.__setattr__(
            self, "symbols", _cadence(self.symbols, name="symbols")
        )
        object.__setattr__(
            self, "labels", _cadence(self.labels, name="labels")
        )

    @staticmethod
    def indices(cadence, major_count):
        """Return selected indices without changing the scientific samples."""
        cadence = _cadence(cadence, name="cadence")
        if isinstance(major_count, bool) or not isinstance(major_count, int):
            raise TypeError("major_count must be an integer.")
        if major_count < 1:
            raise ValueError("major_count must be positive.")
        if cadence == "none":
            return ()
        if cadence == "start":
            return (0,)
        return tuple(range(major_count))

    def symbol_indices(self, major_count):
        return self.indices(self.symbols, major_count)

    def label_indices(self, major_count):
        return self.indices(self.labels, major_count)


def select_spherical_entities(geometry, indices):
    """Select already-realized entities without changing their coordinates."""
    if indices is None:
        return geometry
    indices = tuple(indices)
    positions = list(indices)
    common = {
        "coordinate_spec": geometry.coordinate_spec,
        "ids": None if geometry.ids is None else geometry.ids[positions],
        "labels": None if geometry.labels is None else geometry.labels[positions],
        "names": None if geometry.names is None else geometry.names[positions],
        "metadata": dict(geometry.metadata),
    }
    if isinstance(geometry, SphericalPoints):
        return SphericalPoints(
            geometry.lon_deg[positions], geometry.lat_deg[positions], **common
        )
    closed = (
        {"closed": geometry.closed[positions]}
        if isinstance(geometry, SphericalCurves) else {}
    )
    return type(geometry)(
        tuple(geometry.lon_deg[index] for index in indices),
        tuple(geometry.lat_deg[index] for index in indices),
        **common,
        **closed,
    )
