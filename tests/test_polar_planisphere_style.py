from dataclasses import FrozenInstanceError, replace

import pytest
import numpy as np

from wenu import (
    AtlasChartStyle,
    PolarPlanispherePairRequest,
    PolarPlanisphereStylePalette,
    compose_chart,
    polar_planisphere_chart_style,
)
from wenu.configuration import (
    load_packaged_defaults,
    translate_style_mode_defaults,
)
from wenu.charts.detail_application import configured_stellar_symbol_sizes
from wenu.rendering.preparation import configured_magnitude_sizes


def test_packaged_physical_palette_has_clean_white_and_provisional_blue():
    palette = translate_style_mode_defaults().polar_planisphere_palette

    assert palette == PolarPlanisphereStylePalette()
    assert palette.paper_color == "#FFFFFF"
    assert palette.star_color == "#003F66"
    assert palette.reference_color == "#456B7D"
    assert palette.star_minimum_area == pytest.approx(1.25)
    assert palette.star_magnitude_scale == pytest.approx(2.2727272727272725)
    assert palette.star_magnitude_exponent == pytest.approx(0.30488598388546717)
    assert palette.bright_star_magnitude_limit == pytest.approx(0.5)
    assert palette.bright_star_magnitude_scale == pytest.approx(1.0 / 1.62)
    assert palette.bright_star_magnitude_offset == pytest.approx(-1.0 / 9.0)
    assert palette.bright_star_symbol_area_scale == pytest.approx(
        0.70**2 / 0.38**2
    )
    assert palette.ordinary_star_magnitude_scale == pytest.approx(4.0 / 5.32)
    assert palette.ordinary_star_magnitude_offset == pytest.approx(
        -0.18 * 4.0 / 5.32
    )
    assert palette.constellation_linewidth == pytest.approx(0.675)
    assert palette.reference_linewidth == pytest.approx(0.75)
    assert palette.reference_opacity == pytest.approx(0.65)
    assert palette.reference_label_fontsize == pytest.approx(5.25)
    assert palette.deep_sky_label_fontsize == pytest.approx(4.5)
    assert palette.deep_sky_outline_minimum_size_arcmin == pytest.approx(
        40.0
    )
    assert palette.globular_cluster_minimum_size_arcmin == pytest.approx(
        80.0
    )
    assert palette.star_area_scale < AtlasChartStyle().stars.area_scale


def test_polar_print_composition_uses_dedicated_physical_style():
    chart = PolarPlanispherePairRequest().resolve().south

    composition = compose_chart(chart, style="atlas", mode="print")
    style = composition.style

    assert style.canvas.sky_color == "#FFFFFF"
    assert style.stars.color == "#003F66"
    assert style.stars.area_scale == pytest.approx(0.55)
    assert (
        style.stars.magnitude_sizing.minimum_area * style.stars.area_scale
        == pytest.approx(1.25)
    )
    assert style.stars.draw_variable_symbols is False
    assert style.stars.draw_multiple_symbols is False
    assert style.stars.draw_bright_symbols is True
    assert style.stars.bright_magnitude_limit == pytest.approx(0.5)
    assert style.stars.bright_magnitude_scale == pytest.approx(1.0 / 1.62)
    assert style.stars.bright_magnitude_offset == pytest.approx(-1.0 / 9.0)
    assert style.stars.bright_symbol_area_scale == pytest.approx(
        0.70**2 / 0.38**2
    )
    assert style.stars.ordinary_magnitude_scale == pytest.approx(4.0 / 5.32)
    assert style.legend.visible is False
    assert style.grids.constellation_linewidth == pytest.approx(0.675)
    assert style.grids.constellation_label_color == "#23495D"
    assert style.grids.equatorial_color == "#456B7D"
    assert style.grids.ecliptic_color == "#456B7D"
    assert style.grids.galactic_color == "#456B7D"
    assert style.grids.coordinate_label_color == "#456B7D"
    assert style.grids.coordinate_label_fontsize == pytest.approx(5.25)
    assert style.grids.coordinate_linewidth == pytest.approx(0.75)
    assert style.grids.coordinate_alpha == pytest.approx(0.65)
    assert style.canvas.label_fontsize == pytest.approx(7.5)
    deep_sky = style.deep_sky
    assert deep_sky.galaxy_draw_labels is True
    assert deep_sky.open_cluster_draw_labels is True
    assert deep_sky.globular_cluster_draw_labels is True
    assert deep_sky.planetary_nebula_draw_labels is True
    assert deep_sky.nonstellar_draw_labels is True
    assert deep_sky.galaxy_label_fontsize == pytest.approx(4.5)
    assert deep_sky.open_cluster_label_fontsize == pytest.approx(4.5)
    assert deep_sky.globular_cluster_label_fontsize == pytest.approx(4.5)
    assert deep_sky.planetary_nebula_label_fontsize == pytest.approx(4.5)
    assert deep_sky.nonstellar_label_fontsize == pytest.approx(4.5)
    assert deep_sky.nonstellar_minimum_size_arcmin == pytest.approx(40.0)
    assert deep_sky.galaxy_minimum_size_arcmin == pytest.approx(40.0)
    assert deep_sky.globular_cluster_minimum_size_arcmin == pytest.approx(
        80.0
    )
    assert style.calendar.day_label_fontsize == pytest.approx(6.45)
    assert style.calendar.day_label_fontweight == "semibold"
    assert style.calendar.month_label_fontsize == pytest.approx(11.5)
    assert style.calendar.month_label_fontweight == "semibold"


