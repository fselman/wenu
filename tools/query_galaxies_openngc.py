#!/usr/bin/env python3
"""Build Wenu's bright-galaxy development catalogue from OpenNGC.

This maintenance utility downloads a pinned OpenNGC release, selects
individual galaxies down to a configurable integrated-magnitude limit, and
writes a canonical ECSV file, a CSV derivative, and provenance metadata.
It is not used at Wenu runtime.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import sys
from urllib.request import Request, urlopen

try:
    from astropy import units as u
    from astropy.coordinates import SkyCoord
    from astropy.table import Table
except ModuleNotFoundError as error:
    if error.name == "astropy":
        raise SystemExit(
            "Astropy is required. Run this script from the Python "
            "environment in which Wenu is installed."
        ) from error
    raise


OPENNGC_RELEASE = "v20260501"
REPOSITORY_URL = "https://github.com/mattiaverga/OpenNGC"
RAW_ROOT = (
    "https://raw.githubusercontent.com/mattiaverga/OpenNGC/"
    f"{OPENNGC_RELEASE}"
)
SOURCE_FILES = {
    "NGC.csv": f"{RAW_ROOT}/database_files/NGC.csv",
    "addendum.csv": f"{RAW_ROOT}/database_files/addendum.csv",
}
LICENSE_URL = f"{RAW_ROOT}/LICENSES/CC-BY-SA-4.0.txt"
LICENSE_NAME = "CC-BY-SA-4.0.txt"

EXPECTED_COLUMNS = {
    "Name",
    "Type",
    "RA",
    "Dec",
    "Const",
    "MajAx",
    "MinAx",
    "PosAng",
    "B-Mag",
    "V-Mag",
    "SurfBr",
    "Hubble",
    "M",
    "NGC",
    "IC",
    "Identifiers",
    "Common names",
    "Sources",
}

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIRECTORY = (
    REPOSITORY_ROOT
    / "src"
    / "wenu"
    / "data"
    / "catalogs"
    / "galaxies"
)


def sha256_bytes(content: bytes) -> str:
    """Return the hexadecimal SHA-256 checksum of bytes."""
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    """Return the hexadecimal SHA-256 checksum of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download(url: str) -> bytes:
    """Download one pinned OpenNGC resource."""
    request = Request(
        url,
        headers={"User-Agent": "Wenu-catalogue-maintenance/1.0"},
    )
    with urlopen(request, timeout=120) as response:
        return response.read()


def text(value: object) -> str:
    """Normalize an OpenNGC text field."""
    if value is None:
        return ""
    return str(value).strip()


def number(value: object) -> float:
    """Convert a possibly blank catalogue field to a float or NaN."""
    candidate = text(value)
    if not candidate:
        return math.nan
    try:
        return float(candidate)
    except ValueError as error:
        raise ValueError(
            f"Expected a number, received {candidate!r}."
        ) from error


def read_source(name: str, content: bytes) -> list[dict[str, str]]:
    """Parse and validate one semicolon-separated OpenNGC source file."""
    decoded = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded), delimiter=";")
    available = set(reader.fieldnames or ())
    missing = EXPECTED_COLUMNS - available
    if missing:
        raise RuntimeError(
            f"{name} is missing expected columns: "
            + ", ".join(sorted(missing))
        )
    rows = list(reader)
    if not rows:
        raise RuntimeError(f"{name} contains no catalogue rows.")
    return rows


def selection_magnitude(row: dict[str, str]) -> tuple[float, str]:
    """Return V magnitude, falling back conservatively to B."""
    v_magnitude = number(row["V-Mag"])
    if math.isfinite(v_magnitude):
        return v_magnitude, "V"
    b_magnitude = number(row["B-Mag"])
    if math.isfinite(b_magnitude):
        return b_magnitude, "B"
    return math.nan, ""


