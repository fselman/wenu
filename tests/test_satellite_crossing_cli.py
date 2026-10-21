from __future__ import annotations

from argparse import Namespace
from hashlib import sha256
import json
from pathlib import Path

import pytest

from wenu.cli import satellite_crossings as cli


DIGEST = "a" * 64


def request_document(fields=None):
    value = {
        "product": cli.REQUEST_PRODUCT,
        "schema_version": 1,
        "document_kind": "initial_request",
        "created_utc": "2026-09-19T16:00:00.000000Z",
        "snapshot": {
            "directory": "/absolute/snapshot",
            "snapshot_id": "snapshot",
            "content_sha256": DIGEST,
        },
        "observer": {
            "observer_id": "la-ligua",
            "longitude_deg": -71.230289,
            "latitude_deg": -32.443342,
            "elevation_m": 52.0,
            "refraction_policy": "vacuum",
            "earth_orientation_policy": "astropy",
        },
        "policy": {
            "max_interval_seconds": 60.0,
            "maximum_airmass": 2.0,
            "processing_chunk_size": 10,
            "sky_motion_bound_deg_per_s": 0.005,
            "certification_time_tolerance_seconds": 0.01,
        },
        "fields": fields or [{"field_id": "valid"}, {"field_id": "invalid"}],
    }
    return cli._signed(value)


def validation_document(derived):
    value = {
        "product": cli.VALIDATION_PRODUCT,
        "schema_version": 1,
        "document_kind": "validation_output",
        "source_bytes_sha256": "b" * 64,
        "source_request_identity_sha256": "c" * 64,
        "snapshot": {
            "directory": "/absolute/snapshot",
            "snapshot_id": "snapshot",
            "content_sha256": DIGEST,
        },
        "results": [
            {
                "field_id": "valid",
                "source_index": 0,
                "status": "valid",
                "code": None,
                "detail": None,
            },
            {
                "field_id": "invalid",
                "source_index": 1,
                "status": "invalid",
                "code": "airmass-not-certified",
                "detail": "field centre exceeds the maximum airmass.",
            },
        ],
        "derived_request": derived,
    }
    return cli._signed(value)


def arguments(**changes):
    values = {
        "request": None,
        "validated_request": None,
        "direct": False,
        "snapshot_directory": None,
        "snapshot_id": None,
        "snapshot_sha256": None,
        "created_utc": None,
        "observer_json": None,
        "policy_json": None,
        "field": None,
        "output": Path("/output"),
        "validation_output": None,
    }
    values.update(changes)
    return Namespace(**values)


def test_signed_documents_are_deterministic_and_tamper_evident():
    left = request_document()
    right = request_document()
    assert left == right
    assert len(left["request_identity_sha256"]) == 64
    cli._identity(left)
    left["created_utc"] = "2026-09-19T17:00:00.000000Z"
    with pytest.raises(cli.ProtocolInputError, match="does not match"):
        cli._identity(left)


def test_strict_json_rejects_duplicate_keys_bom_nonfinite_and_invalid_utf8():
    for value, message in (
        (b'{"x":1,"x":2}', "duplicate"),
        (b"\xef\xbb\xbf{}", "byte-order"),
        (b'{"x":NaN}', "non-finite"),
        (b"\xff", "UTF-8"),
    ):
        with pytest.raises(cli.ProtocolInputError, match=message):
            cli._load_json_bytes(value, name="request")


def test_validation_output_preserves_partition_and_only_embeds_valid_subset():
    source = request_document()
    results = [
        {
            "field_id": "valid",
            "source_index": 0,
            "status": "valid",
            "code": None,
            "detail": None,
        },
        {
            "field_id": "invalid",
            "source_index": 1,
            "status": "invalid",
            "code": "airmass-not-certified",
            "detail": "outside domain",
        },
    ]
    value = cli._validation_document(source, "d" * 64, results)
    assert value["results"] == results
    assert [
        field["field_id"]
        for field in value["derived_request"]["fields"]
    ] == ["valid"]
    assert (
        value["source_request_identity_sha256"]
        == source["request_identity_sha256"]
    )
    cli._identity(value)


