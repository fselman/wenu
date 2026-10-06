"""Offline, immutable HIP-linked Wikidata candidates, separate from astrometry.

Labels and aliases are evidence, not approved proper names. No designation or
component preference is inferred here; editorial decisions belong to curation.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from wenu.resources import star_designations_manifest_path

_RANKS = frozenset(("NormalRank", "PreferredRank", "DeprecatedRank"))


@dataclass(frozen=True)
class HipLink:
    statement_id: str
    value: str
    rank: str


@dataclass(frozen=True)
class DesignationStatement:
    statement_id: str
    item_id: str
    kind: str
    code: str
    rank: str
    hip_links: tuple[HipLink, ...]
    references: tuple[str, ...]


@dataclass(frozen=True)
class NameCandidate:
    item_id: str
    value: str
    language: str
    role: str


@dataclass(frozen=True)
class StarDesignations:
    hip: int
    statements: tuple[DesignationStatement, ...]
    names: tuple[NameCandidate, ...]
    review_fields: tuple[str, ...]

    def candidates(self, kind: str) -> tuple[DesignationStatement, ...]:
        """Return active source claims without choosing or normalizing one."""
        if kind not in ("bayer", "flamsteed"):
            raise ValueError(f"Unknown designation kind: {kind!r}")
        return tuple(
            s
            for s in self.statements
            if s.kind == kind and s.rank != "DeprecatedRank"
        )

    @property
    def item_ids(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {s.item_id for s in self.statements}
                | {n.item_id for n in self.names}
            )
        )


@dataclass(frozen=True)
class StarDesignationCatalogue:
    edition: str
    source_sha256: str
    by_hip: Mapping[int, StarDesignations]
    unjoined_statements: tuple[DesignationStatement, ...]

    def get(self, hip: int) -> StarDesignations | None:
        return self.by_hip.get(hip)


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _keys(value, expected):
    _require(
        isinstance(value, dict) and set(value) == set(expected),
        "Invalid Wikidata record fields",
    )


def _text(value):
    _require(
        isinstance(value, str) and bool(value.strip()),
        "Expected nonempty text",
    )
    return value


def _item(value):
    _require(
        isinstance(value, str) and re.fullmatch(r"Q[1-9][0-9]*", value),
        "Invalid Wikidata item ID",
    )
    return value


def _rank(value):
    _require(
        isinstance(value, str) and value in _RANKS,
        "Invalid Wikidata statement rank",
    )
    return value


def _statement_id(value, item=None):
    _text(value)
    _require(
        re.fullmatch(
            r"http://www.wikidata.org/entity/statement/[Qq][1-9][0-9]*-[A-Za-z0-9-]+",
            value,
        ),
        "Invalid Wikidata statement ID",
    )
    if item is not None:
        _require(
            value.rsplit("/", 1)[-1].upper().startswith(item + "-"),
            "Statement belongs to a different item",
        )
    return value


def _statement(value):
    _keys(
        value,
        ("id", "item", "kind", "code", "rank", "hip_links", "references"),
    )
    item = _item(value["item"])
    _require(
        value["kind"] in ("bayer", "flamsteed"), "Invalid designation kind"
    )
    _require(isinstance(value["hip_links"], list), "Invalid HIP links")
    links = []
    for link in value["hip_links"]:
        _require(isinstance(link, list) and len(link) == 3, "Invalid HIP link")
        links.append(
            HipLink(
                _statement_id(link[0], item), _text(link[1]), _rank(link[2])
            )
        )
    _require(len(set(links)) == len(links), "Duplicate HIP link")
    refs = value["references"]
    _require(
        isinstance(refs, list)
        and all(
            isinstance(x, str)
            and re.fullmatch(r"http://www.wikidata.org/reference/[0-9a-f]+", x)
            for x in refs
        ),
        "Invalid Wikidata references",
    )
    _require(len(set(refs)) == len(refs), "Duplicate reference")
    return DesignationStatement(
        _statement_id(value["id"], item),
        item,
        value["kind"],
        _text(value["code"]),
        _rank(value["rank"]),
        tuple(links),
        tuple(refs),
    )


def _json(payload):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            _require(key not in result, f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(payload, object_pairs_hook=unique)


def load_star_designations(manifest_path=None) -> StarDesignationCatalogue:
    """Read and verify a packaged snapshot, or an explicit local manifest.

    Missing HIPs return None. Ambiguous/malformed HIP assignments stay unjoined;
    deprecated claims stay in the evidence but are absent from candidates().
    """
    path = (
        star_designations_manifest_path()
        if manifest_path is None
        else Path(manifest_path)
    )
    manifest = _json(path.read_bytes())
    _require(
        manifest.get("schema") == "wenu-star-designations-manifest/1",
        "Unsupported designation manifest",
    )
    _require(
        manifest.get("source") == "Wikidata"
        and manifest.get("license") == "CC0-1.0",
        "Unsupported designation source/license",
    )
    _require(
        manifest.get("file") == "wikidata.json", "Invalid snapshot filename"
    )
    digest = manifest.get("sha256")
    _require(
        isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest),
        "Invalid snapshot digest",
    )
    payload = path.parent.joinpath("wikidata.json").read_bytes()
    _require(
        hashlib.sha256(payload).hexdigest() == digest,
        "Designation snapshot digest mismatch",
    )
    document = _json(payload)
    _keys(document, ("schema", "records", "unjoined_statements"))
    _require(
        document["schema"] == "wenu-wikidata-designations/1",
        "Unsupported snapshot schema",
    )
    _require(
        isinstance(document["records"], list)
        and isinstance(document["unjoined_statements"], list),
        "Invalid snapshot collections",
    )
    index = {}
    ids = set()

    def checked_statement(value):
        result = _statement(value)
        _require(
            result.statement_id not in ids, "Duplicate designation statement"
        )
        ids.add(result.statement_id)
        return result

    for value in document["records"]:
        _keys(value, ("hip", "statements", "names", "review_fields"))
        hip = value["hip"]
        _require(
            type(hip) is int and hip > 0 and hip not in index,
            "Invalid/duplicate HIP",
        )
        _require(
            isinstance(value["statements"], list)
            and isinstance(value["names"], list),
            "Invalid candidate collections",
        )
        statements = tuple(checked_statement(s) for s in value["statements"])
        for statement in statements:
            active = [
                link.value
                for link in statement.hip_links
                if link.rank != "DeprecatedRank"
            ]
            _require(
                bool(active) and set(active) == {f"HIP {hip}"},
                "Unsafe HIP join",
            )
        names = []
        for name in value["names"]:
            _require(
                isinstance(name, list) and len(name) == 4,
                "Invalid name candidate",
            )
            _require(
                name[3] in ("label", "alias") and name[2] == "en",
                "Invalid name scope",
            )
            names.append(
                NameCandidate(_item(name[0]), _text(name[1]), name[2], name[3])
            )
        _require(len(set(names)) == len(names), "Duplicate name candidate")
        fields = value["review_fields"]
        _require(
            isinstance(fields, list)
            and all(x in ("bayer", "flam") for x in fields)
            and len(set(fields)) == len(fields),
            "Invalid review fields",
        )
        index[hip] = StarDesignations(
            hip, statements, tuple(names), tuple(fields)
        )
    unjoined = tuple(
        checked_statement(s) for s in document["unjoined_statements"]
    )
    for key, count in (
        ("record_count", len(index)),
        ("statement_count", len(ids)),
        ("unjoined_statement_count", len(unjoined)),
    ):
        _require(
            type(manifest.get(key)) is int and manifest[key] == count,
            "Snapshot count mismatch",
        )
    return StarDesignationCatalogue(
        _text(manifest["edition"]), digest, MappingProxyType(index), unjoined
    )
