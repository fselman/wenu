"""Request-time semantic horizon lifecycle contracts."""

from pathlib import Path

import pytest

from wenu import (
    ChartObserverRequest,
    ChartProductOptions,
    ChartRequest,
    ChartSubjectRequest,
    DetailOverrides,
    HorizonReference,
    ResolvedDetail,
    configure_chart_request_grids,
    configure_chart_request_horizon,
)
from wenu.charts.detail_application import apply_resolved_detail
from wenu.sky.celestial_sphere import CelestialSphere
from wenu.sky.coordinate_grids import AltAzGrid


def request(
    family="regional",
    *,
    horizon=False,
    horizon_mask=False,
    detail=None,
):
    subject = (
        ChartSubjectRequest(constellations=("Cru",))
        if family == "regional"
        else ChartSubjectRequest()
    )
    return ChartRequest(
        observer=ChartObserverRequest(
            location="La Ligua", time="2026-08-15 21:00"
        ),
        family=family,
        subject=subject,
        horizon=horizon,
        horizon_mask=horizon_mask,
        detail=detail or DetailOverrides(),
        product=ChartProductOptions(output=Path("output/chart.png")),
    )


def horizons(sky):
    return tuple(
        layer for layer in sky.layers
        if isinstance(layer, HorizonReference)
    )


def test_selected_reference_registers_exactly_one_semantic_horizon():
    sky = CelestialSphere(object())

    configured = configure_chart_request_horizon(
        sky, request(horizon=True)
    )

    assert isinstance(configured, HorizonReference)
    assert horizons(sky) == (configured,)
    assert sky.horizon_reference is configured


def test_reconfiguration_replaces_reference_without_accumulation():
    sky = CelestialSphere(object())

    first = configure_chart_request_horizon(sky, request(horizon=True))
    second = configure_chart_request_horizon(sky, request(horizon=True))

    assert first not in sky.layers
    assert horizons(sky) == (second,)


def test_unselected_and_planisphere_requests_clear_prior_reference():
    sky = CelestialSphere(object())
    configure_chart_request_horizon(sky, request(horizon=True))

    assert configure_chart_request_horizon(sky, request()) is None
    assert horizons(sky) == ()
    assert sky.horizon_reference is None

    configure_chart_request_horizon(sky, request(horizon=True))
    assert configure_chart_request_horizon(
        sky, request("planisphere", horizon=True)
    ) is None
    assert horizons(sky) == ()


def test_horizon_mask_and_altaz_grid_do_not_imply_or_duplicate_reference():
    sky = CelestialSphere(object())
    value = request(
        horizon_mask=True,
        detail=DetailOverrides(
            enabled_layer_additions={"altaz_grid"}
        ),
    )

    configured_grids = configure_chart_request_grids(sky, value)
    configured_horizon = configure_chart_request_horizon(sky, value)

    assert configured_horizon is None
    assert horizons(sky) == ()
    assert len(configured_grids) == 1
    assert isinstance(configured_grids[0], AltAzGrid)
    assert configured_grids[0].include_horizon is False


def test_selected_horizon_is_independent_of_detail_density():
    sky = CelestialSphere(object())
    horizon = configure_chart_request_horizon(
        sky, request(horizon=True)
    )

    application = apply_resolved_detail(
        sky, ResolvedDetail(enabled_layers={"stars"})
    )

    assert application.layer_options[horizon]["enabled"] is True


def test_configuration_rejects_untyped_inputs():
    with pytest.raises(TypeError, match="ChartRequest"):
        configure_chart_request_horizon(CelestialSphere(object()), object())
