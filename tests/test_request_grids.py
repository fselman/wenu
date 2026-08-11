"""Request-time semantic grid configuration contracts."""

from pathlib import Path

import pytest

from wenu import (
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
    ("family", "step", "samples"),
    (
        ("planisphere", 30, 1441),
        ("regional", 15, 721),
        ("circumpolar", 30, 1441),
        ("binocular", 5, 721),
    ),
)
def test_family_grid_density_matches_canonical_examples(
    family, step, samples
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
    assert second[0].ra == tuple(range(0, 360, 5))


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


def test_grid_configuration_rejects_untyped_inputs():
    with pytest.raises(TypeError, match="ChartRequest"):
        configure_chart_request_grids(CelestialSphere(object()), object())
