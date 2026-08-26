"""Deterministic semantic annotations for Matplotlib SVG output."""

from __future__ import annotations

from html import escape
from pathlib import Path
import re


_METADATA_ATTRIBUTE = "_wenu_svg_semantics"


def attach_semantic_svg_metadata(
    artist, *, layer, zorder, paint_role, edit_policy
):
    """Attach renderer-neutral values for the later SVG export boundary."""
    metadata = {
        "layer": str(layer),
        "zorder": float(zorder),
        "edit_policy": edit_policy.value,
    }
    if paint_role is not None:
        metadata["paint_role"] = paint_role.name
        metadata["paint_band"] = paint_role.band.name
    setattr(artist, _METADATA_ATTRIBUTE, metadata)


def annotate_semantic_svg(path, figure):
    """Add Wenu classes and data attributes without moving SVG elements."""
    path = Path(path)
    records = []
    find_objects = getattr(figure, "findobj", None)
    if callable(find_objects):
        for artist in find_objects():
            svg_id = getattr(artist, "get_gid", lambda: None)()
            metadata = getattr(artist, _METADATA_ATTRIBUTE, None)
            if svg_id and metadata:
                records.append((str(svg_id), dict(metadata)))
    if not records:
        return path

    serialized = path.read_text(encoding="utf-8")
    for svg_id, metadata in records:
        classes = [
            "wenu-semantic-artist",
            f"wenu-layer-{metadata['layer'].replace('_', '-')}",
            f"wenu-edit-{metadata['edit_policy']}",
        ]
        attributes = {
            "class": " ".join(classes),
            "data-wenu-layer": metadata["layer"],
            "data-wenu-zorder": f"{metadata['zorder']:.12g}",
            "data-wenu-edit": metadata["edit_policy"],
        }
        paint_role = metadata.get("paint_role")
        paint_band = metadata.get("paint_band")
        if paint_role is not None:
            classes.append(f"wenu-paint-{paint_role.replace('_', '-')}")
            attributes["class"] = " ".join(classes)
            attributes["data-wenu-paint-role"] = paint_role
        if paint_band is not None:
            classes.append(f"wenu-band-{paint_band.replace('_', '-')}")
            attributes["class"] = " ".join(classes)
            attributes["data-wenu-paint-band"] = paint_band
        extra = "".join(
            f' {name}="{escape(str(value), quote=True)}"'
            for name, value in attributes.items()
        )
        pattern = re.compile(
            rf'(<g\s+id="{re.escape(svg_id)}")(?P<rest>[^>]*>)'
        )
        serialized, count = pattern.subn(
            rf"\1{extra}\g<rest>",
            serialized,
            count=1,
        )
        if count != 1:
            raise ValueError(
                f"Expected exactly one SVG group for Wenu id {svg_id!r}."
            )
    path.write_text(serialized, encoding="utf-8")
    return path
