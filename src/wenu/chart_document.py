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
    exact_svg_id: bool = True

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
                svg_id="page-background",
                edit_policy=EditPolicy.STYLE,
                semantic_path=("page", "background"),
                display_name="Page background",
                presentation_order=0,
                style_role="page_background",
            ),
        )
    boundary_background = getattr(
        renderer, "_boundary_background_patch", None
    )
    axes_patch = getattr(ax, "patch", None)
    sky_background = (
        boundary_background
        if boundary_background is not None
        else axes_patch
    )
    if (
        sky_background is not None
        and sky_background.get_visible()
    ):
        assign(
            (sky_background,),
            SemanticArtistIdentity(
                name="sky_background",
                svg_id="sky-background",
                edit_policy=EditPolicy.STYLE,
                semantic_path=("sky", "background"),
                display_name="Sky background",
                presentation_order=0,
                style_role="sky_background",
            ),
        )
    chart_boundary = getattr(renderer, "_clip_patch", None)
    if chart_boundary is not None and chart_boundary.get_visible():
        assign(
            (chart_boundary,),
            SemanticArtistIdentity(
                name="chart_boundary",
                svg_id="chart-boundary",
                edit_policy=EditPolicy.STYLE,
                semantic_path=(
                    "chart",
                    "masks_and_boundary",
                    "chart_boundary",
                ),
                display_name="Chart boundary",
                presentation_order=81,
                style_role="chart_boundary",
            ),
        )
    spines = tuple(
        spine
        for spine in getattr(ax, "spines", {}).values()
        if spine.get_visible()
    )
    if spines and chart_boundary is None:
        assign(
            spines,
            SemanticArtistIdentity(
                name="chart_boundary",
                svg_id="chart-boundary",
                edit_policy=EditPolicy.STYLE,
                semantic_path=(
                    "chart",
                    "masks_and_boundary",
                    "chart_boundary",
                ),
                display_name="Chart boundary",
                presentation_order=81,
                style_role="chart_boundary",
            ),
        )


def _semantic_token(value):
    """Return a concise safe token for one legend entry."""
    import re

    text = str(value).strip()
    if text.startswith("RA "):
        return "coordinates-ra"
    if text.startswith("Dec "):
        return "coordinates-dec"
    if "J2000" in text or text.startswith(("FK", "ICRS")):
        return "coordinates-frame"
    magnitude = re.match(r"^([+-]?\d+)(?:\s|$)", text)
    if magnitude is not None:
        return (
            magnitude.group(1)
            .replace("+", "plus-")
            .replace("-", "minus-")
        )
    token = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return token or "entry"


def _name_legend_contents(legend, prefix, *, entry_prefix=""):
    """Pair legend symbols and descriptions with meaningful SVG IDs."""
    frame = getattr(legend, "get_frame", lambda: None)()
    if frame is not None:
        frame.set_gid(f"{prefix}-frame")
    title = getattr(legend, "get_title", lambda: None)()
    if title is not None and getattr(title, "get_text", lambda: "")():
        title.set_gid(f"{prefix}-title")
    handles = tuple(getattr(legend, "legend_handles", ()))
    texts = tuple(getattr(legend, "get_texts", lambda: ())())
    declared = tuple(
        getattr(legend, "_wenu_legend_entry_keys", ())
    )
    if declared and len(declared) != len(handles):
        raise ValueError(
            "Legend semantic keys must match rendered handles."
        )
    if len(handles) != len(texts):
        raise ValueError(
            "Legend handles and descriptions must remain paired."
        )
    bases = (
        tuple(_semantic_token(key) for key in declared)
        if declared
        else tuple(_semantic_token(label.get_text()) for label in texts)
    )
    used = {}
    for handle, label, base in zip(handles, texts, bases):
        count = used.get(base, 0) + 1
        used[base] = count
        token = base if count == 1 else f"{base}-{count}"
        entry = (
            token
            if declared or not entry_prefix
            else f"{entry_prefix}-{token}"
        )
        handle.set_gid(f"{entry}-symbol")
        label.set_gid(f"{entry}-label")


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
                svg_id="title",
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
        _name_legend_contents(objects, "object-key")
        assign(
            (objects,),
            SemanticArtistIdentity(
                name="chart_information_and_object_key",
                svg_id="object-key",
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
        _name_legend_contents(
            stars,
            "magnitude-scale",
            entry_prefix="mag",
        )
        assign(
            (stars,),
            SemanticArtistIdentity(
                name="stellar_magnitude_scale",
                svg_id="magnitude-scale",
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
