from dataclasses import FrozenInstanceError

import pytest

from wenu import (
    AdaptiveDetailPolicy,
    AtlasChartStyle,
    BinocularChart,
    DetailOverrides,
    FieldDetailLevel,
    FullSkyChart,
    PrintMode,
    RegionalChart,
    compose_chart,
)


def regional(width, height):
    return RegionalChart(
        center_alt_deg=35.0,
        center_az_deg=210.0,
        field_width_deg=width,
        field_height_deg=height,
    )


def resolve(chart, *, width_inches=7.0, policy=None):
    policy = AdaptiveDetailPolicy() if policy is None else policy
    mode = PrintMode(width_inches=width_inches).resolve(
        chart.chart_context
    )
    return policy.resolve(chart.chart_context, mode)


def test_narrower_fields_receive_deeper_stellar_limits():
    full_sky = resolve(FullSkyChart())
    regional_detail = resolve(regional(30.0, 20.0))
    binocular = resolve(
        BinocularChart(
            center_alt_deg=35.0,
            center_az_deg=210.0,
            field_diameter_deg=6.5,
        )
    )
    assert (
        full_sky.star_magnitude_limit
        < regional_detail.star_magnitude_limit
        < binocular.star_magnitude_limit
    )
    assert full_sky.star_magnitude_limit == pytest.approx(
        6.19,
        abs=0.02,
    )
    assert binocular.star_magnitude_limit > 11.0


def test_field_coverage_not_aspect_ratio_drives_detail():
    square = resolve(regional(30.0, 20.0))
    wide = resolve(regional(60.0, 10.0))
    assert wide.star_magnitude_limit == pytest.approx(
        square.star_magnitude_limit
    )
    assert wide.minimum_open_cluster_size_arcmin == pytest.approx(
        square.minimum_open_cluster_size_arcmin
    )


def test_output_size_is_only_a_small_bounded_correction():
    chart = regional(30.0, 20.0)
    small = resolve(chart, width_inches=5.0)
    large = resolve(chart, width_inches=14.0)
    assert large.star_magnitude_limit > small.star_magnitude_limit
    assert (
        large.star_magnitude_limit
        - small.star_magnitude_limit
    ) < 0.6


def test_wide_fields_suppress_only_crowded_specialized_layers():
    detail = resolve(FullSkyChart())
    assert detail.layer_enabled("stars")
    assert detail.layer_enabled("milky_way")
    assert detail.layer_enabled("galaxies")
    assert not detail.layer_enabled("open_clusters")
    assert not detail.layer_enabled("planetary_nebulae")
    assert not detail.layer_enabled("supernova_remnants")


def test_explicit_layer_and_magnitude_overrides_have_final_precedence():
    enabled = frozenset(
        {
            "stars",
            "constellation_lines",
            "constellation_labels",
        }
    )
    composition = compose_chart(
        regional(30.0, 20.0),
        style=AtlasChartStyle(),
        detail=AdaptiveDetailPolicy(),
        detail_overrides=DetailOverrides(
            star_magnitude_limit=4.5,
            enabled_layers=enabled,
        ),
    )
    assert composition.detail.star_magnitude_limit == 4.5
    assert composition.detail.enabled_layers == enabled
    assert not composition.detail.layer_enabled("galaxies")


def test_custom_profile_is_interpolated_in_log_field_span():
    policy = AdaptiveDetailPolicy(
        levels=(
            FieldDetailLevel(
                10.0, 10.0, 12.0, 1.0, 1.0, 1.0, 1.0, 1.0
            ),
            FieldDetailLevel(
                40.0, 6.0, 10.0, 9.0, 9.0, 9.0, 9.0, 0.5
            ),
        ),
        output_magnitude_adjustment_per_octave=0.0,
        adapt_enabled_layers=False,
    )
    detail = resolve(regional(20.0, 20.0), policy=policy)
    assert detail.star_magnitude_limit == pytest.approx(8.0)
    assert detail.minimum_open_cluster_size_arcmin == pytest.approx(5.0)
    assert detail.enabled_layers is None


def test_adaptive_results_are_immutable():
    detail = resolve(regional(30.0, 20.0))
    with pytest.raises(FrozenInstanceError):
        detail.star_magnitude_limit = 12.0


def test_adaptive_detail_contract_has_no_backend_dependency():
    from pathlib import Path
    import wenu.charts.detail as detail_module

    source = Path(detail_module.__file__).read_text().lower()
    assert "matplotlib" not in source
