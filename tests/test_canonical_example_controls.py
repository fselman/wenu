"""Milestone 44F.B.2 shared controls in canonical examples."""

import importlib.util
from pathlib import Path

import pytest

from wenu import (
    CartoonDetailPolicy,
    FixedDetailPolicy,
    RegionalChart,
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


def resolved_detail(arguments, *, style):
    chart = RegionalChart(45.0, 180.0, 20.0, 15.0)
    policy = (
        CartoonDetailPolicy()
        if style == "cartoon"
        else FixedDetailPolicy(
            ResolvedDetail(star_magnitude_limit=6.5)
        )
    )
    return compose_chart(
        chart,
        style=style,
        mode="presentation",
        detail=policy,
        detail_overrides=chart_detail_overrides(arguments),
    ).detail

@pytest.mark.parametrize("style", ["atlas", "cartoon"])
def test_labels_and_boundaries_are_opt_in(style):
    module = load(EXAMPLES[2])
    hidden = resolved_detail(module.parser().parse_args([]), style=style)
    visible = resolved_detail(
        module.parser().parse_args(
            ["--constellation-labels", "--constellation-boundaries"]
        ),
        style=style,
    )

    assert hidden.layer_enabled("constellation_labels") is False
    assert hidden.layer_enabled("constellation_boundaries") is False
    assert visible.layer_enabled("constellation_labels") is True
    assert visible.layer_enabled("constellation_boundaries") is True


def test_cartoon_constellation_vertices_follow_line_switch():
    module = load(EXAMPLES[2])
    hidden = resolved_detail(
        module.parser().parse_args(["--magnitude-limit", "4.25"]),
        style="cartoon",
    )
    visible = resolved_detail(
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
    source = EXAMPLES[0].read_text(encoding="utf-8")

    assert 'family="planisphere"' in source
    assert "position_angle_deg=0.0" in source
    assert "mask=False" in source


def test_regional_mask_does_not_require_visible_boundary_lines():
    module = load(EXAMPLES[2])
    detail = resolved_detail(
        module.parser().parse_args(["--mask"]),
        style="atlas",
    )

    assert "mask=arguments.mask" in EXAMPLES[2].read_text(encoding="utf-8")
    assert detail.layer_enabled("constellation_boundaries") is False


@pytest.mark.parametrize("path", EXAMPLES)
def test_examples_apply_render_local_style_overrides(path):
    source = path.read_text(encoding="utf-8")

    assert "draw_chart_view_from_arguments(" in source
    assert "compose_chart(" not in source
    assert ".export(" not in source
