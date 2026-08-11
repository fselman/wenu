"""Canonical selected-object binocular integration contracts."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from wenu import BinocularChart, BoundaryKind, ChartRequest


pytestmark = pytest.mark.integration


EXAMPLE = Path("examples/binocular_object.py")


def test_example_uses_packaged_targets_without_a_private_registry(
    canonical_builds,
):
    module = canonical_builds.module(EXAMPLE)

    assert not hasattr(module, "TARGETS")
    assert module.parser().parse_args(["--target", "M57"]).target == "M57"
    request = module.chart_request("omega-centauri", 7.0)
    assert request.subject.target == "omega-centauri"
    assert request.title == (
        "Omega Centauri (NGC 5139) — 7° binocular field"
    )
    assert all(
        options.detail.detail.extended_object_samples == 73
        for options in request.product_compositions
    )


def test_centaurus_a_retains_its_approved_atlas_detail(canonical_builds):
    module = canonical_builds.module(EXAMPLE)
    request = module.chart_request("centaurus-a")

    assert all(
        options.detail.detail.galaxy_magnitude_limit == pytest.approx(11.0)
        for options in request.product_compositions
    )
    assert all(
        options.detail.detail.extended_object_samples == 97
        for options in request.product_compositions
    )


@pytest.mark.parametrize("target_key", ["centaurus-a", "omega-centauri"])
def test_chart_is_centered_on_selected_catalogue_target(
    target_key, canonical_builds,
):
    sky, chart, target = canonical_builds.build(EXAMPLE, target_key, 7.0)
    horizontal = target.coordinate.transform_to(sky.observer.altaz_frame)
    x, y = chart.projection.project_spherical(
        horizontal.az.deg,
        horizontal.alt.deg,
    )

    assert isinstance(chart, BinocularChart)
    assert chart.field_diameter_deg == pytest.approx(7.0)
    assert chart.chart_context.boundary_kind == BoundaryKind.CIRCULAR
    assert x == pytest.approx(0.0, abs=2.0e-8)
    assert y == pytest.approx(0.0, abs=2.0e-8)
    assert sky.galaxies is not None
    assert sky.globular_clusters is not None

def test_cartoon_retains_both_supported_target_layer_types(canonical_builds):
    module = canonical_builds.module(EXAMPLE)

    assert module.STAR_MAGNITUDE_LIMIT == pytest.approx(11.0)
    assert module.CARTOON_CONTENT_LAYERS == frozenset({
        "stars",
        "constellation_lines",
        "galaxies",
        "globular_clusters",
    })


def test_ordinary_packaged_target_adds_its_resolved_family(canonical_builds):
    module = canonical_builds.module(EXAMPLE)
    request = module.chart_request("M57")

    assert all(
        "planetary_nebulae" in options.detail.detail.enabled_layers
        for options in request.product_compositions
    )


def test_generation_delegates_the_pure_request_to_the_common_facade(
    monkeypatch, tmp_path, canonical_builds
):
    module = canonical_builds.module(EXAMPLE)
    captured = []
    output = tmp_path / "m57.png"
    monkeypatch.setattr(
        module,
        "generate_chart_request",
        lambda request: captured.append(request) or SimpleNamespace(
            outputs=(output,)
        ),
    )

    paths = module.generate(module.parser().parse_args([
        "--target", "M57", "--output", str(output)
    ]))

    assert paths == (output,)
    assert len(captured) == 1
    assert isinstance(captured[0], ChartRequest)
    assert captured[0].subject.target == "M57"
