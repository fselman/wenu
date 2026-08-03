"""Declarative-workflow contracts for Milestone 43H cartoon examples."""

import ast
from pathlib import Path

import pytest


EXAMPLES = (
    Path("tests/fixtures/example_regressions/cartoon_modes.py"),
    Path("tests/fixtures/example_regressions/cartoon_modes_explicit_labels.py"),
)


def calls_named(tree, name):
    return tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and (
            (
                isinstance(node.func, ast.Name)
                and node.func.id == name
            )
            or (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == name
            )
        )
    )


@pytest.mark.parametrize("path", EXAMPLES)
def test_cartoon_examples_use_one_canonical_export(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    exports = calls_named(tree, "export")

    assert len(exports) == 1
    assert any(
        keyword.arg == "composition"
        for keyword in exports[0].keywords
    )
    assert calls_named(tree, "savefig") == ()
    assert calls_named(tree, "layer_options") == ()


@pytest.mark.parametrize("path", EXAMPLES)
def test_cartoon_examples_do_not_use_legacy_composition(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }

    assert "compose_chart" in imported
    assert "compose_cartoon_chart" not in imported


def test_explicit_label_example_keeps_user_configuration():
    source = EXAMPLES[1].read_text(encoding="utf-8")

    assert "CONSTELLATION_LABEL_POSITIONS" in source
    assert "CONSTELLATION_LABEL_OFFSETS" in source
    assert "constellation_label_positions=" in source
    assert "constellation_label_offsets=" in source
