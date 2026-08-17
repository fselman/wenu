"""Packaged binocular content for paired physical polar planispheres."""

from __future__ import annotations

from importlib.resources import files
import json
from dataclasses import dataclass

from .detail import SkyContentSelection


_SELECTION_FIELDS = (
    "nonstellar_objects",
    "galaxies",
    "open_clusters",
    "globular_clusters",
    "planetary_nebulae",
)


@dataclass(frozen=True)
class PolarBinocularTargets:
    """Curated identifiers and their compact printed labels."""

    content_selection: SkyContentSelection
    label_overrides: tuple[tuple[str, str, str | None], ...]


def polar_binocular_targets() -> PolarBinocularTargets:
    """Load reviewed catalogue identifiers and display-label policy."""
    resource = files("wenu.data") / "polar_binocular_targets.json"
    values = json.loads(resource.read_text(encoding="utf-8"))
    configured = values.get("content_selection")
    if not isinstance(configured, dict):
        raise ValueError(
            "polar_binocular_targets.json requires content_selection."
        )
    unknown = set(configured).difference(_SELECTION_FIELDS)
    if unknown:
        raise ValueError(
            "Unknown polar binocular content families: "
            + ", ".join(sorted(unknown))
        )
    missing = set(_SELECTION_FIELDS).difference(configured)
    if missing:
        raise ValueError(
            "Missing polar binocular content families: "
            + ", ".join(sorted(missing))
        )
    selection = SkyContentSelection(
        **{
            name: frozenset(configured[name])
            for name in _SELECTION_FIELDS
        }
    )
    labels = values.get("labels")
    if not isinstance(labels, dict):
        raise ValueError("polar_binocular_targets.json requires labels.")
    if set(labels) != set(_SELECTION_FIELDS):
        raise ValueError(
            "Polar binocular label families must match content selection."
        )
    overrides = []
    for family in _SELECTION_FIELDS:
        configured_labels = labels[family]
        if not isinstance(configured_labels, dict):
            raise ValueError(f"{family} labels must be an object.")
        unknown_labels = set(configured_labels).difference(
            configured[family]
        )
        if unknown_labels:
            raise ValueError(
                f"{family} labels contain unselected identifiers: "
                + ", ".join(sorted(unknown_labels))
            )
        overrides.extend(
            (family, identifier, label)
            for identifier, label in configured_labels.items()
        )
    aliases = values.get("label_aliases", {})
    if not isinstance(aliases, dict):
        raise ValueError("polar binocular label_aliases must be an object.")
    unknown_alias_families = set(aliases).difference(_SELECTION_FIELDS)
    if unknown_alias_families:
        raise ValueError(
            "Unknown polar binocular label alias families: "
            + ", ".join(sorted(unknown_alias_families))
        )
    for family, configured_aliases in aliases.items():
        if not isinstance(configured_aliases, dict):
            raise ValueError(f"{family} label_aliases must be an object.")
        overrides.extend(
            (family, source_label, label)
            for source_label, label in configured_aliases.items()
        )
    return PolarBinocularTargets(selection, tuple(overrides))


def polar_binocular_content_selection() -> SkyContentSelection:
    """Return the selected identifiers for compatibility and inspection."""
    return polar_binocular_targets().content_selection
