"""Immutable installed artificial-satellite element snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import resources
import json
from types import MappingProxyType
from typing import Mapping
import re

from .elements import (
    SatelliteElementRecord,
    _utc,
    canonical_json_bytes,
    sha256_hex,
)


DEFAULT_SNAPSHOT_ID = "synthetic_50s4b_v1"
_SNAPSHOT_ID = re.compile(r"^[a-z0-9][a-z0-9_]*$")


def _text(value, *, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string.")
    value = value.strip()
    if not value:
        raise ValueError(f"{name} must be non-empty.")
    return value


def _digest(value, *, name: str) -> str:
    value = _text(value, name=name).lower()
    if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError(
            f"{name} must contain exactly 64 hexadecimal characters."
        )
    return value


@dataclass(frozen=True)
class SatelliteSnapshotManifest:
    """Provenance and content identity for one installed snapshot."""

    schema_version: int
    snapshot_id: str
    created_utc: str
    source_identity: str
    source_url: str
    source_format: str
    records_file: str
    content_sha256: str
    record_count: int
    builder_identity: str
    provider_policy_url: str
    provider_policy_checked_utc: str
    provenance: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if self.schema_version != 1:
            raise ValueError("schema_version must be 1.")
        if not isinstance(self.record_count, int) or isinstance(
            self.record_count, bool
        ):
            raise TypeError("record_count must be an integer.")
        if self.record_count <= 0:
            raise ValueError("record_count must be positive.")
        for name in (
            "snapshot_id",
            "source_identity",
            "source_url",
            "source_format",
            "records_file",
            "builder_identity",
            "provider_policy_url",
        ):
            object.__setattr__(
                self, name, _text(getattr(self, name), name=name)
            )
        for name in ("created_utc", "provider_policy_checked_utc"):
            object.__setattr__(
                self, name, _utc(getattr(self, name), name=name)
            )
        if not _SNAPSHOT_ID.fullmatch(self.snapshot_id):
            raise ValueError("snapshot_id contains unsupported characters.")
        if "/" in self.records_file or "\\" in self.records_file:
            raise ValueError("records_file must be a local resource name.")
        object.__setattr__(
            self,
            "content_sha256",
            _digest(self.content_sha256, name="content_sha256"),
        )
        for name in ("provenance", "warnings"):
            value = getattr(self, name)
            if isinstance(value, (str, bytes)):
                raise TypeError(f"{name} must be an iterable of strings.")
            object.__setattr__(
                self,
                name,
                tuple(
                    _text(item, name=f"{name} entry") for item in value
                ),
            )

    @classmethod
    def from_mapping(cls, mapping: Mapping):
        """Build a manifest while rejecting missing or unknown fields."""
        expected = {
            "schema_version",
            "snapshot_id",
            "created_utc",
            "source_identity",
            "source_url",
            "source_format",
            "records_file",
            "content_sha256",
            "record_count",
            "builder_identity",
            "provider_policy_url",
            "provider_policy_checked_utc",
            "provenance",
            "warnings",
        }
        if not isinstance(mapping, Mapping) or set(mapping) != expected:
            raise ValueError("manifest keys do not match schema version 1.")
        return cls(**mapping)


@dataclass(frozen=True)
class SatelliteElementSnapshot:
    """One immutable, ordered set of canonical satellite elements."""

    manifest: SatelliteSnapshotManifest
    records: tuple[SatelliteElementRecord, ...]

    def __post_init__(self):
        if not isinstance(self.manifest, SatelliteSnapshotManifest):
            raise TypeError("manifest must be a SatelliteSnapshotManifest.")
        records = tuple(self.records)
        if not records or not all(
            isinstance(item, SatelliteElementRecord) for item in records
        ):
            raise TypeError(
                "records must contain SatelliteElementRecord instances."
            )
        identifiers = tuple(item.norad_catalog_id for item in records)
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("snapshot contains duplicate NORAD identifiers.")
        if identifiers != tuple(sorted(identifiers)):
            raise ValueError(
                "snapshot records must be ordered by full NORAD identifier."
            )
        if len(records) != self.manifest.record_count:
            raise ValueError("record_count does not match snapshot records.")
        object.__setattr__(self, "records", records)

    @property
    def by_norad_catalog_id(self):
        """Return an immutable full-NORAD lookup."""
        return MappingProxyType(
            {record.norad_catalog_id: record for record in self.records}
        )


def snapshot_from_bytes(manifest_bytes: bytes, records_bytes: bytes):
    """Validate and construct a snapshot from exact UTF-8 resource bytes."""
    try:
        manifest_data = json.loads(manifest_bytes)
        records_data = json.loads(records_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(
            "snapshot resources must be valid UTF-8 JSON."
        ) from error
    if canonical_json_bytes(records_data) != records_bytes:
        raise ValueError("snapshot records are not canonical JSON bytes.")
    manifest = SatelliteSnapshotManifest.from_mapping(manifest_data)
    actual_digest = sha256_hex(records_bytes)
    if actual_digest != manifest.content_sha256:
        raise ValueError(
            "snapshot content_sha256 does not match records bytes."
        )
    if not isinstance(records_data, list):
        raise ValueError("snapshot records payload must be a JSON list.")
    records = tuple(
        SatelliteElementRecord.from_mapping(item) for item in records_data
    )
    return SatelliteElementSnapshot(manifest=manifest, records=records)


def load_snapshot(snapshot_id: str = DEFAULT_SNAPSHOT_ID):
    """Load and fully validate one installed satellite snapshot."""
    snapshot_id = _text(snapshot_id, name="snapshot_id")
    if not _SNAPSHOT_ID.fullmatch(snapshot_id):
        raise ValueError("snapshot_id contains unsupported characters.")
    root = resources.files("wenu.data.satellites.snapshots").joinpath(
        snapshot_id
    )
    manifest_bytes = root.joinpath("manifest.json").read_bytes()
    try:
        manifest_data = json.loads(manifest_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("manifest must be valid UTF-8 JSON.") from error
    records_name = manifest_data.get("records_file")
    if not isinstance(records_name, str):
        raise ValueError("manifest records_file must be a string.")
    result = snapshot_from_bytes(
        manifest_bytes,
        root.joinpath(records_name).read_bytes(),
    )
    if result.manifest.snapshot_id != snapshot_id:
        raise ValueError(
            "manifest snapshot_id does not match resource path."
        )
    return result
