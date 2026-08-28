from __future__ import annotations

import numpy as np
import pytest

from wenu.coordinates import CoordinateSpec, GENERIC_SPHERICAL_SPEC

from wenu.geometry.spherical import (
    SphericalCurves,
    SphericalGrid,
    SphericalPoints,
    SphericalPolygons,
)


def test_coordinate_spec_is_required() -> None:
    with pytest.raises(TypeError, match="coordinate_spec"):
        SphericalPoints(lon_deg=[], lat_deg=[])


def test_coordinate_spec_must_be_typed() -> None:
    with pytest.raises(TypeError, match="CoordinateSpec"):
        SphericalPoints(
            lon_deg=[],
            lat_deg=[],
            coordinate_spec="altaz",
        )


def test_grid_rejects_component_in_another_coordinate_system() -> None:
    curves = SphericalCurves(
        lon_deg=(),
        lat_deg=(),
        coordinate_spec=GENERIC_SPHERICAL_SPEC,
    )
    altaz = CoordinateSpec(frame="altaz", origin="observer")
    with pytest.raises(ValueError, match="different coordinate spec"):
        SphericalGrid(
            components={"curves": curves},
            coordinate_spec=altaz,
        )


class TestSphericalPoints:
    def test_constructs_from_python_sequences(self) -> None:
        points = SphericalPoints(coordinate_spec=GENERIC_SPHERICAL_SPEC,
            lon_deg=[10.0, 20.0, 30.0],
            lat_deg=[-5.0, 0.0, 5.0],
        )

        np.testing.assert_array_equal(
            points.lon_deg,
            np.array([10.0, 20.0, 30.0]),
        )
        np.testing.assert_array_equal(
            points.lat_deg,
            np.array([-5.0, 0.0, 5.0]),
        )

        assert points.lon_deg.dtype == float
        assert points.lat_deg.dtype == float
        assert len(points) == 3

    def test_accepts_empty_collection(self) -> None:
        points = SphericalPoints(coordinate_spec=GENERIC_SPHERICAL_SPEC,
            lon_deg=[],
            lat_deg=[],
        )

        assert len(points) == 0
        assert points.finite.size == 0

    def test_accepts_single_point_collection(self) -> None:
        points = SphericalPoints(coordinate_spec=GENERIC_SPHERICAL_SPEC,
            lon_deg=[42.0],
            lat_deg=[-17.0],
        )

        assert len(points) == 1
        assert points.lon_deg[0] == pytest.approx(42.0)
        assert points.lat_deg[0] == pytest.approx(-17.0)

    def test_preserves_entity_data(self) -> None:
        points = SphericalPoints(coordinate_spec=GENERIC_SPHERICAL_SPEC,
            lon_deg=[10.0, 20.0],
            lat_deg=[-10.0, 10.0],
            ids=[101, 102],
            labels=["A", "B"],
            names=["Alpha", "Beta"],
        )

        np.testing.assert_array_equal(
            points.ids,
            np.array([101, 102], dtype=object),
        )
        np.testing.assert_array_equal(
            points.labels,
            np.array(["A", "B"], dtype=object),
        )
        np.testing.assert_array_equal(
            points.names,
            np.array(["Alpha", "Beta"], dtype=object),
        )

    def test_copies_metadata_mapping(self) -> None:
        metadata = {"frame": "generic"}

        points = SphericalPoints(coordinate_spec=GENERIC_SPHERICAL_SPEC,
            lon_deg=[0.0],
            lat_deg=[0.0],
            metadata=metadata,
        )

        assert points.metadata == {"frame": "generic"}
        assert points.metadata is not metadata

    def test_finite_mask_requires_both_coordinates_to_be_finite(
        self,
    ) -> None:
        points = SphericalPoints(coordinate_spec=GENERIC_SPHERICAL_SPEC,
            lon_deg=[0.0, np.nan, 2.0, np.inf],
            lat_deg=[0.0, 1.0, np.inf, 3.0],
        )

        np.testing.assert_array_equal(
            points.finite,
            np.array([True, False, False, False]),
        )

    def test_rejects_non_one_dimensional_longitude(self) -> None:
        with pytest.raises(
            ValueError,
            match="lon_deg must be a one-dimensional array",
        ):
            SphericalPoints(coordinate_spec=GENERIC_SPHERICAL_SPEC,
                lon_deg=[[0.0, 1.0]],
                lat_deg=[0.0, 1.0],
            )

    def test_rejects_non_one_dimensional_latitude(self) -> None:
        with pytest.raises(
            ValueError,
            match="lat_deg must be a one-dimensional array",
        ):
            SphericalPoints(coordinate_spec=GENERIC_SPHERICAL_SPEC,
                lon_deg=[0.0, 1.0],
                lat_deg=[[0.0, 1.0]],
            )

    def test_rejects_coordinate_shape_mismatch(self) -> None:
        with pytest.raises(
            ValueError,
            match="lon_deg and lat_deg must have the same shape",
        ):
            SphericalPoints(coordinate_spec=GENERIC_SPHERICAL_SPEC,
                lon_deg=[0.0, 1.0],
                lat_deg=[0.0],
            )

    @pytest.mark.parametrize(
        "field_name",
        ["ids", "labels", "names"],
    )
    def test_rejects_entity_data_with_wrong_length(
        self,
        field_name: str,
    ) -> None:
        arguments = {
            "lon_deg": [0.0, 1.0],
            "lat_deg": [0.0, 1.0],
            field_name: ["only-one"],
        }

        with pytest.raises(
            ValueError,
            match=rf"{field_name} must contain one value per entity",
        ):
            SphericalPoints(coordinate_spec=GENERIC_SPHERICAL_SPEC, **arguments)

    @pytest.mark.parametrize(
        "field_name",
        ["ids", "labels", "names"],
    )
    def test_rejects_non_one_dimensional_entity_data(
        self,
        field_name: str,
    ) -> None:
        arguments = {
            "lon_deg": [0.0, 1.0],
            "lat_deg": [0.0, 1.0],
            field_name: [["A", "B"]],
        }

        with pytest.raises(
            ValueError,
            match=rf"{field_name} must be a one-dimensional array",
        ):
            SphericalPoints(coordinate_spec=GENERIC_SPHERICAL_SPEC, **arguments)


