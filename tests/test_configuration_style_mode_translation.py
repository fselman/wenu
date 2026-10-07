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


@pytest.mark.parametrize("policy", ["chart", "upright", "up-away-from-cp"])
def test_label_orientation_overlay_and_explicit_override(tmp_path, policy):
    from wenu.configuration import load_configuration_defaults
    from wenu.charts.style_overrides import ChartStyleOverrides

    path = tmp_path / "labels.toml"
    path.write_text('schema_version = 2\n[styles.atlas.canvas]\n'
                    f'labels_orientation = "{policy}"\n')
    configured = load_configuration_defaults(path)
    style = configured.style_mode.atlas
    assert style.canvas.labels_orientation == policy
    assert style.as_publication_style().labels_orientation == policy
    changed = ChartStyleOverrides(labels_orientation="upright").apply(style)
    assert changed.canvas.labels_orientation == "upright"
    assert style.canvas.labels_orientation == policy
    assert replace(changed, canvas=style.canvas) == style


def test_invalid_label_orientation_overlay_is_rejected(tmp_path):
    from wenu.configuration import load_configuration_defaults

    path = tmp_path / "labels.toml"
    path.write_text('schema_version = 2\n[styles.atlas.canvas]\n'
                    'labels_orientation = "radial"\n')
    with pytest.raises(ConfigurationError):
        load_configuration_defaults(path)


@pytest.mark.parametrize("style_name", ["atlas", "cartoon"])
@pytest.mark.parametrize("mode", ["print", "presentation"])
def test_title_color_overlay_changes_only_the_title(tmp_path, style_name, mode):
    import matplotlib.pyplot as plt
    from matplotlib.colors import to_rgba
    from wenu.configuration import load_configuration_defaults

    baseline = load_configuration_defaults()
    path = tmp_path / "title.toml"
    path.write_text(
        "schema_version = 2\n"
        f"[styles.{style_name}.canvas]\n"
        'title_color = "#0262AD"\n',
        encoding="utf-8",
    )
    configured = load_configuration_defaults(path)
    chart = RegionalChart(
        center_alt_deg=45.0, center_az_deg=180.0,
        field_width_deg=30.0, field_height_deg=20.0,
    )
    before = compose_chart(
        chart, style=style_name, mode=mode, configuration=baseline,
    ).style
    after = compose_chart(
        chart, style=style_name, mode=mode, configuration=configured,
    ).style
    assert replace(after, canvas=before.canvas) == before
    assert replace(after.canvas, title_color=None) == before.canvas
    for style, expected in (
        (before, before.canvas.foreground_color),
        (after, "#0262AD"),
        (before, before.canvas.foreground_color),
    ):
        figure, ax = plt.subplots()
        style.configure_axes(ax, title="La Ligua")
        assert to_rgba(ax.title.get_color()) == to_rgba(expected)
        assert ax.get_facecolor() == to_rgba(before.canvas.sky_color)
        plt.close(figure)
    assert load_configuration_defaults() == baseline



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


@pytest.mark.integration
@pytest.mark.parametrize("style_name", ["atlas", "cartoon"])
@pytest.mark.parametrize("mode", ["print", "presentation"])
def test_independent_constellation_size_preserves_other_style_fields(
    tmp_path, style_name, mode,
):
    from wenu.configuration import load_configuration_defaults

    baseline = load_configuration_defaults()
    original = getattr(baseline.style_mode, style_name)
    half_size = original.canvas.label_fontsize / 2.0
    path = tmp_path / "labels.toml"
    path.write_text(
        "schema_version = 2\n"
        f"[styles.{style_name}.constellation_labels]\n"
        f"font_size = {half_size}\n",
        encoding="utf-8",
    )
    configured = load_configuration_defaults(path)
    chart = RegionalChart(
        center_alt_deg=45.0, center_az_deg=180.0,
        field_width_deg=30.0, field_height_deg=20.0,
    )
    before = compose_chart(
        chart, style=style_name, mode=mode, configuration=baseline,
    ).style
    after = compose_chart(
        chart, style=style_name, mode=mode, configuration=configured,
    ).style
    assert after.grids.constellation_label_fontsize == pytest.approx(
        before.canvas.label_fontsize / 2.0
    )
    assert replace(
        after.grids,
        constellation_label_fontsize=before.grids.constellation_label_fontsize,
    ) == before.grids
    for name in ("canvas", "stars", "isophotes", "deep_sky", "legend"):
        assert getattr(after, name) == getattr(before, name)
    assert load_configuration_defaults() == baseline
