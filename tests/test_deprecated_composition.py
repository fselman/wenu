"""Compatibility contracts for deprecated cartoon composition."""

import subprocess
import sys

import pytest

from wenu import (
    CartoonDetailPolicy,
    RegionalChart,
    cartoon_output_mode,
    compose_cartoon_chart,
)
from wenu.charts.modes import PrintMode


def chart():
    return RegionalChart(
        center_alt_deg=45.0,
        center_az_deg=190.0,
        field_width_deg=45.0,
        field_height_deg=30.0,
    )


def test_legacy_mode_selector_warns_and_identifies_replacement():
    with pytest.warns(DeprecationWarning, match="compose_chart"):
        mode = cartoon_output_mode("print")

    assert isinstance(mode, PrintMode)


def test_legacy_composition_warns_once_and_still_functions():
    with pytest.warns(DeprecationWarning) as observed:
        composition = compose_cartoon_chart(
            chart(), mode="presentation"
        )

    assert len(observed) == 1
    assert "compose_chart" in str(observed[0].message)
    assert composition.style_name == "cartoon"
    assert composition.mode_name == "presentation"
    assert composition.detail == CartoonDetailPolicy().resolve(
        composition.context,
        composition.mode,
    )


def test_canonical_cartoon_composition_does_not_import_legacy_module():
    script = """
import sys
from wenu import RegionalChart, compose_chart

chart = RegionalChart(
    center_alt_deg=45.0,
    center_az_deg=190.0,
    field_width_deg=45.0,
    field_height_deg=30.0,
)
for mode in ("print", "presentation"):
    composition = compose_chart(chart, style="cartoon", mode=mode)
    assert composition.style_name == "cartoon"
assert "wenu.charts.cartoon_composition" not in sys.modules
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
