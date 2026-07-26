#!/usr/bin/env python3
"""Download the HEASARC Messier catalogue with provenance metadata.

The untouched HEASARC result is stored as an Astropy ECSV file, which
preserves column metadata, units, datatypes, and provenance. A plain CSV
derivative and a JSON provenance sidecar are also generated.

This is a catalogue-maintenance utility and is not used at Wenu runtime.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import astroquery
from astroquery.heasarc import Heasarc


CATALOG_NAME = "messier"
QUERY = "SELECT * FROM messier"

SOURCE_NAME = "NASA HEASARC"
TAP_URL = "https://heasarc.gsfc.nasa.gov/xamin/vo/tap"
DOCUMENTATION_URL = (
    "https://heasarc.gsfc.nasa.gov/w3browse/all/messier.html"
)
CATALOG_REFERENCE = (
    "Sky Catalog 2000.0, Volume 2, edited by "
    "A. Hirshfeld and R. W. Sinnott, 1985"
)

EXPECTED_ROW_COUNT = 109
EXPECTED_COLUMNS = {
    "name",
    "alt_name",
    "ra",
    "dec",
    "constell",
    "dimension",
    "vmag",
    "vmag_uncert",
    "object_type",
    "class",
    "notes",
}

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIRECTORY = (
    REPOSITORY_ROOT
    / "src"
    / "wenu"
    / "data"
    / "catalogs"
    / "messier"
)

ECSV_PATH = OUTPUT_DIRECTORY / "messier_heasarc.ecsv"
CSV_PATH = OUTPUT_DIRECTORY / "messier_heasarc.csv"
PROVENANCE_PATH = (
    OUTPUT_DIRECTORY / "messier_heasarc.provenance.json"
)


def sha256(path: Path) -> str:
    """Return the hexadecimal SHA-256 checksum of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_table(table) -> None:
    """Reject an incomplete or unexpectedly changed catalogue result."""
    if len(table) != EXPECTED_ROW_COUNT:
        raise RuntimeError(
            "Unexpected HEASARC Messier row count: "
            f"expected {EXPECTED_ROW_COUNT}, received {len(table)}."
        )

    available = {name.lower() for name in table.colnames}
    missing = EXPECTED_COLUMNS - available
    if missing:
        raise RuntimeError(
            "The HEASARC Messier schema is missing expected columns: "
            + ", ".join(sorted(missing))
        )


def download_catalog():
    """Query and return the complete HEASARC Messier table."""
    if not hasattr(Heasarc, "query_tap"):
        raise RuntimeError(
            "This version of astroquery does not provide "
            "Heasarc.query_tap(). Upgrade it with:\n\n"
            "    python -m pip install --upgrade astroquery\n"
        )

    return Heasarc.query_tap(QUERY).to_table()


def main() -> int:
    """Download, validate, document, and store the catalogue."""
    print(f"Querying {SOURCE_NAME}: {QUERY}")

    table = download_catalog()
    validate_table(table)

    retrieved_at = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
    )

    provenance = {
        "source": SOURCE_NAME,
        "catalog": CATALOG_NAME,
        "source_url": TAP_URL,
        "documentation_url": DOCUMENTATION_URL,
        "catalog_reference": CATALOG_REFERENCE,
        "query": QUERY,
        "retrieved_at_utc": retrieved_at,
        "astroquery_version": astroquery.__version__,
        "row_count": len(table),
        "expected_row_count": EXPECTED_ROW_COUNT,
        "notes": (
            "The HEASARC table contains 109 rows. "
            "HEASARC treats M102 as a duplicate or erroneous "
            "observation of M101."
        ),
    }

    # These entries are written into the ECSV metadata header.
    table.meta.update(provenance)

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    # Canonical source snapshot. ECSV preserves metadata, units and types.
    table.write(
        ECSV_PATH,
        format="ascii.ecsv",
        overwrite=True,
    )

    # Plain derivative for inspection and software that expects CSV.
    table.write(
        CSV_PATH,
        format="ascii.csv",
        overwrite=True,
    )

    # The ordinary CSV format cannot carry standardized metadata, so its
    # provenance and checksums are kept in this adjacent JSON document.
    provenance_document = {
        **provenance,
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
        "columns": list(table.colnames),
    }

    with PROVENANCE_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            provenance_document,
            file,
            indent=2,
            ensure_ascii=False,
        )
        file.write("\n")

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


