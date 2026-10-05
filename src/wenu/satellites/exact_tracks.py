"""Exact local track evidence for one accepted satellite crossing."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from math import acos, asin, atan2, degrees, isfinite
from typing import Callable

import numpy as np

from wenu.coordinates import CoordinateSpec, PositionStatus
from wenu.satellite_crossings import SatelliteCrossingResult, _utc_instant

from .sgp4 import Sgp4TemePropagator
from .snapshots import SatelliteElementSnapshot
from .topocentric import SatelliteTopocentricTransformer


EXACT_LOCAL_TRACK_PRODUCT = "wenu.artificial_satellite_exact_local_track"
EXACT_LOCAL_TRACK_SCHEMA_VERSION = 1
EXACT_LOCAL_TRACK_IMPLEMENTATION = "wenu exact local track sampler v1"
EXACT_LOCAL_TRACK_STATUS = "exact local connected-visit track"
_EVENT_ROLES = ("entry", "closest_approach", "exit")


def _finite_positive(value, *, name):
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a positive finite number.")
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise TypeError(f"{name} must be a positive finite number.") from error
    if not isfinite(result) or result <= 0.0:
        raise ValueError(f"{name} must be a positive finite number.")
    return result


def _positive_integer(value, *, name, minimum=1):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer.")
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}.")
    return value


def _datetime(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _instant(value):
    return value.astimezone(timezone.utc).isoformat(
        timespec="microseconds"
    ).replace("+00:00", "Z")


def _unit(value):
    vector = np.asarray(value, dtype=float)
    if vector.shape != (3,) or not np.all(np.isfinite(vector)):
        raise ValueError("direction must contain three finite values.")
    norm = float(np.linalg.norm(vector))
    if not isfinite(norm) or norm <= 0.0:
        raise ValueError("direction must be non-zero.")
    return tuple(float(item) for item in vector / norm)


def _angles(direction):
    x, y, z = direction
    longitude = degrees(atan2(y, x)) % 360.0
    latitude = degrees(asin(float(np.clip(z, -1.0, 1.0))))
    return longitude, latitude


def _separation(left, right):
    dot = float(np.clip(np.dot(left, right), -1.0, 1.0))
    return degrees(acos(dot))


def _canonical(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _coordinate_document(spec):
    return {
        "corrections": sorted(spec.corrections),
        "epoch": spec.epoch,
        "equinox": spec.equinox,
        "frame": spec.frame,
        "instant": spec.instant,
        "latitude_unit": spec.latitude_unit,
        "longitude_unit": spec.longitude_unit,
        "model": spec.model,
        "origin": spec.origin,
        "position_status": spec.position_status.value,
        "provenance": list(spec.provenance),
        "provider": spec.provider,
        "representation": spec.representation,
        "time_scale": spec.time_scale,
    }


def _crossing_document(value):
    candidate = value.candidate
    identity = candidate.satellite
    observer = candidate.observer
    field = candidate.field_of_view
    interval = candidate.interval
    return {
        "angular_rate_deg_per_s": value.angular_rate_deg_per_s,
        "candidate_provenance": list(candidate.provenance),
        "candidate_warnings": list(candidate.warnings),
        "closest_approach_deg": value.closest_approach_deg,
        "closest_approach_instant": value.closest_approach_instant,
        "element_epoch": candidate.element_epoch,
        "entry_instant": value.entry_instant,
        "exit_instant": value.exit_instant,
        "field": {
            "angular_radius_deg": field.angular_radius_deg,
            "boundary": field.boundary,
            "center_latitude_deg": field.center_latitude_deg,
            "center_longitude_deg": field.center_longitude_deg,
            "coordinate_spec": _coordinate_document(field.coordinate_spec),
            "field_id": field.field_id,
        },
        "identity": {
            "classification": identity.classification,
            "international_designator": identity.international_designator,
            "norad_catalog_id": identity.norad_catalog_id,
            "object_name": identity.object_name,
        },
        "illumination": value.illumination,
        "interval": {
            "boundary": interval.boundary,
            "start": interval.start,
            "stop": interval.stop,
            "time_scale": interval.time_scale,
        },
        "observer": {
            "earth_orientation_policy": observer.earth_orientation_policy,
            "elevation_m": observer.elevation_m,
            "latitude_deg": observer.latitude_deg,
            "longitude_deg": observer.longitude_deg,
            "observer_id": observer.observer_id,
            "refraction_policy": observer.refraction_policy,
        },
        "orbit_solution_id": candidate.orbit_solution_id,
        "provider_event_id": value.provider_event_id,
        "range_km": value.range_km,
        "result_provenance": list(value.provenance),
        "result_warnings": list(value.warnings),
        "snapshot_sha256": candidate.snapshot_sha256,
        "source_provider": candidate.source_provider,
    }


@dataclass(frozen=True)
class ExactLocalTrackPolicy:
    """Deterministic adaptive-sampling policy and fail-closed limits."""

    angular_chord_tolerance_deg: float = 0.01
    maximum_step_seconds: float = 1.0
    max_depth: int = 32
    max_evaluations: int = 20000
    max_samples: int = 10000

    def __post_init__(self):
        object.__setattr__(
            self,
            "angular_chord_tolerance_deg",
            _finite_positive(
                self.angular_chord_tolerance_deg,
                name="angular_chord_tolerance_deg",
            ),
        )
        object.__setattr__(
            self,
            "maximum_step_seconds",
            _finite_positive(
                self.maximum_step_seconds,
                name="maximum_step_seconds",
            ),
        )
        object.__setattr__(
            self, "max_depth", _positive_integer(self.max_depth, name="max_depth")
        )
        object.__setattr__(
            self,
            "max_evaluations",
            _positive_integer(
                self.max_evaluations, name="max_evaluations", minimum=3
            ),
        )
        object.__setattr__(
            self,
            "max_samples",
            _positive_integer(self.max_samples, name="max_samples"),
        )


@dataclass(frozen=True)
class ExactLocalTrackEvaluation:
    """One evaluator result before event roles are attached."""

    instant_utc: str
    direction: tuple[float, float, float]
    range_km: float
    provenance: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        object.__setattr__(
            self, "instant_utc", _utc_instant(self.instant_utc, name="instant_utc")
        )
        object.__setattr__(self, "direction", _unit(self.direction))
        object.__setattr__(
            self, "range_km", _finite_positive(self.range_km, name="range_km")
        )
        object.__setattr__(self, "provenance", tuple(self.provenance))
        object.__setattr__(self, "warnings", tuple(self.warnings))
        if any(not isinstance(item, str) or not item.strip() for item in self.provenance):
            raise ValueError("provenance entries must be non-empty strings.")
        if any(not isinstance(item, str) or not item.strip() for item in self.warnings):
            raise ValueError("warning entries must be non-empty strings.")


@dataclass(frozen=True)
class ExactLocalSatelliteTrackSample:
    """One retained exact local direction with optional event roles."""

    instant_utc: str
    direction: tuple[float, float, float]
    longitude_deg: float
    latitude_deg: float
    range_km: float
    roles: tuple[str, ...] = field(default_factory=tuple)
    provenance: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        instant = _utc_instant(self.instant_utc, name="instant_utc")
        direction = _unit(self.direction)
        longitude, latitude = _angles(direction)
        supplied_longitude = float(self.longitude_deg)
        supplied_latitude = float(self.latitude_deg)
        if not isfinite(supplied_longitude) or not isfinite(supplied_latitude):
            raise ValueError("sample longitude and latitude must be finite.")
        if abs(((supplied_longitude - longitude + 180.0) % 360.0) - 180.0) > 1e-10:
            raise ValueError("longitude_deg does not match direction.")
        if abs(supplied_latitude - latitude) > 1e-10:
            raise ValueError("latitude_deg does not match direction.")
        roles = tuple(self.roles)
        if len(set(roles)) != len(roles) or any(role not in _EVENT_ROLES for role in roles):
            raise ValueError("roles must be unique accepted event roles.")
        roles = tuple(role for role in _EVENT_ROLES if role in roles)
        object.__setattr__(self, "instant_utc", instant)
        object.__setattr__(self, "direction", direction)
        object.__setattr__(self, "longitude_deg", longitude)
        object.__setattr__(self, "latitude_deg", latitude)
        object.__setattr__(
            self, "range_km", _finite_positive(self.range_km, name="range_km")
        )
        object.__setattr__(self, "roles", roles)
        object.__setattr__(self, "provenance", tuple(self.provenance))
        object.__setattr__(self, "warnings", tuple(self.warnings))


class ExactLocalTrackError(RuntimeError):
    """Fail-closed exact-track convergence or evaluation failure."""


@dataclass(frozen=True)
class ExactLocalSatelliteTrack:
    """Immutable evidence for one exact connected satellite visit."""

    crossing: SatelliteCrossingResult
    samples: tuple[ExactLocalSatelliteTrackSample, ...]
    coordinate_spec: CoordinateSpec
    policy: ExactLocalTrackPolicy
    provenance: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    implementation: str = EXACT_LOCAL_TRACK_IMPLEMENTATION
    sample_time_scale: str = "utc"
    track_identity_sha256: str = field(init=False)

    def __post_init__(self):
        if not isinstance(self.crossing, SatelliteCrossingResult):
            raise TypeError("crossing must be a SatelliteCrossingResult.")
        samples = tuple(self.samples)
        if not samples or not all(
            isinstance(item, ExactLocalSatelliteTrackSample) for item in samples
        ):
            raise TypeError("samples must contain exact local track samples.")
        instants = tuple(item.instant_utc for item in samples)
        if instants != tuple(sorted(set(instants))):
            raise ValueError("sample instants must be strictly increasing.")
        if instants[0] != self.crossing.entry_instant:
            raise ValueError("first sample must be the exact entry instant.")
        if instants[-1] != self.crossing.exit_instant:
            raise ValueError("last sample must be the exact exit instant.")
        required = {
            "entry": self.crossing.entry_instant,
            "closest_approach": self.crossing.closest_approach_instant,
            "exit": self.crossing.exit_instant,
        }
        for role, instant in required.items():
            matches = [item for item in samples if role in item.roles]
            if len(matches) != 1 or matches[0].instant_utc != instant:
                raise ValueError(f"{role} role must mark its exact event instant.")
        if not isinstance(self.coordinate_spec, CoordinateSpec):
            raise TypeError("coordinate_spec must be a CoordinateSpec.")
        spec = self.coordinate_spec
        if (
            spec.frame != "gcrs-axes"
            or spec.origin != "topocentric-direction"
            or spec.position_status is not PositionStatus.GEOMETRIC
            or spec.instant is not None
            or spec.time_scale is not None
        ):
            raise ValueError("coordinate_spec must be timeless geometric topocentric GCRS axes.")
        if not isinstance(self.policy, ExactLocalTrackPolicy):
            raise TypeError("policy must be an ExactLocalTrackPolicy.")
        if self.sample_time_scale != "utc":
            raise ValueError("sample_time_scale must be 'utc'.")
        object.__setattr__(self, "samples", samples)
        object.__setattr__(self, "provenance", tuple(self.provenance))
        object.__setattr__(self, "warnings", tuple(self.warnings))
        document = self.identity_document()
        object.__setattr__(
            self,
            "track_identity_sha256",
            sha256(_canonical(document).encode("utf-8")).hexdigest(),
        )

    def identity_document(self):
        return {
            "algorithm": {
                "implementation": self.implementation,
                "policy": {
                    "angular_chord_tolerance_deg": self.policy.angular_chord_tolerance_deg,
                    "max_depth": self.policy.max_depth,
                    "max_evaluations": self.policy.max_evaluations,
                    "max_samples": self.policy.max_samples,
                    "maximum_step_seconds": self.policy.maximum_step_seconds,
                },
            },
            "coordinate_spec": _coordinate_document(self.coordinate_spec),
            "crossing": _crossing_document(self.crossing),
            "product": EXACT_LOCAL_TRACK_PRODUCT,
            "provenance": list(self.provenance),
            "sample_time_scale": self.sample_time_scale,
            "samples": [
                {
                    "direction": list(item.direction),
                    "instant_utc": item.instant_utc,
                    "latitude_deg": item.latitude_deg,
                    "longitude_deg": item.longitude_deg,
                    "provenance": list(item.provenance),
                    "range_km": item.range_km,
                    "roles": list(item.roles),
                    "warnings": list(item.warnings),
                }
                for item in self.samples
            ],
            "schema_version": EXACT_LOCAL_TRACK_SCHEMA_VERSION,
            "scientific_status": EXACT_LOCAL_TRACK_STATUS,
            "warnings": list(self.warnings),
        }


class _EvaluationCache:
    def __init__(self, evaluator, policy, crossing):
        self._evaluator = evaluator
        self._policy = policy
        self._crossing = crossing
        self._values = {}

    def __call__(self, instant):
        normalized = _instant(instant)
        if normalized in self._values:
            return self._values[normalized]
        if len(self._values) >= self._policy.max_evaluations:
            raise ExactLocalTrackError(
                f"NORAD {self._crossing.candidate.satellite.norad_catalog_id}: "
                f"evaluation limit {self._policy.max_evaluations} exhausted."
            )
        try:
            value = self._evaluator(normalized)
        except ExactLocalTrackError:
            raise
        except Exception as error:
            raise ExactLocalTrackError(
                f"NORAD {self._crossing.candidate.satellite.norad_catalog_id}: "
                f"track evaluation failed at {normalized}: {error}"
            ) from error
        if not isinstance(value, ExactLocalTrackEvaluation):
            raise TypeError("track evaluator must return ExactLocalTrackEvaluation.")
        if value.instant_utc != normalized:
            raise ExactLocalTrackError("track evaluator returned a mismatched instant.")
        self._values[normalized] = value
        return value


def _refine(cache, start, stop, policy, depth):
    left = cache(start)
    right = cache(stop)
    width = (stop - start).total_seconds()
    if width <= 0.0:
        return (left,)
    midpoint = start + (stop - start) / 2
    middle = cache(midpoint)
    chord = np.asarray(left.direction) + np.asarray(right.direction)
    norm = float(np.linalg.norm(chord))
    deviation = (
        float("inf")
        if norm <= 0.0
        else _separation(np.asarray(middle.direction), chord / norm)
    )
    needs_split = (
        width > policy.maximum_step_seconds
        or deviation > policy.angular_chord_tolerance_deg
    )
    if not needs_split:
        return (left, right)
    if depth >= policy.max_depth:
        raise ExactLocalTrackError(
            f"adaptive subdivision exceeded depth {policy.max_depth}."
        )
    left_values = _refine(cache, start, midpoint, policy, depth + 1)
    right_values = _refine(cache, midpoint, stop, policy, depth + 1)
    return left_values[:-1] + right_values


def _track_coordinate_spec(provenance):
    return CoordinateSpec(
        frame="gcrs-axes",
        origin="topocentric-direction",
        position_status=PositionStatus.GEOMETRIC,
        provider="wenu local satellite propagation",
        model="SGP4 TEME through installed-IERS-A topocentric GCRS-axis direction",
        provenance=tuple(provenance) + (
            "Each vertex retains its own UTC instant in exact-track evidence.",
        ),
        corrections=frozenset(
            {"earth-orientation", "polar-motion", "observer-parallax"}
        ),
    )


def _realize_track(crossing, policy, evaluator, *, provenance=(), warnings=()):
    """Build exact evidence from a deterministic evaluator; used by tests too."""
    if not isinstance(crossing, SatelliteCrossingResult):
        raise TypeError("crossing must be a SatelliteCrossingResult.")
    if not isinstance(policy, ExactLocalTrackPolicy):
        raise TypeError("policy must be an ExactLocalTrackPolicy.")
    if not callable(evaluator):
        raise TypeError("evaluator must be callable.")
    event_roles = {}
    for role, instant in (
        ("entry", crossing.entry_instant),
        ("closest_approach", crossing.closest_approach_instant),
        ("exit", crossing.exit_instant),
    ):
        event_roles.setdefault(instant, []).append(role)
    anchors = tuple(sorted(_datetime(value) for value in event_roles))
    cache = _EvaluationCache(evaluator, policy, crossing)
    if len(anchors) == 1:
        evaluations = (cache(anchors[0]),)
    else:
        values = []
        for start, stop in zip(anchors, anchors[1:]):
            refined = _refine(cache, start, stop, policy, 0)
            values.extend(refined if not values else refined[1:])
        evaluations = tuple(values)
    if len(evaluations) > policy.max_samples:
        raise ExactLocalTrackError(
            f"retained sample limit {policy.max_samples} exhausted."
        )
    samples = []
    for value in evaluations:
        longitude, latitude = _angles(value.direction)
        samples.append(
            ExactLocalSatelliteTrackSample(
                instant_utc=value.instant_utc,
                direction=value.direction,
                longitude_deg=longitude,
                latitude_deg=latitude,
                range_km=value.range_km,
                roles=tuple(event_roles.get(value.instant_utc, ())),
                provenance=value.provenance,
                warnings=value.warnings,
            )
        )
    return ExactLocalSatelliteTrack(
        crossing=crossing,
        samples=tuple(samples),
        coordinate_spec=_track_coordinate_spec(provenance),
        policy=policy,
        provenance=(EXACT_LOCAL_TRACK_IMPLEMENTATION, *tuple(provenance)),
        warnings=tuple(warnings),
    )


class ExactLocalSatelliteTrackRealizer:
    """Compose accepted snapshot, SGP4, and topocentric owners once per visit."""

    def __init__(
        self,
        *,
        propagator_factory=Sgp4TemePropagator,
        transformer_factory=SatelliteTopocentricTransformer,
    ):
        self._propagator_factory = propagator_factory
        self._transformer_factory = transformer_factory

    def realize(self, crossing, snapshot, policy=None):
        if not isinstance(crossing, SatelliteCrossingResult):
            raise TypeError("crossing must be a SatelliteCrossingResult.")
        if not isinstance(snapshot, SatelliteElementSnapshot):
            raise TypeError("snapshot must be a SatelliteElementSnapshot.")
        policy = ExactLocalTrackPolicy() if policy is None else policy
        if not isinstance(policy, ExactLocalTrackPolicy):
            raise TypeError("policy must be an ExactLocalTrackPolicy.")
        candidate = crossing.candidate
        digest = snapshot.manifest.content_sha256
        if candidate.snapshot_sha256 != digest:
            raise ValueError("crossing snapshot digest does not match snapshot.")
        identifier = candidate.satellite.norad_catalog_id
        record = snapshot.by_norad_catalog_id.get(identifier)
        if record is None:
            raise ValueError(f"snapshot has no NORAD {identifier} record.")
        identity = candidate.satellite
        for name in ("object_name", "international_designator", "classification"):
            candidate_value = getattr(identity, name)
            record_value = getattr(record, name)
            if candidate_value is not None and candidate_value != record_value:
                raise ValueError(f"crossing satellite {name} does not match snapshot.")
        if (
            candidate.orbit_solution_id is not None
            and candidate.orbit_solution_id != record.source_identity
        ):
            raise ValueError("crossing orbit solution does not match snapshot record.")
        if (
            candidate.element_epoch is not None
            and candidate.element_epoch != record.epoch_utc
        ):
            raise ValueError("crossing element epoch does not match snapshot record.")

        propagator = self._propagator_factory(
            record, snapshot_sha256=digest
        )
        transformer = self._transformer_factory()

        def evaluate(instant_utc):
            topocentric = transformer.transform(
                propagator.propagate(instant_utc),
                candidate.observer,
            )
            longitude = np.radians(topocentric.gcrs_axis_longitude_deg)
            latitude = np.radians(topocentric.gcrs_axis_latitude_deg)
            direction = (
                float(np.cos(latitude) * np.cos(longitude)),
                float(np.cos(latitude) * np.sin(longitude)),
                float(np.sin(latitude)),
            )
            state = topocentric.teme_state
            evidence = topocentric.earth_orientation
            return ExactLocalTrackEvaluation(
                instant_utc=instant_utc,
                direction=direction,
                range_km=topocentric.range_km,
                provenance=(
                    f"snapshot SHA-256 {digest}",
                    f"source record SHA-256 {record.source_record_sha256}",
                    f"orbit solution {record.source_identity}",
                    f"SGP4 {state.sgp4_version}; {state.implementation}; {state.gravity_model}",
                    f"IERS-A SHA-256 {evidence.source_sha256}",
                    *topocentric.provenance,
                ),
                warnings=topocentric.warnings,
            )

        return _realize_track(
            crossing,
            policy,
            evaluate,
            provenance=(
                snapshot.manifest.snapshot_id,
                f"observer {candidate.observer.observer_id}",
                "accepted SGP4/TEME and topocentric transformation route",
            ),
        )
