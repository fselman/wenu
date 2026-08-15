"""Immutable projection-selection boundary."""

from dataclasses import FrozenInstanceError

import pytest

from wenu import ProjectionSelection
from wenu.projections import (
    MollweideProjection,
    PolarAzimuthalEquidistantProjection,
    StereographicProjection,
)


@pytest.mark.parametrize(
    ("name", "coordinate_frame", "kind", "geometry"),
    (
        ("stereographic", "horizontal", StereographicProjection, {}),
        ("mollweide", "galactic", MollweideProjection, {}),
        (
            "polar_azimuthal_equidistant",
            "equatorial",
            PolarAzimuthalEquidistantProjection,
            {"pole": "south", "position_angle_deg": 12.0},
        ),
    ),
)
def test_selection_builds_the_declared_projection_lazily(
    name,
    coordinate_frame,
    kind,
    geometry,
):
    selection = ProjectionSelection(name, coordinate_frame)

    projection = selection.build(radius=3.0, flip_ew=False, **geometry)

    assert isinstance(projection, kind)
    assert projection.radius == 3.0
    assert projection.flip_ew is False


def test_selection_is_normalized_immutable_and_isolated():
    first = ProjectionSelection(" STEREOGRAPHIC ", " HORIZONTAL ")
    second = ProjectionSelection(
        "polar_azimuthal_equidistant", "equatorial"
    )

    assert first.name == "stereographic"
    assert second.name == "polar_azimuthal_equidistant"
    assert first.build() is not first.build()
    with pytest.raises(FrozenInstanceError):
        first.name = "mollweide"


@pytest.mark.parametrize(
    ("name", "coordinate_frame"),
    (
        ("stereographic", "galactic"),
        ("mollweide", "horizontal"),
        ("polar_azimuthal_equidistant", "horizontal"),
    ),
)
def test_projection_and_coordinate_frame_must_match(
    name,
    coordinate_frame,
):
    with pytest.raises(ValueError, match="requires coordinate_frame"):
        ProjectionSelection(name, coordinate_frame)


def test_unknown_projection_is_explicit():
    with pytest.raises(ValueError, match="Unsupported projection"):
        ProjectionSelection("mercator", "equatorial")
