"""Parity contracts for TOML geometry and detail translation."""

from dataclasses import replace
from types import MappingProxyType

import pytest

from wenu.charts.detail import (
    AdaptiveDetailPolicy,
    CARTOON_CONTENT_LAYERS,
    CartoonDetailPolicy,
    DEFAULT_CONTENT_LAYERS,
    DEFAULT_FIELD_DETAIL_LEVELS,
    DetailOverrides,
    FixedDetailPolicy,
    PolarPlanisphereDetailPolicy,
    ResolvedDetail,
)
from wenu.charts.style_components import StellarMagnitudeSizing
from wenu.charts.view_defaults import CHART_VIEW_DEFAULTS, chart_view_defaults
from wenu.charts.regional import RegionalChart
from wenu import compose_chart
from wenu.configuration import (
    ConfigurationError,
    load_packaged_defaults,
    packaged_geometry_detail_defaults,
    translate_geometry_detail_defaults,
    validate_configuration,
)


def test_packaged_family_geometry_translates_with_exact_parity():
    defaults = translate_geometry_detail_defaults()
    assert isinstance(defaults.view_defaults, MappingProxyType)
    assert dict(defaults.view_defaults) == dict(CHART_VIEW_DEFAULTS)

    with pytest.raises(TypeError):
        defaults.view_defaults["binocular"] = CHART_VIEW_DEFAULTS["binocular"]


def test_family_geometry_gateway_uses_cached_packaged_authority():
    packaged_geometry_detail_defaults.cache_clear()
    defaults = packaged_geometry_detail_defaults()
    assert defaults is packaged_geometry_detail_defaults()
    assert chart_view_defaults("binocular") is defaults.view_defaults[
        "binocular"
    ]
    assert chart_view_defaults("regional", group=True) is (
        defaults.view_defaults["regional-group"]
    )


def test_packaged_neutral_content_and_cartoon_detail_have_parity():
    defaults = translate_geometry_detail_defaults()
    assert defaults.neutral_detail == ResolvedDetail()
    assert defaults.default_content_layers == DEFAULT_CONTENT_LAYERS
    assert defaults.cartoon_content_layers == CARTOON_CONTENT_LAYERS
    assert defaults.cartoon_policy == CartoonDetailPolicy()
    assert defaults.cartoon_policy.galaxy_magnitude_limit == pytest.approx(8.0)
    assert defaults.cartoon_policy.minimum_open_cluster_size_arcmin == (
        pytest.approx(60.0)
    )
    assert defaults.cartoon_policy.minimum_globular_cluster_size_arcmin == (
        pytest.approx(30.0)
    )


def test_packaged_adaptive_levels_and_family_ceilings_have_parity():
    defaults = translate_geometry_detail_defaults()
    assert defaults.adaptive_policy == AdaptiveDetailPolicy()
    assert defaults.adaptive_policy.levels == DEFAULT_FIELD_DETAIL_LEVELS
    assert dict(defaults.family_atlas_policies) == {
        "all_sky": AdaptiveDetailPolicy(star_magnitude_limit=5.0),
        "planisphere": AdaptiveDetailPolicy(star_magnitude_limit=5.0),
        "regional": AdaptiveDetailPolicy(star_magnitude_limit=6.5),
        "circumpolar": AdaptiveDetailPolicy(star_magnitude_limit=6.5),
    }
    assert defaults.polar_planisphere_policy == (
        PolarPlanisphereDetailPolicy()
    )


def test_packaged_binocular_detail_and_stellar_sizing_have_parity():
    defaults = translate_geometry_detail_defaults()
    common = {
        "star_magnitude_limit": 11.0,
        "galaxy_magnitude_limit": 11.0,
    }
    assert defaults.binocular_globular_policy == FixedDetailPolicy(
        ResolvedDetail(**common, extended_object_samples=73)
    )
    assert defaults.binocular_other_policy == FixedDetailPolicy(
        ResolvedDetail(**common, extended_object_samples=97)
    )
    assert defaults.binocular_stellar_sizing == StellarMagnitudeSizing(
        reference="limiting_magnitude",
        scale=1.0,
        exponent=0.35,
        minimum_area=1.0,
        maximum_area=40.0,
    )


