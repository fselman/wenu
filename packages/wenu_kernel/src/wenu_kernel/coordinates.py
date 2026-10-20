"""Pure shared coordinate vocabulary; no source or observer defaults."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


def _identifier(value, *, name):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string.")
    normalized = value.strip().lower()
    if not normalized:
        raise ValueError(f"{name} must be non-empty.")
    return normalized


def _text(value, *, name):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{name} must be non-empty.")
    return normalized


def _optional_text(value, *, name):
    if value is None:
        return None
    return _text(value, name=name)


class PositionStatus(str, Enum):
    """Scientific status of one represented astronomical position."""

    GEOMETRIC = "geometric"
    ASTROMETRIC = "astrometric"
    APPARENT = "apparent"
    OBSERVED = "observed"


@dataclass(frozen=True)
class CoordinateSpec:
    """Immutable scientific identity of spherical astronomical coordinates."""

    frame: str
    origin: str
    position_status: PositionStatus = PositionStatus.GEOMETRIC
    epoch: str | None = None
    equinox: str | None = None
    instant: str | None = None
    time_scale: str | None = None
    longitude_unit: str = "deg"
    latitude_unit: str = "deg"
    representation: str = "spherical"
    provider: str | None = None
    model: str | None = None
    provenance: tuple[str, ...] = ()
    corrections: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self):
        object.__setattr__(
            self,
            "frame",
            _identifier(self.frame, name="frame"),
        )
        object.__setattr__(
            self,
            "origin",
            _identifier(self.origin, name="origin"),
        )
        try:
            status = PositionStatus(self.position_status)
        except ValueError as error:
            raise ValueError(
                f"Unsupported position status: {self.position_status!r}."
            ) from error
        object.__setattr__(self, "position_status", status)

        for name in ("epoch", "equinox", "instant", "provider", "model"):
            object.__setattr__(
                self,
                name,
                _optional_text(getattr(self, name), name=name),
            )

        time_scale = (
            None
            if self.time_scale is None
            else _identifier(self.time_scale, name="time_scale")
        )
        if (self.instant is None) != (time_scale is None):
            raise ValueError(
                "instant and time_scale must be supplied together."
            )
        object.__setattr__(self, "time_scale", time_scale)

        for name in (
            "longitude_unit",
            "latitude_unit",
            "representation",
        ):
            object.__setattr__(
                self,
                name,
                _identifier(getattr(self, name), name=name),
            )

        provenance = tuple(
            _text(value, name="provenance entry")
            for value in self.provenance
        )
        object.__setattr__(self, "provenance", provenance)

        corrections = frozenset(
            _identifier(value, name="correction")
            for value in self.corrections
        )
        object.__setattr__(self, "corrections", corrections)


GENERIC_SPHERICAL_SPEC = CoordinateSpec(
    frame="generic-spherical",
    origin="unit-sphere",
    provider="wenu synthetic geometry",
)


