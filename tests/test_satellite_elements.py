from dataclasses import FrozenInstanceError
import hashlib
from importlib import resources
import json

import pytest

from wenu.satellites import (
    DEFAULT_SNAPSHOT_ID,
    SatelliteElementRecord,
    SatelliteElementSnapshot,
    SatelliteSnapshotManifest,
    load_snapshot,
    load_snapshot_directory,
)
from wenu.satellites.elements import canonical_json_bytes
from wenu.satellites.snapshots import snapshot_from_bytes


def test_installed_snapshot_is_canonical_ordered_and_synthetic():
    value = load_snapshot()

    assert value.manifest.snapshot_id == DEFAULT_SNAPSHOT_ID
    assert value.manifest.record_count == 3
    assert tuple(value.by_norad_catalog_id) == (300001, 300002, 300003)
    assert [record.mean_motion_rev_per_day for record in value.records] == [
        15.5,
        2.0056,
        1.0027,
    ]
    for record in value.records:
        assert record.object_name.startswith("WENU SYNTHETIC")
        assert record.center_name == "EARTH"
        assert record.reference_frame == "TEME"
        assert record.time_system == "UTC"
        assert record.mean_element_theory == "SGP4"
        assert "Not derived from a tracked object" in record.provenance[1]
    assert "No live provider record" in value.manifest.provenance[1]
    assert "Synthetic non-operational" in value.manifest.warnings[0]


def test_records_snapshot_and_lookup_are_immutable():
    value = load_snapshot()

    with pytest.raises(FrozenInstanceError):
        value.records[0].object_name = "changed"
    with pytest.raises(TypeError):
        value.by_norad_catalog_id[300001] = value.records[1]
    assert isinstance(value.records, tuple)


def test_full_six_digit_norad_identifiers_are_not_truncated():
    value = load_snapshot()

    assert value.records[0].norad_catalog_id == 300001
    assert value.by_norad_catalog_id[300001] is value.records[0]


def test_snapshot_rejects_duplicate_or_unsorted_identifiers():
    value = load_snapshot()
    manifest = value.manifest

    with pytest.raises(ValueError, match="duplicate"):
        SatelliteElementSnapshot(
            manifest=manifest,
            records=(value.records[0], value.records[0], value.records[2]),
        )
    with pytest.raises(ValueError, match="ordered"):
        SatelliteElementSnapshot(
            manifest=manifest,
            records=tuple(reversed(value.records)),
        )


def test_record_rejects_wrong_omm_semantics_and_nonfinite_values():
    record = load_snapshot().records[0]
    values = dict(record.__dict__)

    with pytest.raises(ValueError, match="reference_frame"):
        SatelliteElementRecord(**{**values, "reference_frame": "ICRS"})
    with pytest.raises(ValueError, match="mean_element_theory"):
        SatelliteElementRecord(
            **{**values, "mean_element_theory": "SGP8"}
        )
    with pytest.raises(ValueError, match="eccentricity"):
        SatelliteElementRecord(**{**values, "eccentricity": 1.0})
    with pytest.raises(ValueError, match="finite"):
        SatelliteElementRecord(**{**values, "bstar": float("nan")})


def test_record_source_digest_fails_closed_after_mutation():
    root = resources.files(
        "wenu.data.satellites.snapshots"
    ).joinpath(DEFAULT_SNAPSHOT_ID)
    records = json.loads(root.joinpath("records.json").read_bytes())
    records[0]["MEAN_MOTION"] += 0.1
    records_bytes = canonical_json_bytes(records)
    manifest = json.loads(root.joinpath("manifest.json").read_bytes())
    manifest["content_sha256"] = hashlib.sha256(records_bytes).hexdigest()

    with pytest.raises(ValueError, match="source_record_sha256"):
        snapshot_from_bytes(
            json.dumps(manifest).encode("utf-8"),
            records_bytes,
        )


