"""Drawable observed Venus disk sequence contracts."""

from argparse import Namespace
from types import SimpleNamespace

import numpy as np

from wenu.charts.chart_arguments import chart_disk_options, chart_disk_sequence_options
from wenu.charts.request_disks import ObservedSolarSystemDiskSequenceDisplayRequest
from wenu.charts.solar_system_disk_preparation import MagnifyProjectedDiskSequence
from wenu.geometry.projected import ProjectedCurve, ProjectedCurves, ProjectedPoints
from wenu.sky.semantic_identity import semantic_layer_identity
from wenu.sky.venus_disk_sequence import observed_venus_disk_sequence_layers


def arguments(**values):
    defaults = {
        "planet_appearance": [],
        "planet_disk_magnification": ["venus=200"],
        "planet_disk_sequence": "venus",
        "disk_sequence_model": "observed",
        "disk_sequence_start": "2026-08-30T00:00:00Z",
        "disk_sequence_step": 28.0,
        "disk_sequence_n_steps": 3,
        "disk_sequence_labels": True,
    }
    defaults.update(values)
    return Namespace(**defaults)


def test_cli_builds_start_inclusive_observed_sequence_without_minor_step():
    value = chart_disk_sequence_options(arguments())
    assert isinstance(value, ObservedSolarSystemDiskSequenceDisplayRequest)
    assert value.sequence.sample_count == 4
    assert value.sequence.sample_offsets_days == (0.0, 28.0, 56.0, 84.0)
    assert value.magnification == 200.0
    assert value.label_dates is True
    assert chart_disk_options(arguments()) == ()


def test_sequence_layers_share_state_and_have_stable_semantics():
    request = chart_disk_sequence_options(arguments())
    layers = observed_venus_disk_sequence_layers(
        request.sequence,
        magnification=request.magnification,
        label_dates=True,
    )
    assert tuple(layer.layer_name for layer in layers) == (
        "venus_disk_sequence_illuminated",
        "venus_disk_sequence_limb",
        "venus_disk_sequence_terminator",
        "venus_disk_sequence_labels",
    )
    assert len({id(layer.disk_realization) for layer in layers}) == 1
    assert tuple(
        semantic_layer_identity(layer).semantic_path_text for layer in layers
    ) == (
        "sky/solar_system/planets/venus/disk_sequence/illuminated",
        "sky/solar_system/planets/venus/disk_sequence/limb",
        "sky/solar_system/planets/venus/disk_sequence/terminator",
        "sky/solar_system/planets/venus/disk_sequence/labels",
    )


def test_post_projection_magnification_uses_each_physical_centre():
    realization = SimpleNamespace(
        transformed=SimpleNamespace(centres=object())
    )
    preparation = MagnifyProjectedDiskSequence(realization, 3.0)
    projected = ProjectedCurves([
        ProjectedCurve(x=np.asarray((0.0, 1.0)), y=np.asarray((0.0, 0.0))),
        ProjectedCurve(x=np.asarray((10.0, 11.0)), y=np.asarray((5.0, 5.0))),
    ])

    def project(value):
        assert value is realization.transformed.centres
        return ProjectedPoints(
            x=np.asarray((0.0, 10.0)),
            y=np.asarray((0.0, 5.0)),
        )

    result = preparation.bind_project_geometry(project)(None, projected)
    assert np.allclose(result[0].x, (0.0, 3.0))
    assert np.allclose(result[1].x, (10.0, 13.0))
    assert np.allclose(result[1].y, (5.0, 5.0))
    assert result.metadata["display_magnification"] == 3.0
