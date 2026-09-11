"""Manifest-backed minor-body source resolution and lifecycle contracts."""

import json
from hashlib import sha256
from types import SimpleNamespace

import pytest

from wenu.minor_body_resources import MinorBodyResourceSession
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
            "1 Ceres\nJPL 48\n2021-Apr-13_11:04:44"
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
