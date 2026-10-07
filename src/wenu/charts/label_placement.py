"""Reusable discrete placement rules for constellation labels."""

from __future__ import annotations

from typing import Mapping

import numpy as np

from wenu.rendering.label_placement import rotation_with_down_toward


def apply_object_label_orientation(options, *, sky, style=None, polar=False):
    """Apply chart-specific point/area typography without touching tracks or grids.

    A polar disk has one unambiguous projected pole at the origin. Other
    families keep text upright, even when a celestial pole is in the viewport.
    Both ordinary mappings and deferred render factories remain render-local.
    """
    policy = getattr(style, "labels_orientation", "chart")
    if policy not in {"chart", "upright", "up-away-from-cp"}:
        raise ValueError("unsupported labels_orientation")
    if policy == "up-away-from-cp" and not polar:
        raise ValueError("up-away-from-cp labels require a polar-planisphere chart")

    def rotation(x, y):
        return rotation_with_down_toward(
            np.degrees(np.arctan2(y, x)) + 90.0, (x, y), (0.0, 0.0),
        )

    resolved_rotation = rotation if polar and policy != "upright" else 0.0

    def orient(render):
        render = dict(render)
        render["label_style"] = {
            **dict(render.get("label_style", {})),
            "rotation": resolved_rotation,
            "rotation_mode": "anchor",
        }
        return render

    result = dict(options)
    layers = [getattr(sky, name, None) for name in (
        "stars", "constellation_labels", "nonstellar", "galaxies",
        "open_clusters", "globular_clusters", "planetary_nebulae",
        "supernova_remnants", "venus", "moon",
    )]
    layers.extend(getattr(sky, "solar_system_bodies", {}).values())
    layers.extend(layer for layer in getattr(sky, "layers", ())
                  if getattr(layer, "display_kind", None) == "symbolic_point")
    for layer in dict.fromkeys(layers):
        if layer is None or layer not in result:
            continue
        configured = dict(result[layer])
        render = configured.get("render", {})
        if callable(render):
            def oriented(spherical, projected, factory=render):
                return orient(factory(spherical, projected))
            configured["render"] = oriented
        else:
            configured["render"] = orient(render)
        result[layer] = configured
    return result


LABEL_POSITION_VECTORS = {
    "ul": (-1.0, 1.0),
    "u": (0.0, 1.0),
    "ur": (1.0, 1.0),
    "cl": (-1.0, 0.0),
    "c": (0.0, 0.0),
    "cr": (1.0, 0.0),
    "ll": (-1.0, -1.0),
    "lc": (0.0, -1.0),
    "lr": (1.0, -1.0),
}


def _pair(value, *, name):
    try:
        x, y = value
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must contain exactly two values.") from error
    return float(x), float(y)


def resolve_constellation_label_offsets(
    positions: Mapping[str, str] | None,
    offsets: Mapping[str, tuple[float, float]] | None = None,
    *,
    clearance=(0.24, 0.20),
    default_position="c",
):
    """Resolve discrete positions plus additive manual corrections."""
    positions = {
        str(name): str(position).strip().lower()
        for name, position in dict(positions or {}).items()
    }
    offsets = {
        str(name): _pair(value, name=f"offset for {name}")
        for name, value in dict(offsets or {}).items()
    }
    default_position = str(default_position).strip().lower()
    invalid = {
        value
        for value in (*positions.values(), default_position)
        if value not in LABEL_POSITION_VECTORS
    }
    if invalid:
        accepted = ", ".join(LABEL_POSITION_VECTORS)
        rejected = ", ".join(sorted(invalid))
        raise ValueError(
            f"Unknown label position(s): {rejected}. "
            f"Accepted positions are: {accepted}."
        )

    clearance_x, clearance_y = _pair(
        clearance,
        name="label clearance",
    )

    def displacement(code):
        direction_x, direction_y = LABEL_POSITION_VECTORS[code]
        return (
            direction_x * clearance_x,
            direction_y * clearance_y,
        )

    default_manual = offsets.get("__default__", (0.0, 0.0))
    default_x, default_y = displacement(
        positions.get("__default__", default_position)
    )
    resolved = {
        "__default__": (
            default_x + default_manual[0],
            default_y + default_manual[1],
        )
    }
    names = set(positions).union(offsets).difference({"__default__"})
    for name in sorted(names):
        position_x, position_y = displacement(
            positions.get(name, default_position)
        )
        manual_x, manual_y = offsets.get(name, (0.0, 0.0))
        resolved[name] = (
            position_x + manual_x,
            position_y + manual_y,
        )
    return resolved
