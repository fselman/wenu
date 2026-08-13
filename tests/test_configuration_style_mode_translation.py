"""Parity contracts for TOML-to-style/mode translation."""

from dataclasses import FrozenInstanceError

import pytest

from wenu.charts.atlas_modes import ATLAS_PRESENTATION_PALETTE
from wenu.charts.cartoon_modes import (
    CARTOON_PRESENTATION_PALETTE,
    CARTOON_PRINT_PALETTE,
    CartoonModeChartStyle,
)
from wenu.charts.composition import _resolve_mode, _resolve_style
from wenu.charts.modes import PresentationMode, PrintMode
from wenu.charts.presets import AtlasChartStyle, CartoonChartStyle
from wenu.configuration import (
    ConfigurationError,
    load_packaged_defaults,
    translate_style_mode_defaults,
)


def test_packaged_styles_translate_to_existing_immutable_contracts():
    defaults = translate_style_mode_defaults()
    assert defaults.atlas == AtlasChartStyle()
    assert defaults.cartoon == CartoonChartStyle()
    assert type(defaults.atlas) is AtlasChartStyle
    assert type(defaults.cartoon) is CartoonChartStyle

    with pytest.raises(FrozenInstanceError):
        defaults.atlas.canvas.sky_color = "red"


def test_packaged_modes_translate_to_existing_immutable_contracts():
    defaults = translate_style_mode_defaults()
    assert defaults.print_mode == PrintMode()
    assert defaults.presentation_mode == PresentationMode()
    assert type(defaults.print_mode) is PrintMode
    assert type(defaults.presentation_mode) is PresentationMode


def test_packaged_palettes_and_cartoon_transform_values_have_parity():
    defaults = translate_style_mode_defaults()
    assert defaults.atlas_presentation_palette == ATLAS_PRESENTATION_PALETTE
    assert defaults.cartoon_print_palette == CARTOON_PRINT_PALETTE
    assert (
        defaults.cartoon_presentation_palette
        == CARTOON_PRESENTATION_PALETTE
    )
    assert defaults.cartoon_label_offset == (0.18, 0.14)
    assert defaults.cartoon_label_clearance == (0.24, 0.20)
    assert defaults.cartoon_label_halo_opacity == 0.78
    assert CartoonModeChartStyle().constellation_label_offset == (
        defaults.cartoon_label_offset
    )
    assert CartoonModeChartStyle().constellation_label_halo_alpha == (
        defaults.cartoon_label_halo_opacity
    )


def test_existing_composition_defaults_are_not_rewired_yet():
    defaults = translate_style_mode_defaults()
    atlas_name, atlas = _resolve_style("atlas")
    cartoon_name, cartoon = _resolve_style("cartoon")
    print_name, print_mode = _resolve_mode(None)
    presentation_name, presentation = _resolve_mode("presentation")

    assert (atlas_name, atlas) == ("atlas", defaults.atlas)
    assert (cartoon_name, cartoon) == ("cartoon", defaults.cartoon)
    assert (print_name, print_mode) == ("print", defaults.print_mode)
    assert (presentation_name, presentation) == (
        "presentation",
        defaults.presentation_mode,
    )


def test_unmigrated_independent_grid_width_reports_complete_path():
    values = load_packaged_defaults()
    values["styles"]["atlas"]["ecliptic_grid"]["line_width"] = 0.7
    with pytest.raises(ConfigurationError) as error:
        translate_style_mode_defaults(values)
    assert "styles.atlas.coordinate_grids.line_width" in str(error.value)
