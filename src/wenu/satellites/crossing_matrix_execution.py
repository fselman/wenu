"""Explicit offline production path for satellite equivalence evidence.

The module contains no discovery or network adapter.  Its subprocess protocol
is intentionally private to the developer command and remains digest-bound.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
import json
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time
import tracemalloc

from wenu.coordinates import CoordinateSpec, PositionStatus
from wenu.satellite_crossings import (
    InclusiveTimeInterval,
    SatelliteFieldOfView,
    SatelliteObserver,
)

from .crossing_acceleration import (
    AcceleratedCrossingEvidence,
    AcceleratedCrossingPolicy,
    AcceleratedLocalSatelliteCrossingOracle,
    ConeShellDecision,
    ConeShellPolicy,
    ConeShellSelection,
    ConservativeConeShellSelector,
)
from .crossing_batch import FieldAirmassCertifier, MultiFieldCrossingPolicy
from .crossing_matrix import (
    CrossingMatrixPolicy,
    MatrixResourceObservation,
    MatrixRouteRun,
    MatrixSpecimenIdentity,
    run_equivalence_matrix,
)
from .crossing_oracle import LocalSatelliteCrossingOracle, LocalSatelliteCrossingQuery
from .elements import canonical_json_bytes, sha256_hex
from .snapshot_admission import (
    ExternalSnapshotAdmissionPolicy,
    ExternalSnapshotIdentity,
)
from .snapshot_evidence import MEDIUM_SPECIMEN_IMPLEMENTATION
from .snapshots import load_snapshot_directory


MATRIX_EXECUTION_IMPLEMENTATION = "wenu.satellites.crossing_matrix_execution/1"
MATRIX_WORKER_PROTOCOL = "wenu.satellites.crossing_matrix_worker/1"
REAL_EXECUTION_ACKNOWLEDGEMENT = "I_ACKNOWLEDGE_THE_EXPLICIT_OFFLINE_REAL_MATRIX_RUN"

ACCEPTED_MEDIUM_IDENTITY = MatrixSpecimenIdentity(
    content_sha256="2e85c576e287a047b12fe58b9487f96533ae739c46a594945cedb4236f08ab8b",
    selection_receipt_sha256="1a1048a24d619ec15817dbbc63cb461240fbce243a5414f266179f9cba57a895",
    parent_content_sha256="e80306c843b9e3004b1d5bf7a8e4e7eb76a4f56284cd659978dc9bd3461f2347",
    record_count=256,
)

_OBSERVER = {
    "observer_id": "la-ligua",
    "longitude_deg": -71.230289,
    "latitude_deg": -32.443342,
    "elevation_m": 52.0,
    "refraction_policy": "vacuum",
    "earth_orientation_policy": "iers-a-bundled",
}

# Frozen decimal GCRS-axis centres.  The recipe uses the midpoint local
# sidereal angle at La Ligua minus the declared hour-angle offset; declination
# is the site latitude plus the declared offset.  Durations are only 15 or 60 s.
_FIELDS = (
    ("field-00", 329.785643112, -47.443342, 0.25, "2026-09-17T01:00:00.000000Z", "2026-09-17T01:00:15.000000Z", -30.0, -15.0),
    ("field-01", 319.785643112, -42.443342, 0.50, "2026-09-17T01:00:00.000000Z", "2026-09-17T01:00:15.000000Z", -20.0, -10.0),
    ("field-02", 310.287012037, -37.443342, 1.00, "2026-09-17T01:02:00.000000Z", "2026-09-17T01:02:15.000000Z", -10.0, -5.0),
    ("field-03", 300.882387719, -32.443342, 2.00, "2026-09-17T01:04:00.000000Z", "2026-09-17T01:05:00.000000Z", 0.0, 0.0),
    ("field-04", 291.289749886, -27.443342, 3.00, "2026-09-17T01:06:00.000000Z", "2026-09-17T01:06:15.000000Z", 10.0, 5.0),
    ("field-05", 281.885125569, -22.443342, 0.25, "2026-09-17T01:08:00.000000Z", "2026-09-17T01:09:00.000000Z", 20.0, 10.0),
    ("field-06", 272.292487905, -17.443342, 0.50, "2026-09-17T01:10:00.000000Z", "2026-09-17T01:10:15.000000Z", 30.0, 15.0),
    ("field-07", 327.887863419, -44.443342, 1.00, "2026-09-17T01:12:00.000000Z", "2026-09-17T01:13:00.000000Z", -25.0, -12.0),
    ("field-08", 298.295225754, -24.443342, 2.00, "2026-09-17T01:14:00.000000Z", "2026-09-17T01:14:15.000000Z", 5.0, 8.0),
    ("field-09", 278.890601436, -20.443342, 3.00, "2026-09-17T01:16:00.000000Z", "2026-09-17T01:17:00.000000Z", 25.0, 12.0),
)


def _fixture_mapping():
    return {
        "schema_version": 1,
        "implementation_identity": MATRIX_EXECUTION_IMPLEMENTATION,
        "observer": _OBSERVER,
        "coordinate_contract": {
            "frame": "gcrs-axes",
            "origin": "topocentric-direction",
            "position_status": "geometric",
            "time_scale": "utc",
            "centre_recipe": "midpoint local sidereal angle minus hour-angle offset; site latitude plus declination offset",
        },
        "time_tolerance_seconds": 0.01,
        "angular_tolerance_deg": 1.0e-5,
        "fields": [
            {
                "field_id": item[0], "center_longitude_deg": item[1],
                "center_latitude_deg": item[2], "angular_radius_deg": item[3],
                "interval_start": item[4], "interval_stop": item[5],
                "hour_angle_offset_deg": item[6], "declination_offset_deg": item[7],
            }
            for item in _FIELDS
        ],
    }


MATRIX_REQUEST_FIXTURE = _fixture_mapping()
MATRIX_REQUEST_FIXTURE_SHA256 = (
    "a7c04ab59d4578221e943e0e21c4be24782fe72a62eff70c230300dfe60cd097"
)
if sha256_hex(canonical_json_bytes(MATRIX_REQUEST_FIXTURE)) != MATRIX_REQUEST_FIXTURE_SHA256:
    raise RuntimeError("frozen matrix request fixture digest mismatch.")


def build_matrix_queries(snapshot):
    """Build the exact accepted ten-field request without implicit defaults."""
    observer = SatelliteObserver(**_OBSERVER)
    queries = []
    for field_id, longitude, latitude, radius, start, stop, _ha, _dec in _FIELDS:
        spec = CoordinateSpec(
            frame="gcrs-axes", origin="topocentric-direction",
            position_status=PositionStatus.GEOMETRIC,
            instant=start, time_scale="utc",
            provider=MATRIX_EXECUTION_IMPLEMENTATION,
        )
        queries.append(LocalSatelliteCrossingQuery(
            snapshot=snapshot,
            observer=observer,
            field_of_view=SatelliteFieldOfView(
                field_id=field_id,
                center_longitude_deg=longitude,
                center_latitude_deg=latitude,
                angular_radius_deg=radius,
                coordinate_spec=spec,
            ),
            interval=InclusiveTimeInterval(start, stop),
            time_tolerance_seconds=0.01,
            angular_tolerance_deg=1.0e-5,
        ))
    return tuple(queries)


def validate_accepted_medium_receipt(receipt):
    """Require every accepted real-medium receipt constraint."""
    if receipt.get("implementation_identity") != MEDIUM_SPECIMEN_IMPLEMENTATION:
        raise ValueError("selection receipt implementation identity mismatch.")
    bins = receipt.get("bin_results")
    if not isinstance(bins, list):
        raise ValueError("selection receipt bin_results must be a list.")
    nonempty = [item for item in bins if item.get("membership_count", 0) > 0]
    mandatory = sum(item.get("required_representative_count", -1) for item in nonempty)
    fill = receipt.get("fill_norad_catalog_ids")
    if len(nonempty) != 24 or mandatory != 48:
        raise ValueError("selection receipt representative constraints mismatch.")
    if not isinstance(fill, list) or len(fill) != 208:
        raise ValueError("selection receipt fill constraint mismatch.")
    if receipt.get("actual_record_count") != 256:
        raise ValueError("selection receipt record count mismatch.")
    if receipt.get("subset_canonical_records_sha256") != ACCEPTED_MEDIUM_IDENTITY.content_sha256:
        raise ValueError("selection receipt subset digest mismatch.")
    parent = receipt.get("parent_identity")
    if not isinstance(parent, dict) or parent.get("content_sha256") != ACCEPTED_MEDIUM_IDENTITY.parent_content_sha256:
        raise ValueError("selection receipt parent digest mismatch.")
    return receipt


class ProductionMatrixAirmassCertifier(FieldAirmassCertifier):
    """Accepted centre-only complete-interval X <= 2 certifier."""

    def __init__(self, *, evaluator=None):
        super().__init__(policy=MultiFieldCrossingPolicy(
            admitted_snapshot_ids=("never-implicit-external",),
            max_interval_seconds=60.0,
            maximum_airmass=2.0,
        ), evaluator=evaluator)


def _jsonable(value):
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted((_jsonable(item) for item in value), key=repr)
    return value


def _query_payload(query):
    return {
        "field": _jsonable(query.field_of_view),
        "observer": _jsonable(query.observer),
        "interval": _jsonable(query.interval),
        "time_tolerance_seconds": query.time_tolerance_seconds,
        "angular_tolerance_deg": query.angular_tolerance_deg,
    }


def _query_from_payload(snapshot, payload):
    field = payload["field"]
    coordinate = dict(field.pop("coordinate_spec"))
    coordinate["position_status"] = PositionStatus(coordinate["position_status"])
    field["coordinate_spec"] = CoordinateSpec(**coordinate)
    return LocalSatelliteCrossingQuery(
        snapshot=snapshot,
        observer=SatelliteObserver(**payload["observer"]),
        field_of_view=SatelliteFieldOfView(**field),
        interval=InclusiveTimeInterval(**payload["interval"]),
        time_tolerance_seconds=payload["time_tolerance_seconds"],
        angular_tolerance_deg=payload["angular_tolerance_deg"],
    )


def _environment():
    values = {"python": platform.python_version(), "os": platform.platform(), "machine": platform.machine()}
    for name in ("wenu", "numpy", "astropy", "skyfield", "sgp4"):
        try:
            values[name] = version(name)
        except PackageNotFoundError:
            values[name] = "unavailable"
    return values


def _selection_from_mapping(value):
    if value is None:
        return None
    return ConeShellSelection(
        snapshot_sha256=value["snapshot_sha256"], field_id=value["field_id"],
        interval_start=value["interval_start"], interval_stop=value["interval_stop"],
        decisions=tuple(ConeShellDecision(**item) for item in value["decisions"]),
        implementation=value["implementation"],
    )


def _evidence_from_mapping(value):
    if value is None:
        return None
    return AcceleratedCrossingEvidence(
        snapshot_sha256=value["snapshot_sha256"], field_id=value["field_id"],
        interval_start=value["interval_start"], interval_stop=value["interval_stop"],
        rejected_norad_catalog_ids=tuple(value["rejected_norad_catalog_ids"]),
        exact_solver_norad_catalog_ids=tuple(value["exact_solver_norad_catalog_ids"]),
        selection=_selection_from_mapping(value["selection"]),
        fallback_to_exhaustive=value["fallback_to_exhaustive"],
        fallback_reason=value.get("fallback_reason"), implementation=value["implementation"],
    )


class FreshSubprocessMatrixExecutor:
    """Execute exactly one route/query/run in one fresh Python process."""

    def __init__(self, snapshot_directory, *, timeout_seconds=3600.0):
        self.snapshot_directory = str(Path(snapshot_directory).expanduser().resolve())
        self.timeout_seconds = float(timeout_seconds)
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive.")

    def __call__(self, route, query, repetition, measured):
        request = {
            "protocol": MATRIX_WORKER_PROTOCOL,
            "route": route, "repetition": repetition, "measured": bool(measured),
            "snapshot_directory": self.snapshot_directory,
            "snapshot_identity": _jsonable(ExternalSnapshotIdentity.from_snapshot(query.snapshot)),
            "query": _query_payload(query),
        }
        with tempfile.TemporaryDirectory(prefix="wenu-matrix-worker-") as directory:
            root = Path(directory)
            request_path, response_path = root / "request.json", root / "response.json"
            request_path.write_bytes(canonical_json_bytes(request))
            try:
                completed = subprocess.run(
                    [sys.executable, "-m", __name__, "worker", str(request_path), str(response_path)],
                    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    timeout=self.timeout_seconds, check=False,
                )
            except subprocess.TimeoutExpired as error:
                raise TimeoutError(f"matrix worker timed out after {self.timeout_seconds:g} s.") from error
            if completed.returncode != 0:
                stderr = completed.stderr.decode("utf-8", errors="replace").strip()
                raise RuntimeError(f"matrix worker exited {completed.returncode}: {stderr}")
            data = response_path.read_bytes()
            value = json.loads(data)
            if canonical_json_bytes(value) != data or value.get("protocol") != MATRIX_WORKER_PROTOCOL:
                raise ValueError("matrix worker returned a non-canonical or unsupported response.")
        resource = MatrixResourceObservation(**value["resource"])
        return MatrixRouteRun(
            results=tuple(value["results"]), resource=resource,
            acceleration_evidence=_evidence_from_mapping(value.get("acceleration_evidence")),
        )


def _worker(request_path, response_path):
    request_bytes = Path(request_path).read_bytes()
    request = json.loads(request_bytes)
    if canonical_json_bytes(request) != request_bytes or request.get("protocol") != MATRIX_WORKER_PROTOCOL:
        raise ValueError("matrix worker request is non-canonical or unsupported.")
    snapshot = load_snapshot_directory(request["snapshot_directory"])
    expected = ExternalSnapshotIdentity(**request["snapshot_identity"])
    admission = ExternalSnapshotAdmissionPolicy(MATRIX_EXECUTION_IMPLEMENTATION, (expected,)).admit(snapshot)
    query = _query_from_payload(snapshot, request["query"])
    route = request["route"]
    tracemalloc.start()
    wall_start, cpu_start = time.monotonic(), time.process_time()
    if route == "exhaustive":
        results = LocalSatelliteCrossingOracle(max_evaluations_per_record=20000).solve(query)
        evidence = None
    elif route == "accelerated":
        selector = ConservativeConeShellSelector(
            policy=ConeShellPolicy(validated_snapshot_ids=(snapshot.manifest.snapshot_id,)),
            external_snapshot_admission=admission,
        )
        oracle = AcceleratedLocalSatelliteCrossingOracle(
            selector=selector,
            policy=AcceleratedCrossingPolicy(
                admitted_snapshot_ids=(snapshot.manifest.snapshot_id,),
                max_interval_seconds=60.0, selector_failure_mode="fail_closed",
            ),
            max_evaluations_per_record=20000,
            external_snapshot_admission=admission,
        )
        results, evidence = oracle.solve_with_evidence(query)
    else:
        raise ValueError("matrix worker route must be exhaustive or accelerated.")
    cpu_seconds, wall_seconds = time.process_time() - cpu_start, time.monotonic() - wall_start
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    resource = MatrixResourceObservation(
        route=route, field_id=query.field_of_view.field_id,
        repetition=max(0, request["repetition"]), wall_seconds=wall_seconds,
        cpu_seconds=cpu_seconds, peak_python_bytes=peak, environment=_environment(),
    )
    response = {
        "protocol": MATRIX_WORKER_PROTOCOL,
        "results": _jsonable(results),
        "resource": _jsonable(resource),
        "acceleration_evidence": None if evidence is None else _jsonable(evidence),
    }
    Path(response_path).write_bytes(canonical_json_bytes(response))


def run_production_equivalence_matrix(snapshot_directory, output_root, *, specimen_identity, acknowledgement, policy=None, certifier=None, executor=None):
    """Run the explicit offline path after exact operator acknowledgements."""
    if acknowledgement != REAL_EXECUTION_ACKNOWLEDGEMENT:
        raise ValueError("exact real-execution acknowledgement is required.")
    if specimen_identity != ACCEPTED_MEDIUM_IDENTITY:
        raise ValueError("specimen identity is not the exact accepted medium.")
    root = Path(snapshot_directory).expanduser()
    snapshot = load_snapshot_directory(root)
    receipt_bytes = (root / "selection-receipt.json").read_bytes()
    if sha256_hex(receipt_bytes) != specimen_identity.selection_receipt_sha256:
        raise ValueError("selection receipt digest does not match accepted identity.")
    validate_accepted_medium_receipt(json.loads(receipt_bytes))
    admission = ExternalSnapshotAdmissionPolicy(
        MATRIX_EXECUTION_IMPLEMENTATION,
        (ExternalSnapshotIdentity.from_snapshot(snapshot),),
    ).admit(snapshot)
    return run_equivalence_matrix(
        root, output_root, specimen_identity=specimen_identity,
        admission=admission, queries=build_matrix_queries(snapshot),
        airmass_certifier=certifier or ProductionMatrixAirmassCertifier(),
        executor=executor or FreshSubprocessMatrixExecutor(root),
        policy=policy or CrossingMatrixPolicy(),
    )


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) == 3 and argv[0] == "worker":
        _worker(argv[1], argv[2])
        return 0
    raise SystemExit("crossing_matrix_execution is an internal worker module.")


if __name__ == "__main__":
    main()
