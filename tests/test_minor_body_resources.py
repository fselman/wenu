"""Manifest-backed minor-body source resolution and lifecycle contracts."""

import json
from hashlib import sha256
from types import SimpleNamespace

import pytest

from wenu.comet_designations import parse_comet_designation
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


def install_fakes(monkeypatch, *, target=20000001, coverage=(0.0, 1.0)):
    closes = []
    kernels = []

    class Kernel:
        def __init__(self, path):
            self.path = path
            self.segments = (SimpleNamespace(
                target=target,
                center=10,
                frame_id=1,
                data_type=21,
                start_jd=coverage[0],
                end_jd=coverage[1],
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

    with pytest.raises(KeyError, match="no installed object"):
        collection.resolve("not present")


def comet_manifest_directory(tmp_path, *, designation="2P", target="1000025"):
    payload = b"DAF/fake Encke kernel"
    (tmp_path / "encke.bsp").write_bytes(payload)
    record = {
        "key": "2p",
        "filename": "encke.bsp",
        "sha256": sha256(payload).hexdigest(),
        "spk_file_id": target,
        "actual_coverage": {
            "start_jd_tdb": 2461327.5,
            "stop_jd_tdb": 2461567.5,
        },
        "horizons_result": (
            "2P/Encke\nSoln.date: 2026-Sep-08_14:23:39\n"
            "soln ref.= JPL#K273/14"
        ),
        "identity": {
            "permanent_number": 2,
            "primary_designation": designation,
            "designation_class": "P",
            "name": "Encke",
            "object_class": "comet",
            "provider_spk_id": target,
        },
        "solution": {
            "provider": "NASA/JPL Horizons API",
            "service_version": "1.2",
            "object_class": "comet",
            "primary_designation": designation,
            "horizons_command": "90000091;",
            "provider_spk_id": target,
            "orbit_solution_id": "K273/14",
            "solution_date": "2026-Sep-08_14:23:39",
            "osculating_epoch": "2459936.5 TDB",
            "reference_system": "J2000 ecliptic and equinox",
            "aliases": ["2P/Encke", "Encke"],
            "model_parameters": {"A1": "radial", "A2": "transverse"},
        },
    }
    (tmp_path / "acquisition-report.json").write_text(
        json.dumps({"resources": [record]}), encoding="utf-8"
    )
    return tmp_path


def test_collection_preserves_typed_encke_identity_and_solution(tmp_path):
    collection = MinorBodyResourceCollection(comet_manifest_directory(tmp_path))

    encke = collection.resolve(" 2P/ENCKE ")

    assert collection.resolve("2p") is encke
    assert collection.resolve("encke") is encke
    assert encke.selection_key == "2p"
    assert encke.target == "2p"
    assert encke.entity_key == "comet_2p"
    assert encke.body_class == "comet"
    assert encke.canonical_designation == "2P/Encke"
    assert encke.physical_body_id == "1000025"
    solution = collection.solution_for(encke)
    assert solution.primary_designation == "2P"
    assert solution.horizons_command == "90000091;"
    assert solution.orbit_solution_id == "K273/14"
    assert set(dict(solution.model_parameters)) == {"A1", "A2"}


def test_collection_does_not_treat_2p_as_asteroid_2(tmp_path):
    collection = MinorBodyResourceCollection(comet_manifest_directory(tmp_path))

    with pytest.raises(KeyError, match="no installed object"):
        collection.resolve("2")


def test_session_opens_encke_once_and_checks_comet_coverage(
    tmp_path, monkeypatch
):
    _, source, kernels, closes = install_fakes(
        monkeypatch,
        target=1000025,
        coverage=(2461327.5, 2461567.5),
    )
    observer = SimpleNamespace(timescale=object())
    session = MinorBodyResourceSession(
        comet_manifest_directory(tmp_path), observer
    )
    descriptor = session.collection.resolve("2P")

    assert session.source_binding(descriptor, observer).target_source is source
    assert session.source_binding(descriptor, observer).target_source is source
    assert len(kernels) == 1
    session.close()
    assert closes == kernels


def test_collection_rejects_unbounded_installed_comet(tmp_path):
    with pytest.raises(ValueError, match="only installed comet 2P"):
        MinorBodyResourceCollection(
            comet_manifest_directory(tmp_path, designation="3D")
        )


@pytest.mark.parametrize(
    ("value", "designation_class", "number"),
    (("2P", "P", 2), ("3D", "D", 3), ("1I", "I", 1)),
)
def test_numbered_comet_designations_preserve_class(value, designation_class, number):
    designation = parse_comet_designation(value)

    assert designation.canonical == value
    assert designation.designation_class == designation_class
    assert designation.permanent_number == number


@pytest.mark.parametrize("value", ("C/2020 F3", "P/2011 NO1", "C/2020 F3-A"))
def test_provisional_comet_designations_preserve_structure(value):
    designation = parse_comet_designation(value.lower())

    assert designation.canonical == value
    assert designation.provisional_year is not None


def test_comet_designation_classes_do_not_collapse_to_one_integer():
    assert parse_comet_designation("2P") != parse_comet_designation("2D")
    with pytest.raises(ValueError, match="invalid comet designation"):
        parse_comet_designation("2")