class TestSphericalCurves:
    def test_constructs_curve_collection(self) -> None:
        curves = SphericalCurves(coordinate_spec=GENERIC_SPHERICAL_SPEC,
            lon_deg=(
                np.array([0.0, 1.0, 2.0]),
                np.array([10.0, 20.0]),
            ),
            lat_deg=(
                np.array([3.0, 4.0, 5.0]),
                np.array([-10.0, -20.0]),
            ),
        )

        assert len(curves) == 2
        assert isinstance(curves.lon_deg, tuple)
        assert isinstance(curves.lat_deg, tuple)

        np.testing.assert_array_equal(
            curves.closed,
            np.array([False, False]),
        )

    def test_converts_nested_sequences_to_coordinate_arrays(self) -> None:
        curves = SphericalCurves(coordinate_spec=GENERIC_SPHERICAL_SPEC,
            lon_deg=([0.0, 1.0], [2.0, 3.0]),
            lat_deg=([4.0, 5.0], [6.0, 7.0]),
        )

        assert all(
            isinstance(values, np.ndarray)
            for values in curves.lon_deg
        )
        assert all(
            values.dtype == float
            for values in curves.lon_deg
        )

    def test_accepts_empty_collection(self) -> None:
        curves = SphericalCurves(coordinate_spec=GENERIC_SPHERICAL_SPEC,
            lon_deg=(),
            lat_deg=(),
        )

        assert len(curves) == 0
        assert curves.closed.size == 0
        assert curves.finite == ()

    def test_accepts_single_curve_collection(self) -> None:
        curves = SphericalCurves(coordinate_spec=GENERIC_SPHERICAL_SPEC,
            lon_deg=([0.0, 1.0],),
            lat_deg=([2.0, 3.0],),
        )

        assert len(curves) == 1

    def test_preserves_closed_flags_and_entity_data(self) -> None:
        curves = SphericalCurves(coordinate_spec=GENERIC_SPHERICAL_SPEC,
            lon_deg=(
                [0.0, 1.0],
                [10.0, 20.0],
            ),
            lat_deg=(
                [2.0, 3.0],
                [30.0, 40.0],
            ),
            closed=[False, True],
            ids=["curve-1", "curve-2"],
            labels=["C1", "C2"],
            names=["First", "Second"],
        )

        np.testing.assert_array_equal(
            curves.closed,
            np.array([False, True]),
        )
        np.testing.assert_array_equal(
            curves.ids,
            np.array(["curve-1", "curve-2"], dtype=object),
        )
        np.testing.assert_array_equal(
            curves.labels,
            np.array(["C1", "C2"], dtype=object),
        )
        np.testing.assert_array_equal(
            curves.names,
            np.array(["First", "Second"], dtype=object),
        )

    def test_returns_one_finite_mask_per_curve(self) -> None:
        curves = SphericalCurves(coordinate_spec=GENERIC_SPHERICAL_SPEC,
            lon_deg=(
                [0.0, np.nan, 2.0],
                [10.0, 20.0],
            ),
            lat_deg=(
                [3.0, 4.0, np.inf],
                [30.0, 40.0],
            ),
        )

        finite = curves.finite

        assert isinstance(finite, tuple)
        assert len(finite) == 2

        np.testing.assert_array_equal(
            finite[0],
            np.array([True, False, False]),
        )
        np.testing.assert_array_equal(
            finite[1],
            np.array([True, True]),
        )

    def test_rejects_different_numbers_of_coordinate_arrays(
        self,
    ) -> None:
        with pytest.raises(
            ValueError,
            match=(
                "lon_deg and lat_deg must contain "
                "the same number of curves"
            ),
        ):
            SphericalCurves(coordinate_spec=GENERIC_SPHERICAL_SPEC,
                lon_deg=([0.0, 1.0], [2.0, 3.0]),
                lat_deg=([4.0, 5.0],),
            )

    def test_rejects_curve_coordinate_shape_mismatch(self) -> None:
        with pytest.raises(
            ValueError,
            match=(
                "Longitude and latitude arrays for curve 0 "
                "must have the same shape"
            ),
        ):
            SphericalCurves(coordinate_spec=GENERIC_SPHERICAL_SPEC,
                lon_deg=([0.0, 1.0, 2.0],),
                lat_deg=([3.0, 4.0],),
            )

    def test_rejects_curve_with_fewer_than_two_samples(self) -> None:
        with pytest.raises(
            ValueError,
            match="Curve 0 requires at least two samples",
        ):
            SphericalCurves(coordinate_spec=GENERIC_SPHERICAL_SPEC,
                lon_deg=([0.0],),
                lat_deg=([1.0],),
            )

    def test_rejects_non_one_dimensional_curve_coordinates(
        self,
    ) -> None:
        with pytest.raises(
            ValueError,
            match=r"lon_deg\[0\] must be a one-dimensional array",
        ):
            SphericalCurves(coordinate_spec=GENERIC_SPHERICAL_SPEC,
                lon_deg=([[0.0, 1.0]],),
                lat_deg=([2.0, 3.0],),
            )

    def test_rejects_non_one_dimensional_closed_flags(self) -> None:
        with pytest.raises(
            ValueError,
            match="closed must be a one-dimensional array",
        ):
            SphericalCurves(coordinate_spec=GENERIC_SPHERICAL_SPEC,
                lon_deg=([0.0, 1.0],),
                lat_deg=([2.0, 3.0],),
                closed=[[True]],
            )

    def test_rejects_wrong_number_of_closed_flags(self) -> None:
        with pytest.raises(
            ValueError,
            match="closed must contain one value per curve",
        ):
            SphericalCurves(coordinate_spec=GENERIC_SPHERICAL_SPEC,
                lon_deg=(
                    [0.0, 1.0],
                    [2.0, 3.0],
                ),
                lat_deg=(
                    [4.0, 5.0],
                    [6.0, 7.0],
                ),
                closed=[True],
            )

    @pytest.mark.parametrize(
        "field_name",
        ["ids", "labels", "names"],
    )
    def test_rejects_entity_data_with_wrong_length(
        self,
        field_name: str,
    ) -> None:
        arguments = {
            "lon_deg": ([0.0, 1.0], [2.0, 3.0]),
            "lat_deg": ([4.0, 5.0], [6.0, 7.0]),
            field_name: ["only-one"],
        }

        with pytest.raises(
            ValueError,
            match=rf"{field_name} must contain one value per entity",
        ):
            SphericalCurves(coordinate_spec=GENERIC_SPHERICAL_SPEC, **arguments)


