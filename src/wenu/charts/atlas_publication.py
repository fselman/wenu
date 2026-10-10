"""Design-bound publication batch planning, without sky or render resources.

This narrow planning protocol is not the full publication/scene-input schema
and installs no producer command. Scientific selection and rendering retain
their canonical owners.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re

from wenu.atlas_design import AtlasBandTiling, AtlasSheetGeometry, select_atlas_sheets


def _positive_integer(value, name):
    if type(value) is not int or value < 1:
        raise ValueError(f"{name} must be a positive integer.")


def _identity(value, name):
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{name} must be a nonempty trimmed string.")


@dataclass(frozen=True)
class AtlasPublicationBatchRequest:
    """Closed version-1 planning input for a later publication invocation."""

    publication_id: str
    revision: int
    design_id: str
    design_revision: int
    design_sha256: str
    charts: str
    jobs: int = 2

    def __post_init__(self):
        for name in ("publication_id", "design_id"):
            _identity(getattr(self, name), name)
        for name in ("revision", "design_revision", "jobs"):
            _positive_integer(getattr(self, name), name)
        if not isinstance(self.design_sha256, str) or not re.fullmatch(
                r"[0-9a-f]{64}", self.design_sha256):
            raise ValueError("design_sha256 must be a lowercase SHA-256 digest.")
        if not isinstance(self.charts, str) or not self.charts.strip():
            raise ValueError("charts must be a nonempty selector string.")

    @classmethod
    def from_dict(cls, data):
        required = {"schema_version", "document_kind", "publication_id",
                    "revision", "design_id", "design_revision", "design_sha256",
                    "charts"}
        if not isinstance(data, dict) or not required <= data.keys() or (
                data.keys() - required - {"jobs"}):
            raise ValueError("Invalid or unknown publication batch planning keys.")
        if type(data["schema_version"]) is not int or data["schema_version"] != 1:
            raise ValueError("Unsupported publication batch planning schema.")
        if data["document_kind"] != "wenu-atlas-publication-batch-request":
            raise ValueError("Unsupported publication batch planning kind.")
        return cls(**{name: data[name] for name in cls.__dataclass_fields__
                      if name in data})

    def resolve(self, design_bytes, *, charts=None, jobs=None):
        """Bind exact input bytes and resolve overrides before any sky loading.

        The caller reads a design once. Hash its original bytes, not a
        reserialization; whitespace changes therefore require a new binding.
        """
        if not isinstance(design_bytes, bytes):
            raise TypeError("design_bytes must be bytes.")
        digest = hashlib.sha256(design_bytes).hexdigest()
        if digest != self.design_sha256:
            raise ValueError("Design bytes do not match design_sha256.")
        requested_jobs = self.jobs if jobs is None else jobs
        _positive_integer(requested_jobs, "jobs")
        atlas = AtlasBandTiling.from_json(design_bytes.decode("utf-8"))
        if (atlas.geometry.design_id, atlas.geometry.revision) != (
                self.design_id, self.design_revision):
            raise ValueError("Design identity/revision does not match the request.")
        selector = self.charts if charts is None else charts
        sheets = select_atlas_sheets(atlas, selector)
        return AtlasPublicationBatchPlan(
            self, atlas, sheets, selector, requested_jobs)


@dataclass(frozen=True)
class AtlasPublicationBatchPlan:
    """Resolved sheets and worker budget, not an executed or complete atlas."""

    request: AtlasPublicationBatchRequest
    atlas: AtlasBandTiling
    sheets: tuple[AtlasSheetGeometry, ...]
    charts: str
    jobs: int

    def __post_init__(self):
        if not isinstance(self.request, AtlasPublicationBatchRequest):
            raise TypeError("request must be an AtlasPublicationBatchRequest.")
        _positive_integer(self.jobs, "jobs")
        selected = select_atlas_sheets(self.atlas, self.charts)
        if tuple(self.sheets) != selected:
            raise ValueError("Plan sheets disagree with its effective selector.")
        if (self.atlas.geometry.design_id, self.atlas.geometry.revision) != (
                self.request.design_id, self.request.design_revision):
            raise ValueError("Plan design identity disagrees with its request.")
        object.__setattr__(self, "sheets", selected)

    @property
    def worker_count(self):
        return min(self.jobs, len(self.sheets))

    @property
    def chart_numbers(self):
        return tuple(sheet.number for sheet in self.sheets)
