"""Shared visibility policy for start-inclusive temporal components."""

from __future__ import annotations

from dataclasses import dataclass


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
