"""Compile frozen Wikidata responses offline; never acquire or adjudicate data.

Run from the repository root:
    python tools/build_wikidata_star_designations.py
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path


def encode(value):
    return (
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        + "\n"
    ).encode("utf-8")


def compile_snapshot(source, review, output):
    receipts = []

    def read(name):
        payload = gzip.decompress((source / (name + ".gz")).read_bytes())
        receipt = json.loads((source / (name + ".receipt.json")).read_text())
        if hashlib.sha256(payload).hexdigest() != receipt["sha256"]:
            raise ValueError(f"Acquisition digest mismatch: {name}")
        if len(payload) != receipt["bytes"]:
            raise ValueError(f"Acquisition size mismatch: {name}")
        receipts.append(
            {
                "file": name,
                "sha256": receipt["sha256"],
                "retrieved_at_utc": receipt["retrieved_at_utc"],
                "url": receipt["url"],
            }
        )
        return json.loads(payload)["results"]["bindings"]

    statements = {}
    for row in read("wikidata-designations.json"):

        def val(key, row=row):
            return row.get(key, {}).get("value")

        identifier = val("statement")
        item = val("item").rsplit("/", 1)[-1]
        entry = statements.setdefault(
            identifier,
            {
                "id": identifier,
                "item": item,
                "kind": {"Q105616": "bayer", "Q111116": "flamsteed"}[
                    val("catalog").rsplit("/", 1)[-1]
                ],
                "code": val("code"),
                "rank": val("rank").rsplit("#", 1)[-1],
                "hip_links": set(),
                "references": set(),
            },
        )
        if (entry["item"], entry["code"], entry["rank"]) != (
            item,
            val("code"),
            val("rank").rsplit("#", 1)[-1],
        ):
            raise ValueError(f"Inconsistent statement: {identifier}")
        if val("hip"):
            entry["hip_links"].add(
                (
                    val("hipstatement"),
                    val("hip"),
                    val("hiprank").rsplit("#", 1)[-1],
                )
            )
        if val("reference"):
            entry["references"].add(val("reference"))

    by_hip = defaultdict(lambda: {"statements": [], "names": set()})
    unjoined = []
    for entry in sorted(statements.values(), key=lambda s: s["id"]):
        entry["hip_links"] = [list(x) for x in sorted(entry["hip_links"])]
        entry["references"] = sorted(entry["references"])
        active = [
            link for link in entry["hip_links"] if link[2] != "DeprecatedRank"
        ]
        valid = {
            int(m.group(1))
            for link in active
            if (m := re.fullmatch(r"HIP ([1-9][0-9]*)", link[1]))
        }
        # Malformed or multiple active HIP assignments never become a guessed join.
        if len(valid) == 1 and all(
            re.fullmatch(r"HIP [1-9][0-9]*", x[1]) for x in active
        ):
            by_hip[next(iter(valid))]["statements"].append(entry)
        else:
            unjoined.append(entry)

    for n in range(1, 5):
        for row in read(f"wikidata-named-targets-{n}.json"):
            hip = int(
                re.fullmatch(r"HIP ([1-9][0-9]*)", row["hip"]["value"]).group(
                    1
                )
            )
            item = row["item"]["value"].rsplit("/", 1)[-1]
            for role in ("label", "alias"):
                if role in row:
                    by_hip[hip]["names"].add(
                        (
                            item,
                            row[role]["value"],
                            row[role].get("xml:lang", "en"),
                            role,
                        )
                    )
    pending = defaultdict(set)
    ledger = json.loads(review.read_text())
    for case in ledger["cases"]:
        if (
            case["status"] != "pending_fernando"
            or case["decision"] is not None
        ):
            raise ValueError("This compiler cannot apply editorial decisions")
        pending[case["hip"]].add(case["field"])
    records = [
        {
            "hip": hip,
            "statements": values["statements"],
            "names": [list(x) for x in sorted(values["names"])],
            "review_fields": sorted(pending[hip]),
        }
        for hip, values in sorted(by_hip.items())
    ]
    document = {
        "schema": "wenu-wikidata-designations/1",
        "records": records,
        "unjoined_statements": unjoined,
    }
    payload = encode(document)
    output.mkdir(parents=True, exist_ok=True)
    (output / "wikidata.json").write_bytes(payload)
    manifest = {
        "schema": "wenu-star-designations-manifest/1",
        "edition": "wikidata-2026-10-05",
        "source": "Wikidata",
        "license": "CC0-1.0",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "file": "wikidata.json",
        "sha256": hashlib.sha256(payload).hexdigest(),
        "record_count": len(records),
        "statement_count": len(statements),
        "unjoined_statement_count": len(unjoined),
        "acquisitions": receipts,
        "review_sha256": hashlib.sha256(review.read_bytes()).hexdigest(),
        "name_scope": "English labels/aliases for the 566 HIP targets in the source audit; not an official-name catalogue",
        "builder": "tools/build_wikidata_star_designations.py",
    }
    (output / "manifest.json").write_bytes(encode(manifest))
    return manifest


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    resource = root / "src/wenu/data/catalogs/star_designations"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=resource / "source")
    parser.add_argument(
        "--review",
        type=Path,
        default=root / "docs/developer/data/stellar_designations_review.json",
    )
    parser.add_argument("--output", type=Path, default=resource)
    args = parser.parse_args()
    print(
        json.dumps(
            compile_snapshot(args.source, args.review, args.output), indent=2
        )
    )