def rendering_class(row: dict[str, str]) -> str:
    """Identify extended systems reserved for later isophote rendering."""
    names = " ".join(
        (
            text(row["Name"]),
            text(row["Identifiers"]),
            text(row["Common names"]),
        )
    ).casefold()
    magellanic = (
        "large magellanic cloud",
        "small magellanic cloud",
        "lmc",
        "smc",
    )
    return (
        "isophote"
        if any(name in names for name in magellanic)
        else "ellipse"
    )


def normalize(
    source_rows: list[tuple[str, dict[str, str]]],
    magnitude_limit: float,
) -> tuple[Table, dict[str, int]]:
    """Select individual galaxies and normalize fields for Wenu."""
    records = []
    statistics = {
        "source_rows": len(source_rows),
        "individual_galaxies": 0,
        "without_selection_magnitude": 0,
        "fainter_than_limit": 0,
        "selected_rows": 0,
    }
    seen_names: set[str] = set()

    for source_file, row in source_rows:
        if text(row["Type"]) != "G":
            continue
        statistics["individual_galaxies"] += 1

        magnitude, band = selection_magnitude(row)
        if not math.isfinite(magnitude):
            statistics["without_selection_magnitude"] += 1
            continue
        if magnitude > magnitude_limit:
            statistics["fainter_than_limit"] += 1
            continue

        name = text(row["Name"])
        if not name:
            raise RuntimeError(
                f"Selected row in {source_file} has no object name."
            )
        if name in seen_names:
            raise RuntimeError(
                f"Duplicate selected OpenNGC name: {name}."
            )
        seen_names.add(name)

        coordinate = SkyCoord(
            text(row["RA"]),
            text(row["Dec"]),
            unit=(u.hourangle, u.deg),
            frame="icrs",
        )
        records.append(
            {
                "name": name,
                "object_type": "galaxy",
                "ra_deg": float(coordinate.ra.deg),
                "dec_deg": float(coordinate.dec.deg),
                "constellation": text(row["Const"]),
                "major_axis_arcmin": number(row["MajAx"]),
                "minor_axis_arcmin": number(row["MinAx"]),
                "position_angle_deg": number(row["PosAng"]),
                "b_magnitude": number(row["B-Mag"]),
                "v_magnitude": number(row["V-Mag"]),
                "selection_magnitude": magnitude,
                "selection_band": band,
                "surface_brightness_b_mag_arcsec2": number(
                    row["SurfBr"]
                ),
                "morphology": text(row["Hubble"]),
                "messier": text(row["M"]),
                "ngc": text(row["NGC"]),
                "ic": text(row["IC"]),
                "identifiers": text(row["Identifiers"]),
                "common_names": text(row["Common names"]),
                "openngc_notes": text(row.get("OpenNGC notes")),
                "ned_notes": text(row.get("NED notes")),
                "sources": text(row["Sources"]),
                "source_file": source_file,
                "rendering_class": rendering_class(row),
            }
        )

    records.sort(
        key=lambda record: (
            record["selection_magnitude"],
            record["name"],
        )
    )
    statistics["selected_rows"] = len(records)
    if len(records) < 50:
        raise RuntimeError(
            "Fewer than 50 galaxies passed the selection. "
            "The upstream data or selection logic may have changed."
        )

    table = Table(rows=records)
    table["ra_deg"].unit = u.deg
    table["dec_deg"].unit = u.deg
    table["major_axis_arcmin"].unit = u.arcmin
    table["minor_axis_arcmin"].unit = u.arcmin
    table["position_angle_deg"].unit = u.deg
    return table, statistics


