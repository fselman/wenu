"""Offline CLI and two-call file protocol for exact satellite crossings."""

from __future__ import annotations

import argparse
import ctypes
from datetime import datetime
import errno
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version
import json
import os
from pathlib import Path
import re
import shutil
import signal
import sys
import tempfile

from wenu.coordinates import CoordinateSpec, PositionStatus
from wenu.satellite_crossing_reports import ExactSatelliteCrossingReport
from wenu.satellite_crossings import (
    InclusiveTimeInterval,
    SatelliteFieldOfView,
    SatelliteObserver,
)
from wenu.satellites.crossing_acceleration import (
    ACCELERATED_ORACLE_IMPLEMENTATION,
)
from wenu.satellites.crossing_batch import (
    MULTI_FIELD_IMPLEMENTATION,
    MultiFieldCrossingPolicy,
    MultiFieldCrossingRequest,
    MultiFieldCrossingValidationError,
    MultiFieldSatelliteCrossingCoordinator,
)
from wenu.satellites.crossing_oracle import (
    LocalSatelliteCrossingQuery,
    ORACLE_IMPLEMENTATION,
)
from wenu.satellites.snapshot_admission import (
    CELESTRAK_ACTIVE_20260917_IDENTITY,
    ExternalSnapshotAdmissionPolicy,
)
from wenu.satellites.snapshots import load_snapshot_directory


REQUEST_PRODUCT = "wenu.artificial_satellite_crossing_request"
VALIDATION_PRODUCT = "wenu.artificial_satellite_crossing_validation"
MANIFEST_PRODUCT = "wenu.artificial_satellite_crossing_bundle"
PROTOCOL_VERSION = 1
CLI_IMPLEMENTATION = "wenu satellite crossing CLI/file protocol v1"
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_UTC = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$"
)
_DIGEST_KEYS = {
    REQUEST_PRODUCT: "request_identity_sha256",
    VALIDATION_PRODUCT: "validation_identity_sha256",
    MANIFEST_PRODUCT: "manifest_identity_sha256",
}


class ProtocolInputError(ValueError):
    """Malformed or semantically invalid protocol input."""


class ValidatedSubsetError(ValueError):
    """Invalid, stale, mismatched, or empty validated-subset input."""


class PublicationError(OSError):
    """Unsafe path or failed atomic publication."""


class FieldValidationError(ValueError):
    """One or more fields failed the complete validation pass."""

    def __init__(self, results):
        self.results = tuple(results)
        invalid = [
            value for value in self.results
            if value["status"] == "invalid"
        ]
        summary = "; ".join(
            f"{value['field_id']}: {value['code']}" for value in invalid
        )
        super().__init__(f"Multi-field request failed validation ({summary}).")


class Terminated(KeyboardInterrupt):
    """SIGTERM translated to cooperative cleanup and status 143."""


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


def _pairs(values):
    result = {}
    for key, value in values:
        if key in result:
            raise ProtocolInputError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value):
    raise ProtocolInputError(f"non-finite JSON number: {value}")


def _load_json_bytes(value, *, name):
    if value.startswith(b"\xef\xbb\xbf"):
        raise ProtocolInputError(f"{name} must not contain a byte-order mark.")
    try:
        text = value.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ProtocolInputError(f"{name} must be UTF-8.") from error
    try:
        document = json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
        )
    except json.JSONDecodeError as error:
        raise ProtocolInputError(f"{name} must be valid JSON.") from error
    if not isinstance(document, dict):
        raise ProtocolInputError(f"{name} must be a JSON object.")
    return document


def _identity(document):
    product = document.get("product")
    key = _DIGEST_KEYS.get(product)
    if key is None:
        raise ProtocolInputError("unsupported protocol product.")
    payload = dict(document)
    supplied = payload.pop(key, None)
    actual = sha256(_canonical(payload).encode("utf-8")).hexdigest()
    if supplied is not None and supplied != actual:
        raise ProtocolInputError(f"{key} does not match document content.")
    return key, actual


def _digest(value, *, name):
    if not isinstance(value, str) or not _DIGEST.fullmatch(value):
        raise ProtocolInputError(f"{name} must be a lowercase SHA-256.")
    return value


