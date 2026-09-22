"""Offline native-grid direct-Sun spectral radiometry tests."""

from dataclasses import FrozenInstanceError, replace

import pytest

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


def spectral_resource():
    wavelength = tuple(
        202.0 + 0.1 * index
        for index in range(TSIS1_HSRS_V2_SAMPLE_COUNT)
    )
    # The unit-test specimen exercises composition without pretending to be
    # provider bytes; only the digest-verifying loader admits installed data.
    irradiance = (1.0,) * TSIS1_HSRS_V2_SAMPLE_COUNT
    uncertainty = (0.1,) * TSIS1_HSRS_V2_SAMPLE_COUNT
    bandwidth = (1.0,) * TSIS1_HSRS_V2_SAMPLE_COUNT
    return SolarSpectralIrradianceResource(
        identity=TSIS1_HSRS_V2_IDENTITY,
        wavelength_nm=wavelength,
        irradiance_w_m2_nm=irradiance,
        uncertainty_w_m2_nm=uncertainty,
        bandwidth_nm=bandwidth,
        native_integral_w_m2=2528.0,
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
    assert result.unocculted_irradiance_w_m2_nm[0] == pytest.approx(
        1.0 / distance_au**2
    )
    assert result.incident_irradiance_w_m2_nm[0] == pytest.approx(expected)
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

    assert result.integrate_energy(202.0, 202.2) == pytest.approx(0.2)
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


def test_resource_contract_keeps_audit_integral_distinct_from_bolometric_tsi():
    assert TSIS1_HSRS_V2_INTEGRAL_W_M2 == pytest.approx(
        1325.759295697943
    )
    assert TSIS1_HSRS_V2_INTEGRAL_W_M2 != 1361.0
