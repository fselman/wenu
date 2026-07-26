import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from wenu.rendering import apply_viewport
from wenu.geometry.viewport import Viewport


def test_apply_viewport_sets_axis_limits():
    figure, ax = plt.subplots()

    viewport = Viewport(
        x_min=-2.0,
        x_max=3.0,
        y_min=-1.0,
        y_max=4.0,
    )

    apply_viewport(
        ax,
        viewport,
    )

    assert ax.get_xlim() == (-2.0, 3.0)
    assert ax.get_ylim() == (-1.0, 4.0)

    plt.close(figure)


def test_apply_viewport_sets_equal_aspect():
    figure, ax = plt.subplots()

    viewport = Viewport.centered(
        width=4.0,
        height=2.0,
    )

    apply_viewport(
        ax,
        viewport,
    )

    assert float(ax.get_aspect()) == 1.0

    plt.close(figure)


def test_equal_aspect_can_be_disabled():
    figure, ax = plt.subplots()

    viewport = Viewport.centered(
        width=4.0,
        height=2.0,
    )

    apply_viewport(
        ax,
        viewport,
        equal_aspect=False,
    )

    assert ax.get_aspect() == "auto"

    plt.close(figure)


