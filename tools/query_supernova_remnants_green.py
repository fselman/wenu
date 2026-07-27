#!/usr/bin/env python3
"""Download Green's 2024 Galactic supernova-remnant catalogue from VizieR."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import astropy
from astropy.coordinates import SkyCoord
from astropy.table import MaskedColumn, Table
import astropy.units as u
import astroquery
from astroquery.vizier import Vizier
import numpy as np


CATALOG_ID = "VII/297"
CATALOG_TABLE = "VII/297/snrs"
CATALOG_VERSION = "2024 October"
EXPECTED_ROW_COUNT = 310
SOURCE_NAME = "VizieR/CDS"
VIZIER_URL = "https://cdsarc.cds.unistra.fr/viz-bin/cat/VII/297"
README_URL = (
    "https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/VII/297"
)
ORIGINAL_SOURCE_URL = "https://www.mrao.cam.ac.uk/surveys/snrs/"
CATALOG_REFERENCE = (
    "Green, D. A. 2025, Journal of Astrophysics and Astronomy, "
    "46, 14; Green, D. A. 2024, A Catalogue of Galactic "
    "Supernova Remnants (2024 October version)."
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = (
    ROOT
    / "src"
    / "wenu"
    / "data"
    / "catalogs"
    / "supernova_remnants"
)
ECSV_PATH = OUTPUT / "supernova_remnants_green_2024.ecsv"
CSV_PATH = OUTPUT / "supernova_remnants_green_2024.csv"
PROVENANCE_PATH = (
    OUTPUT / "supernova_remnants_green_2024.provenance.json"
)
README_PATH = OUTPUT / "README.md"
INIT_PATH = OUTPUT / "__init__.py"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def find_column(table, *candidates, required=True):
    names = {name.casefold(): name for name in table.colnames}
    for candidate in candidates:
        actual = names.get(candidate.casefold())
        if actual is not None:
            return table[actual]
    if required:
        raise RuntimeError(
            "VizieR schema is missing one of: "
            + ", ".join(repr(name) for name in candidates)
        )
    return None


def text_values(values, count):
    if values is None:
        return np.full(count, "", dtype=object)
    return np.asarray(
        [
            ""
            if np.ma.is_masked(value)
            else str(value).strip()
            for value in values
        ],
        dtype=object,
    )


def float_values(values, count):
    if values is None:
        return np.full(count, np.nan, dtype=float)
    return np.asarray(
        [
            np.nan if np.ma.is_masked(value) else float(value)
            for value in values
        ],
        dtype=float,
    )


def integer_values(values, count):
    if values is None:
        return np.full(count, -1, dtype=int)
    return np.asarray(
        [
            -1 if np.ma.is_masked(value) else int(value)
            for value in values
        ],
        dtype=int,
    )


def normalize(source):
    count = len(source)
    raj2000 = find_column(
        source,
        "RAJ2000",
        "_RAJ2000",
        required=False,
    )
    dej2000 = find_column(
        source,
        "DEJ2000",
        "_DEJ2000",
        required=False,
    )
    if raj2000 is not None and dej2000 is not None:
        # Modern VizieR responses expose the catalogue's synthesized
        # sexagesimal RAJ2000/DEJ2000 columns instead of its fixed-width
        # RAh/RAm/RAs and DE-/DEd/DEm storage fields.
        first_ra = next(
            value
            for value in raj2000
            if not np.ma.is_masked(value)
        )
        if isinstance(first_ra, (str, np.str_)):
            coordinates = SkyCoord(
                text_values(raj2000, count),
                text_values(dej2000, count),
                unit=(u.hourangle, u.deg),
                frame="icrs",
            )
        else:
            # Astroquery may expose its underscore-prefixed synthesized
            # coordinate columns directly in decimal degrees.
            coordinates = SkyCoord(
                ra=float_values(raj2000, count) * u.deg,
                dec=float_values(dej2000, count) * u.deg,
                frame="icrs",
            )
    else:
        # Retain compatibility with services exposing the original
        # byte-layout component columns documented in the CDS ReadMe.
        rah = integer_values(find_column(source, "RAh"), count)
        ram = integer_values(find_column(source, "RAm"), count)
        ras = float_values(find_column(source, "RAs"), count)
        dec_sign = text_values(
            find_column(source, "DE-", "DEsign"),
            count,
        )
        ded = integer_values(find_column(source, "DEd"), count)
        dem = float_values(find_column(source, "DEm"), count)

        ra_text = [
            f"{hour:02d}h{minute:02d}m{second:05.2f}s"
            for hour, minute, second in zip(rah, ram, ras)
        ]
        dec_text = [
            f"{'-' if sign.strip() == '-' else '+'}"
            f"{degree:02d}d{minute:04.1f}m"
            for sign, degree, minute in zip(dec_sign, ded, dem)
        ]
        coordinates = SkyCoord(ra_text, dec_text, frame="icrs")

    major = float_values(
        find_column(source, "MajDiam", "Maj_Diam"),
        count,
    )
    minor = float_values(
        find_column(
            source,
            "MinDiam",
            "Min_Diam",
            required=False,
        ),
        count,
    )
    # Green provides one diameter for near-circular remnants.
    minor = np.where(np.isfinite(minor), minor, major)

    table = Table(masked=True)
    table["identifier"] = text_values(
        find_column(source, "SNR"),
        count,
    )
    table["ra_deg"] = coordinates.ra.to_value(u.deg)
    table["dec_deg"] = coordinates.dec.to_value(u.deg)
    galactic = coordinates.galactic
    table["galactic_longitude_deg"] = galactic.l.to_value(u.deg)
    table["galactic_latitude_deg"] = galactic.b.to_value(u.deg)
    table["major_axis_arcmin"] = major
    table["minor_axis_arcmin"] = minor
    table["morphology"] = text_values(
        find_column(source, "type", "Type"),
        count,
    )
    table["flux_1ghz_jy"] = float_values(
        find_column(
            source,
            "S(1GHz)",
            "S_1GHz_",
            "S1GHz",
            required=False,
        ),
        count,
    )
    table["flux_limit_flag"] = text_values(
        find_column(
            source,
            "l_S(1GHz)",
            "l_S_1GHz_",
            required=False,
        ),
        count,
    )
    table["flux_uncertain"] = text_values(
        find_column(
            source,
            "u_S(1GHz)",
            "u_S_1GHz_",
            required=False,
        ),
        count,
    )
    table["spectral_index"] = float_values(
        find_column(
            source,
            "Sp-Index",
            "Sp_Index",
            required=False,
        ),
        count,
    )
    table["spectral_index_flag"] = text_values(
        find_column(
            source,
            "u_Sp-Index",
            "u_Sp_Index",
            required=False,
        ),
        count,
    )
    table["alternate_names"] = text_values(
        find_column(source, "Names", required=False),
        count,
    )

    for name in (
        "ra_deg",
        "dec_deg",
        "galactic_longitude_deg",
        "galactic_latitude_deg",
    ):
        table[name].unit = u.deg
    table["major_axis_arcmin"].unit = u.arcmin
    table["minor_axis_arcmin"].unit = u.arcmin
    table["flux_1ghz_jy"].unit = u.Jy
    return table


def validate(table):
    if len(table) != EXPECTED_ROW_COUNT:
        raise RuntimeError(
            f"Expected {EXPECTED_ROW_COUNT} rows; received {len(table)}."
        )
    if len(set(table["identifier"])) != EXPECTED_ROW_COUNT:
        raise RuntimeError("SNR identifiers are not unique.")
    if np.any(~np.isfinite(table["ra_deg"])):
        raise RuntimeError("One or more right ascensions are invalid.")
    if np.any(~np.isfinite(table["dec_deg"])):
        raise RuntimeError("One or more declinations are invalid.")
    if np.any(table["major_axis_arcmin"] <= 0.0):
        raise RuntimeError("One or more major diameters are invalid.")
    if np.any(table["minor_axis_arcmin"] <= 0.0):
        raise RuntimeError("One or more minor diameters are invalid.")


def retrieve():
    query = Vizier(columns=["**"], row_limit=-1)
    result = query.get_catalogs(CATALOG_TABLE)
    if len(result) != 1:
        raise RuntimeError(
            f"Expected one VizieR table for {CATALOG_TABLE}; "
            f"received {len(result)}."
        )
    return result[0]


def write_readme():
    README_PATH.write_text(
        """# Green Galactic supernova-remnant catalogue

