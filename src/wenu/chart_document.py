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


def assign_canvas_semantics(renderer):
    """Attach identities to page, sky background, and visible frame sides."""
    assign = getattr(renderer, "assign_semantic_identity", None)
    ax = getattr(renderer, "ax", None)
    if not callable(assign) or ax is None:
        return
    figure_patch = getattr(getattr(ax, "figure", None), "patch", None)
    if figure_patch is not None and figure_patch.get_visible():
        assign(
            (figure_patch,),
            SemanticArtistIdentity(
                name="page_background",
                svg_id="wenu-page-background",
                edit_policy=EditPolicy.STYLE,
                semantic_path=("page", "background"),
                display_name="Page background",
                presentation_order=0,
                style_role="page_background",
            ),
        )
    axes_patch = getattr(ax, "patch", None)
    if axes_patch is not None and axes_patch.get_visible():
        assign(
            (axes_patch,),
            SemanticArtistIdentity(
                name="sky_background",
                svg_id="wenu-sky-background",
                edit_policy=EditPolicy.STYLE,
                semantic_path=("sky", "background"),
                display_name="Sky background",
                presentation_order=0,
                style_role="sky_background",
            ),
        )
    spines = tuple(
        spine
        for spine in getattr(ax, "spines", {}).values()
        if spine.get_visible()
    )
    if spines:
        assign(
            spines,
            SemanticArtistIdentity(
                name="rectangular_viewport_frame",
                svg_id="wenu-chart-rectangular-viewport-frame",
                edit_policy=EditPolicy.STYLE,
                semantic_path=(
                    "chart",
                    "masks_and_boundary",
                    "rectangular_viewport_frame",
                ),
                display_name="Rectangular viewport frame",
                presentation_order=81,
                style_role="chart_boundary",
            ),
        )


def assign_furniture_semantics(renderer, rendering):
    """Attach identities to title and composed legend containers."""
    assign = getattr(renderer, "assign_semantic_identity", None)
    if not callable(assign):
        return
    title = getattr(getattr(renderer, "ax", None), "title", None)
    if title is not None and getattr(title, "get_text", lambda: "")():
        assign(
            (title,),
            SemanticArtistIdentity(
                name="title",
                svg_id="wenu-furniture-title",
                edit_policy=EditPolicy.LAYOUT,
                semantic_path=("furniture", "title"),
                display_name="Title",
                presentation_order=90,
                style_role="title",
            ),
        )
    legends = getattr(rendering, "legends", None)
    if legends is None:
        return
    while getattr(legends, "legends", None) is not None:
        legends = legends.legends
    objects = getattr(legends, "objects", None)
    if objects is not None:
        assign(
            (objects,),
            SemanticArtistIdentity(
                name="chart_information_and_object_key",
                svg_id="wenu-furniture-chart-information-object-key",
                edit_policy=EditPolicy.LAYOUT,
                semantic_path=(
                    "furniture",
                    "legends",
                    "chart_information_and_object_key",
                ),
                display_name="Chart information and object key",
                presentation_order=91,
                style_role="chart_legend",
            ),
        )
    stars = getattr(getattr(legends, "stars", None), "artist", None)
    if stars is not None:
        assign(
            (stars,),
            SemanticArtistIdentity(
                name="stellar_magnitude_scale",
                svg_id="wenu-furniture-stellar-magnitude-scale",
                edit_policy=EditPolicy.LAYOUT,
                semantic_path=(
                    "furniture",
                    "legends",
                    "stellar_magnitude_scale",
                ),
                display_name="Stellar magnitude scale",
                presentation_order=92,
                style_role="stellar_magnitude_legend",
            ),
        )


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
