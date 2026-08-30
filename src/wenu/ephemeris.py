"""Typed Cartesian ephemeris-state boundary."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from typing import Protocol, runtime_checkable


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


def _vector3(value, *, name):
    if isinstance(value, (str, bytes)):
        raise TypeError(f"{name} must be a three-component numeric value.")
    try:
        normalized = tuple(float(component) for component in value)
    except (TypeError, ValueError) as error:
        raise TypeError(
            f"{name} must be a three-component numeric value."
        ) from error
    if len(normalized) != 3:
        raise ValueError(f"{name} must contain exactly three components.")
    if not all(isfinite(component) for component in normalized):
        raise ValueError(f"{name} components must be finite.")
    return normalized


def _provenance(value):
    return tuple(_text(item, name="provenance entry") for item in value)


@dataclass(frozen=True)
class EphemerisResourceIdentity:
    """Immutable identity of one resolved ephemeris resource."""

    provider: str
    model: str
    filename: str
    sha256: str
    coverage_start: str
    coverage_end: str
    coverage_time_scale: str
    provenance: tuple[str, ...] = ()

    def __post_init__(self):
        for name in (
            "provider",
            "model",
            "filename",
            "coverage_start",
            "coverage_end",
        ):
            object.__setattr__(
                self,
                name,
                _text(getattr(self, name), name=name),
            )

        if not isinstance(self.sha256, str):
            raise TypeError("sha256 must be a string.")
        digest = self.sha256.strip().lower()
        if len(digest) != 64 or any(
            character not in "0123456789abcdef" for character in digest
        ):
            raise ValueError(
                "sha256 must contain exactly 64 hexadecimal characters."
            )
        object.__setattr__(self, "sha256", digest)
        object.__setattr__(
            self,
            "coverage_time_scale",
            _text(
                self.coverage_time_scale,
                name="coverage_time_scale",
            ).lower(),
        )
        object.__setattr__(self, "provenance", _provenance(self.provenance))


@dataclass(frozen=True)
class EphemerisStateRequest:
    """One geometric Cartesian state evaluation request."""

    target: str
    centre: str
    frame: str
    instant: str
    time_scale: str

    def __post_init__(self):
        for name in ("target", "centre", "instant"):
            object.__setattr__(
                self,
                name,
                _text(getattr(self, name), name=name),
            )
        object.__setattr__(
            self,
            "frame",
            _text(self.frame, name="frame").lower(),
        )
        object.__setattr__(
            self,
            "time_scale",
            _text(self.time_scale, name="time_scale").lower(),
        )


@dataclass(frozen=True)
class EphemerisState:
    """Complete geometric position-velocity state from one source."""

    request: EphemerisStateRequest
    position: tuple[float, float, float]
    velocity: tuple[float, float, float]
    position_unit: str
    velocity_unit: str
    resource: EphemerisResourceIdentity
    provider_target_id: str | None = None
    provider_centre_id: str | None = None
    provenance: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if not isinstance(self.request, EphemerisStateRequest):
            raise TypeError(
                "request must be an EphemerisStateRequest."
            )
        if not isinstance(self.resource, EphemerisResourceIdentity):
            raise TypeError(
                "resource must be an EphemerisResourceIdentity."
            )
        object.__setattr__(
            self,
            "position",
            _vector3(self.position, name="position"),
        )
        object.__setattr__(
            self,
            "velocity",
            _vector3(self.velocity, name="velocity"),
        )
        object.__setattr__(
            self,
            "position_unit",
            _text(self.position_unit, name="position_unit"),
        )
        object.__setattr__(
            self,
            "velocity_unit",
            _text(self.velocity_unit, name="velocity_unit"),
        )
        object.__setattr__(
            self,
            "provider_target_id",
            _optional_text(
                self.provider_target_id,
                name="provider_target_id",
            ),
        )
        object.__setattr__(
            self,
            "provider_centre_id",
            _optional_text(
                self.provider_centre_id,
                name="provider_centre_id",
            ),
        )
        object.__setattr__(self, "provenance", _provenance(self.provenance))


@runtime_checkable
class EphemerisStateSource(Protocol):
    """Evaluate native geometric Cartesian states without chart policy."""

    def state(self, request: EphemerisStateRequest) -> EphemerisState:
        """Return one complete state for the declared request."""
        ...
