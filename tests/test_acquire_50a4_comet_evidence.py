"""Contracts for deliberate 50A.4 comet evidence acquisition."""

import pytest

from tools.acquire_50a4_comet_evidence import (
    _epochs,
    _horizons_parameters,
    _sbdb_identity,
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
    obj, orbit, perihelion = _sbdb_identity(_sbdb())

    assert obj["des"] == "2P"
    assert orbit["model_pars"][0]["name"] == "A1"
    assert perihelion == 2461446.5


def test_sbdb_identity_rejects_gravity_only_solution():
    document = _sbdb([{"name": "J2", "value": "1"}])

    with pytest.raises(ValueError, match="non-gravitational"):
        _sbdb_identity(document)


def test_epochs_are_symmetric_around_provider_perihelion_day():
    epochs = _epochs(2461446.5)

    assert len(epochs) == 3
    assert epochs[0].endswith("T00:00:00Z")
    assert epochs[1].endswith("T00:00:00Z")
    assert epochs[2].endswith("T00:00:00Z")


def test_horizons_requests_freeze_vector_and_observer_policies():
    epochs = ("2026-11-01T00:00:00Z", "2027-02-01T00:00:00Z")

    vectors = _horizons_parameters("vectors", epochs)
    topocentric = _horizons_parameters(
        "observer", epochs, topocentric=True
    )

    assert vectors["CENTER"] == "'@0'"
    assert vectors["VEC_CORR"] == "'NONE'"
    assert vectors["REF_PLANE"] == "'FRAME'"
    assert vectors["TIME_TYPE"] == "'TDB'"
    assert vectors["TLIST"] == (
        "'2026-11-01T00:00:00','2027-02-01T00:00:00'"
    )
    assert topocentric["CENTER"] == "'coord@399'"
    assert topocentric["APPARENT"] == "'AIRLESS'"
    assert topocentric["QUANTITIES"] == "'1,20,21,45'"
    assert topocentric["TIME_TYPE"] == "'UT'"
    assert topocentric["SITE_COORD"] == "'-71.230289,-32.443342,0.052'"
