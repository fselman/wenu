"""Contracts for partial user TOML overlays over packaged authority."""

from dataclasses import FrozenInstanceError

import pytest

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
            "schema_version = 1\n[styles.atlas.horizon]\n"
            "renderer_operation = 'plot'\n"
        )
    assert (
        "styles.atlas.horizon.renderer_operation: unknown configuration key"
        in str(error.value)
    )


def test_overlay_merge_is_recursive_and_does_not_mutate_inputs():
    packaged = load_packaged_defaults()
    overlay = parse_configuration_overlay(
        "schema_version = 1\n"
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
        "schema_version = 1\n"
        "[families.regional_single]\n"
        "width = 12.0\n"
    )
    with pytest.raises(ConfigurationError) as error:
        merge_configuration_overlay(packaged, overlay)
    assert "families.regional_single.height" in str(error.value)


def test_optional_user_file_translates_all_existing_typed_contracts(tmp_path):
    path = tmp_path / "wenu.toml"
    path.write_text(
        "schema_version = 1\n"
        "[modes.print]\n"
        "dpi = 240\n"
        "[detail.neutral]\n"
        "label_density = 1.75\n"
        "[products.default]\n"
        "language = 'es'\n",
        encoding="utf-8",
    )

    values = load_configuration(path)
    defaults = load_configuration_defaults(path)

    assert values["modes"]["print"]["dpi"] == 240
    assert defaults.style_mode.print_mode.dpi == 240
    assert defaults.geometry_detail.neutral_detail.label_density == 1.75
    assert defaults.furniture_product_export.product.language == "es"
    with pytest.raises(FrozenInstanceError):
        defaults.style_mode.print_mode.dpi = 300


def test_sequential_overlays_do_not_leak_into_each_other_or_packaged_state(
    tmp_path,
):
    first_path = tmp_path / "first.toml"
    first_path.write_text(
        "schema_version = 1\n[modes.print]\ndpi = 240\n",
        encoding="utf-8",
    )
    second_path = tmp_path / "second.toml"
    second_path.write_text(
        "schema_version = 1\n[products.default]\nlanguage = 'es'\n",
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
