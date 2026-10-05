"""Validated Vallado-compatible SGP4 propagation into geometric TEME."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from importlib.metadata import version
from math import isfinite

import numpy as np
from sgp4 import omm
from sgp4.api import SGP4_ERRORS, WGS72, Satrec, accelerated, jday

from .elements import SatelliteElementRecord


def _utc_datetime(value: str, *, name: str) -> tuple[str, datetime]:
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"{name} must be a non-empty UTC string.")
    value = value.strip()
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as error:
        raise ValueError(f"{name} must be an ISO-8601 UTC instant.") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(
        parsed
    ):
        raise ValueError(f"{name} must be an ISO-8601 UTC instant.")
    parsed = parsed.astimezone(timezone.utc)
    normalized = parsed.isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )
    return normalized, parsed


def split_julian_date(value: str) -> tuple[str, float, float]:
    """Convert one UTC instant to a midnight-based split Julian date."""
    normalized, instant = _utc_datetime(value, name="evaluation_utc")
    jd, fraction = jday(
        instant.year,
        instant.month,
        instant.day,
        instant.hour,
        instant.minute,
        instant.second + instant.microsecond / 1_000_000.0,
    )
    return normalized, float(jd), float(fraction)


def _omm_fields(record: SatelliteElementRecord) -> dict[str, object]:
    epoch = record.epoch_utc.removesuffix("Z")
    return {
        "CLASSIFICATION_TYPE": record.classification,
        "OBJECT_ID": record.international_designator,
        "EPHEMERIS_TYPE": record.ephemeris_type,
        "ELEMENT_SET_NO": record.element_set_number,
        "REV_AT_EPOCH": record.revolution_number_at_epoch,
        "EPOCH": epoch,
        "ARG_OF_PERICENTER": record.argument_of_pericenter_deg,
        "BSTAR": record.bstar,
        "ECCENTRICITY": record.eccentricity,
        "INCLINATION": record.inclination_deg,
        "MEAN_ANOMALY": record.mean_anomaly_deg,
        "MEAN_MOTION_DDOT": record.mean_motion_ddot,
        "MEAN_MOTION_DOT": record.mean_motion_dot,
        "MEAN_MOTION": record.mean_motion_rev_per_day,
        "RA_OF_ASC_NODE": record.ra_of_ascending_node_deg,
        "NORAD_CAT_ID": record.norad_catalog_id,
    }


class SatellitePropagationError(RuntimeError):
    """One explicit non-zero SGP4 status."""

    def __init__(self, code: int, norad_catalog_id: int, evaluation_utc: str):
        self.code = int(code)
        self.norad_catalog_id = norad_catalog_id
        self.evaluation_utc = evaluation_utc
        self.sgp4_message = SGP4_ERRORS.get(self.code, "unknown SGP4 error")
        super().__init__(
            f"SGP4 error {self.code} for NORAD {norad_catalog_id} at "
            f"{evaluation_utc}: {self.sgp4_message}."
        )


@dataclass(frozen=True)
class SatelliteTemeState:
    """One successful geocentric geometric TEME position and velocity."""

    norad_catalog_id: int
    object_name: str
    international_designator: str
    source_record_sha256: str
    snapshot_sha256: str | None
    evaluation_utc: str
    julian_day: float
    julian_fraction: float
    element_age_days: float
    position_km: tuple[float, float, float]
    velocity_km_per_s: tuple[float, float, float]
    sgp4_version: str
    implementation: str
    gravity_model: str = "WGS-72"
    operation_mode: str = "improved"
    status_code: int = 0
    frame: str = "TEME"
    center: str = "EARTH"
    representation: str = "geocentric geometric Cartesian"
    provenance: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if self.status_code != 0:
            raise ValueError("a TEME state requires SGP4 status_code zero.")
        if self.gravity_model != "WGS-72":
            raise ValueError("gravity_model must be 'WGS-72'.")
        if self.operation_mode != "improved":
            raise ValueError("operation_mode must be 'improved'.")
        if self.frame != "TEME" or self.center != "EARTH":
            raise ValueError("state must be geocentric TEME.")
        for name in (
            "julian_day",
            "julian_fraction",
            "element_age_days",
        ):
            if not isfinite(getattr(self, name)):
                raise ValueError(f"{name} must be finite.")
        if not 0.0 <= self.julian_fraction < 1.0:
            raise ValueError("julian_fraction must lie in [0, 1).")
        for name in ("position_km", "velocity_km_per_s"):
            values = tuple(float(item) for item in getattr(self, name))
            if len(values) != 3 or not all(isfinite(item) for item in values):
                raise ValueError(f"{name} must contain three finite values.")
            object.__setattr__(self, name, values)
        object.__setattr__(self, "provenance", tuple(self.provenance))
        object.__setattr__(self, "warnings", tuple(self.warnings))


class Sgp4TemePropagator:
    """Map one canonical element record to successful typed TEME states."""

    def __init__(
        self,
        record: SatelliteElementRecord,
        *,
        snapshot_sha256: str | None = None,
    ):
        if not isinstance(record, SatelliteElementRecord):
            raise TypeError("record must be a SatelliteElementRecord.")
        satellite = Satrec()
        omm.initialize(satellite, _omm_fields(record), WGS72)
        self._record = record
        self._satellite = satellite
        self._snapshot_sha256 = snapshot_sha256
        self._version = version("sgp4")
        self._implementation = (
            "python-sgp4 Vallado C++"
            if accelerated
            else "python-sgp4 Vallado Python"
        )
        _, self._epoch_jd, self._epoch_fraction = split_julian_date(
            record.epoch_utc
        )

    @property
    def record(self) -> SatelliteElementRecord:
        return self._record

    def _state(
        self,
        evaluation_utc: str,
        jd: float,
        fraction: float,
        code: int,
        position,
        velocity,
    ) -> SatelliteTemeState:
        if int(code) != 0:
            raise SatellitePropagationError(
                int(code),
                self._record.norad_catalog_id,
                evaluation_utc,
            )
        age = (
            float(jd) - self._epoch_jd
            + (float(fraction) - self._epoch_fraction)
        )
        return SatelliteTemeState(
            norad_catalog_id=self._record.norad_catalog_id,
            object_name=self._record.object_name,
            international_designator=self._record.international_designator,
            source_record_sha256=self._record.source_record_sha256,
            snapshot_sha256=self._snapshot_sha256,
            evaluation_utc=evaluation_utc,
            julian_day=float(jd),
            julian_fraction=float(fraction),
            element_age_days=age,
            position_km=tuple(position),
            velocity_km_per_s=tuple(velocity),
            sgp4_version=self._version,
            implementation=self._implementation,
            provenance=(
                "Mapped from canonical OMM fields with explicit WGS-72.",
                self._record.source_identity,
            ),
        )

    def propagate(self, evaluation_utc: str) -> SatelliteTemeState:
        """Propagate one UTC instant with split Julian-date input."""
        normalized, jd, fraction = split_julian_date(evaluation_utc)
        code, position, velocity = self._satellite.sgp4(jd, fraction)
        return self._state(
            normalized,
            jd,
            fraction,
            code,
            position,
            velocity,
        )

    def propagate_many(
        self, evaluation_instants_utc
    ) -> tuple[SatelliteTemeState, ...]:
        """Propagate ordered UTC instants with accelerated parity if present."""
        converted = tuple(
            split_julian_date(value) for value in evaluation_instants_utc
        )
        if not converted:
            return ()
        if accelerated and hasattr(self._satellite, "sgp4_array"):
            jd = np.asarray([item[1] for item in converted], dtype=float)
            fraction = np.asarray(
                [item[2] for item in converted], dtype=float
            )
            codes, positions, velocities = self._satellite.sgp4_array(
                jd, fraction
            )
            return tuple(
                self._state(
                    converted[index][0],
                    jd[index],
                    fraction[index],
                    codes[index],
                    positions[index],
                    velocities[index],
                )
                for index in range(len(converted))
            )
        return tuple(self.propagate(item[0]) for item in converted)
