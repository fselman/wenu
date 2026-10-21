"""Offline direct-Sun spectral radiometry for artificial satellites."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field, fields
from datetime import date
from importlib import resources
import json
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


@dataclass(frozen=True)
class _SolarSpectralResourceMetadata:
    """Validated edition facts; immutable and separate from numerical policy."""

    schema_version: int
    label: str
    doi: str
    product: str
    source_url: str
    access_date: str
    byte_count: int
    content_sha256: str
    header: tuple[str, ...]
    wavelength_unit: str
    irradiance_unit: str
    uncertainty_unit: str
    sample_count: int
    minimum_wavelength_nm: float
    maximum_wavelength_nm: float
    sampling_nm: float
    resolution_fwhm_nm: float
    native_integral_w_m2: float
    redistribution_status: str

    def __post_init__(self):
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError("unsupported solar spectral metadata schema")
        for name in ("label", "doi", "product", "source_url", "access_date"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"metadata {name} must be non-empty text")
        if date.fromisoformat(self.access_date).isoformat() != self.access_date:
            raise ValueError("metadata access_date must be an ISO date")
        if (not isinstance(self.content_sha256, str)
                or len(self.content_sha256) != 64
                or any(c not in "0123456789abcdef" for c in self.content_sha256)):
            raise ValueError("metadata content_sha256 must be lowercase SHA-256")
        for name in ("byte_count", "sample_count"):
            value = getattr(self, name)
            if type(value) is not int or value <= (1 if name == "sample_count" else 0):
                raise ValueError(f"metadata {name} must be a positive integer")
        if (not isinstance(self.header, tuple) or len(self.header) != 4
                or any(not isinstance(x, str) or not x.strip() for x in self.header)
                or len(set(self.header)) != 4):
            raise ValueError("metadata header must contain four distinct columns")
        if (self.wavelength_unit != "nm" or self.irradiance_unit != "W m-2 nm-1"
                or self.uncertainty_unit != "W m-2 nm-1"):
            raise ValueError("unsupported solar spectral metadata units")
        if self.redistribution_status != "not_established_external_install_only":
            raise ValueError("metadata must retain external-install-only policy")
        for name in ("minimum_wavelength_nm", "maximum_wavelength_nm", "sampling_nm",
                     "resolution_fwhm_nm", "native_integral_w_m2"):
            value = getattr(self, name)
            if type(value) not in (int, float) or not isfinite(value) or value <= 0:
                raise ValueError(f"metadata {name} must be positive and finite")
        span = self.maximum_wavelength_nm - self.minimum_wavelength_nm
        if span <= 0 or abs(span - (self.sample_count - 1) * self.sampling_nm) > 1e-9:
            raise ValueError("metadata count, endpoints and native spacing disagree")


def _metadata_pairs(values):
    result = {}
    for key, value in values:
        if key in result:
            raise ValueError(f"duplicate solar spectral metadata key: {key}")
        result[key] = value
    return result


def _metadata_constant(value):
    raise ValueError(f"non-finite solar spectral metadata value: {value}")


def _load_solar_spectral_metadata():
    """Load only the packaged declaration; never infer or acquire a spectrum."""
    text = resources.files("wenu.data").joinpath(
        "solar_spectral_resource_tsis1_hsrs_v2.json"
    ).read_text(encoding="utf-8")
    document = json.loads(text, object_pairs_hook=_metadata_pairs,
                          parse_constant=_metadata_constant)
    expected = {item.name for item in fields(_SolarSpectralResourceMetadata)}
    if not isinstance(document, dict) or set(document) != expected:
        raise ValueError("solar spectral metadata has missing or unknown fields")
    if not isinstance(document["header"], list):
        raise ValueError("solar spectral metadata header must be an array")
    document["header"] = tuple(document["header"])
    return _SolarSpectralResourceMetadata(**document)


_TSIS1_HSRS_V2_METADATA: Final = _load_solar_spectral_metadata()
# Compatibility names retain the accepted public values; source facts live in data.
TSIS1_HSRS_V2_PRODUCT: Final = _TSIS1_HSRS_V2_METADATA.product
TSIS1_HSRS_V2_SHA256: Final = _TSIS1_HSRS_V2_METADATA.content_sha256
TSIS1_HSRS_V2_SOURCE_URL: Final = _TSIS1_HSRS_V2_METADATA.source_url
TSIS1_HSRS_V2_DOI: Final = _TSIS1_HSRS_V2_METADATA.doi
TSIS1_HSRS_V2_BYTE_COUNT: Final = _TSIS1_HSRS_V2_METADATA.byte_count
TSIS1_HSRS_V2_SAMPLE_COUNT: Final = _TSIS1_HSRS_V2_METADATA.sample_count
TSIS1_HSRS_V2_MINIMUM_NM: Final = _TSIS1_HSRS_V2_METADATA.minimum_wavelength_nm
TSIS1_HSRS_V2_MAXIMUM_NM: Final = _TSIS1_HSRS_V2_METADATA.maximum_wavelength_nm
TSIS1_HSRS_V2_SAMPLING_NM: Final = _TSIS1_HSRS_V2_METADATA.sampling_nm
TSIS1_HSRS_V2_RESOLUTION_FWHM_NM: Final = _TSIS1_HSRS_V2_METADATA.resolution_fwhm_nm
TSIS1_HSRS_V2_INTEGRAL_W_M2: Final = _TSIS1_HSRS_V2_METADATA.native_integral_w_m2
TSIS1_HSRS_V2_HEADER: Final = _TSIS1_HSRS_V2_METADATA.header
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
    access_date: str = _TSIS1_HSRS_V2_METADATA.access_date
    byte_count: int = TSIS1_HSRS_V2_BYTE_COUNT
    content_sha256: str = TSIS1_HSRS_V2_SHA256
    header: tuple[str, ...] = TSIS1_HSRS_V2_HEADER
    wavelength_unit: str = _TSIS1_HSRS_V2_METADATA.wavelength_unit
    irradiance_unit: str = _TSIS1_HSRS_V2_METADATA.irradiance_unit
    uncertainty_unit: str = _TSIS1_HSRS_V2_METADATA.uncertainty_unit
    sample_count: int = TSIS1_HSRS_V2_SAMPLE_COUNT
    minimum_wavelength_nm: float = TSIS1_HSRS_V2_MINIMUM_NM
    maximum_wavelength_nm: float = TSIS1_HSRS_V2_MAXIMUM_NM
    sampling_nm: float = TSIS1_HSRS_V2_SAMPLING_NM
    resolution_fwhm_nm: float = TSIS1_HSRS_V2_RESOLUTION_FWHM_NM
    redistribution_status: str = _TSIS1_HSRS_V2_METADATA.redistribution_status

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
        if (
            self.wavelength_nm[0] != self.identity.minimum_wavelength_nm
            or self.wavelength_nm[-1] != self.identity.maximum_wavelength_nm
            or any(
                not isfinite(value)
                for value in self.wavelength_nm
            )
            or any(
                abs((right - left) - self.identity.sampling_nm) > 1.0e-10
                for left, right in zip(
                    self.wavelength_nm,
                    self.wavelength_nm[1:],
                )
            )
            or any(
                not isfinite(value) or value < 0.0
                for values in (
                    self.irradiance_w_m2_nm,
                    self.uncertainty_w_m2_nm,
                )
                for value in values
            )
            or any(
                value != self.identity.resolution_fwhm_nm
                for value in self.bandwidth_nm
            )
        ):
            raise ValueError("spectral resource native-grid values are invalid.")
        calculated = _native_integral(
            self.wavelength_nm,
            self.irradiance_w_m2_nm,
            self.wavelength_nm[0],
            self.wavelength_nm[-1],
        )
        if (
            not isfinite(self.native_integral_w_m2)
            or abs(self.native_integral_w_m2 - calculated) > 1.0e-12
            or abs(
                self.native_integral_w_m2
                - TSIS1_HSRS_V2_INTEGRAL_W_M2
            )
            > 1.0e-9
        ):
            raise ValueError("native_integral_w_m2 is inconsistent.")


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


def _parse_verified_spectral_payload(payload, identity):
    """Parse bytes only after the public loader verifies their identity."""
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
    return _parse_verified_spectral_payload(payload, identity)


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

    def __post_init__(self):
        if not isinstance(self.geometry, SatelliteIlluminationGeometry):
            raise TypeError(
                "geometry must be a SatelliteIlluminationGeometry."
            )
        if not isinstance(
            self.policy,
            DirectSolarSpectralIrradiancePolicy,
        ):
            raise TypeError(
                "policy must be a DirectSolarSpectralIrradiancePolicy."
            )
        if self.resource_identity != self.policy.resource_identity:
            raise ValueError("resource identity must match policy.")
        count = self.resource_identity.sample_count
        vectors = (
            self.wavelength_nm,
            self.unocculted_irradiance_w_m2_nm,
            self.incident_irradiance_w_m2_nm,
            self.pointwise_uncertainty_w_m2_nm,
        )
        if any(len(values) != count for values in vectors):
            raise ValueError("spectral result sample count is inconsistent.")
        if (
            self.wavelength_nm[0]
            != self.resource_identity.minimum_wavelength_nm
            or self.wavelength_nm[-1]
            != self.resource_identity.maximum_wavelength_nm
            or any(
                not isfinite(value) or value < 0.0
                for values in vectors[1:]
                for value in values
            )
            or not isfinite(self.satellite_to_sun_distance_au)
            or self.satellite_to_sun_distance_au <= 0.0
            or not 0.0 <= self.visible_disk_fraction <= 1.0
            or self.integrated_uncertainty_status != "not_evaluated"
        ):
            raise ValueError("spectral result values are inconsistent.")
        occultation = self.geometry.solar_occultation
        if (
            self.visible_disk_fraction
            != occultation.visible_disk_fraction
            or self.occultation_class is not occultation.occultation_class
        ):
            raise ValueError("spectral result must match accepted geometry.")
        object.__setattr__(self, "provenance", tuple(self.provenance))
        object.__setattr__(self, "warnings", tuple(self.warnings))

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
                f"{_TSIS1_HSRS_V2_METADATA.label} {self.resource.identity.product} "
                "external installed resource.",
                f"Native {self.resource.identity.sampling_nm:g} nm grid; "
                f"{self.resource.identity.resolution_fwhm_nm:g} nm FWHM spectral resolution.",
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
