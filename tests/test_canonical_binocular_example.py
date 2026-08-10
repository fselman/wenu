"""Canonical selected-object binocular integration contracts."""

from pathlib import Path

import pytest

from wenu import BinocularChart, BoundaryKind


pytestmark = pytest.mark.integration


EXAMPLE = Path("examples/binocular_object.py")


def test_target_registry_includes_cen_a_and_omega_cen(canonical_builds):
    module = canonical_builds.module(EXAMPLE)

    assert tuple(module.TARGETS) == ("centaurus-a", "omega-centauri")
    assert module.TARGETS["centaurus-a"].identifier == "NGC 5128"
    assert module.TARGETS["omega-centauri"].identifier == "NGC 5139"


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
