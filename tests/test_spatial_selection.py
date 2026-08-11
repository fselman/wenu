"""Automatic render-local catalogue selection by chart footprint."""

from pathlib import Path
from types import SimpleNamespace

import numpy as np

from wenu import (
    CANONICAL_MAXIMAL_SPHERE_PROFILE,
    ChartContentExclusions,
    ChartObserverRequest,
    ChartProductOptions,
    ChartRequest,
    ChartSubjectRequest,
    SkyContentSelection,
    resolve_chart_request,
    select_spatial_chart_content,
)
from wenu.geometry.spherical import SphericalPoints
from wenu.geometry.projected import ProjectedCurve
from wenu.geometry.viewport import Viewport


class Projection:
    def project_spherical(self, longitude, latitude):
        return np.asarray(longitude), np.asarray(latitude)


class Layer:
    def __init__(self, identifiers, longitude, latitude):
        self.geometry = SphericalPoints(
            np.asarray(longitude), np.asarray(latitude),
            ids=np.asarray(identifiers, dtype=object),
        )

    def spherical_geometry(self, observer):
        return self.geometry


def resolved(*, exclusions=None):
    request = ChartRequest(
        observer=ChartObserverRequest(
            location="La Ligua", time="2026-08-15 22:00"
        ),
        family="binocular",
        subject=ChartSubjectRequest(target="M57"),
        content=SkyContentSelection(open_clusters={"explicit"}),
        exclusions=exclusions or ChartContentExclusions(),
        product=ChartProductOptions(output=Path("output/chart.png")),
    )
    return resolve_chart_request(
        request, CANONICAL_MAXIMAL_SPHERE_PROFILE
    )


def test_field_selection_unions_visible_and_explicit_identifiers():
    sky = SimpleNamespace(
        observer=object(),
        nonstellar=None,
        galaxies=None,
        open_clusters=Layer(
            ["inside", "outside"], [0.0, 5.0], [0.0, 0.0]
        ),
        globular_clusters=None,
        planetary_nebulae=Layer(
            ["PN G063.1+13.9", "other"], [0.0, 5.0], [0.0, 0.0]
        ),
        supernova_remnants=None,
    )
    chart = SimpleNamespace(
        projection=Projection(),
        viewport=Viewport.centered(width=2.0, height=2.0),
    )

    selected = select_spatial_chart_content(sky, chart, resolved())

    assert selected.request.content.open_clusters == {
        "inside", "explicit"
    }
    assert selected.request.content.planetary_nebulae == {
        "PN G063.1+13.9"
    }


def test_spatial_selection_is_immutable_and_repeatable():
    original = resolved()
    sky = SimpleNamespace(
        observer=object(),
        **{
            attribute: None
            for attribute in (
                "nonstellar", "galaxies", "open_clusters",
                "globular_clusters", "planetary_nebulae",
                "supernova_remnants",
            )
        },
    )
    chart = SimpleNamespace(
        projection=Projection(),
        viewport=Viewport.centered(width=2.0, height=2.0),
    )

    first = select_spatial_chart_content(sky, chart, original)
    second = select_spatial_chart_content(sky, chart, original)

    assert first == second
    assert original.request.content.open_clusters == {"explicit"}


def test_explicit_exclusions_override_automatic_field_selection():
    sky = SimpleNamespace(
        observer=object(),
        nonstellar=None,
        galaxies=None,
        open_clusters=Layer(
            ["retained", "excluded"], [0.0, 0.5], [0.0, 0.0]
        ),
        globular_clusters=None,
        planetary_nebulae=Layer(
            ["PN G063.1+13.9"], [0.0], [0.0]
        ),
        supernova_remnants=None,
    )
    chart = SimpleNamespace(
        projection=Projection(),
        viewport=Viewport.centered(width=2.0, height=2.0),
    )
    request = resolved(
        exclusions=ChartContentExclusions(open_clusters={"excluded"})
    )

    selected = select_spatial_chart_content(sky, chart, request)

    assert selected.request.content.open_clusters == {
        "retained", "explicit"
    }
    assert request.request.exclusions.open_clusters == {"excluded"}


def test_full_sky_horizon_limits_automatic_selection():
    sky = SimpleNamespace(
        observer=object(),
        nonstellar=None,
        galaxies=None,
        open_clusters=Layer(
            ["inside", "corner"], [0.5, 1.5], [0.0, 1.5]
        ),
        globular_clusters=None,
        planetary_nebulae=Layer(
            ["PN G063.1+13.9"], [0.0], [0.0]
        ),
        supernova_remnants=None,
    )
    chart = SimpleNamespace(
        projection=Projection(),
        viewport=Viewport.centered(width=4.0, height=4.0),
        horizon=ProjectedCurve(
            x=[-2.0, 0.0, 2.0, 0.0],
            y=[0.0, 2.0, 0.0, -2.0],
            closed=True,
        ),
    )

    selected = select_spatial_chart_content(sky, chart, resolved())

    assert selected.request.content.open_clusters == {"inside", "explicit"}
