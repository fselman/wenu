"""Observer-relative Solar-System direction realization."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import asin, atan2, degrees, isfinite, sqrt

import numpy as np
from astropy import units as u
from astropy.constants import c
from astropy.time import Time, TimeDelta

from wenu.coordinates import CoordinateSpec, PositionStatus
from wenu.ephemeris import (
    EphemerisResourceIdentity,
    EphemerisStateRequest,
    EphemerisStateSource,
)
from wenu.geometry.spherical import SphericalPoints

LIGHT_SPEED_AU_PER_DAY = c.to_value(u.au / u.day)


class AstrometricDirectionError(ValueError):
    """Base error for deterministic astrometric-realization failures."""


class AstrometricDirectionConvergenceError(AstrometricDirectionError):
    """The one-way light-time iteration did not converge."""


class AstrometricDirectionIdentityError(AstrometricDirectionError):
    """Provider state identity does not match the realization request."""


def _isot(value):
    precise = value.copy()
    precise.precision = 9
    return precise.isot


def _text(value, *, name):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{name} must be non-empty.")
    return normalized


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


@dataclass(frozen=True)
class ObserverBarycentricState:
    """One terrestrial observer state at the reception instant."""

    observer_id: str
    centre: str
    frame: str
    instant: str
    time_scale: str
    position: tuple[float, float, float]
    velocity: tuple[float, float, float]
    position_unit: str
    velocity_unit: str
    resource: EphemerisResourceIdentity
    provider_observer_id: str | None = None
    provider_centre_id: str | None = None
    provenance: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        for name in ("observer_id", "centre", "instant"):
            object.__setattr__(
                self, name, _text(getattr(self, name), name=name)
            )
        for name in ("frame", "time_scale", "position_unit", "velocity_unit"):
            object.__setattr__(
                self,
                name,
                _text(getattr(self, name), name=name).lower(),
            )
        object.__setattr__(
            self, "position", _vector3(self.position, name="position")
        )
        object.__setattr__(
            self, "velocity", _vector3(self.velocity, name="velocity")
        )
        if not isinstance(self.resource, EphemerisResourceIdentity):
            raise TypeError("resource must be an EphemerisResourceIdentity.")
        for name in ("provider_observer_id", "provider_centre_id"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _text(value, name=name))
        object.__setattr__(
            self,
            "provenance",
            tuple(
                _text(value, name="provenance entry")
                for value in self.provenance
            ),
        )


@dataclass(frozen=True)
class AstrometricDirectionRequest:
    """One observer-relative astrometric direction request."""

    target: str
    centre: str
    reception_instant: str
    reception_time_scale: str
    light_time_tolerance_days: float = 1.0e-12
    maximum_iterations: int = 10

    def __post_init__(self):
        for name in ("target", "centre", "reception_instant"):
            object.__setattr__(
                self, name, _text(getattr(self, name), name=name)
            )
        object.__setattr__(
            self,
            "reception_time_scale",
            _text(
                self.reception_time_scale,
                name="reception_time_scale",
            ).lower(),
        )
        tolerance = float(self.light_time_tolerance_days)
        if not isfinite(tolerance) or tolerance <= 0.0:
            raise ValueError(
                "light_time_tolerance_days must be positive and finite."
            )
        object.__setattr__(self, "light_time_tolerance_days", tolerance)
        if isinstance(self.maximum_iterations, bool) or not isinstance(
            self.maximum_iterations, int
        ):
            raise TypeError("maximum_iterations must be an integer.")
        if self.maximum_iterations < 1:
            raise ValueError("maximum_iterations must be positive.")


@dataclass(frozen=True)
class AstrometricDirection:
    """One realized direction plus retained distance and timing evidence."""

    request: AstrometricDirectionRequest
    observer_state: ObserverBarycentricState
    geometry: SphericalPoints
    distance_au: float
    relative_velocity_au_per_day: tuple[float, float, float]
    light_time_days: float
    emission_instant: str
    emission_time_scale: str
    iterations: int
    target_provider_id: str | None
    provenance: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if not isinstance(self.request, AstrometricDirectionRequest):
            raise TypeError("request must be an AstrometricDirectionRequest.")
        if not isinstance(self.observer_state, ObserverBarycentricState):
            raise TypeError(
                "observer_state must be an ObserverBarycentricState."
            )
        if not isinstance(self.geometry, SphericalPoints):
            raise TypeError("geometry must be a SphericalPoints.")
        for name in ("distance_au", "light_time_days"):
            value = float(getattr(self, name))
            if not isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be positive and finite.")
            object.__setattr__(self, name, value)
        object.__setattr__(
            self,
            "relative_velocity_au_per_day",
            _vector3(
                self.relative_velocity_au_per_day,
                name="relative_velocity_au_per_day",
            ),
        )
        object.__setattr__(
            self,
            "emission_instant",
            _text(self.emission_instant, name="emission_instant"),
        )
        object.__setattr__(
            self,
            "emission_time_scale",
            _text(
                self.emission_time_scale,
                name="emission_time_scale",
            ).lower(),
        )
        if isinstance(self.iterations, bool) or not isinstance(
            self.iterations,
            int,
        ):
            raise TypeError("iterations must be an integer.")
        if self.iterations < 1:
            raise ValueError("iterations must be positive.")
        if self.target_provider_id is not None:
            object.__setattr__(
                self,
                "target_provider_id",
                _text(self.target_provider_id, name="target_provider_id"),
            )
        object.__setattr__(
            self,
            "provenance",
            tuple(
                _text(value, name="provenance entry")
                for value in self.provenance
            ),
        )


class AstrometricDirectionRealizer:
    """Iterate one-way light time from typed provider and observer states."""

    def direction(
        self,
        source: EphemerisStateSource,
        request: AstrometricDirectionRequest,
        observer_state: ObserverBarycentricState,
    ) -> AstrometricDirection:
        if not isinstance(source, EphemerisStateSource):
            raise TypeError("source must satisfy EphemerisStateSource.")
        if not isinstance(request, AstrometricDirectionRequest):
            raise TypeError("request must be an AstrometricDirectionRequest.")
        if not isinstance(observer_state, ObserverBarycentricState):
            raise TypeError(
                "observer_state must be an ObserverBarycentricState."
            )
        if observer_state.centre != request.centre:
            raise AstrometricDirectionIdentityError(
                "observer-state centre does not match the direction request."
            )
        if observer_state.frame != "icrf":
            raise AstrometricDirectionIdentityError(
                "observer state must use frame='icrf'."
            )
        if observer_state.position_unit != "au":
            raise AstrometricDirectionIdentityError(
                "observer position must use AU."
            )
        if observer_state.velocity_unit != "au/day":
            raise AstrometricDirectionIdentityError(
                "observer velocity must use AU/day."
            )

        reception = Time(
            request.reception_instant,
            scale=request.reception_time_scale,
        )
        observer_instant = Time(
            observer_state.instant,
            scale=observer_state.time_scale,
        )
        observer_offset_days = float(
            (observer_instant - reception).to_value("day")
        )
        if abs(observer_offset_days) > 1.0e-12:
            raise AstrometricDirectionIdentityError(
                "observer state must be evaluated at the reception instant."
            )

        light_time_days = 0.0
        target_state = None
        vector = None
        emission = reception
        for iteration in range(1, request.maximum_iterations + 1):
            emission = reception - TimeDelta(light_time_days, format="jd")
            state_request = EphemerisStateRequest(
                target=request.target,
                centre=request.centre,
                frame="icrf",
                instant=_isot(emission),
                time_scale=emission.scale,
            )
            target_state = source.state(state_request)
            self._validate_target_state(
                target_state,
                state_request,
                observer_state,
            )
            vector = tuple(
                target - observer
                for target, observer in zip(
                    target_state.position,
                    observer_state.position,
                )
            )
            distance_au = sqrt(
                sum(component * component for component in vector)
            )
            if not isfinite(distance_au) or distance_au <= 0.0:
                raise AstrometricDirectionError(
                    "observer-to-target distance must be positive and finite."
                )
            updated_light_time = distance_au / LIGHT_SPEED_AU_PER_DAY
            if abs(updated_light_time - light_time_days) <= (
                request.light_time_tolerance_days
            ):
                light_time_days = updated_light_time
                break
            light_time_days = updated_light_time
        else:
            raise AstrometricDirectionConvergenceError(
                "one-way light-time iteration did not converge within "
                f"{request.maximum_iterations} iterations."
            )

        x, y, z = vector
        longitude = degrees(atan2(y, x)) % 360.0
        latitude = degrees(asin(z / distance_au))
        resource = target_state.resource
        coordinate_spec = CoordinateSpec(
            frame="icrs",
            origin="observer",
            position_status=PositionStatus.ASTROMETRIC,
            instant=_isot(reception),
            time_scale=reception.scale,
            provider=resource.provider,
            model=resource.model,
            provenance=(
                f"ephemeris file: {resource.filename}",
                f"ephemeris sha256: {resource.sha256}",
                f"observer: {observer_state.observer_id}",
                f"target: {request.target}",
            ),
            corrections=frozenset(("one-way-light-time",)),
        )
        geometry = SphericalPoints(
            np.array((longitude,)),
            np.array((latitude,)),
            coordinate_spec=coordinate_spec,
            ids=np.array((request.target,), dtype=object),
        )
        return AstrometricDirection(
            request=request,
            observer_state=observer_state,
            geometry=geometry,
            distance_au=distance_au,
            relative_velocity_au_per_day=tuple(
                target - observer
                for target, observer in zip(
                    target_state.velocity,
                    observer_state.velocity,
                )
            ),
            light_time_days=light_time_days,
            emission_instant=_isot(emission),
            emission_time_scale=emission.scale,
            iterations=iteration,
            target_provider_id=target_state.provider_target_id,
            provenance=(
                "iterated target at retarded emission time",
                "observer held at reception time",
                (
                    "light-time tolerance days: "
                    f"{request.light_time_tolerance_days:.17g}"
                ),
            ),
        )

    @staticmethod
    def _validate_target_state(target_state, state_request, observer_state):
        if target_state.request != state_request:
            raise AstrometricDirectionIdentityError(
                "provider returned a different state request."
            )
        state_request = target_state.request
        if state_request.frame != "icrf":
            raise AstrometricDirectionIdentityError(
                "target state must use frame='icrf'."
            )
        if target_state.position_unit != "au":
            raise AstrometricDirectionIdentityError(
                "target position must use AU."
            )
        if target_state.velocity_unit != "au/day":
            raise AstrometricDirectionIdentityError(
                "target velocity must use AU/day."
            )
        if target_state.resource != observer_state.resource:
            raise AstrometricDirectionIdentityError(
                "target and observer states must use the same resource."
            )
        if (
            target_state.provider_centre_id is not None
            and observer_state.provider_centre_id is not None
            and target_state.provider_centre_id
            != observer_state.provider_centre_id
        ):
            raise AstrometricDirectionIdentityError(
                "target and observer states must use the same provider centre."
            )


@dataclass(frozen=True)
class ApparentCorrectionPolicy:
    """Explicit Skyfield aberration and gravitational-deflection policy."""

    model: str = "Skyfield apparent"
    deflector_naif_ids: tuple[int, ...] = (10, 599, 699)
    earth_deflection: bool = True
    aberration: bool = True

    def __post_init__(self):
        object.__setattr__(self, "model", _text(self.model, name="model"))
        try:
            deflectors = tuple(self.deflector_naif_ids)
        except TypeError as error:
            raise TypeError(
                "deflector_naif_ids must be an iterable of integers."
            ) from error
        if any(
            isinstance(value, bool) or not isinstance(value, int)
            for value in deflectors
        ):
            raise TypeError("deflector_naif_ids must contain only integers.")
        if len(deflectors) != len(set(deflectors)):
            raise ValueError("deflector_naif_ids must not contain duplicates.")
        object.__setattr__(self, "deflector_naif_ids", deflectors)
        for name in ("earth_deflection", "aberration"):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be a boolean.")
            if not getattr(self, name):
                raise ValueError(
                    f"{name} must be enabled for an apparent direction."
                )


@dataclass(frozen=True)
class ApparentDirection:
    """One apparent ICRS direction derived from an astrometric result."""

    astrometric: AstrometricDirection
    policy: ApparentCorrectionPolicy
    geometry: SphericalPoints
    provenance: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if not isinstance(self.astrometric, AstrometricDirection):
            raise TypeError("astrometric must be an AstrometricDirection.")
        if not isinstance(self.policy, ApparentCorrectionPolicy):
            raise TypeError("policy must be an ApparentCorrectionPolicy.")
        if not isinstance(self.geometry, SphericalPoints):
            raise TypeError("geometry must be a SphericalPoints.")
        spec = self.geometry.coordinate_spec
        if (
            spec.frame != "icrs"
            or spec.origin != "observer"
            or spec.position_status is not PositionStatus.APPARENT
        ):
            raise ValueError(
                "geometry must be an observer-origin apparent ICRS direction."
            )
        if spec.epoch is not None or spec.equinox is not None:
            raise ValueError(
                "apparent ICRS geometry must not declare epoch or equinox."
            )
        object.__setattr__(
            self,
            "provenance",
            tuple(
                _text(value, name="provenance entry")
                for value in self.provenance
            ),
        )
