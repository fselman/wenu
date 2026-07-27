#!/usr/bin/env python3
"""Download confirmed/probable Galactic planetary nebulae from HEASARC."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import astropy
from astropy.coordinates import SkyCoord
from astropy.table import Table
import astropy.units as u
import astroquery
from astroquery.heasarc import Heasarc
import numpy as np


CATALOG_NAME = "plnebulae"
CATALOG_VERSION = "Strasbourg-ESO 1992"
EXPECTED_ROW_COUNT = 1143
QUERY = (
    "SELECT * FROM plnebulae "
    "WHERE pn_name IS NOT NULL"
)

SOURCE_NAME = "NASA HEASARC"
TAP_URL = "https://heasarc.gsfc.nasa.gov/xamin/vo/tap"
DOCUMENTATION_URL = (
    "https://heasarc.gsfc.nasa.gov/W3Browse/"
    "nebula-catalog/plnebulae.html"
)
VIZIER_URL = "https://cdsarc.cds.unistra.fr/viz-bin/cat/V/84"
HASH_URL = "https://hashpn.space/"
CATALOG_REFERENCE = (
    "Acker, A., Ochsenbein, F., Stenholm, B., Tylenda, R., "
    "Marcout, J., & Schohn, C. 1992, Strasbourg-ESO Catalogue "
    "of Galactic Planetary Nebulae, ESO, ISBN 3-923524-41-2"
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = (
    ROOT
    / "src"
    / "wenu"
    / "data"
    / "catalogs"
    / "planetary_nebulae"
)
ECSV_PATH = OUTPUT / "planetary_nebulae_acker_heasarc.ecsv"
CSV_PATH = OUTPUT / "planetary_nebulae_acker_heasarc.csv"
PROVENANCE_PATH = (
    OUTPUT / "planetary_nebulae_acker_heasarc.provenance.json"
)
README_PATH = OUTPUT / "README.md"
INIT_PATH = OUTPUT / "__init__.py"


def sha256(path: Path) -> str:
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
            "HEASARC schema is missing one of: "
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
    result = np.full(count, np.nan, dtype=float)
    for index, value in enumerate(values):
        if np.ma.is_masked(value):
            continue
        try:
            result[index] = float(value)
        except (TypeError, ValueError):
            continue
    return result


def combine_names(*columns):
    rows = zip(*columns)
    return np.asarray(
        [
            "; ".join(
                dict.fromkeys(
                    value
                    for value in row
                    if value
                )
            )
            for row in rows
        ],
        dtype=object,
    )


def normalize(source):
    count = len(source)
    ra = find_column(source, "ra", "ra_deg")
    dec = find_column(source, "dec", "dec_deg")

    # HEASARC TAP normally supplies decimal-degree coordinates. Retain a
    # sexagesimal fallback for compatibility with alternate table services.
    try:
        ra_deg = float_values(ra, count)
        dec_deg = float_values(dec, count)
        if np.any(~np.isfinite(ra_deg)) or np.any(~np.isfinite(dec_deg)):
            raise ValueError
        coordinates = SkyCoord(
            ra=ra_deg * u.deg,
            dec=dec_deg * u.deg,
            frame="icrs",
        )
    except (TypeError, ValueError):
        coordinates = SkyCoord(
            text_values(ra, count),
            text_values(dec, count),
            unit=(u.hourangle, u.deg),
            frame="icrs",
        )

    identifier = text_values(
        find_column(source, "pn_name"),
        count,
    )
    common_name = text_values(
        find_column(source, "name", required=False),
        count,
    )
    pk_name = text_values(
        find_column(source, "pk_name", required=False),
        count,
    )
    alternate_columns = [
        text_values(
            find_column(
                source,
                f"alt_name_{number}",
                required=False,
            ),
            count,
        )
        for number in range(1, 5)
    ]

    optical_diameter_arcsec = float_values(
        find_column(source, "opt_diameter", required=False),
        count,
    )
    optical_diameter_arcmin = optical_diameter_arcsec / 60.0

    table = Table(masked=True)
    table["identifier"] = identifier
    table["ra_deg"] = coordinates.ra.to_value(u.deg)
    table["dec_deg"] = coordinates.dec.to_value(u.deg)
    galactic = coordinates.galactic
    table["galactic_longitude_deg"] = galactic.l.to_value(u.deg)
    table["galactic_latitude_deg"] = galactic.b.to_value(u.deg)
    table["common_name"] = common_name
    table["pk_name"] = pk_name
    table["alternate_names"] = combine_names(*alternate_columns)
    table["major_axis_arcmin"] = optical_diameter_arcmin
    table["minor_axis_arcmin"] = optical_diameter_arcmin
    table["optical_diameter_limit"] = text_values(
        find_column(
            source,
            "limit_opt_diameter",
            required=False,
        ),
        count,
    )
    table["optical_diameter_uncertain"] = text_values(
        find_column(
            source,
            "flag_opt_diameter",
            required=False,
        ),
        count,
    )
    table["log_hbeta_flux"] = float_values(
        find_column(source, "log_hbeta_flux", required=False),
        count,
    )
    table["position_quality"] = text_values(
        find_column(source, "position_quality", required=False),
        count,
    )
    table["object_type"] = np.full(
        count,
        "planetary nebula",
        dtype=object,
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
    return table


def validate(table):
    if len(table) != EXPECTED_ROW_COUNT:
        raise RuntimeError(
            f"Expected {EXPECTED_ROW_COUNT} true/probable planetary "
            f"nebulae; received {len(table)}."
        )
    if np.any(np.asarray(table["identifier"], dtype=str) == ""):
        raise RuntimeError("One or more PN identifiers are empty.")
    if len(set(table["identifier"])) != len(table):
        raise RuntimeError("Planetary-nebula identifiers are not unique.")
    for name in ("ra_deg", "dec_deg"):
        if np.any(~np.isfinite(table[name])):
            raise RuntimeError(f"One or more {name} values are invalid.")


def retrieve():
    if not hasattr(Heasarc, "query_tap"):
        raise RuntimeError(
            "This version of astroquery does not provide "
            "Heasarc.query_tap(). Install astroquery 0.4.11 or later."
        )
    return Heasarc.query_tap(QUERY).to_table()


def write_support_files():
    README_PATH.write_text(
        """# Strasbourg–ESO Galactic planetary-nebula catalogue

