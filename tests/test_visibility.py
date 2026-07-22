import numpy as np
import pytest

from wenu.visibility import (
    split_visible_segments,
    visibility_mask,
    visible_segments,
)


def test_visibility_mask_uses_strict_altitude_limit():
    alt_deg = np.array([-1.0, 0.0, 1.0])

    result = visibility_mask(
        alt_deg,
        min_altitude=0.0,
    )

    expected = np.array([False, False, True])

    np.testing.assert_array_equal(result, expected)


def test_visibility_mask_accepts_custom_altitude_limit():
    alt_deg = np.array([4.9, 5.0, 5.1])

    result = visibility_mask(
        alt_deg,
        min_altitude=5.0,
    )

    expected = np.array([False, False, True])

    np.testing.assert_array_equal(result, expected)


def test_split_visible_segments_returns_contiguous_indices():
    visible = np.array(
        [False, True, True, False, True, True, True, False]
    )

    segments = split_visible_segments(visible)

    assert len(segments) == 2
    np.testing.assert_array_equal(
        segments[0],
        np.array([1, 2]),
    )
    np.testing.assert_array_equal(
        segments[1],
        np.array([4, 5, 6]),
    )


def test_split_visible_segments_ignores_short_segments():
    visible = np.array(
        [False, True, False, True, True]
    )

    segments = split_visible_segments(
        visible,
        minimum_length=2,
    )

    assert len(segments) == 1
    np.testing.assert_array_equal(
        segments[0],
        np.array([3, 4]),
    )


def test_split_visible_segments_returns_empty_list_when_none_visible():
    visible = np.array([False, False, False])

    assert split_visible_segments(visible) == []


def test_split_visible_segments_requires_one_dimension():
    visible = np.array(
        [
            [True, False],
            [False, True],
        ]
    )

    with pytest.raises(
        ValueError,
        match="visible must be a one-dimensional array",
    ):
        split_visible_segments(visible)


def test_split_visible_segments_rejects_invalid_minimum_length():
    with pytest.raises(
        ValueError,
        match="minimum_length must be at least 1",
    ):
        split_visible_segments(
            [True, True],
            minimum_length=0,
        )


def test_visible_segments_combines_mask_and_segmentation():
    alt_deg = np.array(
        [-1.0, 2.0, 3.0, -2.0, 4.0, 5.0]
    )

    segments = visible_segments(
        alt_deg,
        min_altitude=0.0,
    )

    assert len(segments) == 2
    np.testing.assert_array_equal(
        segments[0],
        np.array([1, 2]),
    )
    np.testing.assert_array_equal(
        segments[1],
        np.array([4, 5]),
    )


