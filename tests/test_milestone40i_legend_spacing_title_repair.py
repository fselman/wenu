import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

from wenu import (
    StellarMagnitudeLegendStyle,
    stellar_magnitude_scale,
)
from wenu.charts.magnitude_legend_matplotlib import (
    _required_handle_height,
    draw_stellar_magnitude_legend,
    stellar_magnitude_handles,
)


def test_default_title_is_stars_everywhere():
    scale = stellar_magnitude_scale(-1.0, 5.0)
    style = StellarMagnitudeLegendStyle()
    assert scale.title == "Stars"
    assert style.title == "Stars"


def test_large_markers_increase_handle_height():
    scale = stellar_magnitude_scale(
        -1.0,
        5.0,
        area_scale=2.0,
    )
    handles = stellar_magnitude_handles(scale)
    height = _required_handle_height(handles, 9.0)
    assert height > 0.7
    assert height * 9.0 > max(
        handle.get_markersize() for handle in handles
    )


def test_explicit_handle_height_is_supported():
    figure, ax = plt.subplots()
    scale = stellar_magnitude_scale(-1.0, 5.0)
    legend = draw_stellar_magnitude_legend(
        ax,
        scale,
        handle_height=2.5,
    )
    assert legend is not None
    assert legend._legend_handle_box is not None
    plt.close(figure)


def test_nonpositive_explicit_height_is_rejected():
    figure, ax = plt.subplots()
    scale = stellar_magnitude_scale(-1.0, 5.0)
    with pytest.raises(ValueError, match="handle_height"):
        draw_stellar_magnitude_legend(
            ax,
            scale,
            handle_height=0.0,
        )
    plt.close(figure)
