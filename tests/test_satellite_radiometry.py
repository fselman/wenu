"""Offline native-grid direct-Sun spectral radiometry tests."""

from dataclasses import FrozenInstanceError, replace
import csv
import importlib.util
from io import StringIO
import json
from pathlib import Path
import sys

import pytest

import wenu.satellites.radiometry as radiometry_module
from wenu.satellites.illumination import (
    AU_KM,
    SatelliteIlluminationGeometry,
    SolarOccultationClass,
    SolarOccultationGeometry,
    SolarOccultationPolicy,
)
from wenu.satellites.radiometry import (
    DIRECT_SOLAR_SPECTRAL_MODEL,
    TSIS1_HSRS_V2_IDENTITY,
    TSIS1_HSRS_V2_INTEGRAL_W_M2,
    TSIS1_HSRS_V2_SAMPLE_COUNT,
    DirectSolarSpectralIrradianceEvaluator,
    DirectSolarSpectralIrradiancePolicy,
    SolarSpectralIrradianceResource,
    SolarSpectralRadiometryError,
    SolarSpectralRadiometryFailureCode,
    load_solar_spectral_irradiance_resource,
)


LIME_INSPECTION_PATH = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "validate_50s7d3b_lime_offline_inspection.py"
)


def load_lime_inspection_module():
    specification = importlib.util.spec_from_file_location(
        "validate_50s7d3b_lime_offline_inspection",
        LIME_INSPECTION_PATH,
    )
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def spectral_resource():
    wavelength = tuple(
        202.0 + 0.1 * index
        for index in range(TSIS1_HSRS_V2_SAMPLE_COUNT)
    )
    # The unit-test specimen exercises composition without pretending to be
    # provider bytes; only the digest-verifying loader admits installed data.
    irradiance_value = TSIS1_HSRS_V2_INTEGRAL_W_M2 / 2528.0
    irradiance = (irradiance_value,) * TSIS1_HSRS_V2_SAMPLE_COUNT
    uncertainty = (0.1,) * TSIS1_HSRS_V2_SAMPLE_COUNT
    bandwidth = (1.0,) * TSIS1_HSRS_V2_SAMPLE_COUNT
    return SolarSpectralIrradianceResource(
        identity=TSIS1_HSRS_V2_IDENTITY,
        wavelength_nm=wavelength,
        irradiance_w_m2_nm=irradiance,
        uncertainty_w_m2_nm=uncertainty,
        bandwidth_nm=bandwidth,
        native_integral_w_m2=TSIS1_HSRS_V2_INTEGRAL_W_M2,
    )


def geometry(*, distance_au=1.0, fraction=1.0):
    instance = object.__new__(SatelliteIlluminationGeometry)
    object.__setattr__(instance, "policy", SolarOccultationPolicy())
    if fraction == 0.0:
        kind = SolarOccultationClass.UMBRA
    elif fraction == 1.0:
        kind = SolarOccultationClass.SUNLIT
    else:
        kind = SolarOccultationClass.PENUMBRA
    occultation = object.__new__(SolarOccultationGeometry)
    object.__setattr__(occultation, "visible_disk_fraction", fraction)
    object.__setattr__(occultation, "occultation_class", kind)
    object.__setattr__(
        occultation,
        "satellite_to_sun_distance_km",
        distance_au * AU_KM,
    )
    object.__setattr__(instance, "solar_occultation", occultation)
    return instance


def test_policy_retains_exact_resource_and_native_grid_contract():
    policy = DirectSolarSpectralIrradiancePolicy()

    assert policy.model == DIRECT_SOLAR_SPECTRAL_MODEL
    assert policy.resource_identity is TSIS1_HSRS_V2_IDENTITY
    assert policy.resource_identity.sample_count == 25_281
    assert policy.resource_identity.sampling_nm == 0.1
    assert policy.resource_identity.resolution_fwhm_nm == 1.0
    assert policy.interpolation == "forbidden"
    assert policy.extrapolation == "forbidden"
    assert policy.renormalization == "forbidden"
    assert policy.integrated_uncertainty_status == "not_evaluated"
    with pytest.raises(FrozenInstanceError):
        policy.interpolation = "linear"