This directory contains Wenu's canonical snapshot of D. A. Green's
2024 October Galactic supernova-remnant catalogue, obtained through
VizieR catalogue VII/297.

The catalogue contains confirmed Galactic remnants. Its 1 GHz flux
is a radio measurement and must not be interpreted as optical
brightness or naked-eye visibility.

Regenerate the files from the repository root with:

```shell
python tools/query_supernova_remnants_green.py
```

Please cite Green (2025, JApA, 46, 14), the 2024 October catalogue,
and VizieR/CDS when using these data.
""",
        encoding="utf-8",
    )
    INIT_PATH.write_text(
        '"""Packaged Green Galactic supernova-remnant catalogue."""\n',
        encoding="utf-8",
    )


def main():
    print(
        f"Querying VizieR {CATALOG_ID}: Green {CATALOG_VERSION} "
        "Galactic SNR catalogue..."
    )
    source = retrieve()
    table = normalize(source)
    validate(table)

    retrieved = (
        datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    )
    provenance = {
        "source": SOURCE_NAME,
        "catalog": CATALOG_ID,
        "table": CATALOG_TABLE,
        "catalog_version": CATALOG_VERSION,
        "source_url": VIZIER_URL,
        "readme_url": README_URL,
        "original_source_url": ORIGINAL_SOURCE_URL,
        "catalog_reference": CATALOG_REFERENCE,
        "retrieved_at_utc": retrieved,
        "astropy_version": astropy.__version__,
        "astroquery_version": astroquery.__version__,
        "row_count": len(table),
        "expected_row_count": EXPECTED_ROW_COUNT,
        "selection": "All 310 confirmed remnants in VizieR VII/297.",
        "coordinate_frame": "ICRS/J2000",
        "size_definition": (
            "Green major and minor radio angular diameters. When only "
            "one diameter is supplied, Wenu copies it to the minor axis."
        ),
        "position_angle_notice": (
            "The catalogue does not provide position angles. No position "
            "angle is inferred during acquisition."
        ),
        "visibility_notice": (
            "The 1 GHz flux is a radio quantity and is not an optical "
            "visibility or chart magnitude."
        ),
        "acknowledgement": (
            "This research has made use of the VizieR catalogue access "
            "tool, CDS, Strasbourg, France."
        ),
    }
    table.meta.update(provenance)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_readme()
    table.write(ECSV_PATH, format="ascii.ecsv", overwrite=True)
    table.write(CSV_PATH, format="ascii.csv", overwrite=True)

    document = {
        **provenance,
        "columns": list(table.colnames),
        "files": {
            "canonical_snapshot": {
                "name": ECSV_PATH.name,
                "format": "Astropy ECSV",
                "sha256": sha256(ECSV_PATH),
            },
            "csv_derivative": {
                "name": CSV_PATH.name,
                "format": "CSV",
                "sha256": sha256(CSV_PATH),
            },
        },
    }
    PROVENANCE_PATH.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Selected remnants:  {len(table)}")
    print(f"Canonical snapshot: {ECSV_PATH}")
    print(f"CSV derivative:     {CSV_PATH}")
    print(f"Provenance:         {PROVENANCE_PATH}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        raise
