"""Offline direct-Sun spectral radiometry for artificial satellites."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from io import StringIO
from math import fsum, isfinite
from pathlib import Path
from typing import Final

from wenu.satellites.illumination import (
    AU_KM,
    SatelliteIlluminationGeometry,
    SolarOccultationClass,
)


TSIS1_HSRS_V2_PRODUCT: Final = "tsis1_hsrs_1nm"
TSIS1_HSRS_V2_SHA256: Final = (
    "1cf3b07e6ac9669c429ad7ce9e92d50dfd741422efcfffa3d1e0eeb5f901616f"
)
TSIS1_HSRS_V2_SOURCE_URL: Final = (
    "https://lasp.colorado.edu/lisird/latis/dap/tsis1_hsrs_1nm.csv"
)
TSIS1_HSRS_V2_DOI: Final = "10.25980/ta3f-7h90"
TSIS1_HSRS_V2_BYTE_COUNT: Final = 1_298_915
TSIS1_HSRS_V2_SAMPLE_COUNT: Final = 25_281
TSIS1_HSRS_V2_MINIMUM_NM: Final = 202.0
TSIS1_HSRS_V2_MAXIMUM_NM: Final = 2730.0
TSIS1_HSRS_V2_SAMPLING_NM: Final = 0.1
TSIS1_HSRS_V2_RESOLUTION_FWHM_NM: Final = 1.0
TSIS1_HSRS_V2_INTEGRAL_W_M2: Final = 1325.759295697943
TSIS1_HSRS_V2_HEADER: Final = (
    "wavelength (nm)",
    "irradiance (W/m^2/nm)",
    "uncertainty (W/m^2/nm)",
    "bandwidth (nm)",
)
DIRECT_SOLAR_SPECTRAL_MODEL: Final = (
    "tsis-1-hsrs-v2-native-grid-uniform-disk-v1"
)


class SolarSpectralRadiometryFailureCode(str, Enum):
    """Stable terminal failures owned by spectral solar radiometry."""

    RESOURCE_NOT_FOUND = "resource_not_found"
    RESOURCE_IDENTITY_MISMATCH = "resource_identity_mismatch"
    RESOURCE_SCHEMA_MISMATCH = "resource_schema_mismatch"
    RESOURCE_DATA_INVALID = "resource_data_invalid"
    UNSUPPORTED_MODEL = "unsupported_model"
    INCONSISTENT_GEOMETRY = "inconsistent_geometry"
    OFF_NATIVE_GRID = "off_native_grid"


class SolarSpectralRadiometryError(ValueError):
    """Typed fail-closed spectral radiometry error."""

    def __init__(self, code, message):
        if not isinstance(code, SolarSpectralRadiometryFailureCode):
            raise TypeError(
                "code must be a SolarSpectralRadiometryFailureCode."
            )
        super().__init__(str(message))
        self.code = code


@dataclass(frozen=True)
class SolarSpectralIrradianceResourceIdentity:
    """Exact externally installed TSIS-1 HSRS v2 resource identity."""

    doi: str = TSIS1_HSRS_V2_DOI
    product: str = TSIS1_HSRS_V2_PRODUCT
    source_url: str = TSIS1_HSRS_V2_SOURCE_URL
    access_date: str = "2026-09-22"
    byte_count: int = TSIS1_HSRS_V2_BYTE_COUNT
    content_sha256: str = TSIS1_HSRS_V2_SHA256
    header: tuple[str, ...] = TSIS1_HSRS_V2_HEADER
    wavelength_unit: str = "nm"
    irradiance_unit: str = "W m-2 nm-1"
    uncertainty_unit: str = "W m-2 nm-1"
    sample_count: int = TSIS1_HSRS_V2_SAMPLE_COUNT
    minimum_wavelength_nm: float = TSIS1_HSRS_V2_MINIMUM_NM
    maximum_wavelength_nm: float = TSIS1_HSRS_V2_MAXIMUM_NM
    sampling_nm: float = TSIS1_HSRS_V2_SAMPLING_NM
    resolution_fwhm_nm: float = TSIS1_HSRS_V2_RESOLUTION_FWHM_NM
    redistribution_status: str = "not_established_external_install_only"

    def __post_init__(self):
        expected = (
            self.doi == TSIS1_HSRS_V2_DOI
            and self.product == TSIS1_HSRS_V2_PRODUCT
            and self.source_url == TSIS1_HSRS_V2_SOURCE_URL
            and self.byte_count == TSIS1_HSRS_V2_BYTE_COUNT
            and self.content_sha256 == TSIS1_HSRS_V2_SHA256
            and self.header == TSIS1_HSRS_V2_HEADER
            and self.sample_count == TSIS1_HSRS_V2_SAMPLE_COUNT
            and self.minimum_wavelength_nm == TSIS1_HSRS_V2_MINIMUM_NM
            and self.maximum_wavelength_nm == TSIS1_HSRS_V2_MAXIMUM_NM
            and self.sampling_nm == TSIS1_HSRS_V2_SAMPLING_NM
            and self.resolution_fwhm_nm
            == TSIS1_HSRS_V2_RESOLUTION_FWHM_NM
        )
        if not expected:
            raise ValueError("resource identity must be exact TSIS-1 HSRS v2.")


TSIS1_HSRS_V2_IDENTITY: Final = SolarSpectralIrradianceResourceIdentity()


@dataclass(frozen=True)
class SolarSpectralIrradianceResource:
    """Validated immutable native-grid spectral resource."""

    identity: SolarSpectralIrradianceResourceIdentity
    wavelength_nm: tuple[float, ...]
    irradiance_w_m2_nm: tuple[float, ...]
    uncertainty_w_m2_nm: tuple[float, ...]
    bandwidth_nm: tuple[float, ...]
    native_integral_w_m2: float

    def __post_init__(self):
        if self.identity != TSIS1_HSRS_V2_IDENTITY:
            raise ValueError("unsupported spectral resource identity.")
        vectors = (
            self.wavelength_nm,
            self.irradiance_w_m2_nm,
            self.uncertainty_w_m2_nm,
            self.bandwidth_nm,
        )
        if any(len(values) != self.identity.sample_count for values in vectors):
            raise ValueError("spectral resource sample count is inconsistent.")
        if not isfinite(self.native_integral_w_m2):
            raise ValueError("native_integral_w_m2 must be finite.")


def _resource_error(code, message, error=None):
    result = SolarSpectralRadiometryError(code, message)
    if error is not None:
        raise result from error
    raise result


def _native_integral(wavelength_nm, values, start, stop):
    try:
        left = wavelength_nm.index(float(start))
        right = wavelength_nm.index(float(stop))
    except ValueError as error:
        _resource_error(
            SolarSpectralRadiometryFailureCode.OFF_NATIVE_GRID,
            "integration boundaries must be exact native wavelengths.",
            error,
        )
    if left >= right:
        _resource_error(
            SolarSpectralRadiometryFailureCode.OFF_NATIVE_GRID,
            "integration requires increasing native-grid boundaries.",
        )
    return fsum(
        (wavelength_nm[index + 1] - wavelength_nm[index])
        * (values[index + 1] + values[index])
        / 2.0
        for index in range(left, right)
    )


def load_solar_spectral_irradiance_resource(path):
    """Load the one admitted external CSV without network acquisition."""
    resource_path = Path(path)
    try:
        payload = resource_path.read_bytes()
    except OSError as error:
        _resource_error(
            SolarSpectralRadiometryFailureCode.RESOURCE_NOT_FOUND,
            f"unable to read installed spectral resource: {resource_path}",
            error,
        )
    identity = TSIS1_HSRS_V2_IDENTITY
    if len(payload) != identity.byte_count or sha256(payload).hexdigest() != (
        identity.content_sha256
    ):
        _resource_error(
            SolarSpectralRadiometryFailureCode.RESOURCE_IDENTITY_MISMATCH,
            "installed spectral resource byte identity is not admitted.",
        )
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        _resource_error(
            SolarSpectralRadiometryFailureCode.RESOURCE_SCHEMA_MISMATCH,
            "spectral resource must be UTF-8 CSV.",
            error,
        )
    rows = csv.reader(StringIO(text, newline=""))
    try:
        header = tuple(next(rows))
    except StopIteration:
        header = ()
    if header != identity.header:
        _resource_error(
            SolarSpectralRadiometryFailureCode.RESOURCE_SCHEMA_MISMATCH,
            "spectral resource header does not match the admitted schema.",
        )
    columns = ([], [], [], [])
    try:
        for row in rows:
            if len(row) != 4:
                raise ValueError("row must contain four columns")
            for values, value in zip(columns, row, strict=True):
                values.append(float(value))
    except (TypeError, ValueError) as error:
        _resource_error(
            SolarSpectralRadiometryFailureCode.RESOURCE_DATA_INVALID,
            "spectral resource contains invalid numeric data.",
            error,
        )
    wavelength, irradiance, uncertainty, bandwidth = map(tuple, columns)
    if any(len(values) != identity.sample_count for values in columns):
        _resource_error(
            SolarSpectralRadiometryFailureCode.RESOURCE_DATA_INVALID,
            "spectral resource row count is not admitted.",
        )
    if (
        wavelength[0] != identity.minimum_wavelength_nm
        or wavelength[-1] != identity.maximum_wavelength_nm
        or any(
            not isfinite(value) or value < 0.0
            for values in (irradiance, uncertainty)
            for value in values
        )
        or any(not isfinite(value) for value in wavelength)
        or any(
            abs((right - left) - identity.sampling_nm) > 1.0e-10
            for left, right in zip(wavelength, wavelength[1:])
        )
        or any(value != identity.resolution_fwhm_nm for value in bandwidth)
    ):
        _resource_error(
            SolarSpectralRadiometryFailureCode.RESOURCE_DATA_INVALID,
            "spectral resource domain, spacing, values, or bandwidth is invalid.",
        )
    integral = _native_integral(
        wavelength,
        irradiance,
        wavelength[0],
        wavelength[-1],
    )
    if abs(integral - TSIS1_HSRS_V2_INTEGRAL_W_M2) > 1.0e-9:
        _resource_error(
            SolarSpectralRadiometryFailureCode.RESOURCE_DATA_INVALID,
            "spectral resource native-grid integral is inconsistent.",
        )
    return SolarSpectralIrradianceResource(
        identity=identity,
        wavelength_nm=wavelength,
        irradiance_w_m2_nm=irradiance,
        uncertainty_w_m2_nm=uncertainty,
        bandwidth_nm=bandwidth,
        native_integral_w_m2=integral,
    )


@dataclass(frozen=True)
class DirectSolarSpectralIrradiancePolicy:
    """Immutable native-grid TSIS-1 HSRS v2 policy."""

    model: str = DIRECT_SOLAR_SPECTRAL_MODEL
    resource_identity: SolarSpectralIrradianceResourceIdentity = (
        TSIS1_HSRS_V2_IDENTITY
    )
    astronomical_unit_km: float = AU_KM
    compatible_occultation_model: str = (
        "uniform-solar-disk-wgs84-vacuum-ray-quadrature-v1"
    )
    integration_method: str = "native-grid trapezoidal energy integration"
    interpolation: str = "forbidden"
    extrapolation: str = "forbidden"
    renormalization: str = "forbidden"
    integrated_uncertainty_status: str = "not_evaluated"


@dataclass(frozen=True)
class DirectSolarSpectralIrradiance:
    """Immutable direct-Sun native-grid energy spectral irradiance."""

    geometry: SatelliteIlluminationGeometry
    policy: DirectSolarSpectralIrradiancePolicy
    resource_identity: SolarSpectralIrradianceResourceIdentity
    wavelength_nm: tuple[float, ...]
    unocculted_irradiance_w_m2_nm: tuple[float, ...]
    incident_irradiance_w_m2_nm: tuple[float, ...]
    pointwise_uncertainty_w_m2_nm: tuple[float, ...]
    visible_disk_fraction: float
    satellite_to_sun_distance_au: float
    occultation_class: SolarOccultationClass
    integrated_uncertainty_status: str = "not_evaluated"
    provenance: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def identity(self):
        return (
            self.resource_identity.content_sha256,
            self.policy,
            self.geometry,
            self.wavelength_nm[0],
            self.wavelength_nm[-1],
        )

    def integrate_energy(self, start_wavelength_nm=None, stop_wavelength_nm=None):
        start = (
            self.wavelength_nm[0]
            if start_wavelength_nm is None
            else float(start_wavelength_nm)
        )
        stop = (
            self.wavelength_nm[-1]
            if stop_wavelength_nm is None
            else float(stop_wavelength_nm)
        )
        return _native_integral(
            self.wavelength_nm,
            self.incident_irradiance_w_m2_nm,
            start,
            stop,
        )


class DirectSolarSpectralIrradianceEvaluator:
    """Compose admitted TSIS-1 samples with accepted illumination geometry."""

    def __init__(self, resource, policy=None):
        if not isinstance(resource, SolarSpectralIrradianceResource):
            raise TypeError("resource must be a SolarSpectralIrradianceResource.")
        self.resource = resource
        self.policy = (
            DirectSolarSpectralIrradiancePolicy()
            if policy is None
            else policy
        )
        if not isinstance(self.policy, DirectSolarSpectralIrradiancePolicy):
            raise TypeError(
                "policy must be a DirectSolarSpectralIrradiancePolicy."
            )

    def evaluate(self, geometry):
        if not isinstance(geometry, SatelliteIlluminationGeometry):
            raise TypeError(
                "geometry must be a SatelliteIlluminationGeometry."
            )
        policy = self.policy
        if (
            policy.model != DIRECT_SOLAR_SPECTRAL_MODEL
            or policy.resource_identity != self.resource.identity
            or policy.interpolation != "forbidden"
            or policy.extrapolation != "forbidden"
            or policy.renormalization != "forbidden"
            or policy.integrated_uncertainty_status != "not_evaluated"
            or geometry.policy.model != policy.compatible_occultation_model
        ):
            _resource_error(
                SolarSpectralRadiometryFailureCode.UNSUPPORTED_MODEL,
                "unsupported direct-Sun spectral policy or geometry.",
            )
        occultation = geometry.solar_occultation
        distance_au = (
            occultation.satellite_to_sun_distance_km
            / policy.astronomical_unit_km
        )
        fraction = occultation.visible_disk_fraction
        if (
            not isfinite(distance_au)
            or distance_au <= 0.0
            or not 0.0 <= fraction <= 1.0
        ):
            _resource_error(
                SolarSpectralRadiometryFailureCode.INCONSISTENT_GEOMETRY,
                "spectral scaling geometry is inconsistent.",
            )
        scale = 1.0 / distance_au**2
        incident_scale = scale * fraction
        clear = tuple(value * scale for value in self.resource.irradiance_w_m2_nm)
        incident = tuple(
            value * incident_scale
            for value in self.resource.irradiance_w_m2_nm
        )
        uncertainty = tuple(
            value * incident_scale
            for value in self.resource.uncertainty_w_m2_nm
        )
        return DirectSolarSpectralIrradiance(
            geometry=geometry,
            policy=policy,
            resource_identity=self.resource.identity,
            wavelength_nm=self.resource.wavelength_nm,
            unocculted_irradiance_w_m2_nm=clear,
            incident_irradiance_w_m2_nm=incident,
            pointwise_uncertainty_w_m2_nm=uncertainty,
            visible_disk_fraction=fraction,
            satellite_to_sun_distance_au=distance_au,
            occultation_class=occultation.occultation_class,
            integrated_uncertainty_status=(
                policy.integrated_uncertainty_status
            ),
            provenance=(
                "TSIS-1 HSRS v2 tsis1_hsrs_1nm external installed resource.",
                "Native 0.1 nm grid; 1 nm FWHM spectral resolution.",
                "Inverse-square distance and achromatic accepted "
                "uniform-disk visible-fraction scaling.",
            ),
            warnings=(
                "No interpolation, extrapolation, or 1361 W m-2 "
                "renormalization.",
                "Integrated uncertainty is not evaluated because wavelength "
                "covariance is unavailable.",
                "Solar variability and wavelength-dependent limb darkening "
                "are not evaluated.",
            ),
        )