def test_milky_way_is_filled_without_edge_or_contour_outlines():
    chart = PolarPlanispherePairRequest().resolve().north
    style = compose_chart(chart, style="atlas", mode="print").style
    isophotes = style.isophotes
    publication = style.as_publication_style()

    assert isophotes.milky_way_alpha == pytest.approx(0.45)
    assert isophotes.lmc_alpha == pytest.approx(0.32)
    assert isophotes.smc_alpha == pytest.approx(0.28)
    assert isophotes.milky_way_edge_color is None
    assert isophotes.milky_way_edge_alpha == pytest.approx(0.0)
    assert isophotes.milky_way_linewidth == pytest.approx(0.0)
    assert isophotes.milky_way_contour_color is None
    assert isophotes.milky_way_contour_linewidth == pytest.approx(0.0)
    assert isophotes.milky_way_contour_alpha == pytest.approx(0.0)
    assert publication.milky_way_color == "#A8C8D6"
    assert isophotes.lmc_color == "#A8C8D6"
    assert isophotes.smc_color == "#A8C8D6"
    assert publication.milky_way_contour_color is None


def test_print_star_curve_promotes_intermediate_magnitudes_only():
    style = compose_chart(
        PolarPlanispherePairRequest().resolve().south,
        style="atlas",
        mode="print",
    ).style
    sizing = style.stars.magnitude_sizing
    magnitudes = np.asarray((0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 5.5))
    areas = np.maximum(
        sizing.minimum_area,
        sizing.scale
        * 10.0 ** (-sizing.exponent * (magnitudes - sizing.reference_magnitude)),
    ) * style.stars.area_scale
    old = np.maximum(
        1.25,
        0.55 * 1.5 * 10.0 ** (-0.35 * (magnitudes - sizing.reference_magnitude)),
    )

    assert areas[1] == pytest.approx(old[1])
    assert np.all(areas[2:5] > old[2:5])
    assert areas[0] <= old[0]
    assert areas[5] == pytest.approx(1.25)
    assert areas[6] == pytest.approx(1.25)


def test_polar_star_ranges_remap_to_the_requested_existing_areas():
    style = compose_chart(
        PolarPlanispherePairRequest().resolve().south,
        style="atlas",
        mode="print",
    ).style
    current = lambda magnitudes: configured_magnitude_sizes(
        np.asarray(magnitudes, dtype=float),
        style.stars.magnitude_sizing,
    ) * style.stars.area_scale

    ordinary_magnitudes = np.asarray((0.500001, 2.84, 5.5))
    ordinary, _, ordinary_mask = configured_stellar_symbol_sizes(
        ordinary_magnitudes,
        style.stars,
    )
    bright_magnitudes = np.asarray((-1.44, -0.63, 0.5))
    hidden_circles, bright, bright_mask = configured_stellar_symbol_sizes(
        bright_magnitudes,
        style.stars,
    )

    ordinary_reference = (
        ordinary_magnitudes * style.stars.ordinary_magnitude_scale
        + style.stars.ordinary_magnitude_offset
    )
    assert ordinary == pytest.approx(current(ordinary_reference))
    assert not np.any(ordinary_mask)
    assert hidden_circles == pytest.approx(np.zeros(3))
    assert np.all(bright_mask)
    bright_reference = (
        bright_magnitudes * style.stars.bright_magnitude_scale
        + style.stars.bright_magnitude_offset
    )
    assert bright == pytest.approx(
        current(bright_reference) * 0.70**2 / 0.38**2
    )


