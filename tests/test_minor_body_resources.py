"""Manifest-backed minor-body source resolution and lifecycle contracts."""

import json
from hashlib import sha256
from types import SimpleNamespace

import pytest

from wenu.minor_body_resources import (
    MinorBodyResourceCollection,
    MinorBodyResourceSession,
)
from wenu.sky.ceres import CERES_BODY


def manifest_directory(tmp_path, *, digest=None, target="20000001"):
    payload = b"DAF/fake Ceres kernel"
    (tmp_path / "ceres.bsp").write_bytes(payload)
    record = {
        "key": "ceres",
        "filename": "ceres.bsp",
        "sha256": digest or sha256(payload).hexdigest(),
        "spk_file_id": target,
        "horizons_result": (
            "1 Ceres\nSoln.date: 2021-Apr-13_11:04:44\n"
            "soln ref.= JPL#48"
        ),
    }
    (tmp_path / "acquisition-report.json").write_text(
        json.dumps({"resources": [record]}), encoding="utf-8"
    )
    return tmp_path


def install_fakes(monkeypatch):
    closes = []
    kernels = []

    class Kernel:
        def __init__(self, path):
            self.path = path
            self.segments = (SimpleNamespace(
                target=20000001,
                center=10,
                frame_id=1,
                data_type=21,
            ),)
            kernels.append(self)

        def close(self):
            closes.append(self)

    planetary = SimpleNamespace(resource=SimpleNamespace(sha256="p" * 64))
    source = object()
    monkeypatch.setattr(
        "wenu.minor_body_resources.SpiceMinorBodyKernel", Kernel
    )
    monkeypatch.setattr(
        "wenu.minor_body_resources.SkyfieldEphemerisStateSource.from_observer",
        lambda observer: planetary,
    )
    monkeypatch.setattr(
        "wenu.minor_body_resources.SkyfieldMinorBodyStateSource.from_kernels",
        lambda **values: source,
    )
    return planetary, source, kernels, closes


def test_session_resolves_ceres_once_and_closes_one_kernel(tmp_path, monkeypatch):
    planetary, source, kernels, closes = install_fakes(monkeypatch)
    observer = SimpleNamespace(timescale=object())
    session = MinorBodyResourceSession(
        manifest_directory(tmp_path), observer
    )

    first = session.source_binding(CERES_BODY, observer)
    second = session.source_binding(CERES_BODY, observer)

    assert first.target_source is source
    assert first.observer_source is planetary
    assert second == first
    assert len(kernels) == 1
    session.close()
    session.close()
    assert closes == kernels


def test_session_rejects_digest_target_and_observer_mismatch(
    tmp_path, monkeypatch
):
    install_fakes(monkeypatch)
    observer = SimpleNamespace(timescale=object())
    directory = manifest_directory(tmp_path, digest="0" * 64)
    session = MinorBodyResourceSession(directory, observer)
    with pytest.raises(ValueError, match="digest differs"):
        session.source_binding(CERES_BODY, observer)
    with pytest.raises(ValueError, match="different observer"):
        session.source_binding(CERES_BODY, object())


def test_session_requires_manifest_and_declared_ceres_record(
    tmp_path, monkeypatch
):
    install_fakes(monkeypatch)
    observer = SimpleNamespace(timescale=object())
    with pytest.raises(FileNotFoundError, match="acquisition manifest"):
        MinorBodyResourceSession(tmp_path, observer)

    (tmp_path / "acquisition-report.json").write_text(
        json.dumps({"resources": []}), encoding="utf-8"
    )
    session = MinorBodyResourceSession(tmp_path, observer)
    with pytest.raises(FileNotFoundError, match="no resource for 'ceres'"):
        session.source_binding(CERES_BODY, observer)


def numbered_manifest_directory(tmp_path, *, name=None):
    record = {
        "key": "79989",
        "filename": "79989.bsp",
        "sha256": "0" * 64,
        "spk_file_id": "20079989",
        "horizons_result": (
            "1999 FH4\nSoln.date: 2026-Sep-11\nsoln ref.= JPL#1"
        ),
        "identity": {
            "permanent_number": 79989,
            "primary_designation": "1999 FH4",
            "name": name,
            "object_class": "asteroid",
            "provider_spk_id": "20079989",
            "classifications": ["main_belt"],
        },
        "solution": {
            "provider": "NASA/JPL Horizons API",
            "service_version": "1.2",
            "object_class": "asteroid",
            "primary_designation": "1999 FH4",
            "horizons_command": "79989;",
            "provider_spk_id": "20079989",
            "orbit_solution_id": "JPL#1",
            "solution_date": "2026-Sep-11",
            "osculating_epoch": "2461294.5 TDB",
            "reference_system": "ICRF/J2000",
        },
    }
    (tmp_path / "acquisition-report.json").write_text(
        json.dumps({"resources": [record]}), encoding="utf-8"
    )
    return tmp_path


def test_collection_resolves_number_and_installed_official_name(tmp_path):
    collection = MinorBodyResourceCollection(
        numbered_manifest_directory(tmp_path, name="Future Name")
    )

    numbered = collection.resolve("79989")
    named = collection.resolve("  future NAME ")

    assert named is numbered
    assert numbered.selection_key == "79989"
    assert numbered.entity_key == "asteroid_79989"
    assert numbered.canonical_designation == "Future Name (79989)"
    assert collection.solution_for(numbered).iau_number == 79989


def test_collection_rejects_uninstalled_name(tmp_path):
    collection = MinorBodyResourceCollection(
        numbered_manifest_directory(tmp_path)
    )

    with pytest.raises(KeyError, match="no installed asteroid"):
        collection.resolve("not present")