def _utc(value, *, name):
    if not isinstance(value, str) or not _UTC.fullmatch(value):
        raise ProtocolInputError(
            f"{name} must be canonical UTC with six fractional digits."
        )
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ProtocolInputError(
            f"{name} must be a valid UTC instant."
        ) from error
    return value


def _signed(document):
    key, digest = _identity(document)
    result = dict(document)
    result[key] = digest
    return result


def _keys(value, expected, *, name):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ProtocolInputError(
            f"{name} must contain exactly: {', '.join(expected)}."
        )


def _real_file(path, *, name):
    path = Path(path)
    if not path.is_absolute():
        raise PublicationError(f"{name} must be an absolute path.")
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        try:
            info = current.lstat()
        except FileNotFoundError:
            raise PublicationError(f"{name} does not exist.") from None
        if os.path.islink(current):
            raise PublicationError(f"{name} must not contain a symlink.")
    if not path.is_file():
        raise PublicationError(f"{name} must be a regular file.")
    return path


def _safe_destination(path, *, directory):
    path = Path(path)
    if not path.is_absolute():
        raise PublicationError("output path must be absolute.")
    parent = path.parent
    _real_directory(parent, name="output parent")
    try:
        path.lstat()
    except FileNotFoundError:
        return path
    raise PublicationError("output path already exists (no-clobber).")


def _real_directory(path, *, name):
    path = Path(path)
    if not path.is_absolute():
        raise PublicationError(f"{name} must be an absolute path.")
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        try:
            current.lstat()
        except FileNotFoundError:
            raise PublicationError(f"{name} does not exist.") from None
        if os.path.islink(current):
            raise PublicationError(f"{name} must not contain a symlink.")
    if not path.is_dir():
        raise PublicationError(f"{name} must be a directory.")
    return path


def _rename_noreplace(source, destination):
    source = os.fsencode(source)
    destination = os.fsencode(destination)
    try:
        if sys.platform == "darwin":
            libc = ctypes.CDLL(None, use_errno=True)
            call = libc.renamex_np
            call.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint)
            result = call(source, destination, 0x00000004)  # RENAME_EXCL
        elif sys.platform.startswith("linux"):
            libc = ctypes.CDLL(None, use_errno=True)
            call = libc.renameat2
            call.argtypes = (
                ctypes.c_int,
                ctypes.c_char_p,
                ctypes.c_int,
                ctypes.c_char_p,
                ctypes.c_uint,
            )
            result = call(
                -100, source, -100, destination, 1
            )  # RENAME_NOREPLACE
        else:
            raise AttributeError
    except AttributeError as error:
        raise PublicationError(
            "atomic no-clobber rename is unsupported on this platform."
        ) from error
    if result:
        number = ctypes.get_errno()
        if number == errno.EEXIST:
            raise PublicationError("output path already exists (no-clobber).")
        raise PublicationError(os.strerror(number))


def _write_exclusive(path, value):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(descriptor)


def _publish_file(path, value):
    path = _safe_destination(path, directory=False)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    os.close(descriptor)
    temporary = Path(temporary)
    try:
        temporary.unlink()
        _write_exclusive(temporary, value)
        _rename_noreplace(temporary, path)
    finally:
        if temporary.exists() and not temporary.is_symlink():
            temporary.unlink()


def _coordinate(value):
    expected = (
        "frame", "origin", "position_status", "epoch", "equinox",
        "instant", "time_scale", "longitude_unit", "latitude_unit",
        "representation", "provider", "model", "provenance", "corrections",
    )
    _keys(value, expected, name="coordinate_spec")
    return CoordinateSpec(
        frame=value["frame"],
        origin=value["origin"],
        position_status=PositionStatus(value["position_status"]),
        epoch=value["epoch"],
        equinox=value["equinox"],
        instant=value["instant"],
        time_scale=value["time_scale"],
        longitude_unit=value["longitude_unit"],
        latitude_unit=value["latitude_unit"],
        representation=value["representation"],
        provider=value["provider"],
        model=value["model"],
        provenance=tuple(value["provenance"]),
        corrections=frozenset(value["corrections"]),
    )


def _observer(value):
    expected = (
        "observer_id", "longitude_deg", "latitude_deg", "elevation_m",
        "refraction_policy", "earth_orientation_policy",
    )
    _keys(value, expected, name="observer")
    return SatelliteObserver(**value)


