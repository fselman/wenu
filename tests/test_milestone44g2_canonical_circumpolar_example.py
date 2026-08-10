"""Milestone 44G.2 canonical circumpolar example."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from wenu import BoundaryKind, compose_chart
from wenu.charts.detail import ResolvedDetail
from wenu.charts.detail_application import apply_resolved_detail


EXAMPLE = Path("examples/circumpolar.py")


def load():
    spec = importlib.util.spec_from_file_location("circumpolar", EXAMPLE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_chart_preserves_southern_pole_and_lmc_crossing_geometry():
    module = load()
    _, chart = module.build_chart()

    assert module.LIMITING_DECLINATION_DEG == pytest.approx(-69.75)
    assert chart.pole == "south"
    assert chart.limiting_declination_deg == pytest.approx(-69.75)
    assert chart.chart_context.boundary_kind == BoundaryKind.CIRCULAR
    assert chart.chart_context.horizon_altitude_deg == pytest.approx(-90.0)
    assert chart.coordinate_label_anchor.declination_at_left is True


def test_cartoon_product_retains_defining_circumpolar_content():
    module = load()

    assert module.CARTOON_CONTENT_LAYERS == frozenset({
        "stars",
        "constellation_lines",
        "equatorial_grid",
        "milky_way",
        "magellanic_clouds",
    })
    source = EXAMPLE.read_text(encoding="utf-8")
    assert 'add_magellanic_cloud_isophotes("lmc")' in source
    assert 'add_magellanic_cloud_isophotes("smc")' in source


def test_magellanic_isophotes_use_the_shared_content_name():
    layer = SimpleNamespace(layer_name="magellanic_cloud_isophotes")
    sky = SimpleNamespace(layers=(layer,))
    applied = apply_resolved_detail(
        sky,
        ResolvedDetail(enabled_layers=frozenset({"magellanic_clouds"})),
    )

    assert applied.layer_options[
        "magellanic_cloud_isophotes"
    ]["enabled"] is True


def test_style_and_mode_leave_polar_geometry_unchanged():
    module = load()
    _, chart = module.build_chart()
    contexts = [
        compose_chart(chart, style=style, mode=mode).context
        for style in ("atlas", "cartoon")
        for mode in ("print", "presentation")
    ]

    baseline = contexts[0]
    assert all(
        context.viewport == baseline.viewport
        and context.tangent_longitude_deg
        == baseline.tangent_longitude_deg
        and context.tangent_latitude_deg
        == baseline.tangent_latitude_deg
        and context.boundary_kind == baseline.boundary_kind
        and context.horizon_altitude_deg
        == baseline.horizon_altitude_deg
        for context in contexts
    )
    for context in contexts[1:]:
        np.testing.assert_allclose(
            context.clip_boundary.x,
            baseline.clip_boundary.x,
        )
        np.testing.assert_allclose(
            context.clip_boundary.y,
            baseline.clip_boundary.y,
        )
    assert 'sky.add_magellanic_cloud_isophotes("lmc")' in (
        EXAMPLE.read_text(encoding="utf-8")
    )
