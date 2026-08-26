"""Renderer-neutral semantic identity for chart layers."""

from __future__ import annotations

from dataclasses import dataclass
import re


_SAFE_NAME = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True)
class SemanticLayerIdentity:
    """Stable public identity carried from a sky layer to an export."""

    name: str
    svg_id: str


def semantic_layer_identity(layer) -> SemanticLayerIdentity | None:
    """Resolve stable identity without using labels or drawing order."""
    name = getattr(layer, "layer_name", None)
    if name == "coordinates_grid":
        coordinate_system = getattr(layer, "coordinate_system", None)
        if coordinate_system:
            name = f"{coordinate_system}_grid"
    if name is None:
        return None
    if not isinstance(name, str) or not name:
        raise ValueError("layer_name must be a non-empty string or None.")
    if _SAFE_NAME.fullmatch(name) is None:
        raise ValueError(
            f"Layer name {name!r} is not a safe semantic name."
        )
    return SemanticLayerIdentity(
        name=name,
        svg_id=f"wenu-layer-{name.replace('_', '-')}",
    )
