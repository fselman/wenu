from dataclasses import FrozenInstanceError

import numpy as np
import pytest
from sgp4.api import accelerated

from wenu.satellites import (
    SatelliteElementRecord,
    SatellitePropagationError,
    Sgp4TemePropagator,
    load_snapshot,
    split_julian_date,
)


def record(
    *,
    norad_catalog_id,
    object_name,
    international_designator,
    epoch_utc,
    mean_motion_rev_per_day,
    eccentricity,
    inclination_deg,
    ra_of_ascending_node_deg,
    argument_of_pericenter_deg,
    mean_anomaly_deg,
    bstar,
    mean_motion_dot,
    mean_motion_ddot,
):
    return SatelliteElementRecord(
        object_name=object_name,
        international_designator=international_designator,
        norad_catalog_id=norad_catalog_id,
        classification="U",
        epoch_utc=epoch_utc,
        mean_motion_rev_per_day=mean_motion_rev_per_day,
        eccentricity=eccentricity,
        inclination_deg=inclination_deg,
        ra_of_ascending_node_deg=ra_of_ascending_node_deg,
        argument_of_pericenter_deg=argument_of_pericenter_deg,
        mean_anomaly_deg=mean_anomaly_deg,
        bstar=bstar,
        mean_motion_dot=mean_motion_dot,
        mean_motion_ddot=mean_motion_ddot,
        ephemeris_type=0,
        element_set_number=1,
        revolution_number_at_epoch=1,
        source_identity="Vallado SGP4 verification case",
        source_record_sha256="0" * 64,
        provenance=(
            "AIAA 2006-6753 SGP4 verification input.",
            "Copied from upstream SGP4-VER.TLE for wrapper validation.",
        ),
    )


def near_earth_record():
    return record(
        norad_catalog_id=5,
        object_name="VANGUARD 1",
        international_designator="1958-002B",
        epoch_utc="2000-06-27T18:50:19.733568Z",
        mean_motion_rev_per_day=10.82419157,
        eccentricity=0.1859667,
        inclination_deg=34.2682,
        ra_of_ascending_node_deg=348.7242,
        argument_of_pericenter_deg=331.7664,
        mean_anomaly_deg=19.3264,
        bstar=2.8098e-5,
        mean_motion_dot=0.00000023,
        mean_motion_ddot=0.0,
    )


def deep_space_record():
    return record(
        norad_catalog_id=4632,
        object_name="VALLADO DEEP-SPACE CASE",
        international_designator="1970-093B",
        epoch_utc="2004-01-31T21:51:25.308576Z",
        mean_motion_rev_per_day=1.20231981,
        eccentricity=0.1450506,
        inclination_deg=11.4628,
        ra_of_ascending_node_deg=273.1101,
        argument_of_pericenter_deg=207.6,
        mean_anomaly_deg=143.935,
        bstar=0.0001,
        mean_motion_dot=-0.00000084,
        mean_motion_ddot=0.0,
    )


@pytest.mark.parametrize(
    ("element", "position", "velocity"),
    [
        (
            near_earth_record(),
            (7022.46529266, -1400.08296755, 0.03995155),
            (1.893841015, 6.405893759, 4.534807250),
        ),
        (
            deep_space_record(),
            (2334.11450085, -41920.44035349, -0.03867437),
            (2.826321032, -0.065091664, 0.570936053),
        ),
    ],
)
def test_pinned_vallado_near_earth_and_deep_space_epoch_vectors(
    element, position, velocity
):
    state = Sgp4TemePropagator(element).propagate(element.epoch_utc)

    assert state.status_code == 0
    assert state.position_km == pytest.approx(position, abs=5e-7)
    assert state.velocity_km_per_s == pytest.approx(velocity, abs=5e-10)
    assert state.element_age_days == pytest.approx(0.0, abs=1e-14)
    assert state.frame == "TEME"
    assert state.center == "EARTH"
    assert state.representation == "geocentric geometric Cartesian"
    assert state.gravity_model == "WGS-72"
    assert state.operation_mode == "improved"


def test_split_julian_date_preserves_midnight_fraction_and_microseconds():
    normalized, jd, fraction = split_julian_date(
        "2026-09-15T00:00:00.000001Z"
    )

    assert normalized == "2026-09-15T00:00:00.000001Z"
    assert jd == 2461298.5
    assert fraction == pytest.approx(1e-6 / 86400.0, abs=1e-18)


def test_snapshot_records_propagate_with_identity_and_provenance():
    snapshot = load_snapshot()
    state = Sgp4TemePropagator(
        snapshot.records[0],
        snapshot_sha256=snapshot.manifest.content_sha256,
    ).propagate("2026-09-15T00:10:00Z")

    assert state.norad_catalog_id == 300001
    assert state.snapshot_sha256 == snapshot.manifest.content_sha256
    assert state.source_record_sha256 == snapshot.records[0].source_record_sha256
    assert state.sgp4_version
    assert state.implementation.startswith("python-sgp4 Vallado")
    assert state.element_age_days == pytest.approx(10.0 / 1440.0)
    assert all(np.isfinite(state.position_km))
    assert all(np.isfinite(state.velocity_km_per_s))
    with pytest.raises(FrozenInstanceError):
        state.position_km = (0.0, 0.0, 0.0)


def test_scalar_and_array_routes_have_submillimetre_parity():
    propagator = Sgp4TemePropagator(near_earth_record())
    instants = (
        "2000-06-27T18:50:19.733568Z",
        "2000-06-28T00:50:19.733568Z",
        "2000-06-30T18:50:19.733568Z",
    )

    scalar = tuple(propagator.propagate(value) for value in instants)
    array = propagator.propagate_many(instants)

    assert [item.evaluation_utc for item in array] == [
        item.evaluation_utc for item in scalar
    ]
    for expected, actual in zip(scalar, array):
        assert actual.position_km == pytest.approx(
            expected.position_km, abs=1e-6
        )
        assert actual.velocity_km_per_s == pytest.approx(
            expected.velocity_km_per_s, abs=1e-9
        )
        assert actual.status_code == expected.status_code
    assert ("C++" in array[0].implementation) is accelerated


def test_nonzero_sgp4_status_fails_explicitly():
    decaying = record(
        norad_catalog_id=44160,
        object_name="UPSTREAM ERROR CASE",
        international_designator="2019-006AX",
        epoch_utc="2020-06-10T19:07:51.381408Z",
        mean_motion_rev_per_day=15.58006382,
        eccentricity=0.0216413,
        inclination_deg=95.2472,
        ra_of_ascending_node_deg=272.0808,
        argument_of_pericenter_deg=32.6694,
        mean_anomaly_deg=328.7739,
        bstar=0.0034711,
        mean_motion_dot=0.00816806,
        mean_motion_ddot=0.00019088,
    )

    with pytest.raises(SatellitePropagationError) as raised:
        Sgp4TemePropagator(decaying).propagate(
            "2020-06-11T19:07:51.381408Z"
        )

    assert raised.value.code == 1
    assert raised.value.norad_catalog_id == 44160
    assert "mean eccentricity" in raised.value.sgp4_message.lower()


def test_empty_array_route_is_deterministic():
    assert Sgp4TemePropagator(near_earth_record()).propagate_many(()) == ()
