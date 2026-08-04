"""Milestone 44F.B.2 shared controls in canonical examples."""

import importlib.util
from pathlib import Path

import pytest

from wenu import (
    CartoonDetailPolicy,
    FixedDetailPolicy,
    ResolvedDetail,
    chart_detail_overrides,
    compose_chart,
)


EXAMPLES = (
    Path("examples/planisphere.py"),
    Path("examples/regional_constellation_group.py"),
    Path("examples/regional_constellation.py"),
    Path("examples/circumpolar.py"),
)


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("path", EXAMPLES)
def test_shared_content_and_legend_controls_are_available(path):
    arguments = load(path).parser().parse_args(
        [
            "--magnitude-limit", "4.25",
            "--constellation-labels",
            "--constellation-boundaries",
            "--grid-references", "all",
            "--poles",
            "--pole-labels",
            "--object-legend",
            "--magnitude-legend",
            "--star-counts",
        ]
    )

    assert arguments.magnitude_limit == pytest.approx(4.25)
    assert arguments.constellation_labels is True
    assert arguments.constellation_boundaries is True
    assert arguments.grid_references == frozenset(
        {"equatorial", "ecliptic", "galactic"}
    )
    assert arguments.poles is True
    assert arguments.pole_labels is True
    assert arguments.object_legend is True
    assert arguments.magnitude_legend is True
    assert arguments.star_counts is True


def resolved_detail(module, arguments, *, style):
    if module.__name__ == "planisphere":
        _, chart = module.build_chart()
        default_limit = 5.0
    elif module.__name__ == "regional_constellation_group":
        _, chart, _ = module.build_chart("summer-triangle")
        default_limit = 6.5
    elif module.__name__ == "circumpolar":
        _, chart = module.build_chart()
        default_limit = 6.5
    else:
        _, chart = module.build_chart("Cru")
        default_limit = 6.5
    policy = (
        CartoonDetailPolicy()
        if style == "cartoon"
        else FixedDetailPolicy(
            ResolvedDetail(star_magnitude_limit=default_limit)
        )
    )
    return compose_chart(
        chart,
        style=style,
        mode="presentation",
        detail=policy,
        detail_overrides=chart_detail_overrides(arguments),
    ).detail


@pytest.mark.parametrize("path", EXAMPLES)
@pytest.mark.parametrize("style", ["atlas", "cartoon"])
def test_labels_and_boundaries_are_opt_in(path, style):
    module = load(path)
    hidden = resolved_detail(module, module.parser().parse_args([]), style=style)
    visible = resolved_detail(
        module,
        module.parser().parse_args(
            ["--constellation-labels", "--constellation-boundaries"]
        ),
        style=style,
    )

    assert hidden.layer_enabled("constellation_labels") is False
    assert hidden.layer_enabled("constellation_boundaries") is False
    assert visible.layer_enabled("constellation_labels") is True
    assert visible.layer_enabled("constellation_boundaries") is True


@pytest.mark.parametrize("path", EXAMPLES)
def test_cartoon_constellation_vertices_follow_line_switch(path):
    module = load(path)
    hidden = resolved_detail(
        module,
        module.parser().parse_args(["--magnitude-limit", "4.25"]),
        style="cartoon",
    )
    visible = resolved_detail(
        module,
        module.parser().parse_args(
            ["--magnitude-limit", "4.25", "--constellation-lines"]
        ),
        style="cartoon",
    )

    assert hidden.star_magnitude_limit == pytest.approx(4.25)
    assert hidden.constellation_star_mode == "none"
    assert visible.constellation_star_mode == "selected"


def test_shared_cartoon_limit_is_three_with_deep_binocular_exception():
    assert CartoonDetailPolicy().resolve(
        object(), object()
    ).star_magnitude_limit == pytest.approx(3.0)

    binocular = load(Path("examples/binocular_object.py"))
    assert binocular.STAR_MAGNITUDE_LIMIT == pytest.approx(11.0)


def test_planisphere_horizon_is_independent_of_content_switches():
    module = load(EXAMPLES[0])
    _, chart = module.build_chart()
    default = module.parser().parse_args([])
    populated = module.parser().parse_args(
        [
            "--constellation-labels",
            "--constellation-boundaries",
            "--grid-references", "all",
            "--poles",
            "--legends",
        ]
    )

    assert chart.horizon_altitude_deg == pytest.approx(0.0)
    assert chart.horizon_linewidth == pytest.approx(0.8)
    assert chart_detail_overrides(default).disabled_layers
    assert chart_detail_overrides(populated).enabled_layer_additions


def test_regional_mask_does_not_require_visible_boundary_lines():
    module = load(EXAMPLES[2])
    _, chart = module.build_chart("Cru", mask=True)
    detail = resolved_detail(
        module,
        module.parser().parse_args(["--mask"]),
        style="atlas",
    )

    assert chart.outside_mask_constellations == ("Cru",)
    assert detail.layer_enabled("constellation_boundaries") is False


@pytest.mark.parametrize("path", EXAMPLES)
def test_examples_apply_render_local_style_overrides(path):
    source = path.read_text(encoding="utf-8")

    assert "style_overrides=chart_style_overrides(" in source
    assert "detail_overrides=chart_detail_overrides(" in source