def test_named_composition_consumes_packaged_family_and_cartoon_detail(
    monkeypatch,
):
    defaults = packaged_geometry_detail_defaults()
    regional = defaults.family_atlas_policies["regional"]
    configured = replace(
        defaults,
        family_atlas_policies=MappingProxyType({
            **defaults.family_atlas_policies,
            "regional": replace(
                regional,
                levels=tuple(
                    replace(level, label_density=1.7)
                    for level in regional.levels
                ),
                default_content_layers=frozenset({"stars", "galaxies"}),
            ),
        }),
        cartoon_policy=replace(
            defaults.cartoon_policy,
            bright_star_magnitude_limit=2.4,
            cartoon_content_layers=frozenset({"stars"}),
        ),
        default_content_layers=frozenset({"stars", "galaxies"}),
    )
    monkeypatch.setattr(
        "wenu.charts.composition._geometry_detail_defaults",
        lambda: configured,
    )
    chart = RegionalChart(
        center_alt_deg=45.0,
        center_az_deg=180.0,
        field_width_deg=30.0,
        field_height_deg=20.0,
    )

    atlas = compose_chart(chart, style="atlas", mode="print")
    cartoon = compose_chart(chart, style="cartoon", mode="print")
    assert atlas.detail.label_density == 1.7
    assert cartoon.detail.star_magnitude_limit == 2.4
    assert cartoon.detail.enabled_layers == frozenset({"stars"})

    additions = compose_chart(
        chart,
        style="atlas",
        mode="print",
        detail_overrides=DetailOverrides(
            enabled_layer_additions=frozenset({"open_clusters"})
        ),
    )
    assert additions.detail.enabled_layers == frozenset(
        {"stars", "galaxies", "open_clusters"}
    )

    explicit = FixedDetailPolicy(
        ResolvedDetail(star_magnitude_limit=9.0)
    )
    overridden = compose_chart(
        chart,
        style="atlas",
        mode="print",
        detail=explicit,
    )
    assert overridden.detail.star_magnitude_limit == 9.0


def test_translated_policies_carry_configured_content_layer_sets():
    values = load_packaged_defaults()
    values["detail"]["content"]["default_layers"] = ["stars", "galaxies"]
    values["detail"]["content"]["cartoon_layers"] = ["stars"]
    defaults = translate_geometry_detail_defaults(values)

    assert defaults.adaptive_policy.default_content_layers == frozenset(
        {"stars", "galaxies"}
    )
    assert defaults.cartoon_policy.cartoon_content_layers == frozenset(
        {"stars"}
    )


def test_translation_carries_restrained_cartoon_deep_sky_limits():
    values = load_packaged_defaults()
    cartoon = values["detail"]["cartoon"]
    cartoon["galaxy_magnitude_limit"] = 7.5
    cartoon["open_cluster_minimum_size"] = 75.0
    cartoon["globular_cluster_minimum_size"] = 40.0

    policy = translate_geometry_detail_defaults(values).cartoon_policy

    assert policy.galaxy_magnitude_limit == pytest.approx(7.5)
    assert policy.minimum_open_cluster_size_arcmin == pytest.approx(75.0)
    assert policy.minimum_globular_cluster_size_arcmin == pytest.approx(40.0)


def test_translation_carries_optional_regional_field_geometry():
    values = load_packaged_defaults()
    values["families"]["regional_single"].update(width=12.0, height=8.0)
    defaults = translate_geometry_detail_defaults(values)

    regional = defaults.view_defaults["regional-single"]
    assert regional.field_width_deg == 12.0
    assert regional.field_height_deg == 8.0


@pytest.mark.parametrize(
    ("path", "value", "diagnostic"),
    (
        (
            ("detail", "neutral", "extra_stars"),
            ["123"],
            "detail.neutral.extra_stars: array values must be integers",
        ),
        (
            ("detail", "neutral", "enabled_layers"),
            [1],
            "detail.neutral.enabled_layers: array values must be strings",
        ),
        (
            (
                "grids_references",
                "coordinate_grid",
                "requested_longitudes",
            ),
            ["zero"],
            "requested_longitudes: array values must be finite numbers",
        ),
    ),
)
def test_empty_or_optional_list_element_types_are_strict(
    path, value, diagnostic
):
    values = load_packaged_defaults()
    target = values
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(ConfigurationError) as error:
        validate_configuration(values)
    assert diagnostic in str(error.value)
