"""Drawable frozen-Earth ecliptic Venus sequence contracts."""

from argparse import Namespace

from wenu.charts.chart_arguments import chart_disk_sequence_options
from wenu.charts.drawing import _frozen_furniture, _frozen_title
from wenu.charts.furniture import (
    ChartFurnitureOptions,
    ReferenceAnnotations,
    ReferencePlaneAnnotation,
)
from wenu.charts.request_disks import FrozenEarthSolarSystemDiskSequenceDisplayRequest
from wenu.sky.frozen_earth_venus_disk_sequence import (
    frozen_earth_venus_disk_sequence_layers,
)
from wenu.sky.semantic_identity import semantic_layer_identity


def arguments(**values):
    defaults = {
        "planet_appearance": [],
        "planet_disk_magnification": ["venus=200"],
        "planet_disk_sequence": "venus",
        "disk_sequence_model": "frozen-earth-ecliptic",
        "disk_sequence_start": "2026-08-30T00:00:00Z",
        "disk_sequence_step": 28.0,
        "disk_sequence_n_steps": 3,
        "disk_sequence_labels": True,
    }
    defaults.update(values)
    return Namespace(**defaults)


def test_cli_builds_start_inclusive_frozen_sequence_without_minor_step():
    value = chart_disk_sequence_options(arguments())
    assert isinstance(value, FrozenEarthSolarSystemDiskSequenceDisplayRequest)
    assert value.model == "frozen-earth-ecliptic"
    assert value.sequence.sample_count == 4
    assert value.sequence.sample_offsets_days == (0.0, 28.0, 56.0, 84.0)
    assert value.magnification == 200.0
    assert value.label_dates is True


def test_frozen_layers_share_state_and_include_central_six_point_sun():
    request = chart_disk_sequence_options(arguments())
    layers = frozen_earth_venus_disk_sequence_layers(
        request.sequence,
        magnification=request.magnification,
        label_dates=True,
    )
    assert tuple(layer.layer_name for layer in layers) == (
        "venus_disk_sequence_frozen_illuminated",
        "venus_disk_sequence_frozen_limb",
        "venus_disk_sequence_frozen_terminator",
        "venus_disk_sequence_frozen_labels",
        "frozen_earth_sun",
    )
    assert len({id(layer.disk_realization) for layer in layers}) == 1
    assert semantic_layer_identity(layers[-1]).semantic_path_text == (
        "sky/solar_system/star/sun"
    )
    assert all(layer.magnification == 200.0 for layer in layers[:-1])
    assert layers[-1].magnification == 1.0


def test_frozen_component_semantics_are_distinct_from_observed_sequence():
    request = chart_disk_sequence_options(arguments())
    layers = frozen_earth_venus_disk_sequence_layers(request.sequence)
    assert tuple(
        semantic_layer_identity(layer).semantic_path_text for layer in layers[:3]
    ) == (
        "sky/solar_system/planets/venus/frozen_earth_sequence/illuminated",
        "sky/solar_system/planets/venus/frozen_earth_sequence/limb",
        "sky/solar_system/planets/venus/frozen_earth_sequence/terminator",
    )


def test_frozen_title_uses_resolved_language():
    assert _frozen_title("en") == "Frozen-Earth Venus sequence"
    assert _frozen_title("es") == "Secuencia de Venus desde una Tierra fija"


def test_frozen_furniture_preserves_only_requested_ecliptic_reference():
    ecliptic = ReferencePlaneAnnotation(
        state="labeled",
        label="Eclíptica",
    )
    source = ChartFurnitureOptions(
        references=ReferenceAnnotations(
            celestial_equator=ReferencePlaneAnnotation(
                state="labeled",
                label="Ecuador celeste",
            ),
            ecliptic=ecliptic,
            galactic_plane=ReferencePlaneAnnotation(
                state="labeled",
                label="Plano galáctico",
            ),
        ),
    )

    result = _frozen_furniture(source)

    assert result.references.ecliptic is ecliptic
    assert result.references.celestial_equator.state == "none"
    assert result.references.galactic_plane.state == "none"
    assert result.references.ecliptic_keypoints == "none"
    assert result.references.ecliptic_keypoint_legend is False
    assert result.legends is None
    assert result.context is None
