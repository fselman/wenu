"""Download Wenu's pinned D3-Celestial Milky Way isophote snapshot."""

from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


REPOSITORY = "ofrohn/d3-celestial"
BLOB_SHA = "ce06eaa01d80a4eed149c538d2d162c919b58a84"
BLOB_URL = (
    f"https://api.github.com/repos/{REPOSITORY}/git/blobs/{BLOB_SHA}"
)
SOURCE_PATH = "data/mw.json"
LICENSE_URL = (
    "https://raw.githubusercontent.com/ofrohn/d3-celestial/"
    "master/LICENSE"
)
EXPECTED_LEVELS = ("ol1", "ol2", "ol3", "ol4", "ol5")
EXPECTED_RING_COUNTS = (10, 113, 46, 27, 6)


def _download(url):
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "wenu-catalogue-maintenance",
        },
    )
    with urlopen(request, timeout=60) as response:
        return response.read()


def _level(feature):
    return str(
        feature.get("id") or feature.get("properties", {}).get("id")
    )


def _validate(document):
    if document.get("type") != "FeatureCollection":
        raise RuntimeError("Expected a GeoJSON FeatureCollection.")
    features = document.get("features", ())
    levels = tuple(_level(feature) for feature in features)
    if levels != EXPECTED_LEVELS:
        raise RuntimeError(f"Unexpected isophote levels: {levels!r}.")
    counts = []
    for feature in features:
        geometry = feature.get("geometry", {})
        if geometry.get("type") != "MultiPolygon":
            raise RuntimeError("Every level must be a MultiPolygon.")
        counts.append(
            sum(len(polygon) for polygon in geometry["coordinates"])
        )
    if tuple(counts) != EXPECTED_RING_COUNTS:
        raise RuntimeError(f"Unexpected ring counts: {counts!r}.")
    return levels, tuple(counts)


def main():
    root = Path(__file__).resolve().parents[1]
    destination = (
        root / "src/wenu/data/isophotes/milky_way"
    )
    destination.mkdir(parents=True, exist_ok=True)

    blob = json.loads(_download(BLOB_URL).decode("utf-8"))
    if blob.get("sha") != BLOB_SHA or blob.get("encoding") != "base64":
        raise RuntimeError("GitHub returned an unexpected Git blob.")
    raw = base64.b64decode(blob["content"])
    document = json.loads(raw.decode("utf-8"))
    levels, ring_counts = _validate(document)

    canonical = json.dumps(
        document,
        ensure_ascii=False,
        indent=2,
    ) + "\n"
    data_path = destination / "milky_way_d3.json"
    data_path.write_text(canonical, encoding="utf-8")
    level_files = {}
    for feature in document["features"]:
        level = _level(feature)
        single = {
            "type": "FeatureCollection",
            "features": [feature],
        }
        level_path = destination / f"milky_way_{level}.geojson"
        level_path.write_text(
            json.dumps(
                single,
                ensure_ascii=False,
                separators=(",", ":"),
            ) + "\n",
            encoding="utf-8",
        )
        level_files[level] = level_path.name

    license_text = _download(LICENSE_URL).decode("utf-8")
    (destination / "BSD-3-Clause.txt").write_text(
        license_text,
        encoding="utf-8",
    )
    (destination / "__init__.py").write_text(
        '"""Packaged Milky Way isophote data."""\n',
        encoding="utf-8",
    )
    (destination / "README.md").write_text(
        "# Milky Way isophotes\n\n"
        "The canonical GeoJSON snapshot comes from D3-Celestial "
        f"`{SOURCE_PATH}` at Git blob `{BLOB_SHA}`. It is distributed "
        "under the included BSD-3-Clause licence. Coordinates are "
        "longitude/latitude degrees in the source celestial frame.\n",
        encoding="utf-8",
    )

    provenance = {
        "catalogue": "D3-Celestial Milky Way isophotes",
        "repository": REPOSITORY,
        "source_path": SOURCE_PATH,
        "git_blob_sha": BLOB_SHA,
        "source_url": BLOB_URL,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "license": "BSD-3-Clause",
        "canonical_file": data_path.name,
        "canonical_sha256": hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest(),
        "levels": list(levels),
        "single_level_files": level_files,
        "ring_counts": list(ring_counts),
    }
    (destination / "milky_way_d3.provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Milky Way isophotes: {data_path}")
    print(f"Levels: {', '.join(levels)}")
    print(f"Ring counts: {ring_counts}")


if __name__ == "__main__":
    main()
