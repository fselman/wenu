#!/usr/bin/env python3
"""Download the Harris/HEASARC Milky Way globular-cluster catalogue."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import astroquery
from astroquery.heasarc import Heasarc


CATALOG_NAME = "globclust"
QUERY = "SELECT * FROM globclust"
SOURCE_NAME = "NASA HEASARC"
TAP_URL = "https://heasarc.gsfc.nasa.gov/xamin/vo/tap"
DOCUMENTATION_URL = (
    "https://heasarc.gsfc.nasa.gov/w3browse/all/globclust.html"
)
ORIGINAL_SOURCE_URL = "https://physics.mcmaster.ca/~harris/Databases.html"
CATALOG_REFERENCE = (
    "Harris, W. E. 1996, AJ, 112, 1487 "
    "(December 2010 edition; arXiv:1012.3224)"
)
EXPECTED_ROW_COUNT = 157
EXPECTED_COLUMNS = {
    "name",
    "alt_name",
    "ra",
    "dec",
    "lii",
    "bii",
    "helio_distance",
    "metallicity",
    "vmag",
    "abs_vmag",
    "central_concentration",
    "core_radius",
    "half_light_radius",
}

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = (
    ROOT / "src" / "wenu" / "data" / "catalogs" / "globular_clusters"
)
ECSV_PATH = OUTPUT / "globular_clusters_harris_heasarc.ecsv"
CSV_PATH = OUTPUT / "globular_clusters_harris_heasarc.csv"
PROVENANCE_PATH = (
    OUTPUT / "globular_clusters_harris_heasarc.provenance.json"
)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate(table):
    if len(table) != EXPECTED_ROW_COUNT:
        raise RuntimeError(
            f"Expected {EXPECTED_ROW_COUNT} rows; received {len(table)}."
        )
    available = {name.casefold() for name in table.colnames}
    missing = EXPECTED_COLUMNS - available
    if missing:
        raise RuntimeError(
            "HEASARC schema is missing: " + ", ".join(sorted(missing))
        )


def main():
    if not hasattr(Heasarc, "query_tap"):
        raise RuntimeError(
            "Upgrade astroquery before running this tool:\n\n"
            "    python -m pip install --upgrade astroquery"
        )
    print(f"Querying {SOURCE_NAME}: {QUERY}")
    table = Heasarc.query_tap(QUERY).to_table()
    validate(table)

    retrieved = (
        datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    )
    provenance = {
        "source": SOURCE_NAME,
        "catalog": CATALOG_NAME,
        "source_url": TAP_URL,
        "documentation_url": DOCUMENTATION_URL,
        "original_source_url": ORIGINAL_SOURCE_URL,
        "catalog_reference": CATALOG_REFERENCE,
        "query": QUERY,
        "retrieved_at_utc": retrieved,
        "astroquery_version": astroquery.__version__,
        "row_count": len(table),
        "expected_row_count": EXPECTED_ROW_COUNT,
        "size_definition_used_by_wenu": (
            "Twice half_light_radius: Harris half-light diameter."
        ),
        "redistribution_notice": (
            "Catalogue data are supplied free of charge. Redistributors "
            "must refer to the original McMaster source and must not "
            "charge a fee for supplying the catalogue."
        ),
    }
    table.meta.update(provenance)
    OUTPUT.mkdir(parents=True, exist_ok=True)
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
    print(f"Downloaded rows: {len(table)}")
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
