"""Reusable discrete placement rules for constellation labels."""

from __future__ import annotations

from typing import Mapping


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