def test_validated_request_rejects_empty_tampered_and_reordered_partition():
    source = request_document(fields=[{"field_id": "valid"}])
    good = validation_document(source)
    identity, derived = cli._validated_request(good)
    assert identity == good["validation_identity_sha256"]
    assert derived == source

    empty = validation_document(None)
    with pytest.raises(cli.ValidatedSubsetError, match="no valid fields"):
        cli._validated_request(empty)

    reordered = validation_document(source)
    reordered["results"].reverse()
    reordered = cli._signed({
        key: value
        for key, value in reordered.items()
        if key != "validation_identity_sha256"
    })
    with pytest.raises(cli.ValidatedSubsetError, match="partition order"):
        cli._validated_request(reordered)


def test_output_paths_are_absolute_no_clobber_and_symlink_safe(tmp_path):
    destination = tmp_path / "bundle"
    assert cli._safe_destination(destination, directory=True) == destination
    destination.mkdir()
    with pytest.raises(cli.PublicationError, match="already exists"):
        cli._safe_destination(destination, directory=True)

    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(cli.PublicationError, match="symlink"):
        cli._safe_destination(link / "bundle", directory=True)

    with pytest.raises(cli.PublicationError, match="absolute"):
        cli._safe_destination(Path("relative"), directory=True)


def test_single_file_publication_is_atomic_and_no_clobber(tmp_path):
    destination = tmp_path / "validation.json"
    cli._publish_file(destination, b"first\n")
    assert destination.read_bytes() == b"first\n"
    assert not tuple(tmp_path.glob(".validation.json.*"))
    with pytest.raises(cli.PublicationError, match="already exists"):
        cli._publish_file(destination, b"second\n")
    assert destination.read_bytes() == b"first\n"


def test_first_file_call_publishes_validation_before_status_four(
    tmp_path, monkeypatch
):
    request = request_document()
    request_path = tmp_path / "request.json"
    request_bytes = cli._pretty(request).encode()
    request_path.write_bytes(request_bytes)
    validation_path = tmp_path / "validation.json"
    output_path = tmp_path / "bundle"
    query_values = (object(), object())

    monkeypatch.setattr(
        cli,
        "_request",
        lambda document, validated=False: (
            document["request_identity_sha256"],
            object(),
            object(),
            object(),
            query_values,
        ),
    )
    results = [
        {
            "field_id": "valid",
            "source_index": 0,
            "status": "valid",
            "code": None,
            "detail": None,
        },
        {
            "field_id": "invalid",
            "source_index": 1,
            "status": "invalid",
            "code": "airmass-not-certified",
            "detail": "outside domain",
        },
    ]
    monkeypatch.setattr(cli, "_validate_fields", lambda *_args: results)

    with pytest.raises(cli.FieldValidationError):
        cli.run(
            arguments(
                request=request_path,
                output=output_path,
                validation_output=validation_path,
            )
        )

    published = json.loads(validation_path.read_text())
    assert published["results"] == results
    assert (
        published["source_bytes_sha256"]
        == sha256(request_bytes).hexdigest()
    )
    assert not output_path.exists()


def test_parser_requires_exactly_one_input_mode():
    parse = cli.parser().parse_args
    with pytest.raises(SystemExit):
        parse([])
    with pytest.raises(SystemExit):
        parse(["--direct", "--request", "/request.json"])
    assert parse(["--direct"]).direct


@pytest.mark.parametrize(
    ("error", "status"),
    (
        (cli.ProtocolInputError("input"), 3),
        (cli.FieldValidationError([{
            "field_id": "field",
            "status": "invalid",
            "code": "code",
        }]), 4),
        (cli.ValidatedSubsetError("stale"), 5),
        (cli.PublicationError("path"), 6),
        (RuntimeError("science"), 7),
    ),
)
def test_main_maps_expected_failures_without_tracebacks(
    error, status, monkeypatch, capsys
):
    monkeypatch.setattr(
        cli,
        "parser",
        lambda: Namespace(parse_args=lambda _argv: arguments(direct=True)),
    )

    def fail(_arguments):
        raise error

    monkeypatch.setattr(cli, "run", fail)
    assert cli.main([]) == status
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "wenu_satellite_crossings:" in captured.err
    assert "Traceback" not in captured.err


def test_packaged_protocol_schemas_close_every_declared_object():
    root = Path(__file__).resolve().parents[1] / "src/wenu/data"
    for name in (
        "satellite_crossing_request_v1.schema.json",
        "satellite_crossing_validation_v1.schema.json",
        "satellite_crossing_bundle_manifest_v1.schema.json",
    ):
        schema = json.loads((root / name).read_text(encoding="utf-8"))
        pending = [schema]
        while pending:
            value = pending.pop()
            if isinstance(value, dict):
                if value.get("type") == "object":
                    assert value.get("additionalProperties") is False
                pending.extend(value.values())
            elif isinstance(value, list):
                pending.extend(value)


