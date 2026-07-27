#!/usr/bin/env python3
"""Download and normalize optically visible open clusters from HEASARC."""

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


CATALOG_NAME = "openclust"
CATALOG_VERSION = "HEASARC/CDS B/ocl snapshot"
QUERY = "SELECT * FROM openclust"
MINIMUM_EXPECTED_ROWS = 1500

SOURCE_NAME = "NASA HEASARC"
TAP_URL = "https://heasarc.gsfc.nasa.gov/xamin/vo/tap"
DOCUMENTATION_URL = (
    "https://heasarc.gsfc.nasa.gov/W3Browse/"
    "star-catalog/openclust.html"
)
CDS_URL = "https://cdsarc.cds.unistra.fr/ftp/cats/B/ocl/"
CATALOG_REFERENCE = (
    "Dias, W. S., Alessi, B. S., Moitinho, A., & Lepine, J. R. D. "
    "2002, A&A, 389, 871; HEASARC OPENCLUST table updated from "
    "CDS B/ocl"
)

# Flags that do not represent an established open cluster. Ordinary clusters
# have an empty flag. Embedded, recovered, infrared, variable-extinction, and
# explicitly likely clusters remain in the Wenu snapshot.
EXCLUDED_TYPE_FLAGS = {
    "A",    # possible asterism/dust hole/star cloud
    "CR",   # cluster remnant
    "D",    # dubious
    "G",    # possible globular cluster
    "M",    # possible moving group
    "N",    # non-existent NGC
    "NF",   # not found
    "O",    # possible OB association
    "OE",
    "OEV",
    "OC?",  # possible cluster
    "P",    # possible open-cluster remnant
}

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = (
    ROOT / "src" / "wenu" / "data" / "catalogs" / "open_clusters"
)
ECSV_PATH = OUTPUT / "open_clusters_dias_heasarc.ecsv"
CSV_PATH = OUTPUT / "open_clusters_dias_heasarc.csv"
PROVENANCE_PATH = (
    OUTPUT / "open_clusters_dias_heasarc.provenance.json"
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


def integer_values(values, count):
    floats = float_values(values, count)
    return np.asarray(
        [
            -1 if not np.isfinite(value) else int(value)
            for value in floats
        ],
        dtype=int,
    )


def coordinates(source):
    count = len(source)
    ra = find_column(source, "ra", "ra_deg")
    dec = find_column(source, "dec", "dec_deg")
    try:
        ra_deg = float_values(ra, count)
        dec_deg = float_values(dec, count)
        if np.any(~np.isfinite(ra_deg)) or np.any(~np.isfinite(dec_deg)):
            raise ValueError
        return SkyCoord(
            ra=ra_deg * u.deg,
            dec=dec_deg * u.deg,
            frame="icrs",
        )
    except (TypeError, ValueError):
        return SkyCoord(
            text_values(ra, count),
            text_values(dec, count),
            unit=(u.hourangle, u.deg),
            frame="icrs",
        )


def normalize(source):
    count = len(source)
    position = coordinates(source)
    type_flag = text_values(
        find_column(source, "type_flag", required=False),
        count,
    )
    keep = np.asarray(
        [
            value.strip().upper() not in EXCLUDED_TYPE_FLAGS
            for value in type_flag
        ],
        dtype=bool,
    )

    source = source[keep]
    position = position[keep]
    type_flag = type_flag[keep]
    count = len(source)

    apparent_diameter = float_values(
        find_column(
            source,
            "apparent_diameter",
            "diameter",
            required=False,
        ),
        count,
    )

    table = Table(masked=True)
    table["identifier"] = text_values(
        find_column(source, "name"),
        count,
    )
    table["ra_deg"] = position.ra.to_value(u.deg)
    table["dec_deg"] = position.dec.to_value(u.deg)
    galactic = position.galactic
    table["galactic_longitude_deg"] = galactic.l.to_value(u.deg)
    table["galactic_latitude_deg"] = galactic.b.to_value(u.deg)
    table["apparent_diameter_arcmin"] = apparent_diameter
    table["distance_pc"] = float_values(
        find_column(source, "distance", required=False),
        count,
    )
    table["reddening_e_bv"] = float_values(
        find_column(source, "e_bv", required=False),
        count,
    )
    table["log_age_years"] = float_values(
        find_column(source, "log_age", required=False),
        count,
    )
    table["member_count"] = integer_values(
        find_column(source, "num_cluster_stars", required=False),
        count,
    )
    table["proper_motion_ra_mas_per_year"] = float_values(
        find_column(source, "pm_ra", required=False),
        count,
    )
    table["proper_motion_dec_mas_per_year"] = float_values(
        find_column(source, "pm_dec", required=False),
        count,
    )
    table["radial_velocity_km_per_s"] = float_values(
        find_column(source, "rad_vel", required=False),
        count,
    )
    table["metallicity_feh"] = float_values(
        find_column(source, "metallicity", required=False),
        count,
    )
    table["trumpler_type"] = text_values(
        find_column(source, "trumpler_type", required=False),
        count,
    )
    table["source_type_flag"] = type_flag
    table["object_type"] = np.full(
        count,
        "open cluster",
        dtype=object,
    )

    for name in (
        "ra_deg",
        "dec_deg",
        "galactic_longitude_deg",
        "galactic_latitude_deg",
    ):
        table[name].unit = u.deg
    table["apparent_diameter_arcmin"].unit = u.arcmin
    table["distance_pc"].unit = u.pc
    table["proper_motion_ra_mas_per_year"].unit = u.mas / u.yr
    table["proper_motion_dec_mas_per_year"].unit = u.mas / u.yr
    table["radial_velocity_km_per_s"].unit = u.km / u.s
    return table


def validate(table, source_count):
    if source_count < MINIMUM_EXPECTED_ROWS:
        raise RuntimeError(
            f"Expected at least {MINIMUM_EXPECTED_ROWS} OPENCLUST rows; "
            f"received {source_count}."
        )
    if len(table) < 1000:
        raise RuntimeError(
            "Fewer than 1,000 established/likely open clusters remain "
            "after flag filtering."
        )
    identifiers = np.asarray(table["identifier"], dtype=str)
    if np.any(identifiers == ""):
        raise RuntimeError("One or more identifiers are empty.")
    if len(set(identifiers)) != len(table):
        raise RuntimeError("Open-cluster identifiers are not unique.")
    for name in ("ra_deg", "dec_deg"):
        if np.any(~np.isfinite(table[name])):
            raise RuntimeError(f"One or more {name} values are invalid.")
    diameter = np.asarray(
        table["apparent_diameter_arcmin"],
        dtype=float,
    )
    coverage = np.count_nonzero(np.isfinite(diameter)) / len(table)
    if coverage < 0.99:
        raise RuntimeError(
            "Apparent-diameter coverage unexpectedly fell below 99%."
        )


def retrieve():
    if not hasattr(Heasarc, "query_tap"):
        raise RuntimeError(
            "This version of astroquery does not provide "
            "Heasarc.query_tap(). Install astroquery 0.4.11 or later."
        )
    return Heasarc.query_tap(QUERY).to_table()


def write_support_files():
    README_PATH.write_text(
        """# Dias/HEASARC optically visible open clusters

This directory contains Wenu's normalized snapshot of established and likely
open clusters selected from the NASA HEASARC `OPENCLUST` table. Explicit
asterisms, dubious/non-existent objects, associations, moving groups, possible
globular clusters, and cluster remnants are excluded.

The source supplies apparent diameter for almost every object, but no
homogeneous integrated visual magnitude. Wenu therefore applies no magnitude
limit to this snapshot.

Regenerate from the repository root with:

```shell
python tools/query_open_clusters_heasarc.py
```

Please cite Dias et al. (2002) and HEASARC when using these data.
""",
        encoding="utf-8",
    )
    INIT_PATH.write_text(
        '"""Packaged Galactic open-cluster catalogue."""\n',
        encoding="utf-8",
    )


def main():
    print("Querying NASA HEASARC OPENCLUST...")
    source = retrieve()
    table = normalize(source)
    validate(table, len(source))

    retrieved = (
        datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    )
    diameter = np.asarray(
        table["apparent_diameter_arcmin"],
        dtype=float,
    )
    provenance = {
        "source": SOURCE_NAME,
        "catalog": CATALOG_NAME,
        "catalog_version": CATALOG_VERSION,
        "source_url": TAP_URL,
        "documentation_url": DOCUMENTATION_URL,
        "cds_url": CDS_URL,
        "catalog_reference": CATALOG_REFERENCE,
        "query": QUERY,
        "retrieved_at_utc": retrieved,
        "astropy_version": astropy.__version__,
        "astroquery_version": astroquery.__version__,
        "source_row_count": len(source),
        "selected_row_count": len(table),
        "excluded_type_flags": sorted(EXCLUDED_TYPE_FLAGS),
        "selection": (
            "Retain ordinary, embedded, recovered, infrared, "
            "variable-extinction, and explicitly likely open clusters. "
            "Exclude flags denoting asterisms, dubious/non-existent "
            "objects, associations, moving groups, possible globular "
            "clusters, cluster remnants, and merely possible clusters."
        ),
        "coordinate_frame": "ICRS/J2000 as served by HEASARC TAP",
        "diameter_coverage_fraction": float(
            np.count_nonzero(np.isfinite(diameter)) / len(table)
        ),
        "brightness_notice": (
            "OPENCLUST has no homogeneous integrated visual magnitude. "
            "No magnitude threshold is applied or inferred."
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

    print(f"Source rows:       {len(source)}")
    print(f"Selected clusters: {len(table)}")
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
