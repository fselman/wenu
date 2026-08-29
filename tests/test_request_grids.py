"""Request-time semantic grid configuration contracts."""

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from astropy.time import Time

from wenu import (
    CelestialReferencePolicy,
    ChartObserverRequest,
    ChartProductOptions,
    ChartRequest,
    ChartSubjectRequest,
    DetailOverrides,
    configure_chart_request_grids,
    requested_coordinate_grids,
)
from wenu.sky.celestial_sphere import CelestialSphere
from wenu.sky.coordinate_grids import CoordinatesGrid


def request(family, *, detail=None):
    subjects = {
        "regional": ChartSubjectRequest(constellations=("Cru",)),
        "binocular": ChartSubjectRequest(target="centaurus-a"),
    }
    frame = None
    if family == "circumpolar":
        from wenu import ChartFrameRequest

        frame = ChartFrameRequest(limiting_declination_deg=-69.75)
    options = {
        "observer": ChartObserverRequest(
            location="La Ligua", time="2026-08-15 21:00"
        ),
        "family": family,
        "subject": subjects.get(family, ChartSubjectRequest()),
        "detail": detail or DetailOverrides(),
        "product": ChartProductOptions(output=Path("output/chart.png")),
    }
    if frame is not None:
        options["frame"] = frame
    if family == "all_sky":
        options.update(
            projection="mollweide", coordinate_frame="galactic"
        )
    return ChartRequest(**options)


def grids(sky):
    return tuple(
        layer for layer in sky.layers if isinstance(layer, CoordinatesGrid)
    )


def test_grid_selection_is_explicit_and_labels_imply_geometry():
    assert requested_coordinate_grids(DetailOverrides()) == frozenset()
    assert requested_coordinate_grids(
        DetailOverrides(grid_label_layers={"galactic_grid"})
    ) == {"galactic_grid"}
    assert requested_coordinate_grids(
        DetailOverrides(enabled_layers={"coordinate_grids"})
    ) == {
        "altaz_grid",
        "equatorial_grid",
        "ecliptic_grid",
        "galactic_grid",
    }


def test_individual_cli_addition_overrides_disabled_general_alias():
    detail = DetailOverrides(
        enabled_layer_additions={"equatorial_grid"},
        disabled_layers={
            "coordinate_grids",
            "altaz_grid",
            "ecliptic_grid",
            "galactic_grid",
        },
    )

    assert requested_coordinate_grids(detail) == {"equatorial_grid"}


@pytest.mark.parametrize(
    ("family", "frame", "step", "samples"),
    (
        ("planisphere", None, 30, 1441),
        ("all_sky", None, 30, 1441),
        ("regional", SimpleNamespace(
            field_width_deg=59.0, field_height_deg=40.0,
            field_diameter_deg=None, limiting_declination_deg=None,
        ), 15, 721),
        ("regional", SimpleNamespace(
            field_width_deg=60.0, field_height_deg=40.0,
            field_diameter_deg=None, limiting_declination_deg=None,
        ), 15, 721),
        ("circumpolar", SimpleNamespace(
            field_width_deg=None, field_height_deg=None,
            field_diameter_deg=None, limiting_declination_deg=-69.75,
        ), 30, 1441),
        ("binocular", SimpleNamespace(
            field_width_deg=None, field_height_deg=None,
            field_diameter_deg=6.5, limiting_declination_deg=None,
        ), 15, 721),
    ),
)
def test_view_grid_density_uses_resolved_angular_span(
    family, frame, step, samples
):
    sky = CelestialSphere(object())
    configured = configure_chart_request_grids(
        sky,
        request(
            family,
            detail=DetailOverrides(
                enabled_layer_additions={"coordinate_grids"}
            ),
        ),
        frame=frame,
    )

    assert tuple(grid.coordinate_system for grid in configured) == (
        "equatorial", "ecliptic", "galactic", "altaz"
    )
    assert all(grid.samples == samples for grid in configured)
    assert configured[0].ra == tuple(range(0, 360, step))
    assert configured[-1].azimuth == tuple(range(0, 360, step))
    assert all(
        not getattr(grid, "include_equator", False)
        and not getattr(grid, "include_ecliptic", False)
        and not getattr(grid, "include_plane", False)
        and not getattr(grid, "include_horizon", False)
        for grid in configured
    )