This directory contains Wenu's normalized snapshot of the 1,143 true
or probable planetary nebulae in the HEASARC `plnebulae` table. That
table derives from the 1992 Strasbourg–ESO catalogue (CDS V/84).

This is a stable historical source, not a current census. HASH is the
modern primary compilation of Galactic planetary nebulae.

Regenerate the snapshot from the repository root with:

```shell
python tools/query_planetary_nebulae_heasarc.py
```

Please cite Acker et al. (1992) and HEASARC when using these data.
""",
        encoding="utf-8",
    )
    INIT_PATH.write_text(
        '"""Packaged Galactic planetary-nebula catalogue."""\n',
        encoding="utf-8",
    )


def main() -> int:
    print(
        "Querying HEASARC plnebulae for the 1,143 true/probable "
        "planetary nebulae..."
    )
    source = retrieve()
    table = normalize(source)
    validate(table)

    retrieved = (
        datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    )
    provenance = {
        "source": SOURCE_NAME,
        "catalog": CATALOG_NAME,
        "catalog_version": CATALOG_VERSION,
        "source_url": TAP_URL,
        "documentation_url": DOCUMENTATION_URL,
        "vizier_url": VIZIER_URL,
        "modern_catalogue_url": HASH_URL,
        "catalog_reference": CATALOG_REFERENCE,
        "query": QUERY,
        "retrieved_at_utc": retrieved,
        "astropy_version": astropy.__version__,
        "astroquery_version": astroquery.__version__,
        "row_count": len(table),
        "expected_row_count": EXPECTED_ROW_COUNT,
        "selection": (
            "Rows with a non-empty PN_Name: the catalogue's 1,143 "
            "true or probable planetary nebulae. Possible objects are "
            "excluded."
        ),
        "coordinate_frame": "ICRS/J2000 as served by HEASARC TAP",
        "size_definition": (
            "Acker optical diameter, converted from arcseconds to "
            "arcminutes and copied to both axes; no position angle is "
            "available in this source."
        ),
        "brightness_notice": (
            "log_hbeta_flux is an emission-line flux, not a visual "
            "magnitude. No visual-magnitude selection is applied."
        ),
        "currency_notice": (
            "This snapshot is based on the 1992 Strasbourg-ESO "
            "catalogue. HASH is the modern primary Galactic PN "
            "compilation and contains later discoveries and revisions."
        ),
    }
    table.meta.update(provenance)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_support_files()
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

    print(f"Selected planetary nebulae: {len(table)}")
    print(f"Canonical snapshot:          {ECSV_PATH}")
    print(f"CSV derivative:              {CSV_PATH}")
    print(f"Provenance:                  {PROVENANCE_PATH}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        raise
