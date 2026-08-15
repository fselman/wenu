"""Parity contracts for TOML-to-style/mode translation."""

from dataclasses import FrozenInstanceError, replace

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
from wenu.charts.polar_planisphere_style import (
    PolarPlanisphereStylePalette,
)
from wenu.charts.regional import RegionalChart
from wenu import compose_chart
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
    assert defaults.polar_planisphere_palette == (
        PolarPlanisphereStylePalette()
    )

    with pytest.raises(FrozenInstanceError):
        defaults.atlas.canvas.sky_color = "red"


def test_packaged_cartoon_mask_is_strong_but_retains_outside_context():
    defaults = translate_style_mode_defaults()
    assert defaults.cartoon.mask.color == "#fffdf5"
    assert defaults.cartoon.mask.alpha == pytest.approx(0.45)
    assert 0.0 < defaults.cartoon.mask.alpha < 1.0
    assert defaults.atlas.mask == AtlasChartStyle().mask


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


def test_named_composition_defaults_are_the_cached_packaged_authority():
    from wenu.configuration import packaged_style_mode_defaults

    defaults = packaged_style_mode_defaults()
    atlas_name, atlas = _resolve_style("atlas")
    cartoon_name, cartoon = _resolve_style("cartoon")
    print_name, print_mode = _resolve_mode(None)
    presentation_name, presentation = _resolve_mode("presentation")

    assert atlas_name == "atlas" and atlas is defaults.atlas
    assert cartoon_name == "cartoon" and cartoon is defaults.cartoon
    assert print_name == "print" and print_mode is defaults.print_mode
    assert presentation_name == "presentation"
    assert presentation is defaults.presentation_mode


def test_packaged_style_mode_authority_is_cached_and_clearable():
    from wenu.configuration import packaged_style_mode_defaults

    packaged_style_mode_defaults.cache_clear()
    first = packaged_style_mode_defaults()
    second = packaged_style_mode_defaults()
    assert first is second


def test_named_composition_consumes_translated_mode_and_cartoon_values(
    monkeypatch,
):
    from wenu.configuration import packaged_style_mode_defaults

    defaults = packaged_style_mode_defaults()
    configured = replace(
        defaults,
        print_mode=replace(defaults.print_mode, dpi=257),
        cartoon_print_palette=replace(
            defaults.cartoon_print_palette,
            sky="#123456",
        ),
        atlas_presentation_palette=replace(
            defaults.atlas_presentation_palette,
            sky="#654321",
        ),
        cartoon_label_offset=(0.31, 0.27),
        cartoon_label_halo_opacity=0.44,
    )
    monkeypatch.setattr(
        "wenu.charts.composition._style_mode_defaults",
        lambda: configured,
    )
    chart = RegionalChart(
        center_alt_deg=45.0,
        center_az_deg=180.0,
        field_width_deg=30.0,
        field_height_deg=20.0,
    )
    composition = compose_chart(chart, style="cartoon", mode="print")

    assert composition.mode.dpi == 257
    assert composition.style.canvas.sky_color == "#123456"
    assert composition.style.constellation_label_offset == (0.31, 0.27)
    assert composition.style.grids.constellation_label_offset == (0.31, 0.27)
    assert composition.style.constellation_label_halo_alpha == 0.44

    atlas = compose_chart(chart, style="atlas", mode="presentation")
    assert atlas.style.canvas.sky_color == "#654321"


def test_unmigrated_independent_grid_width_reports_complete_path():
    values = load_packaged_defaults()
    values["styles"]["atlas"]["ecliptic_grid"]["line_width"] = 0.7
    with pytest.raises(ConfigurationError) as error:
        translate_style_mode_defaults(values)
    assert "styles.atlas.coordinate_grids.line_width" in str(error.value)