@pytest.mark.parametrize(
    ("distance_au", "fraction", "expected"),
    ((0.5, 1.0, 4.0), (1.0, 0.25, 0.25), (2.0, 1.0, 0.25)),
)
def test_evaluator_scales_native_samples_by_distance_and_visible_fraction(
    distance_au,
    fraction,
    expected,
):
    resource = spectral_resource()
    result = DirectSolarSpectralIrradianceEvaluator(resource).evaluate(
        geometry(distance_au=distance_au, fraction=fraction)
    )

    assert result.wavelength_nm is resource.wavelength_nm
    base = TSIS1_HSRS_V2_INTEGRAL_W_M2 / 2528.0
    assert result.unocculted_irradiance_w_m2_nm[0] == pytest.approx(
        base / distance_au**2
    )
    assert result.incident_irradiance_w_m2_nm[0] == pytest.approx(
        base * expected
    )
    assert result.pointwise_uncertainty_w_m2_nm[0] == pytest.approx(
        0.1 * expected
    )
    assert result.integrated_uncertainty_status == "not_evaluated"
    assert result.resource_identity.content_sha256 in result.identity


def test_umbra_is_evaluated_zero_without_erasing_resource_uncertainty():
    result = DirectSolarSpectralIrradianceEvaluator(
        spectral_resource()
    ).evaluate(geometry(fraction=0.0))

    assert result.occultation_class is SolarOccultationClass.UMBRA
    assert set(result.incident_irradiance_w_m2_nm) == {0.0}
    assert set(result.pointwise_uncertainty_w_m2_nm) == {0.0}
    assert result.integrated_uncertainty_status == "not_evaluated"


def test_energy_integration_uses_exact_native_coordinates_only():
    result = DirectSolarSpectralIrradianceEvaluator(
        spectral_resource()
    ).evaluate(geometry())

    base = TSIS1_HSRS_V2_INTEGRAL_W_M2 / 2528.0
    assert result.integrate_energy(202.0, 202.2) == pytest.approx(
        0.2 * base
    )
    with pytest.raises(SolarSpectralRadiometryError) as caught:
        result.integrate_energy(202.05, 202.2)
    assert (
        caught.value.code
        is SolarSpectralRadiometryFailureCode.OFF_NATIVE_GRID
    )


def test_unsupported_policy_fails_closed():
    policy = replace(
        DirectSolarSpectralIrradiancePolicy(),
        renormalization="1361 W m-2",
    )
    with pytest.raises(SolarSpectralRadiometryError) as caught:
        DirectSolarSpectralIrradianceEvaluator(
            spectral_resource(),
            policy,
        ).evaluate(geometry())
    assert (
        caught.value.code
        is SolarSpectralRadiometryFailureCode.UNSUPPORTED_MODEL
    )


def test_loader_rejects_missing_and_wrong_byte_identity(tmp_path):
    missing = tmp_path / "missing.csv"
    with pytest.raises(SolarSpectralRadiometryError) as caught:
        load_solar_spectral_irradiance_resource(missing)
    assert (
        caught.value.code
        is SolarSpectralRadiometryFailureCode.RESOURCE_NOT_FOUND
    )

    wrong = tmp_path / "wrong.csv"
    wrong.write_text("not the admitted resource", encoding="utf-8")
    with pytest.raises(SolarSpectralRadiometryError) as caught:
        load_solar_spectral_irradiance_resource(wrong)
    assert (
        caught.value.code
        is SolarSpectralRadiometryFailureCode.RESOURCE_IDENTITY_MISMATCH
    )


def serialized_rows(rows, header=None):
    stream = StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(
        TSIS1_HSRS_V2_IDENTITY.header if header is None else header
    )
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def admitted_rows():
    return [
        (202.0 + 0.1 * index, 1.0, 0.1, 1.0)
        for index in range(TSIS1_HSRS_V2_SAMPLE_COUNT)
    ]


def assert_invalid_verified_payload(payload, expected_code):
    with pytest.raises(SolarSpectralRadiometryError) as caught:
        radiometry_module._parse_verified_spectral_payload(
            payload,
            TSIS1_HSRS_V2_IDENTITY,
        )
    assert caught.value.code is expected_code


def test_verified_parser_rejects_header_and_row_shape():
    rows = admitted_rows()
    assert_invalid_verified_payload(
        serialized_rows(rows, header=("wrong",) * 4),
        SolarSpectralRadiometryFailureCode.RESOURCE_SCHEMA_MISMATCH,
    )
    rows[0] = rows[0][:-1]
    assert_invalid_verified_payload(
        serialized_rows(rows),
        SolarSpectralRadiometryFailureCode.RESOURCE_DATA_INVALID,
    )


