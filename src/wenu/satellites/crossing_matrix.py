"""Strict offline exhaustive/accelerated crossing-matrix evidence."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Callable, Literal

from .crossing_acceleration import AcceleratedCrossingEvidence
from .crossing_oracle import LocalSatelliteCrossingQuery
from .elements import canonical_json_bytes, sha256_hex
from .snapshot_admission import ExternalSnapshotAdmission
from .snapshots import load_snapshot_directory


CROSSING_MATRIX_IMPLEMENTATION = "wenu.satellites.crossing_matrix/1"
MATRIX_ISOLATION_IDENTITY = "fresh-subprocess-per-route-query-run/1"
MATRIX_DOCUMENT_KIND = "satellite-crossing-equivalence-report"


def _regular_bytes(path, *, name):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{name} must be an existing non-symlink file.")
    return path.read_bytes()


def _json_object(data, *, name):
    try:
        value = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{name} must be valid UTF-8 JSON.") from error
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a JSON object.")
    return value


def _digest(value, *, name):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string.")
    value = value.lower()
    if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest.")
    return value


def _plain(value):
    if is_dataclass(value):
        return _plain(asdict(value))
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(
        f"unsupported canonical matrix value: {type(value).__name__}."
    )


def _canonical_document(value):
    plain = _plain(value)
    data = canonical_json_bytes(plain)
    return plain, data, sha256_hex(data)


def _query_mapping(query):
    return {
        "snapshot": {
            "schema_version": query.snapshot.manifest.schema_version,
            "snapshot_id": query.snapshot.manifest.snapshot_id,
            "content_sha256": query.snapshot.manifest.content_sha256,
            "record_count": query.snapshot.manifest.record_count,
            "source_identity": query.snapshot.manifest.source_identity,
            "source_url": query.snapshot.manifest.source_url,
            "builder_identity": query.snapshot.manifest.builder_identity,
        },
        "observer": _plain(query.observer),
        "field_of_view": _plain(query.field_of_view),
        "interval": _plain(query.interval),
        "time_tolerance_seconds": query.time_tolerance_seconds,
        "angular_tolerance_deg": query.angular_tolerance_deg,
    }


@dataclass(frozen=True)
class MatrixSpecimenIdentity:
    """Exact admitted specimen and receipt identity for one matrix."""

    content_sha256: str
    selection_receipt_sha256: str
    parent_content_sha256: str
    record_count: int

    def __post_init__(self):
        for name in (
            "content_sha256",
            "selection_receipt_sha256",
            "parent_content_sha256",
        ):
            object.__setattr__(
                self, name, _digest(getattr(self, name), name=name)
            )
        if (
            isinstance(self.record_count, bool)
            or not isinstance(self.record_count, int)
            or self.record_count <= 0
        ):
            raise ValueError("record_count must be a positive integer.")


@dataclass(frozen=True)
class CrossingMatrixPolicy:
    """Bounded fake-data implementation and later execution policy."""

    expected_field_count: int = 10
    max_interval_seconds: float = 60.0
    warmup_count: int = 1
    measured_repetitions: int = 3

    def __post_init__(self):
        for name in (
            "expected_field_count",
            "warmup_count",
            "measured_repetitions",
        ):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value < (0 if name == "warmup_count" else 1)
            ):
                raise ValueError(f"{name} has an invalid count.")
        if (
            isinstance(self.max_interval_seconds, bool)
            or not isinstance(self.max_interval_seconds, (int, float))
            or self.max_interval_seconds <= 0
        ):
            raise ValueError("max_interval_seconds must be positive.")


@dataclass(frozen=True)
class MatrixResourceObservation:
    """One raw isolated route/query observation."""

    route: Literal["exhaustive", "accelerated"]
    field_id: str
    repetition: int
    wall_seconds: float
    cpu_seconds: float
    peak_python_bytes: int
    environment: dict
    implementation: str = MATRIX_ISOLATION_IDENTITY

    def __post_init__(self):
        if self.route not in {"exhaustive", "accelerated"}:
            raise ValueError("route must be exhaustive or accelerated.")
        if not isinstance(self.field_id, str) or not self.field_id:
            raise ValueError("field_id must be non-empty.")
        if (
            isinstance(self.repetition, bool)
            or not isinstance(self.repetition, int)
            or self.repetition < 0
        ):
            raise ValueError("repetition must be a non-negative integer.")
        for name in ("wall_seconds", "cpu_seconds"):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or value < 0
            ):
                raise ValueError(f"{name} must be non-negative.")
        if (
            isinstance(self.peak_python_bytes, bool)
            or not isinstance(self.peak_python_bytes, int)
            or self.peak_python_bytes < 0
        ):
            raise ValueError("peak_python_bytes must be non-negative.")
        if not isinstance(self.environment, dict) or not self.environment:
            raise ValueError("environment must be a non-empty mapping.")
        if self.implementation != MATRIX_ISOLATION_IDENTITY:
            raise ValueError("resource observation isolation is unsupported.")


@dataclass(frozen=True)
class MatrixRouteRun:
    """One isolated route result returned by the injected execution seam."""

    results: tuple
    resource: MatrixResourceObservation
    acceleration_evidence: AcceleratedCrossingEvidence | None = None

    def __post_init__(self):
        object.__setattr__(self, "results", tuple(self.results))
        if not isinstance(self.resource, MatrixResourceObservation):
            raise TypeError("resource must be a MatrixResourceObservation.")


class MatrixEquivalenceError(RuntimeError):
    """Fail-closed matrix scientific or evidence mismatch."""


def _validate_receipt(receipt_bytes, snapshot, expected):
    if sha256_hex(receipt_bytes) != expected.selection_receipt_sha256:
        raise ValueError("selection receipt digest does not match identity.")
    receipt = _json_object(receipt_bytes, name="selection receipt")
    if canonical_json_bytes(receipt) != receipt_bytes:
        raise ValueError("selection receipt must be canonical JSON.")
    if receipt.get("subset_canonical_records_sha256") != expected.content_sha256:
        raise ValueError("receipt subset digest does not match identity.")
    if receipt.get("actual_record_count") != expected.record_count:
        raise ValueError("receipt record count does not match identity.")
    parent = receipt.get("parent_identity")
    if not isinstance(parent, dict) or (
        parent.get("content_sha256") != expected.parent_content_sha256
    ):
        raise ValueError("receipt parent digest does not match identity.")
    if snapshot.manifest.content_sha256 != expected.content_sha256:
        raise ValueError("snapshot digest does not match matrix identity.")
    if len(snapshot.records) != expected.record_count:
        raise ValueError("snapshot count does not match matrix identity.")
    return receipt


def _file_hashes(directory, records_file):
    names = ("manifest.json", records_file, "selection-receipt.json")
    return {
        name: sha256_hex(_regular_bytes(Path(directory) / name, name=name))
        for name in names
    }


def _validate_queries(queries, snapshot, policy):
    if isinstance(queries, (str, bytes)):
        raise TypeError("queries must be an ordered iterable.")
    queries = tuple(queries)
    if len(queries) != policy.expected_field_count:
        raise ValueError(
            f"matrix requires exactly {policy.expected_field_count} fields."
        )
    if not all(isinstance(item, LocalSatelliteCrossingQuery) for item in queries):
        raise TypeError("queries must contain LocalSatelliteCrossingQuery values.")
    field_ids = tuple(item.field_of_view.field_id for item in queries)
    if len(set(field_ids)) != len(field_ids):
        raise ValueError("matrix field identifiers must be unique.")
    observer = queries[0].observer
    dates = set()
    intervals = []
    for query in queries:
        if query.snapshot != snapshot:
            raise ValueError("every matrix query must use the loaded snapshot.")
        if query.observer != observer:
            raise ValueError("every matrix query must use one observer.")
        start = query.interval.start
        stop = query.interval.stop
        dates.add(start[:10])
        intervals.append((start, stop))
        from datetime import datetime
        left = datetime.fromisoformat(start.replace("Z", "+00:00"))
        right = datetime.fromisoformat(stop.replace("Z", "+00:00"))
        if (right - left).total_seconds() > policy.max_interval_seconds:
            raise ValueError("matrix interval exceeds policy.")
    if len(dates) != 1:
        raise ValueError("matrix intervals must begin on one UTC night.")
    if len(set(intervals)) == len(intervals):
        raise ValueError("matrix requires a shared-interval research control.")
    return queries


def _validate_partition(query, evidence, exhaustive_results):
    if not isinstance(evidence, AcceleratedCrossingEvidence):
        raise MatrixEquivalenceError(
            "accelerated route did not return complete evidence."
        )
    identity = (
        query.snapshot.manifest.content_sha256,
        query.field_of_view.field_id,
        query.interval.start,
        query.interval.stop,
    )
    actual = (
        evidence.snapshot_sha256,
        evidence.field_id,
        evidence.interval_start,
        evidence.interval_stop,
    )
    if actual != identity:
        raise MatrixEquivalenceError("acceleration evidence identity mismatch.")
    if evidence.fallback_to_exhaustive:
        raise MatrixEquivalenceError("exhaustive fallback is forbidden.")
    rejected = tuple(evidence.rejected_norad_catalog_ids)
    exact = tuple(evidence.exact_solver_norad_catalog_ids)
    expected = tuple(
        record.norad_catalog_id for record in query.snapshot.records
    )
    if tuple(sorted(rejected + exact)) != expected:
        raise MatrixEquivalenceError(
            "acceleration evidence does not partition the snapshot."
        )
    if not rejected or not exact:
        raise MatrixEquivalenceError(
            "every field must exercise rejection and exact solving."
        )
    crossing_ids = {
        result.candidate.satellite.norad_catalog_id
        for result in exhaustive_results
    }
    overlap = crossing_ids.intersection(rejected)
    if overlap:
        raise MatrixEquivalenceError(
            f"rejected records have exhaustive crossings: {sorted(overlap)}."
        )
    decisions = evidence.selection.decisions if evidence.selection else ()
    counts = {
        outcome: sum(item.outcome == outcome for item in decisions)
        for outcome in ("reject", "retain", "indeterminate")
    }
    return counts


def _validate_existing(directory, report):
    root = Path(directory)
    report_bytes = _regular_bytes(
        root / "equivalence-report.json", name="equivalence report"
    )
    actual = _json_object(report_bytes, name="equivalence report")
    if canonical_json_bytes(actual) != report_bytes:
        raise ValueError("equivalence report is not canonical JSON.")
    if actual != report:
        raise ValueError("existing matrix report does not match.")
    for name, digest in report["file_sha256"].items():
        if sha256_hex(_regular_bytes(root / name, name=name)) != digest:
            raise ValueError(f"existing matrix file digest mismatch: {name}.")
    return root


def run_equivalence_matrix(
    snapshot_directory,
    output_root,
    *,
    specimen_identity,
    admission,
    queries,
    airmass_certifier,
    executor: Callable,
    policy=None,
):
    """Run strict injected matrix evidence and atomically publish success."""
    if not isinstance(specimen_identity, MatrixSpecimenIdentity):
        raise TypeError("specimen_identity must be MatrixSpecimenIdentity.")
    if not isinstance(admission, ExternalSnapshotAdmission):
        raise TypeError("admission must be ExternalSnapshotAdmission.")
    if not callable(getattr(airmass_certifier, "certify", None)):
        raise TypeError("airmass_certifier must provide certify(query).")
    if not callable(executor):
        raise TypeError("executor must be callable.")
    policy = policy or CrossingMatrixPolicy()
    if not isinstance(policy, CrossingMatrixPolicy):
        raise TypeError("policy must be CrossingMatrixPolicy.")

    snapshot_directory = Path(snapshot_directory).expanduser()
    snapshot = load_snapshot_directory(snapshot_directory)
    admission.require(snapshot)
    receipt_bytes = _regular_bytes(
        snapshot_directory / "selection-receipt.json",
        name="selection receipt",
    )
    receipt = _validate_receipt(receipt_bytes, snapshot, specimen_identity)
    before = _file_hashes(
        snapshot_directory, snapshot.manifest.records_file
    )
    queries = _validate_queries(queries, snapshot, policy)

    admissions = []
    try:
        for query in queries:
            admissions.append(airmass_certifier.certify(query))
    except Exception as error:
        raise MatrixEquivalenceError(
            f"atomic airmass admission failed: {type(error).__name__}: {error}"
        ) from error

    request_plain, request_bytes, request_digest = _canonical_document(
        [_query_mapping(query) for query in queries]
    )
    exhaustive_documents = []
    accelerated_documents = []
    evidence_documents = []
    observations = []
    aggregate_counts = {"reject": 0, "retain": 0, "indeterminate": 0}
    field_reports = []

    for field_index, query in enumerate(queries):
        for warmup in range(policy.warmup_count):
            for route in ("exhaustive", "accelerated"):
                executor(route, query, -(warmup + 1), False)

        baseline = {}
        evidence_baseline = None
        for repetition in range(policy.measured_repetitions):
            order = (
                ("exhaustive", "accelerated")
                if (field_index + repetition) % 2 == 0
                else ("accelerated", "exhaustive")
            )
            runs = {}
            for route in order:
                try:
                    run = executor(route, query, repetition, True)
                except Exception as error:
                    raise MatrixEquivalenceError(
                        f"{query.field_of_view.field_id} {route} repetition "
                        f"{repetition} failed: {type(error).__name__}: {error}"
                    ) from error
                if not isinstance(run, MatrixRouteRun):
                    raise MatrixEquivalenceError(
                        "executor did not return MatrixRouteRun."
                    )
                if run.resource.route != route or (
                    run.resource.field_id
                    != query.field_of_view.field_id
                ) or run.resource.repetition != repetition:
                    raise MatrixEquivalenceError(
                        "resource observation does not identify its run."
                    )
                runs[route] = run
                observations.append(_plain(run.resource))

            exhaustive_plain, exhaustive_bytes, exhaustive_digest = (
                _canonical_document(runs["exhaustive"].results)
            )
            accelerated_plain, accelerated_bytes, accelerated_digest = (
                _canonical_document(runs["accelerated"].results)
            )
            if runs["exhaustive"].results != runs["accelerated"].results:
                raise MatrixEquivalenceError(
                    f"{query.field_of_view.field_id} result tuples differ."
                )
            if exhaustive_bytes != accelerated_bytes or (
                exhaustive_digest != accelerated_digest
            ):
                raise MatrixEquivalenceError(
                    f"{query.field_of_view.field_id} result bytes differ."
                )
            counts = _validate_partition(
                query,
                runs["accelerated"].acceleration_evidence,
                runs["exhaustive"].results,
            )
            evidence_plain, _evidence_bytes, evidence_digest = (
                _canonical_document(
                    runs["accelerated"].acceleration_evidence
                )
            )
            signature = (exhaustive_digest, evidence_digest)
            if repetition == 0:
                baseline = {
                    "results": exhaustive_plain,
                    "result_digest": exhaustive_digest,
                }
                evidence_baseline = evidence_plain
                count_baseline = counts
            elif signature != (
                baseline["result_digest"],
                sha256_hex(canonical_json_bytes(evidence_baseline)),
            ):
                raise MatrixEquivalenceError(
                    f"{query.field_of_view.field_id} is nondeterministic."
                )

        exhaustive_documents.append({
            "field_id": query.field_of_view.field_id,
            "results": baseline["results"],
            "sha256": baseline["result_digest"],
        })
        accelerated_documents.append({
            "field_id": query.field_of_view.field_id,
            "results": baseline["results"],
            "sha256": baseline["result_digest"],
        })
        evidence_documents.append({
            "field_id": query.field_of_view.field_id,
            "evidence": evidence_baseline,
            "sha256": sha256_hex(canonical_json_bytes(evidence_baseline)),
        })
        for outcome, count in count_baseline.items():
            aggregate_counts[outcome] += count
        field_reports.append({
            "field_id": query.field_of_view.field_id,
            "result_sha256": baseline["result_digest"],
            "crossing_count": len(baseline["results"]),
            "decision_counts": count_baseline,
        })

    if aggregate_counts["retain"] == 0 or aggregate_counts["indeterminate"] == 0:
        raise MatrixEquivalenceError(
            "complete matrix must exercise retain and indeterminate decisions."
        )

    after = _file_hashes(snapshot_directory, snapshot.manifest.records_file)
    if before != after:
        raise MatrixEquivalenceError("matrix mutated specimen input bytes.")

    documents = {
        "requests.json": request_plain,
        "exhaustive-results.json": exhaustive_documents,
        "accelerated-results.json": accelerated_documents,
        "acceleration-evidence.json": evidence_documents,
        "airmass-admissions.json": [_plain(item) for item in admissions],
        "resource-observations.json": observations,
    }
    file_bytes = {
        name: canonical_json_bytes(value) for name, value in documents.items()
    }
    file_sha256 = {
        name: sha256_hex(data) for name, data in file_bytes.items()
    }
    exhaustive_digest = file_sha256["exhaustive-results.json"]
    accelerated_digest = file_sha256["accelerated-results.json"]
    if exhaustive_digest != accelerated_digest:
        # File wrappers are intentionally named differently but their payloads
        # must remain exactly equal. Compare normalized field payloads instead.
        left = canonical_json_bytes(exhaustive_documents)
        right = canonical_json_bytes(accelerated_documents)
        if left != right:
            raise MatrixEquivalenceError(
                "whole-matrix result documents differ."
            )

    report = {
        "schema_version": 1,
        "document_kind": MATRIX_DOCUMENT_KIND,
        "implementation_identity": CROSSING_MATRIX_IMPLEMENTATION,
        "isolation_identity": MATRIX_ISOLATION_IDENTITY,
        "status": "success",
        "specimen_identity": _plain(specimen_identity),
        "admission_policy_identity": admission.policy_identity,
        "request_sha256": request_digest,
        "field_count": len(queries),
        "warmup_count": policy.warmup_count,
        "measured_repetitions": policy.measured_repetitions,
        "field_results": field_reports,
        "decision_totals": aggregate_counts,
        "whole_matrix_results_sha256": sha256_hex(
            canonical_json_bytes(exhaustive_documents)
        ),
        "file_sha256": file_sha256,
        "equivalence": {
            "python_tuple_equality": True,
            "canonical_byte_equality": True,
            "per_field_digest_equality": True,
            "whole_matrix_digest_equality": True,
            "fallback_count": 0,
            "rejected_exhaustive_crossing_count": 0,
        },
        "resource_statement": (
            "Raw isolated observations are descriptive only and make no "
            "universal speed, capacity, or memory claim."
        ),
        "warnings": receipt.get("warnings", []),
    }
    report_bytes = canonical_json_bytes(report)
    report_digest = sha256_hex(report_bytes)
    manifest = {
        "schema_version": 1,
        "document_kind": "satellite-crossing-matrix-manifest",
        "implementation_identity": CROSSING_MATRIX_IMPLEMENTATION,
        "equivalence_report_file": "equivalence-report.json",
        "equivalence_report_sha256": report_digest,
        "file_sha256": {
            **file_sha256,
            "equivalence-report.json": report_digest,
        },
    }

    output_root = Path(output_root).expanduser()
    output_root.mkdir(parents=True, exist_ok=True)
    if output_root.is_symlink() or not output_root.is_dir():
        raise ValueError("output_root must be a non-symlink directory.")
    destination = output_root / report_digest
    if destination.exists():
        return _validate_existing(destination, report)

    stage = Path(tempfile.mkdtemp(prefix=".matrix-", dir=output_root))
    try:
        for name, data in file_bytes.items():
            (stage / name).write_bytes(data)
        (stage / "equivalence-report.json").write_bytes(report_bytes)
        (stage / "matrix-manifest.json").write_bytes(
            canonical_json_bytes(manifest)
        )
        _validate_existing(stage, report)
        os.rename(stage, destination)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return destination