def _field_query(value, *, snapshot, observer):
    expected = (
        "field_id", "center_longitude_deg", "center_latitude_deg",
        "angular_radius_deg", "coordinate_spec", "boundary", "interval",
        "time_tolerance_seconds", "angular_tolerance_deg",
    )
    _keys(value, expected, name="field")
    interval = value["interval"]
    _keys(
        interval,
        ("start", "stop", "time_scale", "boundary"),
        name="interval",
    )
    field = SatelliteFieldOfView(
        field_id=value["field_id"],
        center_longitude_deg=value["center_longitude_deg"],
        center_latitude_deg=value["center_latitude_deg"],
        angular_radius_deg=value["angular_radius_deg"],
        coordinate_spec=_coordinate(value["coordinate_spec"]),
        boundary=value["boundary"],
    )
    return LocalSatelliteCrossingQuery(
        snapshot=snapshot,
        observer=observer,
        field_of_view=field,
        interval=InclusiveTimeInterval(**interval),
        time_tolerance_seconds=value["time_tolerance_seconds"],
        angular_tolerance_deg=value["angular_tolerance_deg"],
    )


def _policy(value):
    expected = (
        "max_interval_seconds", "maximum_airmass", "processing_chunk_size",
        "sky_motion_bound_deg_per_s", "certification_time_tolerance_seconds",
    )
    _keys(value, expected, name="policy")
    return MultiFieldCrossingPolicy(
        admitted_snapshot_ids=("synthetic_50s4b_v1",), **value
    )