def test_snapshot_digest_and_canonical_bytes_fail_closed():
    root = resources.files(
        "wenu.data.satellites.snapshots"
    ).joinpath(DEFAULT_SNAPSHOT_ID)
    manifest = root.joinpath("manifest.json").read_bytes()
    records = root.joinpath("records.json").read_bytes()

    changed = records.replace(b"15.5", b"15.6", 1)
    with pytest.raises(ValueError, match="content_sha256"):
        snapshot_from_bytes(manifest, changed)

    pretty = json.dumps(json.loads(records), indent=2).encode("utf-8")
    with pytest.raises(ValueError, match="canonical JSON"):
        snapshot_from_bytes(manifest, pretty)


def test_manifest_count_is_enforced():
    value = load_snapshot()
    values = dict(value.manifest.__dict__)
    bad = SatelliteSnapshotManifest(**{**values, "record_count": 2})

    with pytest.raises(ValueError, match="record_count"):
        SatelliteElementSnapshot(manifest=bad, records=value.records)


def _copy_installed_snapshot(directory):
    root = resources.files(
        "wenu.data.satellites.snapshots"
    ).joinpath(DEFAULT_SNAPSHOT_ID)
    directory.mkdir()
    for name in ("manifest.json", "records.json"):
        (directory / name).write_bytes(root.joinpath(name).read_bytes())


def test_explicit_snapshot_directory_reuses_complete_validation(tmp_path):
    directory = tmp_path / "caller-selected-name"
    _copy_installed_snapshot(directory)

    external = load_snapshot_directory(directory)
    installed = load_snapshot()

    assert external == installed
    assert external.manifest.snapshot_id == DEFAULT_SNAPSHOT_ID
    assert tuple(external.by_norad_catalog_id) == (
        300001,
        300002,
        300003,
    )


def test_explicit_snapshot_directory_fails_closed_on_invalid_paths(tmp_path):
    missing = tmp_path / "missing"
    with pytest.raises(ValueError, match="existing non-symlink directory"):
        load_snapshot_directory(missing)
    with pytest.raises(TypeError, match="string or path-like"):
        load_snapshot_directory(b"snapshot")

    ordinary_file = tmp_path / "ordinary-file"
    ordinary_file.write_text("not a directory", encoding="utf-8")
    with pytest.raises(ValueError, match="existing non-symlink directory"):
        load_snapshot_directory(ordinary_file)

    directory = tmp_path / "without-manifest"
    directory.mkdir()
    with pytest.raises(ValueError, match="manifest.json"):
        load_snapshot_directory(directory)


def test_explicit_snapshot_directory_rejects_symlink_resources(tmp_path):
    source = tmp_path / "source"
    _copy_installed_snapshot(source)

    linked_directory = tmp_path / "linked-directory"
    linked_directory.symlink_to(source, target_is_directory=True)
    with pytest.raises(ValueError, match="non-symlink directory"):
        load_snapshot_directory(linked_directory)

    linked_manifest = tmp_path / "linked-manifest"
    linked_manifest.mkdir()
    (linked_manifest / "manifest.json").symlink_to(
        source / "manifest.json"
    )
    (linked_manifest / "records.json").write_bytes(
        (source / "records.json").read_bytes()
    )
    with pytest.raises(ValueError, match="non-symlink manifest.json"):
        load_snapshot_directory(linked_manifest)

    linked_records = tmp_path / "linked-records"
    linked_records.mkdir()
    (linked_records / "manifest.json").write_bytes(
        (source / "manifest.json").read_bytes()
    )
    (linked_records / "records.json").symlink_to(source / "records.json")
    with pytest.raises(ValueError, match="non-symlink regular file"):
        load_snapshot_directory(linked_records)


def test_explicit_snapshot_directory_rejects_escape_and_mutation(tmp_path):
    directory = tmp_path / "snapshot"
    _copy_installed_snapshot(directory)

    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["records_file"] = "../records.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="local resource name"):
        load_snapshot_directory(directory)

    _copy_installed_snapshot(tmp_path / "mutated")
    mutated = tmp_path / "mutated"
    records_path = mutated / "records.json"
    records_path.write_bytes(
        records_path.read_bytes().replace(b"15.5", b"15.6", 1)
    )
    with pytest.raises(ValueError, match="content_sha256"):
        load_snapshot_directory(mutated)
