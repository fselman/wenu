"""Contracts for the first drawable resolved Venus disk."""

from argparse import Namespace
from types import SimpleNamespace

import numpy as np
import pytest

from wenu.charts.chart_arguments import chart_disk_options
from wenu.charts.request_disks import SolarSystemDiskDisplayRequest
from wenu.charts.solar_system_disk_preparation import MagnifyProjectedDisk
from wenu.geometry.projected import (
    ProjectedCurve,
    ProjectedCurves,
    ProjectedPoints,
    ProjectedPolygon,
    ProjectedPolygons,
)
from wenu.sky.semantic_identity import semantic_layer_identity
from wenu.sky.venus_disk import venus_disk_layers


def arguments(*, appearances=(), magnifications=()):
    return Namespace(
        planet_appearance=list(appearances),
        planet_disk_magnification=list(magnifications),
    )


def test_cli_resolves_object_specific_post_projection_magnification():
    assert chart_disk_options(
        arguments(
            appearances=("venus=resolved",),
            magnifications=("venus=40",),
        )
    ) == (SolarSystemDiskDisplayRequest("venus", 40.0),)


def test_resolved_appearance_defaults_to_physical_scale():
    assert chart_disk_options(
        arguments(appearances=("venus=resolved",))
    )[0].magnification == 1.0


def test_magnification_cannot_silently_enable_a_disk():
    with pytest.raises(
        ValueError,
        match="requires resolved appearance",
    ):
        chart_disk_options(
            arguments(magnifications=("venus=40",))
        )


@pytest.mark.parametrize("factor", (0, float("inf"), 1001))
def test_disk_magnification_is_governed(factor):
    with pytest.raises(ValueError):
        SolarSystemDiskDisplayRequest("venus", factor)


def test_component_layers_share_one_realization_and_magnification():
    layers = venus_disk_layers(magnification=40)
    assert tuple(layer.layer_name for layer in layers) == (
        "venus_disk_illuminated",
        "venus_disk_limb",
        "venus_disk_terminator",
    )
    assert len({id(layer.disk_realization) for layer in layers}) == 1
    assert {layer.magnification for layer in layers} == {40.0}


def test_curve_magnification_preserves_exact_projected_centre():
    realization = SimpleNamespace(
        transformed=SimpleNamespace(centre=object())
    )
    preparation = MagnifyProjectedDisk(realization, 4.0)
    projected = ProjectedCurves([
        ProjectedCurve(
            x=np.asarray((1.0, 3.0)),
            y=np.asarray((2.0, 4.0)),
        )
    ])

    def project(value):
        assert value is realization.transformed.centre
        return ProjectedPoints(
            x=np.asarray((1.0,)),
            y=np.asarray((2.0,)),
        )

    result = preparation.bind_project_geometry(project)(None, projected)
    assert np.allclose(result[0].x, (1.0, 9.0))
    assert np.allclose(result[0].y, (2.0, 10.0))
    assert result.metadata["display_magnification"] == 4.0


def test_polygon_magnification_preserves_component_identity():
    realization = SimpleNamespace(
        transformed=SimpleNamespace(centre=object())
    )
    preparation = MagnifyProjectedDisk(realization, 2.0)
    projected = ProjectedPolygons([
        ProjectedPolygon(
            x=np.asarray((0.0, 1.0, 0.0)),
            y=np.asarray((0.0, 0.0, 1.0)),
            name="illuminated",
        )
    ])
    project = lambda value: ProjectedPoints(
        x=np.asarray((0.0,)), y=np.asarray((0.0,))
    )
    result = preparation.bind_project_geometry(project)(None, projected)
    assert result[0].name == "illuminated"
    assert np.allclose(result[0].x, (0.0, 2.0, 0.0))
    assert np.allclose(result[0].y, (0.0, 0.0, 2.0))


def test_disk_components_have_independent_semantic_paths():
    identities = tuple(
        semantic_layer_identity(layer)
        for layer in venus_disk_layers()
    )
    assert tuple(identity.semantic_path_text for identity in identities) == (
        "sky/solar_system/planets/venus/disk/illuminated",
        "sky/solar_system/planets/venus/disk/limb",
        "sky/solar_system/planets/venus/disk/terminator",
    )
