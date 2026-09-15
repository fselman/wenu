"""Complete local circular-field crossing oracle for satellite snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from math import acos, cos, degrees, isfinite, radians, sin, sqrt
from typing import Callable

import numpy as np

from wenu.coordinates import PositionStatus
from wenu.satellite_crossings import (
    InclusiveTimeInterval,
    SatelliteCrossingCandidate,
    SatelliteCrossingResult,
    SatelliteFieldOfView,
    SatelliteIdentity,
    SatelliteObserver,
)

from .sgp4 import Sgp4TemePropagator
from .snapshots import SatelliteElementSnapshot
from .topocentric import SatelliteTopocentricTransformer


ORACLE_IMPLEMENTATION = "wenu exhaustive adaptive local crossing oracle v1"


def _finite_positive(value, *, name: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a positive finite number.")
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise TypeError(f"{name} must be a positive finite number.") from error
    if not isfinite(result) or result <= 0.0:
        raise ValueError(f"{name} must be a positive finite number.")
    return result


def _datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _instant(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(
        timespec="microseconds"
    ).replace("+00:00", "Z")


def _unit_vector(longitude_deg: float, latitude_deg: float) -> np.ndarray:
    longitude = radians(longitude_deg)
    latitude = radians(latitude_deg)
    return np.asarray(
        (
            cos(latitude) * cos(longitude),
            cos(latitude) * sin(longitude),
            sin(latitude),
        ),
        dtype=float,
    )


def _separation_deg(left: np.ndarray, right: np.ndarray) -> float:
    dot = float(np.clip(np.dot(left, right), -1.0, 1.0))
    return degrees(acos(dot))


@dataclass(frozen=True)
class LocalSatelliteCrossingQuery:
    """Immutable request for one exhaustive local snapshot search."""

    snapshot: SatelliteElementSnapshot
    observer: SatelliteObserver
    field_of_view: SatelliteFieldOfView
    interval: InclusiveTimeInterval
    time_tolerance_seconds: float
    angular_tolerance_deg: float

    def __post_init__(self):
        expected = (
            ("snapshot", SatelliteElementSnapshot),
            ("observer", SatelliteObserver),
            ("field_of_view", SatelliteFieldOfView),
            ("interval", InclusiveTimeInterval),
        )
        for name, type_ in expected:
            if not isinstance(getattr(self, name), type_):
                raise TypeError(f"{name} must be a {type_.__name__}.")
        object.__setattr__(
            self,
            "time_tolerance_seconds",
            _finite_positive(
                self.time_tolerance_seconds,
                name="time_tolerance_seconds",
            ),
        )
        object.__setattr__(
            self,
            "angular_tolerance_deg",
            _finite_positive(
                self.angular_tolerance_deg,
                name="angular_tolerance_deg",
            ),
        )
        _validate_field(self.field_of_view)


class SatelliteCrossingConvergenceError(RuntimeError):
    """Raised instead of returning an uncertified partial crossing set."""

    def __init__(self, message: str, *, norad_catalog_id: int | None = None):
        self.norad_catalog_id = norad_catalog_id
        prefix = (
            ""
            if norad_catalog_id is None
            else f"NORAD {norad_catalog_id}: "
        )
        super().__init__(prefix + message)


@dataclass(frozen=True)
class _TrajectoryState:
    instant: datetime
    direction: tuple[float, float, float]
    range_km: float
    angular_rate_deg_per_s: float
    source_state: object | None = field(default=None, compare=False)

    def __post_init__(self):
        if self.instant.tzinfo is None or self.instant.utcoffset() != timedelta(0):
            raise ValueError("trajectory-state instant must be UTC-aware.")
        vector = np.asarray(self.direction, dtype=float)
        if vector.shape != (3,) or not np.all(np.isfinite(vector)):
            raise ValueError("trajectory-state direction must have three finite values.")
        norm = float(np.linalg.norm(vector))
        if not isfinite(norm) or norm <= 0.0:
            raise ValueError("trajectory-state direction must be non-zero.")
        object.__setattr__(self, "direction", tuple(vector / norm))
        object.__setattr__(
            self, "range_km", _finite_positive(self.range_km, name="range_km")
        )
        rate = float(self.angular_rate_deg_per_s)
        if not isfinite(rate) or rate < 0.0:
            raise ValueError("angular_rate_deg_per_s must be finite and non-negative.")
        object.__setattr__(self, "angular_rate_deg_per_s", rate)


@dataclass(frozen=True)
class _Sample:
    state: _TrajectoryState
    separation_deg: float


def _validate_field(field: SatelliteFieldOfView) -> None:
    spec = field.coordinate_spec
    if (
        spec.frame != "gcrs-axes"
        or spec.origin != "topocentric-direction"
        or spec.position_status is not PositionStatus.GEOMETRIC
        or spec.time_scale != "utc"
        or spec.instant is None
    ):
        raise ValueError(
            "field coordinate_spec must describe a geometric topocentric "
            "direction in GCRS axes at one UTC reference instant."
        )


class _EvaluationCache:
    def __init__(self, evaluator, center, limit, norad_catalog_id):
        self._evaluator = evaluator
        self._center = center
        self._limit = limit
        self._norad_catalog_id = norad_catalog_id
        self._values: dict[datetime, _Sample] = {}

    def __call__(self, instant: datetime) -> _Sample:
        instant = instant.astimezone(timezone.utc)
        if instant in self._values:
            return self._values[instant]
        if len(self._values) >= self._limit:
            raise SatelliteCrossingConvergenceError(
                f"adaptive evaluation limit {self._limit} was exhausted.",
                norad_catalog_id=self._norad_catalog_id,
            )
        try:
            state = self._evaluator(instant)
        except SatelliteCrossingConvergenceError:
            raise
        except Exception as error:
            raise SatelliteCrossingConvergenceError(
                f"trajectory evaluation failed at {_instant(instant)}: {error}",
                norad_catalog_id=self._norad_catalog_id,
            ) from error
        if not isinstance(state, _TrajectoryState):
            raise TypeError("trajectory evaluator must return _TrajectoryState.")
        sample = _Sample(
            state=state,
            separation_deg=_separation_deg(
                np.asarray(state.direction), self._center
            ),
        )
        self._values[instant] = sample
        return sample


def _midpoint(start: datetime, stop: datetime) -> datetime:
    return start + (stop - start) / 2


def _motion_envelope_deg(left: _Sample, middle: _Sample, right: _Sample) -> float:
    half_width = (right.state.instant - left.state.instant).total_seconds() / 2.0
    rate_bound = max(
        left.state.angular_rate_deg_per_s,
        middle.state.angular_rate_deg_per_s,
        right.state.angular_rate_deg_per_s,
    ) * half_width
    left_motion = _separation_deg(
        np.asarray(left.state.direction), np.asarray(middle.state.direction)
    )
    right_motion = _separation_deg(
        np.asarray(middle.state.direction), np.asarray(right.state.direction)
    )
    chord_motion = _separation_deg(
        np.asarray(left.state.direction), np.asarray(right.state.direction)
    )
    curvature = max(0.0, left_motion + right_motion - chord_motion)
    return max(rate_bound, left_motion, right_motion) + curvature


def _golden_minimum(cache, start, stop, time_tolerance):
    ratio = (sqrt(5.0) - 1.0) / 2.0
    left = start
    right = stop
    while (right - left).total_seconds() > time_tolerance:
        width = right - left
        one = right - width * ratio
        two = left + width * ratio
        if cache(one).separation_deg <= cache(two).separation_deg:
            right = two
        else:
            left = one
    points = (left, _midpoint(left, right), right)
    return min((cache(item) for item in points), key=lambda item: item.separation_deg)


def _boundary_root(cache, start, stop, radius, time_tolerance, angular_tolerance):
    left = cache(start)
    right = cache(stop)
    left_value = left.separation_deg - radius
    right_value = right.separation_deg - radius
    if abs(left_value) <= angular_tolerance:
        return left
    if abs(right_value) <= angular_tolerance:
        return right
    if left_value * right_value > 0.0:
        raise SatelliteCrossingConvergenceError(
            "boundary refinement received no sign-changing bracket."
        )
    while (right.state.instant - left.state.instant).total_seconds() > time_tolerance:
        middle = cache(_midpoint(left.state.instant, right.state.instant))
        middle_value = middle.separation_deg - radius
        if abs(middle_value) <= angular_tolerance:
            return middle
        if left_value * middle_value <= 0.0:
            right = middle
            right_value = middle_value
        else:
            left = middle
            left_value = middle_value
    return min((left, right), key=lambda item: abs(item.separation_deg - radius))


def _adaptive_leaves(
    cache,
    start,
    stop,
    radius,
    time_tolerance,
    angular_tolerance,
    depth=0,
):
    if depth > 64:
        raise SatelliteCrossingConvergenceError(
            "adaptive subdivision exceeded depth 64."
        )
    left = cache(start)
    right = cache(stop)
    middle_time = _midpoint(start, stop)
    middle = cache(middle_time)
    width = (stop - start).total_seconds()
    envelope = _motion_envelope_deg(left, middle, right)
    minimum_sample = min(
        left.separation_deg, middle.separation_deg, right.separation_deg
    )
    certified_outside = (
        minimum_sample - envelope
        > radius + angular_tolerance
    )
    if certified_outside:
        return ()
    curvature = abs(
        middle.separation_deg
        - (left.separation_deg + right.separation_deg) / 2.0
    )
    if width <= time_tolerance or curvature <= angular_tolerance:
        return ((start, stop),)
    return _adaptive_leaves(
        cache,
        start,
        middle_time,
        radius,
        time_tolerance,
        angular_tolerance,
        depth + 1,
    ) + _adaptive_leaves(
        cache,
        middle_time,
        stop,
        radius,
        time_tolerance,
        angular_tolerance,
        depth + 1,
    )


def _leaf_visit(cache, start, stop, radius, time_tolerance, angular_tolerance):
    left = cache(start)
    right = cache(stop)
    closest = _golden_minimum(cache, start, stop, time_tolerance)
    left_inside = left.separation_deg <= radius
    right_inside = right.separation_deg <= radius
    if closest.separation_deg > radius + angular_tolerance:
        return None
    if left_inside:
        entry = left
    else:
        entry = _boundary_root(
            cache,
            start,
            closest.state.instant,
            radius,
            time_tolerance,
            angular_tolerance,
        )
    if right_inside:
        exit_ = right
    else:
        exit_ = _boundary_root(
            cache,
            closest.state.instant,
            stop,
            radius,
            time_tolerance,
            angular_tolerance,
        )
    return entry, closest, exit_


def _merge_visits(visits, cache, radius, time_tolerance, angular_tolerance):
    merged = []
    for visit in sorted(visits, key=lambda item: item[0].state.instant):
        if not merged:
            merged.append(visit)
            continue
        previous = merged[-1]
        gap = (visit[0].state.instant - previous[2].state.instant).total_seconds()
        gap_midpoint = cache(
            _midpoint(previous[2].state.instant, visit[0].state.instant)
        )
        if (
            gap <= time_tolerance
            and gap_midpoint.separation_deg <= radius + angular_tolerance
        ):
            closest = min(
                (previous[1], visit[1]), key=lambda item: item.separation_deg
            )
            merged[-1] = (previous[0], closest, visit[2])
        else:
            merged.append(visit)
    return tuple(merged)


def _solve_trajectory(
    evaluator,
    *,
    candidate,
    time_tolerance_seconds,
    angular_tolerance_deg,
    max_evaluations,
):
    center = _unit_vector(
        candidate.field_of_view.center_longitude_deg,
        candidate.field_of_view.center_latitude_deg,
    )
    cache = _EvaluationCache(
        evaluator,
        center,
        max_evaluations,
        candidate.satellite.norad_catalog_id,
    )
    start = _datetime(candidate.interval.start)
    stop = _datetime(candidate.interval.stop)
    radius = candidate.field_of_view.angular_radius_deg
    if start == stop:
        sample = cache(start)
        visits = ((sample, sample, sample),) if sample.separation_deg <= radius else ()
    else:
        leaves = _adaptive_leaves(
            cache,
            start,
            stop,
            radius,
            time_tolerance_seconds,
            angular_tolerance_deg,
        )
        visits = tuple(
            visit
            for leaf in leaves
            for visit in (
                _leaf_visit(
                    cache,
                    leaf[0],
                    leaf[1],
                    radius,
                    time_tolerance_seconds,
                    angular_tolerance_deg,
                ),
            )
            if visit is not None
        )
        visits = _merge_visits(
            visits,
            cache,
            radius,
            time_tolerance_seconds,
            angular_tolerance_deg,
        )
    return tuple(
        SatelliteCrossingResult(
            candidate=candidate,
            entry_instant=_instant(entry.state.instant),
            exit_instant=_instant(exit_.state.instant),
            closest_approach_instant=_instant(closest.state.instant),
            closest_approach_deg=min(closest.separation_deg, radius),
            range_km=closest.state.range_km,
            angular_rate_deg_per_s=closest.state.angular_rate_deg_per_s,
            provenance=(
                ORACLE_IMPLEMENTATION,
                f"time tolerance {time_tolerance_seconds:.12g} s",
                f"angular tolerance {angular_tolerance_deg:.12g} deg",
            ),
        )
        for entry, closest, exit_ in visits
    )


class LocalSatelliteCrossingOracle:
    """Scan every snapshot record with the accepted local state chain."""

    def __init__(self, *, max_evaluations_per_record: int = 20000):
        if (
            isinstance(max_evaluations_per_record, bool)
            or not isinstance(max_evaluations_per_record, int)
        ):
            raise TypeError("max_evaluations_per_record must be an integer.")
        if max_evaluations_per_record < 3:
            raise ValueError("max_evaluations_per_record must be at least 3.")
        self._max_evaluations_per_record = max_evaluations_per_record

    def solve(self, query: LocalSatelliteCrossingQuery):
        """Return all connected visits, ordered by full NORAD id and entry."""
        if not isinstance(query, LocalSatelliteCrossingQuery):
            raise TypeError("query must be a LocalSatelliteCrossingQuery.")
        results = []
        for record in query.snapshot.records:
            propagator = Sgp4TemePropagator(
                record,
                snapshot_sha256=query.snapshot.manifest.content_sha256,
            )
            transformer = SatelliteTopocentricTransformer()

            def evaluate(instant, propagator=propagator, transformer=transformer):
                state = transformer.transform(
                    propagator.propagate(_instant(instant)), query.observer
                )
                position = np.asarray(
                    state.topocentric_itrs_position_km, dtype=float
                )
                velocity = np.asarray(
                    state.topocentric_itrs_velocity_km_per_s, dtype=float
                )
                angular_rate = degrees(
                    float(np.linalg.norm(np.cross(position, velocity)))
                    / float(np.dot(position, position))
                )
                return _TrajectoryState(
                    instant=instant,
                    direction=tuple(
                        _unit_vector(
                            state.gcrs_axis_longitude_deg,
                            state.gcrs_axis_latitude_deg,
                        )
                    ),
                    range_km=state.range_km,
                    angular_rate_deg_per_s=angular_rate,
                    source_state=state,
                )

            candidate = SatelliteCrossingCandidate(
                satellite=SatelliteIdentity(
                    norad_catalog_id=record.norad_catalog_id,
                    object_name=record.object_name,
                    international_designator=record.international_designator,
                    classification=record.classification,
                ),
                observer=query.observer,
                field_of_view=query.field_of_view,
                interval=query.interval,
                source_provider="wenu local crossing oracle",
                orbit_solution_id=record.source_identity,
                snapshot_sha256=query.snapshot.manifest.content_sha256,
                element_epoch=record.epoch_utc,
                provenance=(
                    ORACLE_IMPLEMENTATION,
                    query.snapshot.manifest.snapshot_id,
                    record.source_record_sha256,
                    "SGP4 WGS-72 geometric TEME to installed-IERS-A "
                    "topocentric GCRS-axis direction.",
                    f"observer {query.observer.observer_id}",
                    f"refraction policy {query.observer.refraction_policy}",
                    "earth-orientation policy "
                    f"{query.observer.earth_orientation_policy}",
                ),
            )
            results.extend(
                _solve_trajectory(
                    evaluate,
                    candidate=candidate,
                    time_tolerance_seconds=query.time_tolerance_seconds,
                    angular_tolerance_deg=query.angular_tolerance_deg,
                    max_evaluations=self._max_evaluations_per_record,
                )
            )
        return tuple(
            sorted(
                results,
                key=lambda item: (
                    item.candidate.satellite.norad_catalog_id,
                    item.entry_instant,
                ),
            )
        )