@pytest.mark.parametrize(
    ("mutation", "value"),
    (
        ("short_count", None),
        ("duplicate", None),
        ("descending", None),
        ("non_finite", "nan"),
        ("negative_irradiance", -1.0),
        ("negative_uncertainty", -0.1),
        ("wrong_start", 201.9),
        ("wrong_stop", 2730.1),
        ("wrong_spacing", 202.15),
        ("wrong_bandwidth", 0.1),
    ),
)
def test_verified_parser_rejects_invalid_native_resource(mutation, value):
    rows = admitted_rows()
    if mutation == "short_count":
        rows.pop()
    elif mutation == "duplicate":
        rows[1] = (rows[0][0],) + rows[1][1:]
    elif mutation == "descending":
        rows[1], rows[2] = rows[2], rows[1]
    elif mutation == "non_finite":
        rows[100] = (rows[100][0], value, rows[100][2], rows[100][3])
    elif mutation == "negative_irradiance":
        rows[100] = (rows[100][0], value, rows[100][2], rows[100][3])
    elif mutation == "negative_uncertainty":
        rows[100] = (rows[100][0], rows[100][1], value, rows[100][3])
    elif mutation == "wrong_start":
        rows[0] = (value,) + rows[0][1:]
    elif mutation == "wrong_stop":
        rows[-1] = (value,) + rows[-1][1:]
    elif mutation == "wrong_spacing":
        rows[1] = (value,) + rows[1][1:]
    elif mutation == "wrong_bandwidth":
        rows[100] = rows[100][:-1] + (value,)
    assert_invalid_verified_payload(
        serialized_rows(rows),
        SolarSpectralRadiometryFailureCode.RESOURCE_DATA_INVALID,
    )


def test_resource_contract_keeps_audit_integral_distinct_from_bolometric_tsi():
    assert TSIS1_HSRS_V2_INTEGRAL_W_M2 == pytest.approx(
        1325.759295697943
    )
    assert TSIS1_HSRS_V2_INTEGRAL_W_M2 != 1361.0


def test_resource_constructor_enforces_native_grid_invariants():
    resource = spectral_resource()
    invalid = list(resource.wavelength_nm)
    invalid[1] = invalid[0]

    with pytest.raises(ValueError, match="native-grid"):
        replace(resource, wavelength_nm=tuple(invalid))


def test_lime_inspection_freezes_headerless_signed_domain_cases():
    inspection = load_lime_inspection_module()

    rows = list(csv.reader(StringIO(inspection._case_csv())))

    assert len(rows) == 10
    assert all(len(row) == 6 for row in rows)
    assert [float(row[-1]) for row in rows] == [
        -90.001,
        -90.0,
        -15.0,
        -2.0,
        -1.999,
        1.999,
        2.0,
        15.0,
        90.0,
        90.001,
    ]
    assert [case.expected_outside_model_domain for case in inspection.CASES] == [
        True,
        False,
        False,
        False,
        True,
        True,
        False,
        False,
        False,
        True,
    ]


def test_lime_inspection_is_exact_no_install_and_network_denied():
    inspection = load_lime_inspection_module()
    source = LIME_INSPECTION_PATH.read_text(encoding="utf-8")

    assert inspection.PACKAGE_BYTES == 516_220_150
    assert inspection.PACKAGE_SHA256 == (
        "e0a84e250dc4f5beb8a8305278756bbc0b2b136814b9c4defb053970f983ba21"
    )
    assert inspection.COEFFICIENT_SHA256 == (
        "8e6839d95315eb2d797484be559ad70b69010cc1eb9b614770f61bb5ce2cf691"
    )
    assert inspection.SANDBOX_PROFILE == (
        "(version 1) (allow default) (deny network*)"
    )
    assert '"--expand-full"' in source
    assert '"--update"' not in source
    assert '"-u"' not in source
    assert 'Path("/Applications/LimeTBX.app")' in source


def test_lime_inspection_serializes_nonfinite_external_values_as_strict_json():
    inspection = load_lime_inspection_module()

    encoded = inspection._json_text(
        {"values": [float("nan"), float("inf"), float("-inf")]}
    )

    assert json.loads(encoded) == {
        "values": ["NaN", "Infinity", "-Infinity"]
    }