class TestSphericalPolygons:
    def test_constructs_polygon_collection(self) -> None:
        polygons = SphericalPolygons(coordinate_spec=GENERIC_SPHERICAL_SPEC,
            lon_deg=(
                [0.0, 1.0, 2.0],
                [10.0, 20.0, 30.0, 40.0],
            ),
            lat_deg=(
                [3.0, 4.0, 5.0],
                [-10.0, -20.0, -30.0, -40.0],
            ),
        )

        assert len(polygons) == 2
        assert isinstance(polygons.lon_deg, tuple)
        assert isinstance(polygons.lat_deg, tuple)

    def test_accepts_empty_collection(self) -> None:
        polygons = SphericalPolygons(coordinate_spec=GENERIC_SPHERICAL_SPEC,
            lon_deg=(),
            lat_deg=(),
        )

        assert len(polygons) == 0
        assert polygons.finite == ()

    def test_accepts_single_polygon_collection(self) -> None:
        polygons = SphericalPolygons(coordinate_spec=GENERIC_SPHERICAL_SPEC,
            lon_deg=([0.0, 1.0, 2.0],),
            lat_deg=([3.0, 4.0, 5.0],),
        )

        assert len(polygons) == 1

    def test_preserves_entity_data(self) -> None:
        polygons = SphericalPolygons(coordinate_spec=GENERIC_SPHERICAL_SPEC,
            lon_deg=(
                [0.0, 1.0, 2.0],
                [10.0, 20.0, 30.0],
            ),
            lat_deg=(
                [3.0, 4.0, 5.0],
                [40.0, 50.0, 60.0],
            ),
            ids=["polygon-1", "polygon-2"],
            labels=["P1", "P2"],
            names=["First", "Second"],
        )

        np.testing.assert_array_equal(
            polygons.ids,
            np.array(["polygon-1", "polygon-2"], dtype=object),
        )
        np.testing.assert_array_equal(
            polygons.labels,
            np.array(["P1", "P2"], dtype=object),
        )
        np.testing.assert_array_equal(
            polygons.names,
            np.array(["First", "Second"], dtype=object),
        )

    def test_returns_one_finite_mask_per_polygon(self) -> None:
        polygons = SphericalPolygons(coordinate_spec=GENERIC_SPHERICAL_SPEC,
            lon_deg=(
                [0.0, np.nan, 2.0],
                [10.0, 20.0, 30.0],
            ),
            lat_deg=(
                [3.0, 4.0, np.inf],
                [40.0, 50.0, 60.0],
            ),
        )

        finite = polygons.finite

        assert isinstance(finite, tuple)
        assert len(finite) == 2

        np.testing.assert_array_equal(
            finite[0],
            np.array([True, False, False]),
        )
        np.testing.assert_array_equal(
            finite[1],
            np.array([True, True, True]),
        )

    def test_rejects_different_numbers_of_coordinate_arrays(
        self,
    ) -> None:
        with pytest.raises(
            ValueError,
            match=(
                "lon_deg and lat_deg must contain "
                "the same number of polygons"
            ),
        ):
            SphericalPolygons(coordinate_spec=GENERIC_SPHERICAL_SPEC,
                lon_deg=(
                    [0.0, 1.0, 2.0],
                    [3.0, 4.0, 5.0],
                ),
                lat_deg=([6.0, 7.0, 8.0],),
            )

    def test_rejects_polygon_coordinate_shape_mismatch(
        self,
    ) -> None:
        with pytest.raises(
            ValueError,
            match=(
                "Longitude and latitude arrays for polygon 0 "
                "must have the same shape"
            ),
        ):
            SphericalPolygons(coordinate_spec=GENERIC_SPHERICAL_SPEC,
                lon_deg=([0.0, 1.0, 2.0],),
                lat_deg=([3.0, 4.0, 5.0, 6.0],),
            )

    def test_rejects_polygon_with_fewer_than_three_vertices(
        self,
    ) -> None:
        with pytest.raises(
            ValueError,
            match="Polygon 0 requires at least three vertices",
        ):
            SphericalPolygons(coordinate_spec=GENERIC_SPHERICAL_SPEC,
                lon_deg=([0.0, 1.0],),
                lat_deg=([2.0, 3.0],),
            )

    def test_rejects_non_one_dimensional_polygon_coordinates(
        self,
    ) -> None:
        with pytest.raises(
            ValueError,
            match=r"lon_deg\[0\] must be a one-dimensional array",
        ):
            SphericalPolygons(coordinate_spec=GENERIC_SPHERICAL_SPEC,
                lon_deg=([[0.0, 1.0, 2.0]],),
                lat_deg=([3.0, 4.0, 5.0],),
            )

    @pytest.mark.parametrize(
        "field_name",
        ["ids", "labels", "names"],
    )
    def test_rejects_entity_data_with_wrong_length(
        self,
        field_name: str,
    ) -> None:
        arguments = {
            "lon_deg": (
                [0.0, 1.0, 2.0],
                [3.0, 4.0, 5.0],
            ),
            "lat_deg": (
                [6.0, 7.0, 8.0],
                [9.0, 10.0, 11.0],
            ),
            field_name: ["only-one"],
        }

        with pytest.raises(
            ValueError,
            match=rf"{field_name} must contain one value per entity",
        ):
            SphericalPolygons(coordinate_spec=GENERIC_SPHERICAL_SPEC, **arguments)
