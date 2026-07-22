import numpy as np
import pytest

from wenu.viewport import Viewport


def test_viewport_properties():
    viewport = Viewport(
        x_min=-2.0,
        x_max=4.0,
        y_min=-1.0,
        y_max=3.0,
    )

    assert viewport.width == 6.0
    assert viewport.height == 4.0
    assert viewport.center_x == 1.0
    assert viewport.center_y == 1.0
    assert viewport.center == (1.0, 1.0)
    assert viewport.aspect_ratio == 1.5
    assert viewport.xlim == (-2.0, 4.0)
    assert viewport.ylim == (-1.0, 3.0)


def test_centered_constructor():
    viewport = Viewport.centered(
        width=6.0,
        height=4.0,
        center_x=1.0,
        center_y=-2.0,
    )

    assert viewport.xlim == (-2.0, 4.0)
    assert viewport.ylim == (-4.0, 0.0)


def test_contains_scalar_point():
    viewport = Viewport.centered(
        width=4.0,
        height=2.0,
    )

    assert bool(viewport.contains(0.0, 0.0))
    assert not bool(viewport.contains(3.0, 0.0))


def test_contains_array():
    viewport = Viewport(
        x_min=-1.0,
        x_max=1.0,
        y_min=-2.0,
        y_max=2.0,
    )

    result = viewport.contains(
        x=[0.0, 1.0, 1.1, np.nan],
        y=[0.0, 2.0, 0.0, 0.0],
    )

    np.testing.assert_array_equal(
        result,
        [True, True, False, False],
    )


def test_contains_supports_broadcasting():
    viewport = Viewport.centered(
        width=2.0,
        height=2.0,
    )

    result = viewport.contains(
        x=np.array([-2.0, 0.0, 2.0]),
        y=0.0,
    )

    np.testing.assert_array_equal(
        result,
        [False, True, False],
    )


def test_boundary_can_be_excluded():
    viewport = Viewport(
        x_min=-1.0,
        x_max=1.0,
        y_min=-1.0,
        y_max=1.0,
    )

    assert bool(
        viewport.contains(
            1.0,
            0.0,
            include_boundary=True,
        )
    )

    assert not bool(
        viewport.contains(
            1.0,
            0.0,
            include_boundary=False,
        )
    )


@pytest.mark.parametrize(
    "bounds",
    [
        {
            "x_min": 1.0,
            "x_max": 1.0,
            "y_min": -1.0,
            "y_max": 1.0,
        },
        {
            "x_min": 2.0,
            "x_max": 1.0,
            "y_min": -1.0,
            "y_max": 1.0,
        },
        {
            "x_min": -1.0,
            "x_max": 1.0,
            "y_min": 3.0,
            "y_max": 3.0,
        },
        {
            "x_min": -1.0,
            "x_max": 1.0,
            "y_min": 4.0,
            "y_max": 3.0,
        },
    ],
)
def test_invalid_ordered_bounds_raise(bounds):
    with pytest.raises(ValueError):
        Viewport(**bounds)


@pytest.mark.parametrize(
    "bounds",
    [
        {
            "x_min": np.nan,
            "x_max": 1.0,
            "y_min": -1.0,
            "y_max": 1.0,
        },
        {
            "x_min": -1.0,
            "x_max": np.inf,
            "y_min": -1.0,
            "y_max": 1.0,
        },
    ],
)
def test_nonfinite_bounds_raise(bounds):
    with pytest.raises(ValueError):
        Viewport(**bounds)


@pytest.mark.parametrize(
    ("width", "height"),
    [
        (0.0, 1.0),
        (-1.0, 1.0),
        (1.0, 0.0),
        (1.0, -1.0),
        (np.inf, 1.0),
        (1.0, np.nan),
    ],
)
def test_centered_rejects_invalid_dimensions(
    width,
    height,
):
    with pytest.raises(ValueError):
        Viewport.centered(
            width=width,
            height=height,
        )


def test_viewport_is_public_api():
    from wenu import Viewport as PublicViewport

    assert PublicViewport is Viewport


