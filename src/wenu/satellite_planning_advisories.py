"""Offline observatory-neutral advisories from exact satellite reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from math import isfinite
import re

from wenu.satellite_crossing_reports import ExactSatelliteCrossingReport
from wenu.satellite_crossings import (
    SatelliteObserver,
    _instant_datetime,
    _utc_instant,
)


PLANNING_ADVISORY_SCHEMA_VERSION = 1
PLANNING_ADVISORY_DOCUMENT_KIND = "wenu.observatory-planning-advisory"
PLANNING_ADVISORY_PRODUCT = "wenu.offline_satellite_planning_advisory"
PLANNING_ADVISORY_STATUS = (
    "geometric interval overlap only — illumination, brightness, detector "
    "effect, and operational disposition unknown"
)
PLANNING_ADVISORY_IMPLEMENTATION = "wenu offline planning advisory v1"
GENERAL_PLANNING_PROFILE = "general"
GENERAL_PLANNING_PROFILE_SCHEMA_VERSION = 1
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


class PlanningAdvisoryValidationError(ValueError):
    """Stable typed rejection for planning-advisory input."""

    def __init__(self, code, message):
        self.code = code
        super().__init__(f"{code}: {message}")


def _fail(code, message):
    raise PlanningAdvisoryValidationError(code, message)


def _canonical(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _pretty(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def _text(value, *, name):
    if not isinstance(value, str) or not value.strip():
        _fail("invalid_text", f"{name} must be non-empty text.")
    normalized = value.strip()
    if _CONTROL.search(normalized):
        _fail("invalid_text", f"{name} contains control characters.")
    return normalized


def _format_utc(value):
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _finite(value, *, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail("invalid_number", f"{name} must be a finite number.")
    result = float(value)
    if not isfinite(result):
        _fail("invalid_number", f"{name} must be a finite number.")
    return result


def _utc(value, *, name):
    try:
        return _utc_instant(value, name=name)
    except (TypeError, ValueError) as error:
        _fail("invalid_utc", str(error))


def _digest(value, *, name):
    if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
        _fail("invalid_identity", f"{name} must be a lowercase SHA-256 digest.")
    return value


def _labels(value):
    if isinstance(value, dict):
        value = tuple(value.items())
    if isinstance(value, (str, bytes)):
        _fail("invalid_labels", "labels must contain key/value pairs.")
    try:
        result = tuple(value)
    except TypeError:
        _fail("invalid_labels", "labels must contain key/value pairs.")
    normalized = []
    keys = set()
    for item in result:
        if not isinstance(item, (tuple, list)) or len(item) != 2:
            _fail("invalid_labels", "each label must be a key/value pair.")
        key = _text(item[0], name="label key")
        label_value = _text(item[1], name=f"label {key!r}")
        if key in keys:
            _fail("duplicate_label", f"label key {key!r} is duplicated.")
        keys.add(key)
        normalized.append((key, label_value))
    return tuple(normalized)


def _observer_document(observer):
    return {
        "earth_orientation_policy": observer.earth_orientation_policy,
        "elevation_m": observer.elevation_m,
        "latitude_deg": observer.latitude_deg,
        "longitude_deg": observer.longitude_deg,
        "observer_id": observer.observer_id,
        "refraction_policy": observer.refraction_policy,
    }


def _expect_keys(value, expected, *, path):
    if not isinstance(value, dict):
        _fail("invalid_document", f"{path} must be an object.")
    missing = set(expected) - set(value)
    unknown = set(value) - set(expected)
    if missing:
        _fail("missing_key", f"{path} is missing keys: {sorted(missing)}.")
    if unknown:
        _fail("unknown_key", f"{path} contains unknown keys: {sorted(unknown)}.")


def _pairs(values):
    result = {}
    for key, value in values:
        if key in result:
            _fail("duplicate_key", f"duplicate JSON object key: {key!r}.")
        result[key] = value
    return result


def _reject_constant(value):
    _fail("nonfinite_number", f"non-finite JSON number {value!r} is forbidden.")


@dataclass(frozen=True)
class PlanningObservationUnit:
    """One caller-owned half-open planned UTC interval."""

    observation_unit_id: str
    field_id: str
    start_utc: str
    stop_utc: str
    labels: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self):
        object.__setattr__(
            self,
            "observation_unit_id",
            _text(self.observation_unit_id, name="observation_unit_id"),
        )
        object.__setattr__(
            self,
            "field_id",
            _text(self.field_id, name="field_id"),
        )
        start = _utc(self.start_utc, name="start_utc")
        stop = _utc(self.stop_utc, name="stop_utc")
        if _instant_datetime(start) >= _instant_datetime(stop):
            _fail(
                "invalid_interval",
                "planned intervals must be non-empty and increasing.",
            )
        object.__setattr__(self, "start_utc", start)
        object.__setattr__(self, "stop_utc", stop)
        object.__setattr__(self, "labels", _labels(self.labels))


@dataclass(frozen=True)
class ObservatoryPlanningContext:
    """Immutable external context for one offline advisory."""

    planning_context_id: str
    observer: SatelliteObserver
    observation_units: tuple[PlanningObservationUnit, ...]
    profile_id: str = GENERAL_PLANNING_PROFILE
    profile_schema_version: int = GENERAL_PLANNING_PROFILE_SCHEMA_VERSION

    def __post_init__(self):
        object.__setattr__(
            self,
            "planning_context_id",
            _text(self.planning_context_id, name="planning_context_id"),
        )
        if not isinstance(self.observer, SatelliteObserver):
            raise TypeError("observer must be a SatelliteObserver.")
        profile = _text(self.profile_id, name="profile_id").lower()
        if (
            profile != GENERAL_PLANNING_PROFILE
            or self.profile_schema_version
            != GENERAL_PLANNING_PROFILE_SCHEMA_VERSION
        ):
            _fail(
                "unsupported_profile",
                "only general profile version 1 is supported.",
            )
        object.__setattr__(self, "profile_id", profile)
        if isinstance(self.profile_schema_version, bool) or not isinstance(
            self.profile_schema_version, int
        ):
            _fail(
                "unsupported_profile",
                "profile_schema_version must be integer 1.",
            )
        units = tuple(self.observation_units)
        if not units or not all(
            isinstance(item, PlanningObservationUnit) for item in units
        ):
            _fail(
                "invalid_observation_units",
                "observation_units must contain at least one planning unit.",
            )
        identities = [item.observation_unit_id for item in units]
        if len(set(identities)) != len(identities):
            _fail(
                "duplicate_observation_unit",
                "observation_unit_id values must be unique.",
            )
        object.__setattr__(self, "observation_units", units)


def _unit_document(unit):
    return {
        "field_id": unit.field_id,
        "labels": dict(unit.labels),
        "observation_unit_id": unit.observation_unit_id,
        "start_utc": unit.start_utc,
        "stop_utc": unit.stop_utc,
    }


def _context_document(context):
    return {
        "observer": _observer_document(context.observer),
        "observation_units": [
            _unit_document(value) for value in context.observation_units
        ],
        "planning_context_id": context.planning_context_id,
        "profile_id": context.profile_id,
        "profile_schema_version": context.profile_schema_version,
    }


def _typed_observer(document):
    _expect_keys(
        document,
        {
            "earth_orientation_policy",
            "elevation_m",
            "latitude_deg",
            "longitude_deg",
            "observer_id",
            "refraction_policy",
        },
        path="observer",
    )
    try:
        return SatelliteObserver(**document)
    except (TypeError, ValueError) as error:
        _fail("observer_mismatch", str(error))


def _typed_context(document):
    _expect_keys(
        document,
        {
            "observer",
            "observation_units",
            "planning_context_id",
            "profile_id",
            "profile_schema_version",
        },
        path="planning_context",
    )
    if not isinstance(document["observation_units"], list):
        _fail(
            "invalid_observation_units",
            "planning_context.observation_units must be an array.",
        )
    units = []
    for index, item in enumerate(document["observation_units"]):
        _expect_keys(
            item,
            {
                "field_id",
                "labels",
                "observation_unit_id",
                "start_utc",
                "stop_utc",
            },
            path=f"planning_context.observation_units[{index}]",
        )
        if not isinstance(item["labels"], dict):
            _fail("invalid_labels", "labels must be an object.")
        units.append(
            PlanningObservationUnit(
                observation_unit_id=item["observation_unit_id"],
                field_id=item["field_id"],
                start_utc=item["start_utc"],
                stop_utc=item["stop_utc"],
                labels=tuple(item["labels"].items()),
            )
        )
    context = ObservatoryPlanningContext(
        planning_context_id=document["planning_context_id"],
        observer=_typed_observer(document["observer"]),
        observation_units=tuple(units),
        profile_id=document["profile_id"],
        profile_schema_version=document["profile_schema_version"],
    )
    if _context_document(context) != document:
        _fail(
            "noncanonical_context",
            "planning context is not in canonical normalized form.",
        )
    return context


_ROW_KEYS = {
    "closest_approach_deg",
    "closest_approach_instant",
    "crossing_entry_utc",
    "crossing_exit_utc",
    "elevation_m",
    "field_geometry_sha256",
    "field_id",
    "latitude_deg",
    "longitude_deg",
    "norad_catalog_id",
    "object_name",
    "observation_unit_id",
    "orbit_solution_id",
    "overlap_duration_seconds",
    "overlap_start_utc",
    "overlap_stop_utc",
    "planned_start_utc",
    "planned_stop_utc",
    "planning_context_id",
    "profile_id",
    "report_identity_sha256",
    "scientific_status",
    "snapshot_identity_sha256",
    "observer_id",
}


def _validate_row(row, *, index, document, context, units):
    _expect_keys(row, _ROW_KEYS, path=f"rows[{index}]")
    for name in (
        "planning_context_id",
        "observation_unit_id",
        "profile_id",
        "field_id",
        "observer_id",
        "object_name",
        "scientific_status",
    ):
        _text(row[name], name=f"rows[{index}].{name}")
    for name in (
        "report_identity_sha256",
        "snapshot_identity_sha256",
        "field_geometry_sha256",
    ):
        _digest(row[name], name=f"rows[{index}].{name}")
    for name in (
        "planned_start_utc",
        "planned_stop_utc",
        "crossing_entry_utc",
        "closest_approach_instant",
        "crossing_exit_utc",
        "overlap_start_utc",
        "overlap_stop_utc",
    ):
        _utc(row[name], name=f"rows[{index}].{name}")
    if isinstance(row["norad_catalog_id"], bool) or not isinstance(
        row["norad_catalog_id"], int
    ):
        _fail("invalid_row", "norad_catalog_id must be an integer.")
    if row["norad_catalog_id"] <= 0:
        _fail("invalid_row", "norad_catalog_id must be positive.")
    if row["orbit_solution_id"] is not None:
        _text(row["orbit_solution_id"], name="orbit_solution_id")
    for name in (
        "longitude_deg",
        "latitude_deg",
        "elevation_m",
        "closest_approach_deg",
        "overlap_duration_seconds",
    ):
        _finite(row[name], name=f"rows[{index}].{name}")
    if row["planning_context_id"] != context.planning_context_id:
        _fail("context_mismatch", "row planning context does not match.")
    if row["profile_id"] != context.profile_id:
        _fail("context_mismatch", "row profile does not match.")
    unit = units.get(row["observation_unit_id"])
    if unit is None or unit.field_id != row["field_id"]:
        _fail("context_mismatch", "row planning unit does not match.")
    expected_observer = _observer_document(context.observer)
    for name in ("observer_id", "longitude_deg", "latitude_deg", "elevation_m"):
        if row[name] != expected_observer[name]:
            _fail("observer_mismatch", "row observer does not match.")
    if row["report_identity_sha256"] != document[
        "source_report_identity_sha256"
    ]:
        _fail("identity_mismatch", "row report identity does not match.")
    if row["snapshot_identity_sha256"] != document[
        "snapshot_identity_sha256"
    ]:
        _fail("identity_mismatch", "row snapshot identity does not match.")
    if row["scientific_status"] != PLANNING_ADVISORY_STATUS:
        _fail("scientific_status_mismatch", "row scientific status is invalid.")
    overlap_start = max(
        _instant_datetime(row["planned_start_utc"]),
        _instant_datetime(row["crossing_entry_utc"]),
    )
    overlap_stop = min(
        _instant_datetime(row["planned_stop_utc"]),
        _instant_datetime(row["crossing_exit_utc"]),
    )
    if overlap_start >= overlap_stop:
        _fail("invalid_overlap", "row intervals do not overlap.")
    if row["overlap_start_utc"] != _format_utc(overlap_start):
        _fail("invalid_overlap", "overlap_start_utc is inconsistent.")
    if row["overlap_stop_utc"] != _format_utc(overlap_stop):
        _fail("invalid_overlap", "overlap_stop_utc is inconsistent.")
    duration = (overlap_stop - overlap_start).total_seconds()
    if row["overlap_duration_seconds"] != duration:
        _fail("invalid_overlap", "overlap duration is inconsistent.")


def _validate_document(document):
    keys = {
        "created_utc",
        "document_kind",
        "implementations",
        "planning_advisory_identity_sha256",
        "planning_context",
        "product",
        "row_count",
        "rows",
        "schema_version",
        "scientific_status",
        "snapshot_identity_sha256",
        "source_report_identity_sha256",
    }
    _expect_keys(document, keys, path="$")
    if document["document_kind"] != PLANNING_ADVISORY_DOCUMENT_KIND:
        _fail("unsupported_document", "document_kind is unsupported.")
    if document["schema_version"] != PLANNING_ADVISORY_SCHEMA_VERSION:
        _fail("unsupported_version", "schema_version is unsupported.")
    if document["product"] != PLANNING_ADVISORY_PRODUCT:
        _fail("unsupported_document", "product is unsupported.")
    if document["scientific_status"] != PLANNING_ADVISORY_STATUS:
        _fail("scientific_status_mismatch", "scientific_status is invalid.")
    _utc(document["created_utc"], name="created_utc")
    _digest(
        document["source_report_identity_sha256"],
        name="source_report_identity_sha256",
    )
    _digest(
        document["snapshot_identity_sha256"],
        name="snapshot_identity_sha256",
    )
    context = _typed_context(document["planning_context"])
    if _observer_document(context.observer) != document[
        "planning_context"
    ]["observer"]:
        _fail("observer_mismatch", "planning observer is inconsistent.")
    _expect_keys(
        document["implementations"],
        {"advisory", "wenu_version"},
        path="implementations",
    )
    for key, value in document["implementations"].items():
        _text(value, name=f"implementations.{key}")
    if not isinstance(document["rows"], list):
        _fail("invalid_rows", "rows must be an array.")
    if (
        isinstance(document["row_count"], bool)
        or not isinstance(document["row_count"], int)
        or document["row_count"] != len(document["rows"])
    ):
        _fail("invalid_rows", "row_count must match rows.")
    units = {
        item.observation_unit_id: item
        for item in context.observation_units
    }
    for index, row in enumerate(document["rows"]):
        _validate_row(
            row,
            index=index,
            document=document,
            context=context,
            units=units,
        )
    _digest(
        document["planning_advisory_identity_sha256"],
        name="planning_advisory_identity_sha256",
    )
    payload = dict(document)
    claimed = payload.pop("planning_advisory_identity_sha256")
    actual = sha256(_canonical(payload).encode("utf-8")).hexdigest()
    if claimed != actual:
        _fail(
            "identity_mismatch",
            "planning_advisory_identity_sha256 does not match the payload.",
        )


def _row(report_document, context, unit, field, crossing):
    planned_start = _instant_datetime(unit.start_utc)
    planned_stop = _instant_datetime(unit.stop_utc)
    crossing_start = _instant_datetime(crossing["entry_instant"])
    crossing_stop = _instant_datetime(crossing["exit_instant"])
    overlap_start = max(planned_start, crossing_start)
    overlap_stop = min(planned_stop, crossing_stop)
    if overlap_start >= overlap_stop:
        return None
    observer = report_document["observer"]
    geometry = field["field_of_view"]
    snapshot_identity = report_document["snapshot"]["content_sha256"]
    return {
        "closest_approach_deg": crossing["closest_approach_deg"],
        "closest_approach_instant": crossing["closest_approach_instant"],
        "crossing_entry_utc": crossing["entry_instant"],
        "crossing_exit_utc": crossing["exit_instant"],
        "elevation_m": observer["elevation_m"],
        "field_geometry_sha256": sha256(
            _canonical(geometry).encode("utf-8")
        ).hexdigest(),
        "field_id": unit.field_id,
        "latitude_deg": observer["latitude_deg"],
        "longitude_deg": observer["longitude_deg"],
        "norad_catalog_id": crossing["norad_catalog_id"],
        "object_name": crossing["object_name"],
        "observation_unit_id": unit.observation_unit_id,
        "observer_id": observer["observer_id"],
        "orbit_solution_id": crossing["orbit_solution_id"],
        "overlap_duration_seconds": (
            overlap_stop - overlap_start
        ).total_seconds(),
        "overlap_start_utc": _utc_instant(
            overlap_start, name="overlap_start_utc"
        ),
        "overlap_stop_utc": _utc_instant(
            overlap_stop, name="overlap_stop_utc"
        ),
        "planned_start_utc": unit.start_utc,
        "planned_stop_utc": unit.stop_utc,
        "planning_context_id": context.planning_context_id,
        "profile_id": context.profile_id,
        "report_identity_sha256": report_document[
            "report_identity_sha256"
        ],
        "scientific_status": PLANNING_ADVISORY_STATUS,
        "snapshot_identity_sha256": snapshot_identity,
    }


@dataclass(frozen=True)
class SatellitePlanningAdvisory:
    """One immutable, canonical, offline planning advisory."""

    _canonical_document: str

    def __post_init__(self):
        try:
            document = json.loads(
                self._canonical_document,
                object_pairs_hook=_pairs,
                parse_constant=_reject_constant,
            )
        except json.JSONDecodeError as error:
            _fail("invalid_json", str(error))
        _validate_document(document)
        if _canonical(document) != self._canonical_document:
            _fail(
                "noncanonical_document",
                "_canonical_document must use canonical JSON.",
            )

    @classmethod
    def _from_document(cls, document):
        _validate_document(document)
        return cls(_canonical(document))

    @classmethod
    def from_report(
        cls,
        report,
        *,
        context,
        created_utc,
        wenu_version,
        implementation=PLANNING_ADVISORY_IMPLEMENTATION,
    ):
        """Build one offline advisory from an already validated exact report."""
        if not isinstance(report, ExactSatelliteCrossingReport):
            raise TypeError("report must be an ExactSatelliteCrossingReport.")
        if not isinstance(context, ObservatoryPlanningContext):
            raise TypeError("context must be an ObservatoryPlanningContext.")
        report_document = report.document
        if _observer_document(context.observer) != report_document["observer"]:
            _fail(
                "observer_mismatch",
                "planning observer must exactly match the report observer.",
            )
        fields = {
            item["field_id"]: item for item in report_document["fields"]
        }
        for unit in context.observation_units:
            if unit.field_id not in fields:
                _fail(
                    "unknown_field",
                    f"field_id {unit.field_id!r} is absent from the report.",
                )
        rows = []
        for unit in context.observation_units:
            field_document = fields[unit.field_id]
            for crossing in field_document["crossings"]:
                item = _row(
                    report_document,
                    context,
                    unit,
                    field_document,
                    crossing,
                )
                if item is not None:
                    rows.append(item)
        document = {
            "created_utc": _utc(created_utc, name="created_utc"),
            "document_kind": PLANNING_ADVISORY_DOCUMENT_KIND,
            "implementations": {
                "advisory": _text(implementation, name="implementation"),
                "wenu_version": _text(wenu_version, name="wenu_version"),
            },
            "planning_context": _context_document(context),
            "product": PLANNING_ADVISORY_PRODUCT,
            "row_count": len(rows),
            "rows": rows,
            "schema_version": PLANNING_ADVISORY_SCHEMA_VERSION,
            "scientific_status": PLANNING_ADVISORY_STATUS,
            "snapshot_identity_sha256": report_document[
                "snapshot"
            ]["content_sha256"],
            "source_report_identity_sha256": report_document[
                "report_identity_sha256"
            ],
        }
        document["planning_advisory_identity_sha256"] = sha256(
            _canonical(document).encode("utf-8")
        ).hexdigest()
        return cls._from_document(document)

    @classmethod
    def from_json(cls, value):
        """Decode strict canonical UTF-8 advisory JSON."""
        if isinstance(value, bytes):
            try:
                value = value.decode("utf-8")
            except UnicodeDecodeError as error:
                _fail("invalid_utf8", "advisory bytes must be UTF-8.")
        if not isinstance(value, str):
            raise TypeError("advisory JSON must be text or UTF-8 bytes.")
        try:
            document = json.loads(
                value,
                object_pairs_hook=_pairs,
                parse_constant=_reject_constant,
            )
        except json.JSONDecodeError as error:
            _fail("invalid_json", str(error))
        if value != _pretty(document):
            _fail(
                "noncanonical_json",
                "advisory JSON must use canonical formatting.",
            )
        return cls._from_document(document)

    @property
    def document(self):
        """Return a detached JSON-compatible copy."""
        return json.loads(self._canonical_document)

    @property
    def planning_advisory_identity_sha256(self):
        return self.document["planning_advisory_identity_sha256"]

    def to_json(self):
        """Return deterministic UTF-8 JSON text with one final newline."""
        return _pretty(self.document)