@pytest.mark.parametrize("mode", ("direct", "request", "validated-request"))
def test_cli_bundles_consume_kernel_results_and_recheck_live_services(
    tmp_path, monkeypatch, capsys, mode
):
    """Installed synthetic elements; actual CLI/coordinator/kernel/observer chain.

    Altitude admission alone is synthetic, not an observational certificate.
    Single-instant fields test transport, not continuous crossing completeness.
    """
    from dataclasses import asdict, replace
    from importlib import resources
    from types import SimpleNamespace
    import socket
    from wenu_kernel.errors import UnsupportedCapability
    from wenu_kernel.kernel import KernelSession
    from wenu.satellites import load_snapshot
    from wenu.satellites.topocentric import SatelliteFieldCenterAltitudeEvaluator
    from test_satellite_crossing_acceleration import field, observer, start_state, START, iso

    snapshot = load_snapshot()
    state = start_state(snapshot, snapshot.records[0])
    directory = tmp_path / "snapshot"
    directory.mkdir()
    source = resources.files("wenu.data.satellites.snapshots.synthetic_50s4b_v1")
    for name in ("manifest.json", "records.json"):
        (directory / name).write_bytes(source.joinpath(name).read_bytes())
    request = request_document()
    request.pop("request_identity_sha256")
    request["snapshot"] = dict(directory=str(directory), snapshot_id=snapshot.manifest.snapshot_id,
                               content_sha256=snapshot.manifest.content_sha256)
    request["observer"] = asdict(observer())
    request["fields"] = []
    for name, longitude, latitude in (
        ("positive — Ω", state.gcrs_axis_longitude_deg, state.gcrs_axis_latitude_deg),
        ("opposite — 零", (state.gcrs_axis_longitude_deg + 180.) % 360., -state.gcrs_axis_latitude_deg),
    ):
        fov = replace(field(longitude, latitude), field_id=name)
        spec = asdict(fov.coordinate_spec)
        spec["position_status"] = fov.coordinate_spec.position_status.value
        spec["corrections"] = sorted(spec["corrections"])
        spec["provenance"] = list(spec["provenance"])
        request["fields"].append(dict(
            field_id=name, center_longitude_deg=longitude, center_latitude_deg=latitude,
            angular_radius_deg=fov.angular_radius_deg, coordinate_spec=spec, boundary=fov.boundary,
            interval=dict(start=iso(START), stop=iso(START), time_scale="utc", boundary="inclusive"),
            time_tolerance_seconds=.01, angular_tolerance_deg=1e-5))
    request = cli._signed(request)
    phase = {"altitude": 60., "invalid": None}
    def altitude(_self, fov, site, instant):
        assert site == observer() and instant == iso(START)
        return (0. if fov.field_id == phase["invalid"] else phase["altitude"],
                SimpleNamespace(source_sha256="e" * 64))
    monkeypatch.setattr(SatelliteFieldCenterAltitudeEvaluator, "evaluate", altitude)
    def forbidden(*_args, **_kwargs):
        raise AssertionError("network access is forbidden")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    request_path = tmp_path / "request.json"
    request_path.write_text(cli._pretty(request), encoding="utf-8")
    if mode == "direct":
        inputs = ["--direct", "--snapshot-directory", str(directory),
                  "--snapshot-id", snapshot.manifest.snapshot_id,
                  "--snapshot-sha256", snapshot.manifest.content_sha256,
                  "--created-utc", request["created_utc"],
                  "--observer-json", cli._canonical(request["observer"]),
                  "--policy-json", cli._canonical(request["policy"])]
        for fov in request["fields"]:
            inputs.extend(("--field", cli._canonical(fov)))
    elif mode == "request":
        inputs = ["--request", str(request_path)]
    else:
        validation_path = tmp_path / "validation.json"
        phase["invalid"] = "opposite — 零"
        assert cli.main(["--request", str(request_path), "--output", str(tmp_path / "not-published"),
                         "--validation-output", str(validation_path)]) == 4
        assert not (tmp_path / "not-published").exists()
        validation = json.loads(validation_path.read_text(encoding="utf-8"))
        assert [v["status"] for v in validation["results"]] == ["valid", "invalid"]
        assert validation["source_bytes_sha256"] == sha256(request_path.read_bytes()).hexdigest()
        inputs = ["--validated-request", str(validation_path)]
    original = KernelSession.evaluate
    calls = []
    def tracked(session, query):
        calls.append(query)
        return original(session, query)
    monkeypatch.setattr(KernelSession, "evaluate", tracked)
    def execute(name, status):
        destination = tmp_path / name
        assert cli.main([*inputs, "--output", str(destination)]) == status
        if status:
            assert not destination.exists()
            assert not tuple(tmp_path.glob(f".{name}.*"))
            return None
        manifest = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
        cli._identity(manifest)
        for item in manifest["files"]:
            raw = (destination / item["filename"]).read_bytes()
            assert len(raw) == item["byte_count"] and sha256(raw).hexdigest() == item["sha256"]
        reports = (
            cli.ExactSatelliteCrossingReport.from_json((destination / "report.json").read_bytes()),
            cli.ExactSatelliteCrossingReport.from_ecsv((destination / "report.ecsv").read_bytes()),
            cli.ExactSatelliteCrossingReport.from_votable((destination / "report.vot").read_bytes()))
        assert reports[0] == reports[1] == reports[2]
        assert reports[0].report_identity_sha256 == manifest["report_identity_sha256"]
        assert manifest["snapshot_content_sha256"] == snapshot.manifest.content_sha256
        return reports[0]
    before = execute("before", 0)
    fields = before.document["fields"]
    assert fields[0]["crossings"][0]["norad_catalog_id"] == snapshot.records[0].norad_catalog_id
    assert fields[0]["airmass_admission"]["earth_orientation_sha256"] == ["e" * 64]
    if mode != "validated-request":
        assert fields[1]["crossings"] == []
    assert calls and all(q.reference.frame_id == "teme" for q in calls)
    def mirrored(session, query):
        batch = tracked(session, query)
        return replace(batch, states=tuple(replace(row,
            position_m=tuple(-x for x in row.position_m),
            velocity_m_s=tuple(-x for x in row.velocity_m_s)) for row in batch.states))
    monkeypatch.setattr(KernelSession, "evaluate", mirrored)
    after = execute("after", 0)
    assert after.document["fields"][0]["crossings"] == []
    assert after.report_identity_sha256 != before.report_identity_sha256
    preserved = {p.name: p.read_bytes() for p in (tmp_path / "before").iterdir()}
    def unavailable(*_args, **_kwargs):
        raise UnsupportedCapability("current satellite state refused")
    monkeypatch.setattr(KernelSession, "evaluate", unavailable)
    execute("refused", 7)
    phase["altitude"] = 29.
    if mode == "request":
        # Initial invalid file requests require a separate validation destination.
        assert cli.main([*inputs, "--output", str(tmp_path / "stale"),
                         "--validation-output", str(tmp_path / "stale-validation.json")]) == 4
        assert not (tmp_path / "stale").exists()
    else:
        execute("stale", 5 if mode == "validated-request" else 4)
    assert preserved == {p.name: p.read_bytes() for p in (tmp_path / "before").iterdir()}
    assert "Traceback" not in capsys.readouterr().err


@pytest.mark.parametrize("failure", ("write", "race"))
def test_bundle_failure_is_atomic_and_preserves_other_writer(tmp_path, monkeypatch, failure):
    from test_satellite_crossing_reports import report, field_result
    value = report(field_result("publication — Ω"))
    destination = tmp_path / "bundle"
    if failure == "write":
        original = cli._write_exclusive
        def failed(path, data):
            if path.name == "report.ecsv":
                raise OSError("injected staged write failure")
            return original(path, data)
        monkeypatch.setattr(cli, "_write_exclusive", failed)
    else:
        original = cli._rename_noreplace
        def raced(source, target):
            target.mkdir()
            (target / "other-writer").write_bytes(b"retained")
            return original(source, target)
        monkeypatch.setattr(cli, "_rename_noreplace", raced)
    with pytest.raises(OSError):
        cli._publish_bundle(destination, value, request_mode="direct", request_identity="a" * 64)
    assert not tuple(tmp_path.glob(".bundle.*"))
    if failure == "write":
        assert not destination.exists()
    else:
        assert [p.name for p in destination.iterdir()] == ["other-writer"]
        assert (destination / "other-writer").read_bytes() == b"retained"
