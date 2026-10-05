"""Validate 50S.7D.2 from an explicitly installed TSIS-1 HSRS v2 CSV.

This tool never downloads.  It independently checks the admitted bytes,
schema, native coordinate grid, bandwidth, and trapezoidal integral before
comparing them with Wenu's production loader.
"""

from __future__ import annotations

import argparse
import csv
from hashlib import sha256
from io import StringIO
from math import fsum, isfinite
from pathlib import Path

from wenu.satellites.radiometry import (
    TSIS1_HSRS_V2_BYTE_COUNT,
    TSIS1_HSRS_V2_HEADER,
    TSIS1_HSRS_V2_INTEGRAL_W_M2,
    TSIS1_HSRS_V2_MAXIMUM_NM,
    TSIS1_HSRS_V2_MINIMUM_NM,
    TSIS1_HSRS_V2_RESOLUTION_FWHM_NM,
    TSIS1_HSRS_V2_SAMPLE_COUNT,
    TSIS1_HSRS_V2_SAMPLING_NM,
    TSIS1_HSRS_V2_SHA256,
    load_solar_spectral_irradiance_resource,
)


def _independent_parse(payload):
    text = payload.decode("utf-8")
    rows = csv.reader(StringIO(text, newline=""))
    header = tuple(next(rows))
    values = tuple(tuple(float(value) for value in row) for row in rows)
    if any(len(row) != 4 for row in values):
        raise AssertionError("independent parser found a non-four-column row")
    columns = tuple(tuple(row[index] for row in values) for index in range(4))
    wavelength, irradiance, uncertainty, bandwidth = columns
    if header != TSIS1_HSRS_V2_HEADER:
        raise AssertionError(f"header mismatch: {header!r}")
    if len(wavelength) != TSIS1_HSRS_V2_SAMPLE_COUNT:
        raise AssertionError("sample-count mismatch")
    if (
        wavelength[0] != TSIS1_HSRS_V2_MINIMUM_NM
        or wavelength[-1] != TSIS1_HSRS_V2_MAXIMUM_NM
    ):
        raise AssertionError("wavelength endpoints mismatch")
    if any(
        abs((right - left) - TSIS1_HSRS_V2_SAMPLING_NM) > 1.0e-10
        for left, right in zip(wavelength, wavelength[1:])
    ):
        raise AssertionError("native wavelength spacing mismatch")
    if any(
        value != TSIS1_HSRS_V2_RESOLUTION_FWHM_NM
        for value in bandwidth
    ):
        raise AssertionError("bandwidth/resolution mismatch")
    if any(
        not isfinite(value) or value < 0.0
        for column in (irradiance, uncertainty)
        for value in column
    ):
        raise AssertionError("non-finite or negative spectral value")
    integral = fsum(
        (wavelength[index + 1] - wavelength[index])
        * (irradiance[index + 1] + irradiance[index])
        / 2.0
        for index in range(len(wavelength) - 1)
    )
    return header, columns, integral


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "resource",
        type=Path,
        help="explicitly installed tsis1_hsrs_1nm CSV",
    )
    arguments = parser.parse_args()
    payload = arguments.resource.read_bytes()
    digest = sha256(payload).hexdigest()
    if len(payload) != TSIS1_HSRS_V2_BYTE_COUNT:
        raise AssertionError("byte-count mismatch")
    if digest != TSIS1_HSRS_V2_SHA256:
        raise AssertionError("SHA-256 mismatch")
    header, columns, independent_integral = _independent_parse(payload)
    if abs(
        independent_integral - TSIS1_HSRS_V2_INTEGRAL_W_M2
    ) > 1.0e-9:
        raise AssertionError("independent native-grid integral mismatch")

    production = load_solar_spectral_irradiance_resource(
        arguments.resource
    )
    if production.wavelength_nm != columns[0]:
        raise AssertionError("production wavelength tuple mismatch")
    if production.irradiance_w_m2_nm != columns[1]:
        raise AssertionError("production irradiance tuple mismatch")
    if production.uncertainty_w_m2_nm != columns[2]:
        raise AssertionError("production uncertainty tuple mismatch")
    if production.bandwidth_nm != columns[3]:
        raise AssertionError("production bandwidth tuple mismatch")
    if production.native_integral_w_m2 != independent_integral:
        raise AssertionError("production integral mismatch")

    print(f"resource={arguments.resource}")
    print(f"byte_count={len(payload)}")
    print(f"sha256={digest}")
    print(f"header={header!r}")
    print(f"sample_count={len(columns[0])}")
    print(f"minimum_wavelength_nm={columns[0][0]:.1f}")
    print(f"maximum_wavelength_nm={columns[0][-1]:.1f}")
    print(f"sampling_nm={TSIS1_HSRS_V2_SAMPLING_NM:.1f}")
    print(
        "resolution_fwhm_nm="
        f"{TSIS1_HSRS_V2_RESOLUTION_FWHM_NM:.1f}"
    )
    print(f"native_integral_w_m2={independent_integral:.12f}")
    print("production_match=true")
    print("network_access=false")
    print("redistribution=false")


if __name__ == "__main__":
    main()
