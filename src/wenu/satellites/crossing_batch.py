"""Atomic same-observer coordination of bounded local crossing queries."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from math import asin, degrees, isfinite

from .crossing_acceleration import (
    AcceleratedCrossingEvidence,
    AcceleratedLocalSatelliteCrossingOracle,
)
from .crossing_oracle import LocalSatelliteCrossingQuery
from .snapshot_admission import ExternalSnapshotAdmission
from .topocentric import SatelliteFieldCenterAltitudeEvaluator


MULTI_FIELD_IMPLEMENTATION = (
    "wenu atomic same-observer multi-field crossing coordinator v1"
)


def _positive_finite(value, *, name):
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a positive finite number.")
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise TypeError(
            f"{name} must be a positive finite number."
        ) from error
    if not isfinite(result) or result <= 0.0:
        raise ValueError(f"{name} must be a positive finite number.")
    return result


def _instant(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _iso(value):
    return value.astimezone(timezone.utc).isoformat(
        timespec="microseconds"
    ).replace("+00:00", "Z")


@dataclass(frozen=True)
class MultiFieldCrossingPolicy:
    """Bounded batch admission and execution policy."""

    admitted_snapshot_ids: tuple[str, ...] = ("synthetic_50s4b_v1",)
    max_interval_seconds: float = 60.0
    maximum_airmass: float = 2.0
    processing_chunk_size: int = 10
    sky_motion_bound_deg_per_s: float = 0.005
    certification_time_tolerance_seconds: float = 0.01

    def __post_init__(self):
        snapshot_ids = tuple(self.admitted_snapshot_ids)
        if not snapshot_ids or not all(
            isinstance(item, str) and item.strip() for item in snapshot_ids
        ):
            raise ValueError(
                "admitted_snapshot_ids must contain non-empty strings."
            )
        object.__setattr__(self, "admitted_snapshot_ids", snapshot_ids)
        for name in (
            "max_interval_seconds",
            "maximum_airmass",
            "sky_motion_bound_deg_per_s",
            "certification_time_tolerance_seconds",
        ):
            object.__setattr__(
                self,
                name,
                _positive_finite(getattr(self, name), name=name),
            )
        if self.maximum_airmass < 1.0:
            raise ValueError("maximum_airmass must be at least 1.")
        if (
            isinstance(self.processing_chunk_size, bool)
            or not isinstance(self.processing_chunk_size, int)
        ):
            raise TypeError("processing_chunk_size must be an integer.")
        if self.processing_chunk_size < 1:
            raise ValueError("processing_chunk_size must be at least 1.")


@dataclass(frozen=True)
class MultiFieldCrossingRequest:
    """One ordered non-empty batch of complete single-field queries."""

    queries: tuple[LocalSatelliteCrossingQuery, ...]

    def __post_init__(self):
        if isinstance(self.queries, (str, bytes)):
            raise TypeError(
                "queries must be an iterable of LocalSatelliteCrossingQuery."
            )
        try:
            queries = tuple(self.queries)
        except TypeError as error:
            raise TypeError(
                "queries must be an iterable of LocalSatelliteCrossingQuery."
            ) from error
        if not queries:
            raise ValueError("queries must be non-empty.")
        if not all(
            isinstance(query, LocalSatelliteCrossingQuery)
            for query in queries
        ):
            raise TypeError(
                "queries must contain LocalSatelliteCrossingQuery values."
            )
        field_ids = tuple(
            query.field_of_view.field_id for query in queries
        )
        if len(set(field_ids)) != len(field_ids):
            raise ValueError("field identifiers must be unique within a batch.")
        object.__setattr__(self, "queries", queries)


@dataclass(frozen=True)
class FieldAirmassAdmission:
    """Conservative centre-only airmass evidence for one field interval."""

    field_id: str
    maximum_airmass: float
    minimum_altitude_deg: float
    certified_lower_bound_deg: float
    evaluation_count: int
    earth_orientation_sha256: tuple[str, ...]
    provenance: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class MultiFieldValidationFailure:
    """One ordered field-specific reason for atomic batch rejection."""

    field_id: str
    code: str
    message: str


class MultiFieldCrossingValidationError(ValueError):
    """Reject an invalid batch before any crossing query is solved."""

    def __init__(self, failures):
        failures = tuple(failures)
        if not failures or not all(
            isinstance(item, MultiFieldValidationFailure)
            for item in failures
        ):
            raise ValueError(
                "failures must contain MultiFieldValidationFailure values."
            )
        self.failures = failures
        summary = "; ".join(
            f"{item.field_id}: {item.code}" for item in failures
        )
        super().__init__(f"Multi-field request failed validation ({summary}).")


@dataclass(frozen=True)
class MultiFieldCrossingResult:
    """Exact results and separate admission/acceleration evidence per field."""

    query: LocalSatelliteCrossingQuery
    crossings: tuple
    airmass_admission: FieldAirmassAdmission
    acceleration_evidence: AcceleratedCrossingEvidence

    @property
    def field_id(self):
        return self.query.field_of_view.field_id


class FieldAirmassCertifier:
    """Conservatively certify one field centre across its whole interval."""

    def __init__(self, *, policy=None, evaluator=None):
        self._policy = policy or MultiFieldCrossingPolicy()
        if not isinstance(self._policy, MultiFieldCrossingPolicy):
            raise TypeError("policy must be a MultiFieldCrossingPolicy.")
        self._evaluator = evaluator or SatelliteFieldCenterAltitudeEvaluator()
        if not callable(getattr(self._evaluator, "evaluate", None)):
            raise TypeError("evaluator must provide callable evaluate(...).")

    def certify(self, query):
        if not isinstance(query, LocalSatelliteCrossingQuery):
            raise TypeError("query must be a LocalSatelliteCrossingQuery.")
        start = _instant(query.interval.start)
        stop = _instant(query.interval.stop)
        threshold = degrees(asin(1.0 / self._policy.maximum_airmass))
        values = {}
        resource_digests = set()

        def altitude(instant):
            if instant not in values:
                value, evidence = self._evaluator.evaluate(
                    query.field_of_view,
                    query.observer,
                    _iso(instant),
                )
                value = float(value)
                if not isfinite(value):
                    raise ValueError("field-centre altitude must be finite.")
                values[instant] = value
                resource_digests.add(evidence.source_sha256)
            return values[instant]

        lower_bounds = []

        def certify_segment(left, right):
            duration = (right - left).total_seconds()
            middle = left + (right - left) / 2
            middle_altitude = altitude(middle)
            if middle_altitude < threshold:
                raise ValueError(
                    "field centre exceeds the maximum airmass."
                )
            lower_bound = (
                middle_altitude
                - self._policy.sky_motion_bound_deg_per_s * duration / 2.0
            )
            if lower_bound >= threshold:
                lower_bounds.append(lower_bound)
                return
            if duration <= (
                self._policy.certification_time_tolerance_seconds
            ):
                raise ValueError(
                    "field-centre airmass cannot be certified at the "
                    "declared numerical boundary."
                )
            certify_segment(left, middle)
            certify_segment(middle, right)

        if start == stop:
            value = altitude(start)
            if value < threshold:
                raise ValueError(
                    "field centre exceeds the maximum airmass."
                )
            lower_bounds.append(value)
        else:
            certify_segment(start, stop)
        return FieldAirmassAdmission(
            field_id=query.field_of_view.field_id,
            maximum_airmass=self._policy.maximum_airmass,
            minimum_altitude_deg=threshold,
            certified_lower_bound_deg=min(lower_bounds),
            evaluation_count=len(values),
            earth_orientation_sha256=tuple(sorted(resource_digests)),
            provenance=(
                MULTI_FIELD_IMPLEMENTATION,
                "Geometric vacuum field-centre AltAz.",
                "Plane-parallel airmass X = sec(z).",
                "FoV radius is not part of airmass admission.",
                (
                    "Whole-interval altitude Lipschitz bound "
                    f"{self._policy.sky_motion_bound_deg_per_s:.12g} deg/s."
                ),
            ),
        )


class MultiFieldSatelliteCrossingCoordinator:
    """Atomically validate and solve an ordered same-observer field batch."""

    def __init__(
        self,
        *,
        policy=None,
        certifier=None,
        single_field_oracle=None,
        external_snapshot_admission=None,
    ):
        self._policy = policy or MultiFieldCrossingPolicy()
        if not isinstance(self._policy, MultiFieldCrossingPolicy):
            raise TypeError("policy must be a MultiFieldCrossingPolicy.")
        if (
            external_snapshot_admission is not None
            and not isinstance(
                external_snapshot_admission, ExternalSnapshotAdmission
            )
        ):
            raise TypeError(
                "external_snapshot_admission must be an "
                "ExternalSnapshotAdmission."
            )
        self._external_snapshot_admission = external_snapshot_admission
        self._certifier = certifier or FieldAirmassCertifier(
            policy=self._policy
        )
        if not callable(getattr(self._certifier, "certify", None)):
            raise TypeError("certifier must provide callable certify(query).")
        self._single_field_oracle = (
            single_field_oracle
            or AcceleratedLocalSatelliteCrossingOracle(
                external_snapshot_admission=external_snapshot_admission
            )
        )
        if not callable(
            getattr(self._single_field_oracle, "solve_with_evidence", None)
        ):
            raise TypeError(
                "single_field_oracle must provide solve_with_evidence(query)."
            )

    @property
    def policy(self):
        return self._policy

    def validate(self, request):
        """Validate every field atomically without solving any crossing."""
        if not isinstance(request, MultiFieldCrossingRequest):
            raise TypeError("request must be a MultiFieldCrossingRequest.")
        admissions = self._validate(request)
        return tuple(
            admissions[query.field_of_view.field_id]
            for query in request.queries
        )

    def _validate(self, request):
        first = request.queries[0]
        snapshot_identity = (
            first.snapshot.manifest.snapshot_id,
            first.snapshot.manifest.content_sha256,
        )
        observer = first.observer
        failures = []
        admissions = {}
        for query in request.queries:
            field_id = query.field_of_view.field_id
            identity = (
                query.snapshot.manifest.snapshot_id,
                query.snapshot.manifest.content_sha256,
            )
            if identity != snapshot_identity:
                failures.append(
                    MultiFieldValidationFailure(
                        field_id,
                        "snapshot-mismatch",
                        "all fields must use one immutable snapshot",
                    )
                )
                continue
            if query.observer != observer:
                failures.append(
                    MultiFieldValidationFailure(
                        field_id,
                        "observer-mismatch",
                        "all fields must use one observer",
                    )
                )
                continue
            ordinary_admitted = (
                query.snapshot.manifest.snapshot_id
                in self._policy.admitted_snapshot_ids
            )
            if self._external_snapshot_admission is not None:
                try:
                    self._external_snapshot_admission.require(query.snapshot)
                except (TypeError, ValueError) as error:
                    failures.append(
                        MultiFieldValidationFailure(
                            field_id,
                            "snapshot-admission-failed",
                            f"{type(error).__name__}: {error}",
                        )
                    )
                    continue
            elif not ordinary_admitted:
                failures.append(
                    MultiFieldValidationFailure(
                        field_id,
                        "snapshot-outside-domain",
                        "external snapshot requires explicit digest-bound "
                        "admission",
                    )
                )
                continue
            duration = (
                _instant(query.interval.stop)
                - _instant(query.interval.start)
            ).total_seconds()
            if duration > self._policy.max_interval_seconds:
                failures.append(
                    MultiFieldValidationFailure(
                        field_id,
                        "interval-outside-domain",
                        "interval exceeds the bounded 50S.6F duration",
                    )
                )
                continue
        if failures:
            raise MultiFieldCrossingValidationError(failures)
        for query in request.queries:
            field_id = query.field_of_view.field_id
            try:
                admissions[field_id] = self._certifier.certify(query)
            except Exception as error:
                failures.append(
                    MultiFieldValidationFailure(
                        field_id,
                        "airmass-not-certified",
                        f"{type(error).__name__}: {error}",
                    )
                )
        if failures:
            raise MultiFieldCrossingValidationError(failures)
        return admissions

    def solve(self, request):
        if not isinstance(request, MultiFieldCrossingRequest):
            raise TypeError("request must be a MultiFieldCrossingRequest.")
        admissions_values = self.validate(request)
        admissions = {
            value.field_id: value for value in admissions_values
        }
        results = []
        size = self._policy.processing_chunk_size
        for offset in range(0, len(request.queries), size):
            for query in request.queries[offset : offset + size]:
                crossings, evidence = (
                    self._single_field_oracle.solve_with_evidence(query)
                )
                results.append(
                    MultiFieldCrossingResult(
                        query=query,
                        crossings=tuple(crossings),
                        airmass_admission=admissions[
                            query.field_of_view.field_id
                        ],
                        acceleration_evidence=evidence,
                    )
                )
        return tuple(results)