def test_reconfiguration_replaces_grids_without_accumulation():
    sky = CelestialSphere(object())
    selected = DetailOverrides(
        enabled_layer_additions={"equatorial_grid"}
    )

    first = configure_chart_request_grids(
        sky, request("regional", detail=selected)
    )
    second = configure_chart_request_grids(
        sky, request("binocular", detail=selected)
    )

    assert len(first) == len(second) == 1
    assert first[0] not in sky.layers
    assert grids(sky) == second
    assert second[0].ra == tuple(range(0, 360, 30))


def test_family_grid_policy_includes_all_sky_zero_and_two_hour_polar_ra():
    all_sky = configure_chart_request_grids(
        CelestialSphere(object()),
        request("all_sky", detail=DetailOverrides(
            enabled_layer_additions={"equatorial_grid"}
        )),
    )[0]
    circumpolar = configure_chart_request_grids(
        CelestialSphere(object()),
        request("circumpolar", detail=DetailOverrides(
            enabled_layer_additions={"equatorial_grid"}
        )),
        frame=SimpleNamespace(
            field_width_deg=None, field_height_deg=None,
            field_diameter_deg=None, limiting_declination_deg=-69.75,
        ),
    )[0]

    assert 0 in all_sky.dec
    assert circumpolar.ra == tuple(range(0, 360, 30))


def test_explicit_declination_step_adds_only_requested_polar_parallels():
    frame = SimpleNamespace(
        field_width_deg=None,
        field_height_deg=None,
        field_diameter_deg=None,
        limiting_declination_deg=-60.0,
    )
    grid = configure_chart_request_grids(
        CelestialSphere(object()),
        request(
            "circumpolar",
            detail=DetailOverrides(
                enabled_layer_additions={"equatorial_grid"},
                equatorial_declination_step_deg=10.0,
            ),
        ),
        frame=frame,
    )[0]

    assert grid.ra == tuple(range(0, 360, 30))
    assert grid.dec == (-80.0, -70.0)


@pytest.mark.parametrize("value", [0.0, -10.0, float("nan"), 91.0])
def test_detail_declination_step_rejects_invalid_values(value):
    with pytest.raises(ValueError, match="declination_step"):
        DetailOverrides(equatorial_declination_step_deg=value)


def test_all_sky_galactic_grid_uses_requested_meridians_and_parallels():
    grid = configure_chart_request_grids(
        CelestialSphere(object()),
        request(
            "all_sky",
            detail=DetailOverrides(
                enabled_layer_additions={"galactic_grid"}
            ),
        ),
    )[0]

    assert grid.longitude == tuple(range(0, 360, 45))
    assert grid.latitude == (-60, -30, 0, 30, 60)


def test_request_without_grids_clears_previous_request_geometry():
    sky = CelestialSphere(object())
    configure_chart_request_grids(
        sky,
        request(
            "planisphere",
            detail=DetailOverrides(
                enabled_layer_additions={"altaz_grid"}
            ),
        ),
    )

    configured = configure_chart_request_grids(
        sky, request("planisphere")
    )

    assert configured == ()
    assert grids(sky) == ()


def test_of_date_policy_accepts_the_explicit_view_observer():
    selected = DetailOverrides(
        enabled_layer_additions={"equatorial_grid", "ecliptic_grid"}
    )
    chart_request = replace(
        request("regional", detail=selected),
        reference_policy=CelestialReferencePolicy("of_date"),
    )
    instant = Time("2026-08-16T01:00:00", scale="utc")
    observer = SimpleNamespace(t_astropy=instant)

    configured = configure_chart_request_grids(
        CelestialSphere(object()), chart_request, observer=observer
    )

    assert configured[0].equinox == instant
    assert configured[1].equinox == instant


def test_grid_configuration_rejects_untyped_inputs():
    with pytest.raises(TypeError, match="ChartRequest"):
        configure_chart_request_grids(CelestialSphere(object()), object())
