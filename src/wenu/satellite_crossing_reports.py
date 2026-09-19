"""Canonical immutable reports for exact local satellite crossings."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from importlib import resources
import json
from math import isfinite
import re

from wenu.satellite_crossings import SatelliteCrossingResult
from wenu.satellites.crossing_batch import (
    MultiFieldCrossingPolicy,
    MultiFieldCrossingResult,
)


EXACT_REPORT_SCHEMA_VERSION = 1
EXACT_REPORT_DOCUMENT_KIND = "exact_satellite_crossing_report"
EXACT_REPORT_PRODUCT = "wenu.artificial_satellite_exact_crossing_report"
EXACT_REPORT_STATUS = (
    "geometric exact local crossings — visibility not evaluated"
)
EXACT_REPORT_MODEL_IMPLEMENTATION = "wenu exact crossing report model v1"
EXACT_REPORT_ENCODER_IMPLEMENTATION = "wenu exact crossing JSON encoder v1"
_SCHEMA_RESOURCE = "satellite_exact_crossing_report_v1.schema.json"
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$")


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


def _utc(value, *, name):
    from wenu.satellite_crossings import _utc_instant

    result = _utc_instant(value, name=name)
    if not _UTC.fullmatch(result):
        raise ValueError(f"{name} must use UTC microseconds and Z.")
    return result


def _strings(values, *, name):
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{name} must be an iterable of strings.")
    result = tuple(values)
    if any(not isinstance(value, str) or not value.strip() for value in result):
        raise ValueError(f"{name} entries must be non-empty strings.")
    return result


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


def _observer_document(observer):
    return {
        "earth_orientation_policy": observer.earth_orientation_policy,
        "elevation_m": observer.elevation_m,
        "latitude_deg": observer.latitude_deg,
        "longitude_deg": observer.longitude_deg,
        "observer_id": observer.observer_id,
        "refraction_policy": observer.refraction_policy,
    }


def _manifest_document(manifest):
    return {
        "builder_identity": manifest.builder_identity,
        "content_sha256": manifest.content_sha256,
        "created_utc": manifest.created_utc,
        "provenance": list(manifest.provenance),
        "provider_policy_checked_utc": manifest.provider_policy_checked_utc,
        "provider_policy_url": manifest.provider_policy_url,
        "record_count": manifest.record_count,
        "records_file": manifest.records_file,
        "schema_version": manifest.schema_version,
        "snapshot_id": manifest.snapshot_id,
        "source_format": manifest.source_format,
        "source_identity": manifest.source_identity,
        "source_url": manifest.source_url,
        "warnings": list(manifest.warnings),
    }


def _snapshot_document(snapshot):
    result = _manifest_document(snapshot.manifest)
    epochs = tuple(record.epoch_utc for record in snapshot.records)
    result["minimum_element_epoch"] = min(epochs)
    result["maximum_element_epoch"] = max(epochs)
    return result


def _policy_document(policy, field_count):
    return {
        "admitted_snapshot_ids": list(policy.admitted_snapshot_ids),
        "certification_time_tolerance_seconds": (
            policy.certification_time_tolerance_seconds
        ),
        "field_count": field_count,
        "max_interval_seconds": policy.max_interval_seconds,
        "maximum_airmass": policy.maximum_airmass,
        "processing_chunk_size": policy.processing_chunk_size,
        "sky_motion_bound_deg_per_s": policy.sky_motion_bound_deg_per_s,
    }


def _airmass_document(value):
    return {
        "certified_lower_bound_deg": value.certified_lower_bound_deg,
        "earth_orientation_sha256": list(value.earth_orientation_sha256),
        "evaluation_count": value.evaluation_count,
        "field_id": value.field_id,
        "maximum_airmass": value.maximum_airmass,
        "minimum_altitude_deg": value.minimum_altitude_deg,
        "provenance": list(value.provenance),
    }


def _acceleration_document(value):
    selection = value.selection
    return {
        "exact_solver_norad_catalog_ids": list(
            value.exact_solver_norad_catalog_ids
        ),
        "fallback_reason": value.fallback_reason,
        "fallback_to_exhaustive": value.fallback_to_exhaustive,
        "implementation": value.implementation,
        "rejected_norad_catalog_ids": list(
            value.rejected_norad_catalog_ids
        ),
        "selection_implementation": (
            None if selection is None else selection.implementation
        ),
        "snapshot_sha256": value.snapshot_sha256,
    }


def _crossing_document(crossing, acceleration):
    identity = crossing.candidate.satellite
    return {
        "acceleration_provenance": [
            acceleration.implementation,
            *(
                ()
                if acceleration.selection is None
                else (acceleration.selection.implementation,)
            ),
        ],
        "angular_rate_deg_per_s": crossing.angular_rate_deg_per_s,
        "apparent_magnitude": None,
        "closest_approach_deg": crossing.closest_approach_deg,
        "closest_approach_instant": crossing.closest_approach_instant,
        "detector_effect": None,
        "element_epoch": crossing.candidate.element_epoch,
        "entry_instant": crossing.entry_instant,
        "exact_track_samples": None,
        "exit_instant": crossing.exit_instant,
        "field_id": crossing.candidate.field_of_view.field_id,
        "illumination": None,
        "international_designator": identity.international_designator,
        "classification": identity.classification,
        "norad_catalog_id": identity.norad_catalog_id,
        "object_name": identity.object_name,
        "orbit_solution_id": crossing.candidate.orbit_solution_id,
        "oracle_provenance": list(
            crossing.candidate.provenance + crossing.provenance
        ),
        "range_km": crossing.range_km,
        "snapshot_sha256": crossing.candidate.snapshot_sha256,
        "source_provider": crossing.candidate.source_provider,
        "time_in_field_seconds": crossing.time_in_field_seconds,
        "warnings": list(
            crossing.candidate.warnings + crossing.warnings
        ),
    }


def _field_document(result):
    query = result.query
    field = query.field_of_view
    crossings = tuple(result.crossings)
    return {
        "acceleration": _acceleration_document(result.acceleration_evidence),
        "airmass_admission": _airmass_document(result.airmass_admission),
        "angular_tolerance_deg": query.angular_tolerance_deg,
        "crossing_count": len(crossings),
        "crossings": [
            _crossing_document(value, result.acceleration_evidence)
            for value in crossings
        ],
        "field_of_view": {
            "angular_radius_deg": field.angular_radius_deg,
            "boundary": field.boundary,
            "center_latitude_deg": field.center_latitude_deg,
            "center_longitude_deg": field.center_longitude_deg,
            "coordinate_spec": _coordinate_document(field.coordinate_spec),
            "field_id": field.field_id,
        },
        "field_id": field.field_id,
        "interval": {
            "boundary": query.interval.boundary,
            "start_utc": query.interval.start,
            "stop_utc": query.interval.stop,
            "time_scale": query.interval.time_scale,
        },
        "time_tolerance_seconds": query.time_tolerance_seconds,
        "warnings": [],
    }


def _reject_constant(value):
    raise ValueError(f"non-finite JSON number {value!r} is forbidden.")


def _pairs(values):
    result = {}
    for key, value in values:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key!r}.")
        result[key] = value
    return result


def _schema():
    text = resources.files("wenu.data").joinpath(_SCHEMA_RESOURCE).read_text(
        encoding="utf-8"
    )
    return json.loads(text, object_pairs_hook=_pairs, parse_constant=_reject_constant)


def _resolve(schema, root):
    reference = schema.get("$ref")
    if reference is None:
        return schema
    if not reference.startswith("#/$defs/"):
        raise ValueError("report schema contains an unsupported reference.")
    return root["$defs"][reference.rsplit("/", 1)[1]]


def _validate_schema(value, schema, root, path="$"):
    schema = _resolve(schema, root)
    if "const" in schema and value != schema["const"]:
        raise ValueError(f"{path} does not match the schema constant.")
    types = schema.get("type")
    if isinstance(types, str):
        types = (types,)
    elif types is not None:
        types = tuple(types)
    matches = {
        "null": value is None,
        "boolean": isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and isfinite(value)
        ),
        "string": isinstance(value, str),
        "array": isinstance(value, list),
        "object": isinstance(value, dict),
    }
    if types is not None and not any(matches.get(item, False) for item in types):
        raise ValueError(f"{path} has the wrong JSON type.")
    if value is None:
        return
    if isinstance(value, dict):
        required = set(schema.get("required", ()))
        missing = required - set(value)
        if missing:
            raise ValueError(f"{path} is missing required keys: {sorted(missing)}.")
        properties = schema.get("properties", {})
        unknown = set(value) - set(properties)
        if schema.get("additionalProperties") is False and unknown:
            raise ValueError(f"{path} contains unknown keys: {sorted(unknown)}.")
        for key, item in value.items():
            if key in properties:
                _validate_schema(item, properties[key], root, f"{path}.{key}")
    elif isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            raise ValueError(f"{path} contains too few entries.")
        if schema.get("uniqueItems") and len({_canonical(x) for x in value}) != len(value):
            raise ValueError(f"{path} entries must be unique.")
        if "items" in schema:
            for index, item in enumerate(value):
                _validate_schema(item, schema["items"], root, f"{path}[{index}]")
    elif isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            raise ValueError(f"{path} is too short.")
        if "pattern" in schema and re.fullmatch(schema["pattern"], value) is None:
            raise ValueError(f"{path} does not match the required lexical form.")
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise ValueError(f"{path} is below the allowed minimum.")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            raise ValueError(f"{path} is not above the required minimum.")


def _semantic_validation(document):
    if not _DIGEST.fullmatch(document["report_identity_sha256"]):
        raise ValueError("report_identity_sha256 is invalid.")
    payload = dict(document)
    claimed = payload.pop("report_identity_sha256")
    actual = sha256(_canonical(payload).encode("utf-8")).hexdigest()
    if claimed != actual:
        raise ValueError("report_identity_sha256 does not match the payload.")
    _utc(document["created_utc"], name="created_utc")
    observer = document["observer"]
    snapshot = document["snapshot"]
    fields = document["fields"]
    if document["batch"]["field_count"] != len(fields):
        raise ValueError("batch field_count does not match fields.")
    field_ids = [field["field_id"] for field in fields]
    if len(set(field_ids)) != len(field_ids):
        raise ValueError("field identifiers must be unique.")
    for field in fields:
        _utc(field["interval"]["start_utc"], name="interval start")
        _utc(field["interval"]["stop_utc"], name="interval stop")
        if field["field_of_view"]["field_id"] != field["field_id"]:
            raise ValueError("field identity does not match field_of_view.")
        if field["airmass_admission"]["field_id"] != field["field_id"]:
            raise ValueError("field identity does not match airmass admission.")
        if field["crossing_count"] != len(field["crossings"]):
            raise ValueError("crossing_count does not match crossings.")
        start = field["interval"]["start_utc"]
        stop = field["interval"]["stop_utc"]
        ordered = []
        visits = set()
        identities = {}
        acceleration = field["acceleration"]
        partition = (
            acceleration["rejected_norad_catalog_ids"]
            + acceleration["exact_solver_norad_catalog_ids"]
        )
        if len(partition) != snapshot["record_count"] or len(set(partition)) != len(partition):
            raise ValueError("acceleration evidence does not partition the snapshot.")
        for crossing in field["crossings"]:
            if crossing["field_id"] != field["field_id"]:
                raise ValueError("crossing belongs to another field.")
            if crossing["snapshot_sha256"] != snapshot["content_sha256"]:
                raise ValueError("crossing belongs to another snapshot.")
            if any(crossing[name] is not None for name in (
                "illumination", "apparent_magnitude", "detector_effect",
                "exact_track_samples",
            )):
                raise ValueError("version 1 future-science values must be null.")
            entry = crossing["entry_instant"]
            closest = crossing["closest_approach_instant"]
            exit_ = crossing["exit_instant"]
            for name, instant in (
                ("element epoch", crossing["element_epoch"]),
                ("entry instant", entry),
                ("closest approach instant", closest),
                ("exit instant", exit_),
            ):
                _utc(instant, name=name)
            if not start <= entry <= closest <= exit_ <= stop:
                raise ValueError("crossing instants violate interval ordering.")
            if crossing["closest_approach_deg"] > field["field_of_view"]["angular_radius_deg"]:
                raise ValueError("crossing closest approach lies outside the field.")
            key = (crossing["norad_catalog_id"], entry)
            if key in visits:
                raise ValueError("duplicate connected crossing visit.")
            visits.add(key)
            ordered.append(key)
            identity = (
                crossing["object_name"],
                crossing["international_designator"],
                crossing["classification"],
                crossing["orbit_solution_id"],
                crossing["element_epoch"],
            )
            previous = identities.setdefault(crossing["norad_catalog_id"], identity)
            if previous != identity:
                raise ValueError("one NORAD identity has inconsistent element identity.")
        if ordered != sorted(ordered):
            raise ValueError("crossings must be ordered by NORAD identifier and entry.")
    if not isinstance(observer, dict):
        raise ValueError("observer must be an object.")


def _validated_document(document):
    schema = _schema()
    _validate_schema(document, schema, schema)
    _semantic_validation(document)
    return document


@dataclass(frozen=True)
class ExactSatelliteCrossingReport:
    """One immutable exact-local report with canonical identity."""

    _canonical_document: str

    def __post_init__(self):
        document = json.loads(
            self._canonical_document,
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
        )
        _validated_document(document)
        if _canonical(document) != self._canonical_document:
            raise ValueError("_canonical_document must use canonical JSON.")

    @classmethod
    def _from_document(cls, document):
        _validated_document(document)
        return cls(_canonical(document))

    @classmethod
    def from_results(
        cls,
        results,
        *,
        policy,
        created_utc,
        wenu_version,
        crossing_oracle_implementation,
        acceleration_implementation,
        batch_coordinator_implementation,
    ):
        """Build a report from already computed ordered exact results."""
        results = tuple(results)
        if not results or not all(
            isinstance(value, MultiFieldCrossingResult) for value in results
        ):
            raise TypeError("results must contain MultiFieldCrossingResult values.")
        if not isinstance(policy, MultiFieldCrossingPolicy):
            raise TypeError("policy must be a MultiFieldCrossingPolicy.")
        first = results[0].query
        observer = first.observer
        snapshot = first.snapshot
        records_by_id = snapshot.by_norad_catalog_id
        field_ids = [value.field_id for value in results]
        if len(set(field_ids)) != len(field_ids):
            raise ValueError("field identifiers must be unique.")
        fields = []
        for value in results:
            query = value.query
            if query.observer != observer or query.snapshot != snapshot:
                raise ValueError("all results must share observer and snapshot.")
            if value.airmass_admission.field_id != value.field_id:
                raise ValueError("airmass admission belongs to another field.")
            evidence = value.acceleration_evidence
            if (
                evidence.field_id != value.field_id
                or evidence.snapshot_sha256 != snapshot.manifest.content_sha256
                or evidence.interval_start != query.interval.start
                or evidence.interval_stop != query.interval.stop
            ):
                raise ValueError("acceleration evidence belongs to another query.")
            crossings = tuple(value.crossings)
            if not all(isinstance(item, SatelliteCrossingResult) for item in crossings):
                raise TypeError("crossings must contain SatelliteCrossingResult values.")
            expected_order = tuple(sorted(
                crossings,
                key=lambda item: (
                    item.candidate.satellite.norad_catalog_id,
                    item.entry_instant,
                ),
            ))
            if crossings != expected_order:
                raise ValueError("crossings must use accepted oracle order.")
            for crossing in crossings:
                candidate = crossing.candidate
                if (
                    candidate.observer != observer
                    or candidate.field_of_view != query.field_of_view
                    or candidate.interval != query.interval
                    or candidate.snapshot_sha256 != snapshot.manifest.content_sha256
                ):
                    raise ValueError("crossing context does not match its result.")
                record = records_by_id.get(candidate.satellite.norad_catalog_id)
                if record is None:
                    raise ValueError("crossing NORAD identity is absent from snapshot.")
                if (
                    candidate.satellite.object_name != record.object_name
                    or candidate.satellite.international_designator
                    != record.international_designator
                    or candidate.satellite.classification != record.classification
                    or candidate.orbit_solution_id != record.source_identity
                    or candidate.element_epoch != record.epoch_utc
                ):
                    raise ValueError("crossing element identity is inconsistent with snapshot.")
            fields.append(_field_document(value))
        implementations = {
            "acceleration": acceleration_implementation,
            "batch_coordinator": batch_coordinator_implementation,
            "crossing_oracle": crossing_oracle_implementation,
            "encoder": EXACT_REPORT_ENCODER_IMPLEMENTATION,
            "report_model": EXACT_REPORT_MODEL_IMPLEMENTATION,
            "wenu_version": wenu_version,
        }
        _strings(implementations.values(), name="implementation identities")
        document = {
            "batch": _policy_document(policy, len(fields)),
            "created_utc": _utc(created_utc, name="created_utc"),
            "document_kind": EXACT_REPORT_DOCUMENT_KIND,
            "fields": fields,
            "implementations": implementations,
            "observer": _observer_document(observer),
            "product": EXACT_REPORT_PRODUCT,
            "schema_version": EXACT_REPORT_SCHEMA_VERSION,
            "scientific_status": EXACT_REPORT_STATUS,
            "snapshot": _snapshot_document(snapshot),
        }
        document["report_identity_sha256"] = sha256(
            _canonical(document).encode("utf-8")
        ).hexdigest()
        return cls._from_document(document)

    @classmethod
    def from_json(cls, value):
        """Decode strict UTF-8 JSON and verify schema, semantics, and digest."""
        if isinstance(value, bytes):
            try:
                value = value.decode("utf-8")
            except UnicodeDecodeError as error:
                raise ValueError("report bytes must be UTF-8.") from error
        if not isinstance(value, str):
            raise TypeError("report JSON must be text or UTF-8 bytes.")
        try:
            document = json.loads(
                value,
                object_pairs_hook=_pairs,
                parse_constant=_reject_constant,
            )
        except json.JSONDecodeError as error:
            raise ValueError("report must be valid JSON.") from error
        return cls._from_document(document)

    @property
    def document(self):
        """Return a fresh JSON-compatible copy of the report document."""
        return json.loads(self._canonical_document)

    @property
    def report_identity_sha256(self):
        return self.document["report_identity_sha256"]

    def to_json(self):
        """Return deterministic UTF-8 JSON text with one final newline."""
        return _pretty(self.document)
