"""Contracts for partial user TOML overlays over packaged authority."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

def test_installed_regional_v6_profile_has_only_chart_concerns_and_user_precedence(tmp_path):
    from wenu.resources import configuration_preset_names, configuration_preset_path, configuration_input_path
    import tomllib
    assert 'atlas-v6' in configuration_preset_names('atlas-style')
    atlas = tomllib.loads(configuration_preset_path('atlas-v6', kind='atlas-style').read_text())
    chart_path = configuration_preset_path('atlas-v6', kind='chart')
    assert tomllib.loads(chart_path.read_text())['schema_version'] == 2
    assert load_configuration(chart_path) == load_configuration('atlas-v6')
    regional = load_configuration_defaults(family='regional')
    plain = load_configuration_defaults()
    deep = regional.style_mode.atlas.deep_sky
    stars = regional.style_mode.atlas.stars
    assert stars.diameter_scale == atlas['star_size_scale'] == 1.7
    assert stars.magnitude_sizing.algorithm == 'quadratic'
    assert stars.magnitude_sizing.a_mm == atlas['stellar_magnitude_sizing']['a_mm']
    assert deep.open_cluster_symbol_name == 'cluster_circle'
    assert deep.open_cluster_face_color == 'yellow'
    assert deep.globular_cluster_symbol_name == 'globular_cluster'
    assert deep.planetary_nebula_symbol_size == pytest.approx(18 * 1.8**2 * 1.25**2)
    assert deep.open_cluster_angular_sizes and deep.nonstellar_labels_only
    assert regional.geometry_detail.family_atlas_policies['regional'].star_magnitude_limit == 7.5
    assert plain.style_mode.atlas.stars.magnitude_sizing.algorithm == 'legacy'
    assert regional.furniture_product_export == plain.furniture_product_export
    assert 'report_label_scale' not in load_configuration(family='regional')
    overlay = tmp_path/'custom.toml'
    overlay.write_text('schema_version = 2\n[styles.atlas.planetary_nebula]\ncolor = "red"\n[styles.atlas.stars]\ndiameter_scale = 2.0\n')
    custom = load_configuration_defaults(overlay, family='regional')
    assert custom.style_mode.atlas.deep_sky.planetary_nebula_color == 'red'
    assert custom.style_mode.atlas.stars.diameter_scale == 2
    assert load_configuration_defaults('scorpius-v1').style_mode.atlas.stars.diameter_scale == 1.7
    with pytest.raises(ValueError, match='not a chart input'):
        configuration_input_path('b4-portrait', kind='chart')
    with pytest.raises(ValueError, match='Unknown'):
        configuration_preset_path('atlas-v5', kind='atlas-style')

from wenu.configuration import (
    ConfigurationError,
    load_configuration,
    load_configuration_defaults,
    load_packaged_defaults,
    merge_configuration_overlay,
    parse_configuration_overlay,
)


def test_partial_overlay_requires_schema_version_and_known_paths():
    with pytest.raises(ConfigurationError) as error:
        parse_configuration_overlay("[modes.print]\ndpi = 240\n")
    assert "schema_version: missing required overlay key" in str(error.value)

    with pytest.raises(ConfigurationError) as error:
        parse_configuration_overlay(
            "schema_version = 2\n[styles.atlas.horizon]\n"
            "renderer_operation = 'plot'\n"
        )
    assert (
        "styles.atlas.horizon.renderer_operation: unknown configuration key"
        in str(error.value)
    )


def test_overlay_merge_is_recursive_and_does_not_mutate_inputs():
    packaged = load_packaged_defaults()
    overlay = parse_configuration_overlay(
        "schema_version = 2\n"
        "[data]\n"
        "moving_object_policy = 'offline'\n"
        "[modes.print]\n"
        "dpi = 240\n"
        "[styles.atlas.horizon]\n"
        "line_style = 'solid'\n"
    )

    merged = merge_configuration_overlay(packaged, overlay)

    assert merged["modes"]["print"]["dpi"] == 240
    assert merged["modes"]["print"]["font_scale"] == 1.0
    assert merged["styles"]["atlas"]["horizon"]["line_style"] == "solid"
    assert packaged["modes"]["print"]["dpi"] == 300
    assert overlay["modes"]["print"] == {"dpi": 240}


def test_merged_semantic_validation_reports_complete_overlay_path():
    packaged = load_packaged_defaults()
    overlay = parse_configuration_overlay(
        "schema_version = 2\n"
        "[families.regional_single]\n"
        "width = 12.0\n"
    )
    with pytest.raises(ConfigurationError) as error:
        merge_configuration_overlay(packaged, overlay)
    assert "families.regional_single.height" in str(error.value)


def test_optional_user_file_translates_all_existing_typed_contracts(tmp_path):
    path = tmp_path / "wenu.toml"
    path.write_text(
        "schema_version = 2\n"
        "[data]\n"
        "moving_object_policy = 'offline'\n"
        "[modes.print]\n"
        "dpi = 240\n"
        "[detail.neutral]\n"
        "label_density = 1.75\n"
        "[products.default]\n"
        "language = 'es'\n"
        "[observer]\n"
        "minor_body_resource_directory = '~/wenu-minor-bodies'\n",
        encoding="utf-8",
    )

    values = load_configuration(path)
    defaults = load_configuration_defaults(path)

    assert values["modes"]["print"]["dpi"] == 240
    assert defaults.style_mode.print_mode.dpi == 240
    assert defaults.moving_object_data_policy == "offline"
    assert defaults.geometry_detail.neutral_detail.label_density == 1.75
    assert defaults.furniture_product_export.product.language == "es"
    assert defaults.minor_body_resource_directory == (
        Path("~/wenu-minor-bodies").expanduser()
    )
    with pytest.raises(FrozenInstanceError):
        defaults.style_mode.print_mode.dpi = 300


def test_sequential_overlays_do_not_leak_into_each_other_or_packaged_state(
    tmp_path,
):
    first_path = tmp_path / "first.toml"
    first_path.write_text(
        "schema_version = 2\n[modes.print]\ndpi = 240\n",
        encoding="utf-8",
    )
    second_path = tmp_path / "second.toml"
    second_path.write_text(
        "schema_version = 2\n[products.default]\nlanguage = 'es'\n",
        encoding="utf-8",
    )

    first = load_configuration_defaults(first_path)
    second = load_configuration_defaults(second_path)
    packaged = load_configuration_defaults()

    assert first.style_mode.print_mode.dpi == 240
    assert first.furniture_product_export.product.language == "en"
    assert second.style_mode.print_mode.dpi == 300
    assert second.furniture_product_export.product.language == "es"
    assert packaged.style_mode.print_mode.dpi == 300
    assert packaged.furniture_product_export.product.language == "en"


def test_sequence_overlay_translates_as_disabled_or_complete(tmp_path):
    path = tmp_path / "sequence.toml"
    path.write_text(
        "schema_version = 2\n"
        "[sequence]\n"
        "stop = '2026-08-22T07:00:00Z'\n"
        "frames = 3\n"
        "display_timezone = 'America/Santiago'\n"
        "playback_duration = 1.5\n"
        "frames_per_second = 2.0\n"
        "restart_policy = 'resume'\n",
        encoding="utf-8",
    )

    configured = load_configuration_defaults(path)
    packaged = load_configuration_defaults()

    assert configured.sequence.stop == "2026-08-22T07:00:00Z"
    assert configured.sequence.frames == 3
    assert configured.sequence.display_timezone == "America/Santiago"
    assert configured.sequence.playback_duration_seconds == pytest.approx(1.5)
    assert configured.sequence.frames_per_second == pytest.approx(2.0)
    assert configured.sequence.restart_policy == "resume"
    assert packaged.sequence.stop is None
    assert packaged.sequence.frames is None


@pytest.mark.parametrize(
    ("body", "diagnostic"),
    (
        (
            "stop = '2026-08-22T07:00:00Z'\n",
            "sequence.frames",
        ),
        (
            "frames = 3\n",
            "sequence.frames",
        ),
        (
            "playback_duration = 1.5\n",
            "sequence.frames_per_second",
        ),
        (
            "stop = '2026-08-22T07:00:00Z'\n"
            "frames = 3\n"
            "playback_duration = 1.0\n"
            "frames_per_second = 2.0\n",
            "must imply sequence frames",
        ),
    ),
)
def test_sequence_overlay_rejects_incomplete_or_inconsistent_values(
    tmp_path,
    body,
    diagnostic,
):
    path = tmp_path / "invalid-sequence.toml"
    path.write_text(
        "schema_version = 2\n[sequence]\n" + body,
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match=None) as error:
        load_configuration_defaults(path)

    assert diagnostic in str(error.value)


@pytest.mark.parametrize('key,value', [('lines', ['all', 'Sco']),
    ('labels_exclude', ['all']), ('boundaries', ['NoSuchConstellation']),
    ('lines_exclude', [1])])
def test_constellation_feature_overlays_reject_invalid_lists(key, value):
    from wenu.configuration.validation import merge_configuration_overlay, load_packaged_defaults
    with pytest.raises(ValueError):
        merge_configuration_overlay(load_packaged_defaults(), {
            'schema_version': 2, 'detail': {'constellations': {key: value}}})


def test_compact_scorpius_comparison_retains_objects_without_labels():
    previous = load_configuration_defaults('scorpius-v1')
    compact = load_configuration_defaults('scorpius-v2')
    a = previous.style_mode.atlas
    b = compact.style_mode.atlas
    assert b.stars.diameter_scale == pytest.approx(a.stars.diameter_scale * .7)
    for field in ('open_cluster_symbol_size', 'globular_cluster_symbol_size', 'planetary_nebula_symbol_size'):
        assert getattr(b.deep_sky, field) == pytest.approx(getattr(a.deep_sky, field) * .65**2)
    assert b.deep_sky.open_cluster_angular_sizes
    assert b.deep_sky.open_cluster_diameter_scale == .65
    assert b.deep_sky.supernova_remnant_symbol_scale == pytest.approx(a.deep_sky.supernova_remnant_symbol_scale * .65)
    for field in ('nonstellar_draw_labels', 'galaxy_draw_labels', 'open_cluster_draw_labels', 'globular_cluster_draw_labels', 'planetary_nebula_draw_labels', 'supernova_remnant_draw_labels'):
        assert not getattr(b.deep_sky, field)
    before = load_configuration('scorpius-v1')
    after = load_configuration('scorpius-v2')
    old = before['grids_references']['coordinate_grid']['edge_marks']
    new = after['grids_references']['coordinate_grid']['edge_marks']
    assert new['grid_label_fontsize'] == pytest.approx(old['grid_label_fontsize'] * .7)
    assert new['grid_frame_width_scale'] == pytest.approx(old['grid_frame_width_scale'] * .7)
    assert after['detail'] == before['detail']
