import numpy as np
import pandas as pd
import pytest

from wenu.objects.stars import Stars


class DummyProjection:
    def project(self, alt, az):
        alt = np.asarray(alt)
        az = np.asarray(az)
        return alt + 1.0, az - 1.0


def make_stars():
    stars = Stars(
        observer=object(),
        catalog="hipparcos",
        magnitude_limit=5.5,
    )

    stars.hip_df = pd.DataFrame(
        {
            "magnitude": [1.0, 3.0, 5.0],
        },
        index=[100, 200, 300],
    )

    return stars


def test_project_requires_altaz():
    stars = make_stars()

    with pytest.raises(
        RuntimeError,
        match="Alt/Az has not been computed",
    ):
        stars.project(DummyProjection())


def test_project_preserves_current_projection_contract():
    stars = make_stars()

    stars.alt = np.array([10.0, 20.0, 30.0])
    stars.az = np.array([40.0, 50.0, 60.0])

    projection = DummyProjection()

    x, y = stars.project(projection)

    np.testing.assert_allclose(
        x,
        [11.0, 21.0, 31.0],
    )
    np.testing.assert_allclose(
        y,
        [39.0, 49.0, 59.0],
    )

    assert stars.projection is projection
    assert isinstance(stars.x, np.ndarray)
    assert isinstance(stars.y, np.ndarray)


def test_compute_sizes_preserves_current_formula():
    stars = make_stars()

    sizes = stars.compute_sizes(
        scale=1.5,
        reference_magnitude=5.0,
        exponent=0.35,
        minimum=1.0,
    )

    expected = 1.5 * 10.0 ** (
        0.35
        * (
            5.0
            - np.array([1.0, 3.0, 5.0])
        )
    )

    expected = np.maximum(
        expected,
        1.0,
    )

    np.testing.assert_allclose(
        sizes,
        expected,
    )

    assert stars.sizes is sizes


def test_compute_sizes_applies_minimum():
    stars = make_stars()

    stars.hip_df = pd.DataFrame(
        {
            "magnitude": [10.0],
        },
        index=[100],
    )

    sizes = stars.compute_sizes(
        scale=1.0,
        reference_magnitude=5.0,
        exponent=0.35,
        minimum=2.5,
    )

    np.testing.assert_allclose(
        sizes,
        [2.5],
    )


def test_compute_sizes_requires_selected_stars():
    stars = Stars(
        observer=object(),
    )

    with pytest.raises(
        RuntimeError,
        match="No currently selected stars",
    ):
        stars.compute_sizes()

    stars.hip_df = pd.DataFrame(
        {"magnitude": []},
    )

    with pytest.raises(
        RuntimeError,
        match="No currently selected stars",
    ):
        stars.compute_sizes()


def test_hip_index_maps_identifiers_to_array_positions():
    stars = make_stars()

    assert stars.hip_index == {
        100: 0,
        200: 1,
        300: 2,
    }


def test_hip_index_is_empty_before_catalog_selection():
    stars = Stars(
        observer=object(),
    )

    assert stars.hip_index == {}


def test_check_alignment_accepts_equal_lengths():
    stars = make_stars()

    stars.alt = np.array([10.0, 20.0, 30.0])
    stars.az = np.array([40.0, 50.0, 60.0])
    stars.x = np.array([1.0, 2.0, 3.0])
    stars.y = np.array([4.0, 5.0, 6.0])
    stars.sizes = np.array([7.0, 8.0, 9.0])

    stars._check_alignment()


def test_check_alignment_detects_misaligned_arrays():
    stars = make_stars()

    stars.alt = np.array([10.0, 20.0, 30.0])
    stars.az = np.array([40.0, 50.0, 60.0])
    stars.x = np.array([1.0, 2.0])
    stars.y = np.array([4.0, 5.0, 6.0])
    stars.sizes = np.array([7.0, 8.0, 9.0])

    with pytest.raises(
        RuntimeError,
        match="not aligned",
    ):
        stars._check_alignment()


