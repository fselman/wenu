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
