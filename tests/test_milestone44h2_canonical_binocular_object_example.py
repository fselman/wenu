"""Milestone 44H.2 canonical selected-object binocular example."""

import importlib.util
from pathlib import Path

import pytest

from wenu import BinocularChart, BoundaryKind


EXAMPLE = Path("examples/binocular_object.py")


def load():
    spec = importlib.util.spec_from_file_location("binocular_object", EXAMPLE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_target_registry_includes_cen_a_and_omega_cen():
    module = load()

    assert tuple(module.TARGETS) == ("centaurus-a", "omega-centauri")
    assert module.TARGETS["centaurus-a"].identifier == "NGC 5128"
    assert module.TARGETS["omega-centauri"].identifier == "NGC 5139"


@pytest.mark.parametrize("target_key", ["centaurus-a", "omega-centauri"])
def test_chart_is_centered_on_selected_catalogue_target(target_key):
    module = load()
    sky, chart, target = module.build_chart(target_key, 7.0)
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

def test_cartoon_retains_both_supported_target_layer_types():
    module = load()

    assert module.STAR_MAGNITUDE_LIMIT == pytest.approx(11.0)
    assert module.CARTOON_CONTENT_LAYERS == frozenset({
        "stars",
        "constellation_lines",
        "galaxies",
        "globular_clusters",
    })
