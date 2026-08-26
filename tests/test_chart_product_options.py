"""Milestone 44E canonical example-interface contracts."""

import argparse
from pathlib import Path

import pytest

from wenu import (
    CANONICAL_CHART_PRODUCTS,
    ChartFurnitureOptions,
    ChartProduct,
    ChartProductOptions,
    FooterOptions,
    LegendOptions,
    RegionalChart,
    add_chart_product_arguments,
    chart_product_options,
    compose_chart,
)
from wenu.output_policy import OutputFormat, SvgFontPolicy


def parser():
    value = argparse.ArgumentParser()
    return add_chart_product_arguments(
        value,
        default_output="output/reference.png",
    )


def test_invalid_style_and_mode_fail_through_argparse():
    with pytest.raises(SystemExit):
        parser().parse_args(["--style", "engraving"])
    with pytest.raises(SystemExit):
        parser().parse_args(["--mode", "screen"])


def test_normal_invocation_selects_one_exact_output():
    arguments = parser().parse_args(
        [
            "--style",
            "cartoon",
            "--mode",
            "presentation",
            "--output",
            "chosen.png",
        ]
    )
    options = chart_product_options(arguments)

    assert options.products == (
        ChartProduct("cartoon", "presentation"),
    )
    assert options.outputs(stem="regional") == (
        (options.products[0], Path("chosen.png")),
    )


def test_all_selects_four_deterministically_named_outputs():
    arguments = parser().parse_args(
        ["--all-products", "--output", "output/gallery"]
    )
    options = chart_product_options(arguments)

    assert options.products == CANONICAL_CHART_PRODUCTS
    assert [path.name for _, path in options.outputs(stem="planisphere")] == [
        "planisphere-atlas-print.png",
        "planisphere-atlas-presentation.png",
        "planisphere-cartoon-print.png",
        "planisphere-cartoon-presentation.png",
    ]


def test_vague_all_switch_is_rejected():
    with pytest.raises(SystemExit):
        parser().parse_args(["--all"])


def test_directory_output_names_one_selected_product():
    options = ChartProductOptions(
        output=Path("output/gallery"),
        style="atlas",
        mode="presentation",
    )
    assert options.output_path(
        options.products[0], stem="circumpolar"
    ) == Path("output/gallery/circumpolar-atlas-presentation.png")


def test_product_resolves_composition_through_public_apis():
    chart = RegionalChart(45.0, 180.0, 20.0, 15.0)
    product = ChartProduct("cartoon", "presentation")
    composition = compose_chart(
        chart,
        style=product.style,
        mode=product.mode,
        furniture=ChartFurnitureOptions(
            footer=FooterOptions(application=True),
            legends=LegendOptions(stellar_counts=True),
        ),
    )

    assert composition.style_name == "cartoon"
    assert composition.mode_name == "presentation"
    assert composition.furniture.footer.application is True
    assert composition.legends.stellar_counts is True
    assert composition.detail is not None


def calls_named(tree, names):
    return tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in names
    )



def test_explicit_format_names_directory_output_deterministically():
    arguments = parser().parse_args(
        ["--format", "svg", "--output", "output/gallery"]
    )
    options = chart_product_options(arguments)

    assert options.output_format is OutputFormat.SVG
    assert options.outputs(stem="regional")[0][1] == Path(
        "output/gallery/regional-atlas-print.svg"
    )


def test_single_file_rejects_format_extension_contradiction():
    arguments = parser().parse_args(
        ["--format", "svg", "--output", "chosen.pdf"]
    )
    options = chart_product_options(arguments)

    with pytest.raises(ValueError, match="contradicts explicit format"):
        options.outputs(stem="regional")


def test_editable_font_policy_is_public_and_svg_only():
    arguments = parser().parse_args(
        [
            "--format", "svg",
            "--svg-font-policy", "editable",
            "--output", "chosen.svg",
        ]
    )
    options = chart_product_options(arguments)

    assert options.svg_font_policy is SvgFontPolicy.EDITABLE
    assert options.outputs(stem="regional")[0][1] == Path("chosen.svg")

    with pytest.raises(ValueError, match="requires SVG output"):
        chart_product_options(parser().parse_args([
            "--format", "pdf",
            "--svg-font-policy", "editable",
        ]))


def test_output_parser_rejects_backend_font_vocabulary():
    with pytest.raises(SystemExit):
        parser().parse_args(["--svg-font-policy", "none"])
    with pytest.raises(SystemExit):
        parser().parse_args(["--format", "jpeg"])
