"""Immutable, offline HIP index of designation research and accepted policy.

The authored research is report evidence, not an astrometric catalogue or a
claim that every historical question has been resolved.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
from importlib.resources import files
import json
from types import MappingProxyType
from collections.abc import Mapping

from wenu.star_designations import _json, _require


@dataclass(frozen=True)
class StellarResearch:
    source_sha256: str
    policy_sha256: str
    by_hip: Mapping[int, str]
    sources_json: str
    shared_preferences: Mapping[tuple[int, str], str]

    def __contains__(self, hip):
        return hip in self.by_hip

    def get(self, hip):
        """Return an independent report record, keeping the index immutable."""
        value = self.by_hip.get(hip)
        return None if value is None else json.loads(value)

    def shared_preference(self, hip, kind):
        return self.shared_preferences.get((hip, kind))


@lru_cache(maxsize=1)
def load_stellar_research():
    """Load and digest-verify the frozen 77-case evidence once per process."""
    root = files("wenu.data.catalogs.star_designations")
    manifest = _json(root.joinpath("research_manifest.json").read_bytes())
    _require(
        manifest.get("schema") == "wenu-stellar-research-manifest/1",
        "Invalid research manifest",
    )
    payload = root.joinpath("research.json").read_bytes()
    policy_payload = root.joinpath("research_policy.json").read_bytes()
    for value, key in (
        (payload, "research_sha256"),
        (policy_payload, "policy_sha256"),
    ):
        _require(
            hashlib.sha256(value).hexdigest() == manifest.get(key),
            "Stellar research digest mismatch",
        )
    document = _json(payload)
    policy = _json(policy_payload)
    _require(
        document.get("schema_version") == 1
        and document.get("case_count") == 77,
        "Invalid research schema/count",
    )
    _require(
        policy.get("schema") == "wenu-stellar-policy/1",
        "Invalid stellar policy",
    )
    index = {}
    for case in document["cases"]:
        hip = case["hip"]
        _require(
            type(hip) is int and hip > 0 and hip not in index,
            "Invalid or duplicate research HIP",
        )
        _require(
            case["case_id"] == f"HIP-{hip}-{case['field']}",
            "Research identity mismatch",
        )
        index[hip] = json.dumps(case, ensure_ascii=False, sort_keys=True)
    _require(len(index) == 77, "Research must retain all 77 cases")
    preferences = {}
    for entry in policy["shared_preferences"]:
        key = entry["hip"], entry["kind"]
        _require(
            key not in preferences and key[0] in index,
            "Invalid shared-star policy identity",
        )
        case = json.loads(index[key[0]])
        _require(
            case["classification"] == "Historical shared constellation",
            "Preference must refer to a researched shared star",
        )
        _require(
            key[1] == ("flamsteed" if case["field"] == "flam" else "bayer"),
            "Shared preference field mismatch",
        )
        _require(
            entry["designation"] in case["source_values"]["Wikidata"],
            "Shared preference must retain an existing Wikidata alias",
        )
        preferences[key] = entry["designation"]
    return StellarResearch(
        manifest["research_sha256"],
        manifest["policy_sha256"],
        MappingProxyType(index),
        json.dumps(document["sources"], ensure_ascii=False, sort_keys=True),
        MappingProxyType(preferences),
    )
