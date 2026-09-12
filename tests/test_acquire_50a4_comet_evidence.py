"""Contracts for deliberate 50A.4 comet evidence acquisition."""

import pytest

from tools.acquire_50a4_comet_evidence import (
    _epochs,
    _horizons_parameters,
    _sbdb_identity,
    _spk_identity,
    _spk_payload,
    _table_result,
)


def _sbdb(model_parameters=None):
    return {
        "signature": {
            "source": "NASA/JPL Small-Body Database (SBDB) API",
            "version": "1.3",
        },
        "object": {"des": "2P", "kind": "cn", "spkid": "1000025"},
        "orbit": {
            "orbit_id": "K253/1",
            "model_pars": model_parameters or [
                {"name": "A1", "value": "1e-10", "units": "au/d^2"}
            ],
            "elements": [{"name": "tp", "value": "2461446.5"}],
        },
    }


def test_sbdb_identity_requires_exact_numbered_comet_and_model():
    document = _sbdb()
    document["orbit"]["elements"].append(
        {"name": "per", "value": "1207.86"}
    )
    obj, orbit, perihelion, period = _sbdb_identity(document)

    assert obj["des"] == "2P"
    assert orbit["model_pars"][0]["name"] == "A1"
    assert perihelion == 2461446.5
    assert period == 1207.86


def test_sbdb_identity_rejects_gravity_only_solution():
    document = _sbdb([{"name": "J2", "value": "1"}])
    document["orbit"]["elements"].append(
        {"name": "per", "value": "1207.86"}
    )

    with pytest.raises(ValueError, match="non-gravitational"):
        _sbdb_identity(document)


def test_epochs_advance_provider_perihelion_to_2027():
    epochs = _epochs(2460239.895222311, 1207.860100850287)

    assert len(epochs) == 3
    assert epochs[0].endswith("T00:00:00Z")
    assert epochs[1].endswith("T00:00:00Z")
    assert epochs[2].endswith("T00:00:00Z")
    assert all(value.startswith(("2026-", "2027-")) for value in epochs)
    assert epochs[1].startswith("2027-")


def test_horizons_requests_freeze_vector_and_observer_policies():
    epochs = ("2026-11-01T00:00:00Z", "2027-02-01T00:00:00Z")

    vectors = _horizons_parameters("vectors", epochs, "90000091")
    topocentric = _horizons_parameters(
        "observer", epochs, "90000091", topocentric=True
    )

    assert vectors["CENTER"] == "'@0'"
    assert vectors["COMMAND"] == "'90000091;'"
    assert vectors["VEC_CORR"] == "'NONE'"
    assert vectors["REF_PLANE"] == "'FRAME'"
    assert vectors["TIME_TYPE"] == "'TDB'"
    assert vectors["TLIST"].startswith("'24")
    assert vectors["TLIST"].endswith("'")
    assert vectors["TLIST_TYPE"] == "'JD'"
    assert topocentric["CENTER"] == "'coord@399'"
    assert topocentric["APPARENT"] == "'AIRLESS'"
    assert topocentric["QUANTITIES"] == "'1,20,21,45'"
    assert topocentric["TIME_TYPE"] == "'UT'"
    assert topocentric["SITE_COORD"] == "'-71.230289,-32.443342,0.052'"


def test_spk_identity_comes_from_kernel_segment_not_optional_json_field(
    monkeypatch,
):
    class Segment:
        target = 1000025
        center = 10
        data_type = 21
        start_jd = 2461000.5
        end_jd = 2462000.5

    class Kernel:
        def __init__(self, path):
            assert path.read_bytes() == b"DAF/synthetic"
            self.segments = (Segment(),)

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return None

    monkeypatch.setattr(
        "tools.acquire_50a4_comet_evidence.SpiceMinorBodyKernel",
        Kernel,
    )

    identity = _spk_identity(b"DAF/synthetic", "1000025")

    assert identity == {
        "target": "1000025",
        "center": "10",
        "segment_type": 21,
        "coverage_start_jd_tdb": 2461000.5,
        "coverage_end_jd_tdb": 2462000.5,
    }


def test_missing_spk_payload_preserves_horizons_diagnostic():
    with pytest.raises(ValueError, match="No ephemeris for target"):
        _spk_payload({
            "signature": {"source": "NASA/JPL Horizons API"},
            "result": "No ephemeris for target over requested interval",
        })


def test_table_result_rejects_signed_error_and_requires_data_block():
    with pytest.raises(ValueError, match="unreadable TLIST"):
        _table_result({
            "error": "unreadable TLIST",
            "result": "unreadable TLIST",
        }, "vectors")

    assert _table_result(
        {"result": "header\n$$SOE\ndata\n$$EOE\n"}, "vectors"
    ).startswith("header")
