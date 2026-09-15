"""Canonical immutable OMM/GP satellite element records."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from math import isfinite
import re
from typing import Mapping


_REQUIRED_KEYS = frozenset(
    {
        "OBJECT_NAME",
        "OBJECT_ID",
        "NORAD_CAT_ID",
        "CLASSIFICATION_TYPE",
        "EPOCH",
        "MEAN_MOTION",
        "ECCENTRICITY",
        "INCLINATION",
        "RA_OF_ASC_NODE",
        "ARG_OF_PERICENTER",
        "MEAN_ANOMALY",
        "EPHEMERIS_TYPE",
        "ELEMENT_SET_NO",
        "REV_AT_EPOCH",
        "BSTAR",
        "MEAN_MOTION_DOT",
        "MEAN_MOTION_DDOT",
        "CENTER_NAME",
        "REF_FRAME",
        "TIME_SYSTEM",
        "MEAN_ELEMENT_THEORY",
        "source_identity",
        "source_record_sha256",
        "provenance",
    }
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def canonical_json_bytes(value) -> bytes:
    """Return the canonical UTF-8 JSON representation used by snapshots."""
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def sha256_hex(value: bytes) -> str:
    """Return a lowercase SHA-256 hexadecimal digest."""
    return sha256(value).hexdigest()


def source_record_digest(mapping: Mapping) -> str:
    """Digest one canonical source mapping, excluding its digest field."""
    payload = dict(mapping)
    payload.pop("source_record_sha256", None)
    return sha256_hex(canonical_json_bytes(payload))


def _text(value, *, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string.")
    value = value.strip()
    if not value:
        raise ValueError(f"{name} must be non-empty.")
    return value


def _integer(value, *, name: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer.")
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}.")
    return value


def _finite(value, *, name: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a finite number.")
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise TypeError(f"{name} must be a finite number.") from error
    if not isfinite(result):
        raise ValueError(f"{name} must be finite.")
    return result


def _utc(value, *, name: str) -> str:
    value = _text(value, name=name)
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as error:
        raise ValueError(f"{name} must be an ISO-8601 UTC instant.") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(
        parsed
    ):
        raise ValueError(f"{name} must be an ISO-8601 UTC instant.")
    return parsed.astimezone(timezone.utc).isoformat(
        timespec="microseconds"
    ).replace("+00:00", "Z")


def _digest(value, *, name: str) -> str:
    value = _text(value, name=name).lower()
    if not _SHA256.fullmatch(value):
        raise ValueError(
            f"{name} must contain exactly 64 hexadecimal characters."
        )
    return value


@dataclass(frozen=True)
class SatelliteElementRecord:
    """One validated canonical CCSDS OMM-compatible GP element record."""

    object_name: str
    international_designator: str
    norad_catalog_id: int
    classification: str
    epoch_utc: str
    mean_motion_rev_per_day: float
    eccentricity: float
    inclination_deg: float
    ra_of_ascending_node_deg: float
    argument_of_pericenter_deg: float
    mean_anomaly_deg: float
    bstar: float
    mean_motion_dot: float
    mean_motion_ddot: float
    ephemeris_type: int
    element_set_number: int
    revolution_number_at_epoch: int
    source_identity: str
    source_record_sha256: str
    provenance: tuple[str, ...] = field(default_factory=tuple)
    center_name: str = "EARTH"
    reference_frame: str = "TEME"
    time_system: str = "UTC"
    mean_element_theory: str = "SGP4"

    def __post_init__(self):
        for name in (
            "object_name",
            "international_designator",
            "source_identity",
        ):
            object.__setattr__(
                self, name, _text(getattr(self, name), name=name)
            )
        classification = _text(
            self.classification, name="classification"
        ).upper()
        if len(classification) != 1 or not classification.isalpha():
            raise ValueError("classification must be one alphabetic character.")
        object.__setattr__(self, "classification", classification)
        object.__setattr__(
            self, "epoch_utc", _utc(self.epoch_utc, name="epoch_utc")
        )
        for name, minimum in (
            ("norad_catalog_id", 1),
            ("ephemeris_type", 0),
            ("element_set_number", 0),
            ("revolution_number_at_epoch", 0),
        ):
            object.__setattr__(
                self,
                name,
                _integer(getattr(self, name), name=name, minimum=minimum),
            )
        for name in (
            "mean_motion_rev_per_day",
            "eccentricity",
            "inclination_deg",
            "ra_of_ascending_node_deg",
            "argument_of_pericenter_deg",
            "mean_anomaly_deg",
            "bstar",
            "mean_motion_dot",
            "mean_motion_ddot",
        ):
            object.__setattr__(
                self, name, _finite(getattr(self, name), name=name)
            )
        if self.mean_motion_rev_per_day <= 0.0:
            raise ValueError("mean_motion_rev_per_day must be positive.")
        if not 0.0 <= self.eccentricity < 1.0:
            raise ValueError("eccentricity must lie in [0, 1).")
        if not 0.0 <= self.inclination_deg <= 180.0:
            raise ValueError("inclination_deg must lie in [0, 180].")
        for name in (
            "ra_of_ascending_node_deg",
            "argument_of_pericenter_deg",
            "mean_anomaly_deg",
        ):
            if not 0.0 <= getattr(self, name) < 360.0:
                raise ValueError(f"{name} must lie in [0, 360).")
        for name, expected in (
            ("center_name", "EARTH"),
            ("reference_frame", "TEME"),
            ("time_system", "UTC"),
            ("mean_element_theory", "SGP4"),
        ):
            value = _text(getattr(self, name), name=name).upper()
            if value != expected:
                raise ValueError(f"{name} must be {expected!r}.")
            object.__setattr__(self, name, value)
        object.__setattr__(
            self,
            "source_record_sha256",
            _digest(
                self.source_record_sha256,
                name="source_record_sha256",
            ),
        )
        if isinstance(self.provenance, (str, bytes)):
            raise TypeError("provenance must be an iterable of strings.")
        object.__setattr__(
            self,
            "provenance",
            tuple(
                _text(item, name="provenance entry")
                for item in self.provenance
            ),
        )

    @classmethod
    def from_mapping(cls, mapping: Mapping):
        """Build a record from one exact canonical snapshot mapping."""
        if not isinstance(mapping, Mapping):
            raise TypeError("element record must be a mapping.")
        keys = frozenset(mapping)
        if keys != _REQUIRED_KEYS:
            missing = sorted(_REQUIRED_KEYS - keys)
            unexpected = sorted(keys - _REQUIRED_KEYS)
            raise ValueError(
                "element record keys do not match the canonical schema; "
                f"missing={missing}, unexpected={unexpected}."
            )
        expected_digest = source_record_digest(mapping)
        actual_digest = _digest(
            mapping["source_record_sha256"],
            name="source_record_sha256",
        )
        if actual_digest != expected_digest:
            raise ValueError(
                "source_record_sha256 does not match record content."
            )
        return cls(
            object_name=mapping["OBJECT_NAME"],
            international_designator=mapping["OBJECT_ID"],
            norad_catalog_id=mapping["NORAD_CAT_ID"],
            classification=mapping["CLASSIFICATION_TYPE"],
            epoch_utc=mapping["EPOCH"],
            mean_motion_rev_per_day=mapping["MEAN_MOTION"],
            eccentricity=mapping["ECCENTRICITY"],
            inclination_deg=mapping["INCLINATION"],
            ra_of_ascending_node_deg=mapping["RA_OF_ASC_NODE"],
            argument_of_pericenter_deg=mapping["ARG_OF_PERICENTER"],
            mean_anomaly_deg=mapping["MEAN_ANOMALY"],
            bstar=mapping["BSTAR"],
            mean_motion_dot=mapping["MEAN_MOTION_DOT"],
            mean_motion_ddot=mapping["MEAN_MOTION_DDOT"],
            ephemeris_type=mapping["EPHEMERIS_TYPE"],
            element_set_number=mapping["ELEMENT_SET_NO"],
            revolution_number_at_epoch=mapping["REV_AT_EPOCH"],
            center_name=mapping["CENTER_NAME"],
            reference_frame=mapping["REF_FRAME"],
            time_system=mapping["TIME_SYSTEM"],
            mean_element_theory=mapping["MEAN_ELEMENT_THEORY"],
            source_identity=mapping["source_identity"],
            source_record_sha256=actual_digest,
            provenance=tuple(mapping["provenance"]),
        )
