from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from wenu import (
    POLAR_PLANISPHERE_CONTENT_LAYERS,
    PolarPlanisphereDetailPolicy,
    PolarPlanispherePairRequest,
    compose_chart,
)
from wenu.charts.detail_application import apply_resolved_detail
from wenu.configuration import (
    load_packaged_defaults,
    translate_geometry_detail_defaults,
)


DEEP_SKY_LAYERS = frozenset(
    {
        "galaxies",
        "globular_clusters",
        "open_clusters",
        "planetary_nebulae",
        "supernova_remnants",
    }
)


class Layer:
    def __init__(self, name):
        self.layer_name = name


def test_default_policy_is_the_exact_sparse_classroom_content():
    detail = PolarPlanisphereDetailPolicy().resolve(object(), object())

    assert detail.star_magnitude_limit == pytest.approx(5.0)
    assert detail.label_density == pytest.approx(1.0)
    assert detail.enabled_layers == POLAR_PLANISPHERE_CONTENT_LAYERS
    assert detail.constellation_star_mode == "none"
    assert detail.layer_enabled("stars")
    assert detail.layer_enabled("constellation_lines")
    assert detail.layer_enabled("constellation_labels")
    assert detail.layer_enabled("milky_way")
    assert not detail.layer_enabled("constellation_boundaries")
    assert not detail.layer_enabled("magellanic_clouds")
    assert not detail.enabled_layers & DEEP_SKY_LAYERS


@pytest.mark.parametrize("mode", ("print", "presentation"))
def test_atlas_composition_uses_one_policy_for_both_faces(mode):
    pair = PolarPlanispherePairRequest().resolve()

    south = compose_chart(pair.south, style="atlas", mode=mode)
    north = compose_chart(pair.north, style="atlas", mode=mode)

    assert south.detail == north.detail
    assert south.detail == PolarPlanisphereDetailPolicy().resolve(
        south.context, south.mode
    )
    assert south.detail.star_magnitude_limit == pytest.approx(5.0)
    assert south.detail.enabled_layers == POLAR_PLANISPHERE_CONTENT_LAYERS


def test_overlap_content_options_are_identical_before_projection():
    pair = PolarPlanispherePairRequest().resolve()
    south_detail = compose_chart(
        pair.south, style="atlas", mode="print"
    ).detail
    north_detail = compose_chart(
        pair.north, style="atlas", mode="print"
    ).detail
    sky = SimpleNamespace(
        layers=tuple(
            Layer(name)
            for name in (
                "stars",
                "constellation_lines",
                "constellation_labels",
                "constellation_boundaries",
                "milky_way_isophotes",
                *sorted(DEEP_SKY_LAYERS),
            )
        )
    )

    south_options = apply_resolved_detail(
        sky, south_detail
    ).layer_options
    north_options = apply_resolved_detail(
        sky, north_detail
    ).layer_options

    assert south_options == north_options
    stars = next(layer for layer in sky.layers if layer.layer_name == "stars")
    assert south_options[stars]["geometry"] == {
        "magnitude_limit": 5.0,
        "include_ids": frozenset(),
        "include_constellation_vertices": False,
    }
    for layer in sky.layers:
        expected = layer.layer_name in {
            "stars",
            "constellation_lines",
            "constellation_labels",
            "milky_way_isophotes",
        }
        assert south_options[layer]["enabled"] is expected


def test_packaged_configuration_owns_the_physical_disk_policy():
    defaults = translate_geometry_detail_defaults()

    assert defaults.polar_planisphere_policy == (
        PolarPlanisphereDetailPolicy()
    )

    values = load_packaged_defaults()
    values["detail"]["polar_planisphere"][
        "star_magnitude_limit"
    ] = 4.75
    configured = translate_geometry_detail_defaults(values)
    assert configured.polar_planisphere_policy.star_magnitude_limit == (
        pytest.approx(4.75)
    )


def test_policy_is_immutable_and_rejects_content_drift():
    policy = PolarPlanisphereDetailPolicy()

    with pytest.raises(FrozenInstanceError):
        policy.star_magnitude_limit = 6.0
    with pytest.raises(ValueError, match="enabled_layers"):
        PolarPlanisphereDetailPolicy(
            enabled_layers=frozenset({"stars", "galaxies"})
        )
    with pytest.raises(ValueError, match="constellation_star_mode"):
        PolarPlanisphereDetailPolicy(constellation_star_mode="all")
    with pytest.raises(ValueError, match="star_magnitude_limit"):
        PolarPlanisphereDetailPolicy(star_magnitude_limit=float("nan"))


def test_policy_and_content_constant_are_public():
    import wenu

    assert "POLAR_PLANISPHERE_CONTENT_LAYERS" in wenu.__all__
    assert "PolarPlanisphereDetailPolicy" in wenu.__all__
