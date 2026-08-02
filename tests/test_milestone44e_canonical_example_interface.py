"""Milestone 44E canonical example-interface contracts."""

import argparse
import ast
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
        ["--all", "--output", "output/gallery"]
    )
    options = chart_product_options(arguments)

    assert options.products == CANONICAL_CHART_PRODUCTS
    assert [path.name for _, path in options.outputs(stem="planisphere")] == [
        "planisphere-atlas-print.png",
        "planisphere-atlas-presentation.png",
        "planisphere-cartoon-print.png",
        "planisphere-cartoon-presentation.png",
    ]


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


def test_canonical_examples_contain_no_prohibited_low_level_operations():
    prohibited = {
        "savefig",
        "set_clip_boundary",
        "set_clip_path",
        "clip_to_boundary",
    }
    violations = []
    canonical = (
        "planisphere.py",
        "regional_constellation_group.py",
        "regional_constellation.py",
        "circumpolar.py",
        "binocular_object.py",
    )
    for name in canonical:
        path = Path("examples") / name
        if not path.is_file():
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if calls_named(tree, prohibited):
            violations.append(path.name)

    assert violations == []
