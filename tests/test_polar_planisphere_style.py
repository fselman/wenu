from dataclasses import FrozenInstanceError, replace

import pytest

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


def test_packaged_physical_palette_has_clean_white_and_provisional_blue():
    palette = translate_style_mode_defaults().polar_planisphere_palette

    assert palette == PolarPlanisphereStylePalette()
    assert palette.paper_color == "#FFFFFF"
    assert palette.star_color == "#005B8F"
    assert palette.reference_color == "#66899B"
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
    assert style.stars.color == "#005B8F"
    assert style.stars.area_scale == pytest.approx(0.55)
    assert style.stars.draw_variable_symbols is False
    assert style.stars.draw_multiple_symbols is False
    assert style.legend.visible is False
    assert style.grids.constellation_linewidth == pytest.approx(0.35)
    assert style.grids.constellation_label_color == "#365F78"
    assert style.grids.equatorial_color == "#66899B"
    assert style.grids.ecliptic_color == "#66899B"
    assert style.grids.galactic_color == "#66899B"
    assert style.grids.coordinate_label_color == "#66899B"
    assert style.grids.coordinate_label_fontsize == pytest.approx(5.25)
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


def test_milky_way_is_filled_without_edge_or_contour_outlines():
    chart = PolarPlanispherePairRequest().resolve().north
    style = compose_chart(chart, style="atlas", mode="print").style
    isophotes = style.isophotes
    publication = style.as_publication_style()

    assert isophotes.milky_way_alpha == pytest.approx(0.32)
    assert isophotes.milky_way_edge_color is None
    assert isophotes.milky_way_edge_alpha == pytest.approx(0.0)
    assert isophotes.milky_way_linewidth == pytest.approx(0.0)
    assert isophotes.milky_way_contour_color is None
    assert isophotes.milky_way_contour_linewidth == pytest.approx(0.0)
    assert isophotes.milky_way_contour_alpha == pytest.approx(0.0)
    assert publication.milky_way_color == "#C9DFE8"
    assert publication.milky_way_contour_color is None


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
    assert style.stars.color != "#005B8F"


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