def _request(document, *, validated=False):
    expected = (
        "product", "schema_version", "document_kind", "created_utc",
        "snapshot", "observer", "policy", "fields",
        "request_identity_sha256",
    )
    _keys(document, expected, name="request")
    if (
        document["product"] != REQUEST_PRODUCT
        or document["schema_version"] != PROTOCOL_VERSION
        or document["document_kind"] != "initial_request"
    ):
        raise ProtocolInputError("unsupported request product or version.")
    _, identity = _identity(document)
    _utc(document["created_utc"], name="created_utc")
    snapshot_ref = document["snapshot"]
    _keys(
        snapshot_ref,
        ("directory", "snapshot_id", "content_sha256"),
        name="snapshot",
    )
    directory = Path(snapshot_ref["directory"])
    if not directory.is_absolute():
        raise ProtocolInputError("snapshot directory must be absolute.")
    _digest(snapshot_ref["content_sha256"], name="snapshot content digest")
    _real_directory(directory, name="snapshot directory")
    snapshot = load_snapshot_directory(directory)
    if (
        snapshot.manifest.snapshot_id != snapshot_ref["snapshot_id"]
        or snapshot.manifest.content_sha256 != snapshot_ref["content_sha256"]
    ):
        error = ValidatedSubsetError if validated else ProtocolInputError
        raise error("snapshot identity does not match request.")
    try:
        observer = _observer(document["observer"])
        policy = _policy(document["policy"])
    except (KeyError, TypeError, ValueError) as error:
        raise ProtocolInputError(
            f"request context is invalid: {type(error).__name__}: {error}"
        ) from error
    fields = document["fields"]
    if not isinstance(fields, list) or not fields:
        raise ProtocolInputError("fields must be a non-empty array.")
    identities = [
        value.get("field_id")
        for value in fields
        if isinstance(value, dict)
    ]
    if (
        len(identities) != len(fields)
        or len(set(identities)) != len(identities)
    ):
        raise ProtocolInputError(
            "field identifiers must be present and unique."
        )
    try:
        queries = tuple(
            _field_query(value, snapshot=snapshot, observer=observer)
            for value in fields
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ProtocolInputError(
            f"field definition is invalid: {type(error).__name__}: {error}"
        ) from error
    admission = None
    if snapshot.manifest.snapshot_id != "synthetic_50s4b_v1":
        try:
            admission = ExternalSnapshotAdmissionPolicy(
                policy_identity="wenu accepted external snapshot allowlist v1",
                admitted_identities=(CELESTRAK_ACTIVE_20260917_IDENTITY,),
            ).admit(snapshot)
        except ValueError as error:
            raise RuntimeError(str(error)) from error
    coordinator = MultiFieldSatelliteCrossingCoordinator(
        policy=policy, external_snapshot_admission=admission
    )
    return identity, snapshot, policy, coordinator, queries


def _validation_document(request_document, source_digest, results):
    valid_indexes = [
        value["source_index"]
        for value in results
        if value["status"] == "valid"
    ]
    derived = None
    if valid_indexes:
        derived = dict(request_document)
        derived["fields"] = [
            request_document["fields"][index]
            for index in valid_indexes
        ]
        derived.pop("request_identity_sha256", None)
        derived = _signed(derived)
    document = {
        "product": VALIDATION_PRODUCT,
        "schema_version": PROTOCOL_VERSION,
        "document_kind": "validation_output",
        "source_bytes_sha256": source_digest,
        "source_request_identity_sha256": request_document[
            "request_identity_sha256"
        ],
        "snapshot": dict(request_document["snapshot"]),
        "results": results,
        "derived_request": derived,
    }
    return _signed(document)


def _validate_fields(coordinator, queries):
    results = []
    for index, query in enumerate(queries):
        try:
            coordinator.validate(MultiFieldCrossingRequest((query,)))
        except MultiFieldCrossingValidationError as error:
            failure = error.failures[0]
            results.append({
                "field_id": query.field_of_view.field_id,
                "source_index": index,
                "status": "invalid",
                "code": failure.code,
                "detail": failure.message,
            })
        else:
            results.append({
                "field_id": query.field_of_view.field_id,
                "source_index": index,
                "status": "valid",
                "code": None,
                "detail": None,
            })
    return results


def _make_report(results, policy, created_utc):
    try:
        wenu_version = version("wenu")
    except PackageNotFoundError:
        wenu_version = "uninstalled"
    return ExactSatelliteCrossingReport.from_results(
        results,
        policy=policy,
        created_utc=created_utc,
        wenu_version=wenu_version,
        crossing_oracle_implementation=ORACLE_IMPLEMENTATION,
        acceleration_implementation=ACCELERATED_ORACLE_IMPLEMENTATION,
        batch_coordinator_implementation=MULTI_FIELD_IMPLEMENTATION,
    )


def _publish_bundle(path, report, *, request_mode, request_identity):
    path = _safe_destination(path, directory=True)
    payloads = {
        "report.json": report.to_json().encode("utf-8"),
        "report.ecsv": report.to_ecsv().encode("utf-8"),
        "report.vot": report.to_votable(),
    }
    if (
        ExactSatelliteCrossingReport.from_json(payloads["report.json"])
        != report
    ):
        raise ValueError("JSON report round trip failed.")
    if (
        ExactSatelliteCrossingReport.from_ecsv(payloads["report.ecsv"])
        != report
    ):
        raise ValueError("ECSV report round trip failed.")
    if (
        ExactSatelliteCrossingReport.from_votable(payloads["report.vot"])
        != report
    ):
        raise ValueError("VOTable report round trip failed.")
    stage = Path(tempfile.mkdtemp(prefix=f".{path.name}.", dir=path.parent))
    try:
        entries = []
        media = {
            "report.json": "application/json",
            "report.ecsv": "text/x-ecsv",
            "report.vot": "application/x-votable+xml",
        }
        for name, value in payloads.items():
            _write_exclusive(stage / name, value)
            entries.append({
                "filename": name,
                "media_type": media[name],
                "byte_count": len(value),
                "sha256": sha256(value).hexdigest(),
            })
        manifest = _signed({
            "product": MANIFEST_PRODUCT,
            "schema_version": PROTOCOL_VERSION,
            "document_kind": "report_bundle_manifest",
            "implementation": CLI_IMPLEMENTATION,
            "request_mode": request_mode,
            "request_identity_sha256": request_identity,
            "report_identity_sha256": report.report_identity_sha256,
            "snapshot_id": report.document["snapshot"]["snapshot_id"],
            "snapshot_content_sha256": report.document["snapshot"][
                "content_sha256"
            ],
            "files": entries,
        })
        _write_exclusive(
            stage / "manifest.json", _pretty(manifest).encode("utf-8")
        )
        descriptor = os.open(stage, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        _rename_noreplace(stage, path)
    finally:
        if stage.exists() and not stage.is_symlink():
            shutil.rmtree(stage)
    return path / "manifest.json"


def _validated_request(document):
    expected = (
        "product", "schema_version", "document_kind", "source_bytes_sha256",
        "source_request_identity_sha256", "snapshot", "results",
        "derived_request", "validation_identity_sha256",
    )
    _keys(document, expected, name="validation output")
    if (
        document["product"] != VALIDATION_PRODUCT
        or document["schema_version"] != PROTOCOL_VERSION
        or document["document_kind"] != "validation_output"
    ):
        raise ValidatedSubsetError(
            "unsupported validation product or version."
        )
    try:
        _digest(document["source_bytes_sha256"], name="source byte digest")
        _digest(
            document["source_request_identity_sha256"],
            name="source request identity",
        )
    except ProtocolInputError as error:
        raise ValidatedSubsetError(str(error)) from error
    try:
        _, identity = _identity(document)
    except ProtocolInputError as error:
        raise ValidatedSubsetError(str(error)) from error
    derived = document["derived_request"]
    if derived is None:
        raise ValidatedSubsetError(
            "validation output contains no valid fields."
        )
    results = document["results"]
    if not isinstance(results, list) or not results:
        raise ValidatedSubsetError("validation results must be non-empty.")
    indexes = [
        value.get("source_index")
        for value in results
        if isinstance(value, dict)
    ]
    if indexes != list(range(len(results))):
        raise ValidatedSubsetError("validation partition order is invalid.")
    for value in results:
        try:
            _keys(
                value,
                ("field_id", "source_index", "status", "code", "detail"),
                name="validation result",
            )
        except ProtocolInputError as error:
            raise ValidatedSubsetError(str(error)) from error
        if value["status"] not in ("valid", "invalid"):
            raise ValidatedSubsetError("validation status is invalid.")
        if value["status"] == "valid" and (
            value["code"] is not None or value["detail"] is not None
        ):
            raise ValidatedSubsetError(
                "valid fields must not contain failure data."
            )
        if value["status"] == "invalid" and (
            not isinstance(value["code"], str)
            or not isinstance(value["detail"], str)
        ):
            raise ValidatedSubsetError(
                "invalid fields require code and detail."
            )
    valid_ids = [
        value["field_id"]
        for value in results
        if value.get("status") == "valid"
    ]
    derived_ids = [
        value.get("field_id") for value in derived.get("fields", [])
    ]
    if derived_ids != valid_ids:
        raise ValidatedSubsetError(
            "derived request does not match valid partition."
        )
    if derived.get("snapshot") != document["snapshot"]:
        raise ValidatedSubsetError(
            "derived request snapshot does not match validation output."
        )
    return identity, derived


def parser():
    value = argparse.ArgumentParser(
        description="Calculate exact offline artificial-satellite crossings."
    )
    mode = value.add_mutually_exclusive_group(required=True)
    mode.add_argument("--request", type=Path)
    mode.add_argument("--validated-request", type=Path)
    mode.add_argument("--direct", action="store_true")
    value.add_argument("--snapshot-directory", type=Path)
    value.add_argument("--snapshot-id")
    value.add_argument("--snapshot-sha256")
    value.add_argument("--created-utc")
    value.add_argument("--observer-json")
    value.add_argument("--policy-json")
    value.add_argument("--field", action="append")
    value.add_argument("--output", type=Path)
    value.add_argument("--validation-output", type=Path)
    return value


def _direct_document(arguments):
    required = (
        "snapshot_directory", "snapshot_id", "snapshot_sha256", "created_utc",
        "observer_json", "policy_json", "field",
    )
    missing = [
        name.replace("_", "-")
        for name in required
        if not getattr(arguments, name)
    ]
    if missing:
        raise ProtocolInputError(
            "direct mode requires: " + ", ".join(missing) + "."
        )
    try:
        observer = _load_json_bytes(
            arguments.observer_json.encode("utf-8"),
            name="observer argument",
        )
        policy = _load_json_bytes(
            arguments.policy_json.encode("utf-8"),
            name="policy argument",
        )
        fields = [
            _load_json_bytes(value.encode("utf-8"), name="field argument")
            for value in arguments.field
        ]
    except UnicodeEncodeError as error:
        raise ProtocolInputError("direct JSON argument is invalid.") from error
    return _signed({
        "product": REQUEST_PRODUCT,
        "schema_version": PROTOCOL_VERSION,
        "document_kind": "initial_request",
        "created_utc": arguments.created_utc,
        "snapshot": {
            "directory": str(arguments.snapshot_directory),
            "snapshot_id": arguments.snapshot_id,
            "content_sha256": arguments.snapshot_sha256,
        },
        "observer": observer,
        "policy": policy,
        "fields": fields,
    })


def run(arguments):
    if arguments.output is None:
        raise ProtocolInputError("--output is required.")
    source_bytes = None
    mode = "direct"
    validation_identity = None
    if arguments.direct:
        if arguments.validation_output is not None:
            raise ProtocolInputError(
                "direct mode forbids --validation-output."
            )
        document = _direct_document(arguments)
    elif arguments.request is not None:
        mode = "initial-request"
        if any(
            getattr(arguments, name) is not None
            for name in (
                "snapshot_directory", "snapshot_id", "snapshot_sha256",
                "created_utc", "observer_json", "policy_json", "field",
            )
        ):
            raise ProtocolInputError(
                "--request forbids direct-mode arguments."
            )
        source_bytes = _real_file(
            arguments.request, name="request"
        ).read_bytes()
        document = _load_json_bytes(source_bytes, name="request")
        if document.get("product") != REQUEST_PRODUCT:
            raise ProtocolInputError("--request requires an initial request.")
    else:
        mode = "validated-request"
        if any(
            getattr(arguments, name) is not None
            for name in (
                "snapshot_directory", "snapshot_id", "snapshot_sha256",
                "created_utc", "observer_json", "policy_json", "field",
            )
        ):
            raise ProtocolInputError(
                "--validated-request forbids direct-mode arguments."
            )
        if arguments.validation_output is not None:
            raise ProtocolInputError(
                "validated mode forbids --validation-output."
            )
        source_bytes = _real_file(
            arguments.validated_request, name="validated request"
        ).read_bytes()
        validation = _load_json_bytes(source_bytes, name="validation output")
        validation_identity, document = _validated_request(validation)
    try:
        identity, _snapshot, policy, coordinator, queries = _request(
            document, validated=mode == "validated-request"
        )
    except ProtocolInputError as error:
        if mode == "validated-request":
            raise ValidatedSubsetError(str(error)) from error
        raise
    validation = _validate_fields(coordinator, queries)
    invalid = [value for value in validation if value["status"] == "invalid"]
    if invalid:
        if mode == "initial-request":
            if arguments.validation_output is None:
                raise PublicationError(
                    "--validation-output is required for invalid file "
                    "requests."
                )
            output = _validation_document(
                document, sha256(source_bytes).hexdigest(), validation
            )
            _publish_file(
                arguments.validation_output, _pretty(output).encode("utf-8")
            )
        if mode == "validated-request":
            raise ValidatedSubsetError(
                "validated subset no longer passes current validation."
            )
        raise FieldValidationError(validation)
    results = coordinator.solve(MultiFieldCrossingRequest(queries))
    report = _make_report(results, policy, document["created_utc"])
    manifest = _publish_bundle(
        arguments.output,
        report,
        request_mode=mode,
        request_identity=validation_identity or identity,
    )
    return manifest, report.report_identity_sha256


def main(argv=None):
    arguments = parser().parse_args(argv)
    previous_sigterm = signal.getsignal(signal.SIGTERM)
    def terminate(_number, _frame):
        raise Terminated

    signal.signal(signal.SIGTERM, terminate)
    try:
        manifest, identity = run(arguments)
    except Terminated:
        return 143
    except KeyboardInterrupt:
        return 130
    except ValidatedSubsetError as error:
        print(f"wenu_satellite_crossings: {error}", file=sys.stderr)
        return 5
    except PublicationError as error:
        print(f"wenu_satellite_crossings: {error}", file=sys.stderr)
        return 6
    except (FieldValidationError, MultiFieldCrossingValidationError) as error:
        print(f"wenu_satellite_crossings: {error}", file=sys.stderr)
        return 4
    except ProtocolInputError as error:
        print(f"wenu_satellite_crossings: {error}", file=sys.stderr)
        return 3
    except Exception as error:
        print(
            f"wenu_satellite_crossings: {type(error).__name__}: {error}",
            file=sys.stderr,
        )
        return 7
    finally:
        signal.signal(signal.SIGTERM, previous_sigterm)
    print(f"manifest: {manifest}")
    print(f"report_identity_sha256: {identity}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
