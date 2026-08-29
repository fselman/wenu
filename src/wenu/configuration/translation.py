"""Aggregate translation of one validated effective configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .furniture_product_export_translation import (
    FurnitureProductExportDefaults,
    translate_furniture_product_export_defaults,
)
from .geometry_detail_translation import (
    GeometryDetailDefaults,
    translate_geometry_detail_defaults,
)
from .sequence_translation import SequenceDefaults, translate_sequence_defaults
from .style_mode_translation import (
    StyleModeDefaults,
    translate_style_mode_defaults,
)
from .validation import load_configuration, validate_configuration


@dataclass(frozen=True)
class ConfigurationDefaults:
    """Existing immutable runtime contracts from one effective document."""

    style_mode: StyleModeDefaults
    geometry_detail: GeometryDetailDefaults
    furniture_product_export: FurnitureProductExportDefaults
    sequence: SequenceDefaults
    reference_policy: Any


def translate_configuration_defaults(
    configuration: Mapping[str, Any],
) -> ConfigurationDefaults:
    """Translate one complete configuration through all existing owners."""
    values = validate_configuration(configuration)
    from wenu.charts.reference_policy import CelestialReferencePolicy
    return ConfigurationDefaults(
        style_mode=translate_style_mode_defaults(values),
        geometry_detail=translate_geometry_detail_defaults(values),
        furniture_product_export=(
            translate_furniture_product_export_defaults(values)
        ),
        sequence=translate_sequence_defaults(values),
        reference_policy=CelestialReferencePolicy(
            values["coordinates"]["references"]["equinox"]
        ),
    )


def load_configuration_defaults(path=None) -> ConfigurationDefaults:
    """Load and translate packaged defaults plus an optional user overlay."""
    return translate_configuration_defaults(load_configuration(path))
