"""Conservative first-stage selection for local satellite crossings."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from math import asin, degrees, isfinite, pi, sqrt
from typing import Literal

import numpy as np

from wenu.satellites.crossing_oracle import LocalSatelliteCrossingQuery
from wenu.satellites.sgp4 import Sgp4TemePropagator
from wenu.satellites.topocentric import SatelliteTopocentricTransformer


CONE_SHELL_IMPLEMENTATION = (
    "wenu conservative topocentric cone/orbital-shell selector v1"
)
_EARTH_EQUATORIAL_RADIUS_KM = 6378.137
_EARTH_GRAVITATIONAL_PARAMETER_KM3_S2 = 398600.8


def _positive_finite(value, *, name):
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a positive finite number.")
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise TypeError(f"{name} must be a positive finite number.") from error
    if not isfinite(result) or result <= 0.0:
        raise ValueError(f"{name} must be a positive finite number.")
    return result


def _nonnegative_finite(value, *, name):
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a non-negative finite number.")
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise TypeError(
            f"{name} must be a non-negative finite number."
        ) from error
    if not isfinite(result) or result < 0.0:
        raise ValueError(f"{name} must be a non-negative finite number.")
    return result


def _instant(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _unit_vector(longitude_deg, latitude_deg):
    longitude = np.deg2rad(longitude_deg)
    latitude = np.deg2rad(latitude_deg)
    return np.asarray(
        (
            np.cos(latitude) * np.cos(longitude),
            np.cos(latitude) * np.sin(longitude),
            np.sin(latitude),
        ),
        dtype=float,
    )


def _separation_deg(left, right):
    dot = float(np.clip(np.dot(left, right), -1.0, 1.0))
    return degrees(float(np.arccos(dot)))


@dataclass(frozen=True)
class ConeShellPolicy:
    """Declared supported domain and outward safety margins."""

    validated_snapshot_ids: tuple[str, ...] = ("synthetic_50s4b_v1",)
    max_interval_seconds: float = 60.0
    max_abs_element_age_days: float = 14.0
    max_eccentricity: float = 0.25
    max_abs_bstar: float = 0.01
    minimum_perigee_altitude_km: float = 100.0
    orbital_speed_safety_factor: float = 2.5
    observer_speed_bound_km_per_s: float = 0.6
    numerical_margin_deg: float = 1.0e-6

    def __post_init__(self):
        snapshot_ids = tuple(self.validated_snapshot_ids)
        if not snapshot_ids or not all(
            isinstance(item, str) and item.strip() for item in snapshot_ids
        ):
            raise ValueError(
                "validated_snapshot_ids must contain non-empty strings."
            )
        object.__setattr__(self, "validated_snapshot_ids", snapshot_ids)
        for name in (
            "max_interval_seconds",
            "max_abs_element_age_days",
            "max_eccentricity",
            "max_abs_bstar",
            "minimum_perigee_altitude_km",
            "orbital_speed_safety_factor",
            "observer_speed_bound_km_per_s",
        ):
            object.__setattr__(
                self,
                name,
                _positive_finite(getattr(self, name), name=name),
            )
        object.__setattr__(
            self,
            "numerical_margin_deg",
            _nonnegative_finite(
                self.numerical_margin_deg,
                name="numerical_margin_deg",
            ),
        )
        if self.max_eccentricity >= 1.0:
            raise ValueError("max_eccentricity must be less than 1.")


@dataclass(frozen=True)
class ConeShellDecision:
    """One immutable tri-state decision with its decisive geometry."""

    norad_catalog_id: int
    outcome: Literal["reject", "retain", "indeterminate"]
    reason: str
    initial_field_separation_deg: float | None = None
    reachable_cap_deg: float | None = None
    rejection_threshold_deg: float | None = None
    semimajor_axis_km: float | None = None
    perigee_radius_km: float | None = None
    apogee_radius_km: float | None = None
    relative_speed_bound_km_per_s: float | None = None
    interval_seconds: float | None = None
    provenance: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if (
            isinstance(self.norad_catalog_id, bool)
            or not isinstance(self.norad_catalog_id, int)
            or self.norad_catalog_id <= 0
        ):
            raise ValueError("norad_catalog_id must be a positive integer.")
        if self.outcome not in {"reject", "retain", "indeterminate"}:
            raise ValueError("outcome must be reject, retain, or indeterminate.")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("reason must be a non-empty string.")
        object.__setattr__(self, "reason", self.reason.strip())
        for name in (
            "initial_field_separation_deg",
            "reachable_cap_deg",
            "rejection_threshold_deg",
            "semimajor_axis_km",
            "perigee_radius_km",
            "apogee_radius_km",
            "relative_speed_bound_km_per_s",
            "interval_seconds",
        ):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(
                    self, name, _nonnegative_finite(value, name=name)
                )
        object.__setattr__(self, "provenance", tuple(self.provenance))


@dataclass(frozen=True)
class ConeShellSelection:
    """Ordered selector evidence for one immutable exhaustive query."""

    snapshot_sha256: str
    field_id: str
    interval_start: str
    interval_stop: str
    decisions: tuple[ConeShellDecision, ...]
    implementation: str = CONE_SHELL_IMPLEMENTATION

    def __post_init__(self):
        decisions = tuple(self.decisions)
        identifiers = tuple(item.norad_catalog_id for item in decisions)
        if not decisions or identifiers != tuple(sorted(identifiers)):
            raise ValueError("decisions must be non-empty and NORAD ordered.")
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("decisions must have unique NORAD identifiers.")
        object.__setattr__(self, "decisions", decisions)

    @property
    def rejected_norad_catalog_ids(self):
        return tuple(
            item.norad_catalog_id
            for item in self.decisions
            if item.outcome == "reject"
        )

    @property
    def exact_solver_norad_catalog_ids(self):
        """Return retained plus indeterminate records for exact solving."""
        return tuple(
            item.norad_catalog_id
            for item in self.decisions
            if item.outcome != "reject"
        )


class ConservativeConeShellSelector:
    """Reject only records outside a conservative whole-interval cone."""

    def __init__(self, *, policy=None):
        if policy is None:
            policy = ConeShellPolicy()
        if not isinstance(policy, ConeShellPolicy):
            raise TypeError("policy must be a ConeShellPolicy.")
        self._policy = policy

    @property
    def policy(self):
        return self._policy

    def _indeterminate(self, record, reason, *, interval_seconds):
        return ConeShellDecision(
            norad_catalog_id=record.norad_catalog_id,
            outcome="indeterminate",
            reason=reason,
            interval_seconds=interval_seconds,
            provenance=(
                CONE_SHELL_IMPLEMENTATION,
                "Indeterminate records must reach the exact 50S.5 solver.",
            ),
        )

    def _select_record(self, query, record, interval_seconds):
        policy = self._policy
        if (
            query.snapshot.manifest.snapshot_id
            not in policy.validated_snapshot_ids
        ):
            return self._indeterminate(
                record,
                "snapshot is outside the validated cone-shell domain",
                interval_seconds=interval_seconds,
            )
        if interval_seconds > policy.max_interval_seconds:
            return self._indeterminate(
                record,
                "query interval exceeds the validated cone-shell domain",
                interval_seconds=interval_seconds,
            )
        if record.eccentricity > policy.max_eccentricity:
            return self._indeterminate(
                record,
                "eccentricity exceeds the validated cone-shell domain",
                interval_seconds=interval_seconds,
            )
        if abs(record.bstar) > policy.max_abs_bstar:
            return self._indeterminate(
                record,
                "BSTAR exceeds the validated cone-shell domain",
                interval_seconds=interval_seconds,
            )

        mean_motion_rad_per_s = (
            record.mean_motion_rev_per_day * 2.0 * pi / 86400.0
        )
        semimajor_axis = (
            _EARTH_GRAVITATIONAL_PARAMETER_KM3_S2
            / (mean_motion_rad_per_s * mean_motion_rad_per_s)
        ) ** (1.0 / 3.0)
        perigee = semimajor_axis * (1.0 - record.eccentricity)
        apogee = semimajor_axis * (1.0 + record.eccentricity)
        if (
            perigee
            <= _EARTH_EQUATORIAL_RADIUS_KM
            + policy.minimum_perigee_altitude_km
        ):
            return self._indeterminate(
                record,
                "perigee shell is below the validated altitude domain",
                interval_seconds=interval_seconds,
            )

        try:
            propagator = Sgp4TemePropagator(
                record,
                snapshot_sha256=query.snapshot.manifest.content_sha256,
            )
            state = SatelliteTopocentricTransformer().transform(
                propagator.propagate(query.interval.start),
                query.observer,
            )
        except Exception as error:
            return self._indeterminate(
                record,
                "initial accepted-state evaluation failed closed "
                f"({type(error).__name__})",
                interval_seconds=interval_seconds,
            )

        if (
            abs(state.teme_state.element_age_days)
            > policy.max_abs_element_age_days
        ):
            return self._indeterminate(
                record,
                "element age exceeds the validated cone-shell domain",
                interval_seconds=interval_seconds,
            )

        kepler_perigee_speed = sqrt(
            _EARTH_GRAVITATIONAL_PARAMETER_KM3_S2
            * (2.0 / perigee - 1.0 / semimajor_axis)
        )
        relative_speed_bound = (
            policy.orbital_speed_safety_factor * kepler_perigee_speed
            + policy.observer_speed_bound_km_per_s
        )
        displacement_bound = relative_speed_bound * interval_seconds
        if displacement_bound >= state.range_km:
            return self._indeterminate(
                record,
                "whole-interval displacement bound reaches the observer",
                interval_seconds=interval_seconds,
            )

        reachable_cap = degrees(asin(displacement_bound / state.range_km))
        field = query.field_of_view
        separation = _separation_deg(
            _unit_vector(
                state.gcrs_axis_longitude_deg,
                state.gcrs_axis_latitude_deg,
            ),
            _unit_vector(
                field.center_longitude_deg,
                field.center_latitude_deg,
            ),
        )
        threshold = (
            field.angular_radius_deg
            + query.angular_tolerance_deg
            + policy.numerical_margin_deg
            + reachable_cap
        )
        outcome = "reject" if separation > threshold else "retain"
        inequality = (
            f"{separation:.12g} deg > {threshold:.12g} deg"
            if outcome == "reject"
            else f"{separation:.12g} deg <= {threshold:.12g} deg"
        )
        return ConeShellDecision(
            norad_catalog_id=record.norad_catalog_id,
            outcome=outcome,
            reason=(
                "conservative field-cone separation rejects the orbital shell"
                if outcome == "reject"
                else "reachable cone overlaps the closed field bound"
            ),
            initial_field_separation_deg=separation,
            reachable_cap_deg=reachable_cap,
            rejection_threshold_deg=threshold,
            semimajor_axis_km=semimajor_axis,
            perigee_radius_km=perigee,
            apogee_radius_km=apogee,
            relative_speed_bound_km_per_s=relative_speed_bound,
            interval_seconds=interval_seconds,
            provenance=(
                CONE_SHELL_IMPLEMENTATION,
                query.snapshot.manifest.snapshot_id,
                record.source_record_sha256,
                "initial state uses accepted SGP4/WGS-72 and installed-IERS-A "
                "topocentric chain",
                "whole-interval relative displacement bound",
                inequality,
            ),
        )

    def select(self, query):
        """Return ordered tri-state evidence without solving crossings."""
        if not isinstance(query, LocalSatelliteCrossingQuery):
            raise TypeError("query must be a LocalSatelliteCrossingQuery.")
        interval_seconds = (
            _instant(query.interval.stop) - _instant(query.interval.start)
        ).total_seconds()
        decisions = tuple(
            self._select_record(query, record, interval_seconds)
            for record in query.snapshot.records
        )
        return ConeShellSelection(
            snapshot_sha256=query.snapshot.manifest.content_sha256,
            field_id=query.field_of_view.field_id,
            interval_start=query.interval.start,
            interval_stop=query.interval.stop,
            decisions=decisions,
        )
