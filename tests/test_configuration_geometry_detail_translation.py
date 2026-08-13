"""Parity contracts for TOML geometry and detail translation."""

from types import MappingProxyType

import pytest

from wenu.charts.detail import (
    AdaptiveDetailPolicy,
    CARTOON_CONTENT_LAYERS,
    CartoonDetailPolicy,
    DEFAULT_CONTENT_LAYERS,
    DEFAULT_FIELD_DETAIL_LEVELS,
    FixedDetailPolicy,
    ResolvedDetail,
)
from wenu.charts.style_components import StellarMagnitudeSizing
from wenu.charts.view_defaults import CHART_VIEW_DEFAULTS
from wenu.configuration import (
    ConfigurationError,
    load_packaged_defaults,
    translate_geometry_detail_defaults,
    validate_configuration,
)


def test_packaged_family_geometry_translates_with_exact_parity():
    defaults = translate_geometry_detail_defaults()
    assert isinstance(defaults.view_defaults, MappingProxyType)
    assert dict(defaults.view_defaults) == dict(CHART_VIEW_DEFAULTS)

    with pytest.raises(TypeError):
        defaults.view_defaults["binocular"] = CHART_VIEW_DEFAULTS["binocular"]


def test_packaged_neutral_content_and_cartoon_detail_have_parity():
    defaults = translate_geometry_detail_defaults()
    assert defaults.neutral_detail == ResolvedDetail()
    assert defaults.default_content_layers == DEFAULT_CONTENT_LAYERS
    assert defaults.cartoon_content_layers == CARTOON_CONTENT_LAYERS
    assert defaults.cartoon_policy == CartoonDetailPolicy()


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
        exponent=0.20,
        minimum_area=1.0,
        maximum_area=40.0,
    )


def test_translation_rejects_geometry_not_owned_by_current_view_contract():
    values = load_packaged_defaults()
    values["families"]["regional_single"].update(width=12.0, height=8.0)
    with pytest.raises(ConfigurationError) as error:
        translate_geometry_detail_defaults(values)
    assert "families.regional_single.width" in str(error.value)


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