def catalogue_readme(magnitude_limit: float) -> str:
    """Return the README stored beside the generated catalogue."""
    return f"""# OpenNGC bright-galaxy catalogue

This directory is generated by `tools/query_galaxies_openngc.py`.

- Source: OpenNGC release `{OPENNGC_RELEASE}`
- Selection: individual galaxies (`Type == G`)
- Magnitude limit: `{magnitude_limit:g}`
- Magnitude rule: use V when present; otherwise use B
- Canonical data: `galaxies_openngc.ecsv`
- Convenience derivative: `galaxies_openngc.csv`
- Provenance and checksums: `galaxies_openngc.provenance.json`

The selection magnitude is an integrated magnitude and is not, by itself, a
prediction of naked-eye or binocular visibility. Surface brightness and
angular size are retained for later visibility-ranking work.

OpenNGC is licensed under Creative Commons Attribution-ShareAlike 4.0.
The applicable license text is stored as `{LICENSE_NAME}`.
"""


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--magnitude-limit",
        type=float,
        default=12.0,
        help="Maximum V magnitude, or B when V is unavailable (default: 12).",
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=DEFAULT_OUTPUT_DIRECTORY,
        help="Destination directory (normally inferred from the repository).",
    )
    return parser.parse_args()


def main() -> int:
    """Download, select, validate, document, and store the catalogue."""
    arguments = parse_arguments()
    limit = float(arguments.magnitude_limit)
    if not math.isfinite(limit):
        raise ValueError("The magnitude limit must be finite.")

    downloaded: dict[str, bytes] = {}
    source_rows: list[tuple[str, dict[str, str]]] = []
    for name, url in SOURCE_FILES.items():
        print(f"Downloading {name} from OpenNGC {OPENNGC_RELEASE}...")
        content = download(url)
        downloaded[name] = content
        source_rows.extend(
            (name, row) for row in read_source(name, content)
        )

    print("Downloading the OpenNGC licence...")
    license_content = download(LICENSE_URL)
    table, statistics = normalize(source_rows, limit)

    retrieved_at = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
    )
    provenance = {
        "source": "OpenNGC",
        "repository_url": REPOSITORY_URL,
        "release": OPENNGC_RELEASE,
        "retrieved_at_utc": retrieved_at,
        "license": "CC-BY-SA-4.0",
        "license_url": LICENSE_URL,
        "selection": {
            "object_type": "G",
            "magnitude_limit": limit,
            "magnitude_rule": (
                "Use V-Mag when available; otherwise use B-Mag."
            ),
        },
        "statistics": statistics,
        "source_files": {
            name: {
                "url": SOURCE_FILES[name],
                "sha256": sha256_bytes(content),
            }
            for name, content in downloaded.items()
        },
        "notes": (
            "Integrated magnitude does not alone determine naked-eye or "
            "binocular visibility. Angular dimensions and surface brightness "
            "are retained. Magellanic Clouds remain in the catalogue with "
            "rendering_class='isophote'."
        ),
    }
    table.meta.update(provenance)

    output = arguments.output_directory.resolve()
    output.mkdir(parents=True, exist_ok=True)
    ecsv_path = output / "galaxies_openngc.ecsv"
    csv_path = output / "galaxies_openngc.csv"
    provenance_path = output / "galaxies_openngc.provenance.json"
    readme_path = output / "README.md"
    license_path = output / LICENSE_NAME
    init_path = output / "__init__.py"

    table.write(ecsv_path, format="ascii.ecsv", overwrite=True)
    table.write(csv_path, format="ascii.csv", overwrite=True)
    license_path.write_bytes(license_content)
    readme_path.write_text(
        catalogue_readme(limit),
        encoding="utf-8",
    )
    if not init_path.exists():
        init_path.write_text(
            '"""Bundled bright-galaxy catalogue data."""\n',
            encoding="utf-8",
        )

    provenance["generated_files"] = {
        path.name: {"sha256": sha256_file(path)}
        for path in (
            ecsv_path,
            csv_path,
            license_path,
            readme_path,
        )
    }
    provenance["columns"] = list(table.colnames)
    provenance_path.write_text(
        json.dumps(provenance, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Selected galaxies:  {len(table)}")
    print(f"Canonical snapshot: {ecsv_path}")
    print(f"CSV derivative:     {csv_path}")
    print(f"Provenance:         {provenance_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        raise