def test_bright_cut_selects_rigel_and_every_brighter_hipparcos_star():
    from wenu.objects.stars import Stars

    catalogue = Stars(None).load()
    selected = catalogue[
        catalogue["magnitude"]
        <= PolarPlanisphereStylePalette().bright_star_magnitude_limit
    ]

    assert tuple(selected.index) == (
        7588, 24436, 24608, 27989, 30438, 32349, 37279, 69673,
        71683, 91262,
    )
    assert catalogue.loc[24436, "magnitude"] == pytest.approx(0.18)
    assert catalogue.loc[37279, "magnitude"] == pytest.approx(0.40)


def test_physical_style_does_not_change_other_atlas_print_families():
    from wenu import RegionalChart

    regional = RegionalChart(
        center_alt_deg=45.0,
        center_az_deg=180.0,
        field_width_deg=30.0,
        field_height_deg=20.0,
    )

    style = compose_chart(regional, style="atlas", mode="print").style

    assert style == translate_style_mode_defaults().atlas
    assert style.stars.color == "#151515"
    assert style.isophotes.milky_way_contour_color == "#555555"


def test_presentation_remains_the_existing_screen_atlas_mode():
    chart = PolarPlanispherePairRequest().resolve().south

    style = compose_chart(chart, style="atlas", mode="presentation").style

    assert style.canvas.sky_color != "#FFFFFF"
    assert style.stars.color != "#003F66"


def test_configured_palette_flows_through_normal_composition(monkeypatch):
    from wenu.configuration import packaged_style_mode_defaults

    defaults = packaged_style_mode_defaults()
    configured = replace(
        defaults,
        polar_planisphere_palette=replace(
            defaults.polar_planisphere_palette,
            star_color="#123456",
            milky_way_opacity=0.21,
        ),
    )
    monkeypatch.setattr(
        "wenu.charts.composition._style_mode_defaults",
        lambda: configured,
    )
    chart = PolarPlanispherePairRequest().resolve().south

    style = compose_chart(chart, style="atlas", mode="print").style

    assert style.stars.color == "#123456"
    assert style.isophotes.milky_way_alpha == pytest.approx(0.21)


def test_configuration_translation_carries_palette_values():
    values = load_packaged_defaults()
    values["styles"]["polar_planisphere"]["star_color"] = "#123456"
    values["styles"]["polar_planisphere"]["reference_color"] = "#654321"
    values["styles"]["polar_planisphere"][
        "reference_label_font_size"
    ] = 6.0
    values["styles"]["polar_planisphere"][
        "deep_sky_label_font_size"
    ] = 4.25
    values["styles"]["polar_planisphere"][
        "deep_sky_outline_minimum_size_arcmin"
    ] = 36.0
    values["styles"]["polar_planisphere"][
        "globular_cluster_minimum_size_arcmin"
    ] = 72.0

    defaults = translate_style_mode_defaults(values)

    assert defaults.polar_planisphere_palette.star_color == "#123456"
    assert defaults.polar_planisphere_palette.reference_color == "#654321"
    assert defaults.polar_planisphere_palette.reference_label_fontsize == 6.0
    assert defaults.polar_planisphere_palette.deep_sky_label_fontsize == 4.25
    assert (
        defaults.polar_planisphere_palette.
        deep_sky_outline_minimum_size_arcmin
        == 36.0
    )
    assert (
        defaults.polar_planisphere_palette.
        globular_cluster_minimum_size_arcmin
        == 72.0
    )


def test_palette_and_style_adapter_are_immutable_and_validated():
    palette = PolarPlanisphereStylePalette()

    with pytest.raises(FrozenInstanceError):
        palette.star_color = "red"
    with pytest.raises(ValueError, match="star_area_scale"):
        PolarPlanisphereStylePalette(star_area_scale=0.0)
    with pytest.raises(ValueError, match="milky_way_opacity"):
        PolarPlanisphereStylePalette(milky_way_opacity=1.1)
    with pytest.raises(ValueError, match="reference_label_fontsize"):
        PolarPlanisphereStylePalette(reference_label_fontsize=0.0)
    with pytest.raises(TypeError, match="base"):
        polar_planisphere_chart_style(object(), palette)
    with pytest.raises(TypeError, match="palette"):
        polar_planisphere_chart_style(AtlasChartStyle(), object())


def test_physical_style_api_is_public():
    import wenu

    assert "PolarPlanisphereStylePalette" in wenu.__all__
    assert "polar_planisphere_chart_style" in wenu.__all__
