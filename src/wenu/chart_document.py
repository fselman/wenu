"""Neutral records shared by chart orchestration and renderers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class EditPolicy(str, Enum):
    """Supported external editing operations for semantic content."""

    STYLE = "style"
    LAYOUT = "layout"
    NONE = "none"


@dataclass(frozen=True)
class SemanticArtistIdentity:
    """Renderer-neutral identity for chart-owned presentation content."""

    name: str
    svg_id: str
    edit_policy: EditPolicy
    semantic_path: tuple[str, ...]
    display_name: str
    presentation_order: int
    style_role: str

    def component_identity(self, component):
        """Chart-owned identities do not declare renderer subcomponents."""
        return self


@dataclass(frozen=True)
class SemanticArtistRenderingResult:
    """One renderer artist with Wenu identity and paint position."""

    artist: Any
    svg_id: str
    zorder: float
    paint_role: Any | None
    edit_policy: EditPolicy
    semantic_path: tuple[str, ...] = ()
    display_name: str = ""
    presentation_order: int | None = None
    style_role: str = ""
