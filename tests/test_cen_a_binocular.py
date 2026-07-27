"""Focused tests for the Cen A binocular-field example."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "cen_a_binocular.py"


def _example():
    spec = importlib.util.spec_from_file_location(
        "cen_a_binocular_example",
        EXAMPLE,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_binocular_field_constants():
    example = _example()
    assert example.FIELD_DIAMETER_DEG == pytest.approx(6.5)
    assert example.STAR_MAGNITUDE_LIMIT == pytest.approx(11.0)


def test_chart_is_centered_on_cen_a_and_is_square():
    example = _example()
    observer, sky, chart = example.build_chart()
    horizontal = example.CEN_A.transform_to(observer.altaz_frame)
    x, y = chart.projection.project_spherical(
        horizontal.az.deg,
        horizontal.alt.deg,
    )
    assert x == pytest.approx(0.0, abs=2.0e-8)
    assert y == pytest.approx(0.0, abs=2.0e-8)
    assert chart.field_width_deg == pytest.approx(6.5)
    assert chart.field_height_deg == pytest.approx(6.5)
    assert sky.stars.magnitude_limit == pytest.approx(11.0)


def test_circular_aperture_has_expected_projected_radius():
    example = _example()
    _, _, chart = example.build_chart()
    figure, ax = plt.subplots()
    disk, rim = example.circular_aperture(
        ax,
        chart,
        sky_color="midnightblue",
    )
    expected = chart.projection.projected_radius(3.25)
    assert disk.radius == pytest.approx(expected)
    assert rim.radius == pytest.approx(expected)
    assert ax.get_facecolor()[:3] == pytest.approx((1.0, 1.0, 1.0))
    plt.close(figure)
