"""Current stellar magnitude legend contracts."""

# Contracts consolidated from test_milestone40i_chart_magnitude_legend_workflow.py.
from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.legend import Legend

from wenu.charts.magnitude_legend_workflow import (
    StellarMagnitudeLegendResult,
    draw_visible_stellar_magnitude_legend,
)


class m40i_chart_magnitude_legend_workflow_Viewport:
    x_min = -1.0
    x_max = 1.0
    y_min = -1.0
    y_max = 1.0


def m40i_chart_magnitude_legend_workflow_geometry():
    spherical = SimpleNamespace(
        metadata={
            "magnitude": np.asarray(
                [-1.2, 0.4, 2.2, 4.7, 1.0],
                dtype=float,
            )
        }
    )
    projected = SimpleNamespace(
        x=np.asarray([0.0, 0.4, -0.5, 0.8, 2.0]),
        y=np.asarray([0.0, 0.3, 0.5, -0.7, 0.0]),
    )
    return spherical, projected


def test_workflow_uses_only_visible_stars():
    figure, ax = plt.subplots()
    spherical, projected = m40i_chart_magnitude_legend_workflow_geometry()
    result = draw_visible_stellar_magnitude_legend(
        ax,
        spherical,
        projected,
        m40i_chart_magnitude_legend_workflow_Viewport(),
        effective_limit=4.0,
        area_scale=1.5,
    )
    assert isinstance(result, StellarMagnitudeLegendResult)
    assert result.statistics.visible_count == 3
    assert result.statistics.brightest_magnitude == pytest.approx(-1.2)
    assert result.statistics.faintest_magnitude == pytest.approx(2.2)
    assert [entry.magnitude for entry in result.scale.entries] == [
        -1, 0, 1, 2
    ]
    assert isinstance(result.artist, Legend)
    assert result.drawn
    plt.close(figure)


def test_workflow_can_draw_one_reference_magnitude_with_unit_suffix():
    figure, ax = plt.subplots()
    spherical, projected = m40i_chart_magnitude_legend_workflow_geometry()
    result = draw_visible_stellar_magnitude_legend(
        ax,
        spherical,
        projected,
        m40i_chart_magnitude_legend_workflow_Viewport(),
        effective_limit=4.0,
        reference_magnitude=3,
        label_suffix=" mag",
        title="",
    )

    assert result.scale.magnitudes == (3,)
    assert [text.get_text() for text in result.artist.get_texts()] == [
        "3 mag"
    ]
    plt.close(figure)


def test_workflow_preserves_the_existing_object_legend():
    figure, ax = plt.subplots()
    ax.plot([], [], marker="s", label="Galaxy")
    object_legend = ax.legend(loc="upper right")
    spherical, projected = m40i_chart_magnitude_legend_workflow_geometry()

    result = draw_visible_stellar_magnitude_legend(
        ax,
        spherical,
        projected,
        m40i_chart_magnitude_legend_workflow_Viewport(),
        effective_limit=4.0,
        location="lower right",
    )
    assert ax.get_legend() is object_legend
    assert result.artist is not object_legend
    plt.close(figure)


def test_workflow_respects_a_chart_footprint():
    figure, ax = plt.subplots()
    spherical, projected = m40i_chart_magnitude_legend_workflow_geometry()
    result = draw_visible_stellar_magnitude_legend(
        ax,
        spherical,
        projected,
        m40i_chart_magnitude_legend_workflow_Viewport(),
        effective_limit=4.0,
        footprint_contains=lambda x, y: x * x + y * y <= 0.25,
    )
    assert result.statistics.visible_count == 2
    assert [entry.magnitude for entry in result.scale.entries] == [-1, 0]
    plt.close(figure)


def test_empty_visible_set_produces_no_scale_or_artist():
    figure, ax = plt.subplots()
    spherical, projected = m40i_chart_magnitude_legend_workflow_geometry()
    result = draw_visible_stellar_magnitude_legend(
        ax,
        spherical,
        projected,
        m40i_chart_magnitude_legend_workflow_Viewport(),
        effective_limit=-2.0,
    )
    assert result.statistics.visible_count == 0
    assert result.scale is None
    assert result.artist is None
    assert not result.drawn
    plt.close(figure)


def test_interval_without_an_integer_produces_no_artist():
    figure, ax = plt.subplots()
    spherical = SimpleNamespace(
        metadata={"magnitude": np.asarray([0.1, 0.8])}
    )
    projected = SimpleNamespace(
        x=np.asarray([0.0, 0.2]),
        y=np.asarray([0.0, 0.2]),
    )
    result = draw_visible_stellar_magnitude_legend(
        ax,
        spherical,
        projected,
        m40i_chart_magnitude_legend_workflow_Viewport(),
        effective_limit=1.0,
    )
    assert result.statistics.visible_count == 2
    assert result.scale is not None
    assert result.scale.entries == ()
    assert result.artist is None
    plt.close(figure)


def test_public_api_exports_workflow():
    from wenu import draw_visible_stellar_magnitude_legend as exported

    assert exported is draw_visible_stellar_magnitude_legend

# Contracts consolidated from test_milestone40i_legend_spacing_title_repair.py.
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

# Contracts consolidated from test_milestone40i_magnitude_scale_contract.py.
from pathlib import Path

import numpy as np
import pytest

from wenu import (
    StellarMagnitudeEntry,
    StellarMagnitudeScale,
    integer_magnitude_range,
    stellar_magnitude_scale,
)
from wenu.rendering.preparation import magnitude_sizes


def test_integer_range_is_inclusive_and_supports_negative_magnitudes():
    assert integer_magnitude_range(-1.46, 6.3) == (
        -1,
        0,
        1,
        2,
        3,
        4,
        5,
        6,
    )


def test_integer_range_uses_ceil_and_floor():
    assert integer_magnitude_range(0.2, 4.9) == (1, 2, 3, 4)
    assert integer_magnitude_range(2.2, 2.8) == ()


def test_reversed_or_nonfinite_limits_are_rejected():
    with pytest.raises(ValueError):
        integer_magnitude_range(6.0, -1.0)
    with pytest.raises(ValueError):
        integer_magnitude_range(np.nan, 6.0)
    with pytest.raises(ValueError):
        integer_magnitude_range(-1.0, np.inf)


def test_scale_uses_exact_chart_magnitude_area_law():
    scale = stellar_magnitude_scale(
        -1.46,
        4.8,
        area_scale=2.25,
        color="black",
        alpha=0.8,
    )
    expected = magnitude_sizes(scale.magnitudes) * 2.25
    assert isinstance(scale, StellarMagnitudeScale)
    assert all(
        isinstance(item, StellarMagnitudeEntry)
        for item in scale.entries
    )
    assert scale.areas == pytest.approx(tuple(expected))
    assert scale.color == "black"
    assert scale.alpha == pytest.approx(0.8)


def test_brighter_entries_have_larger_areas():
    scale = stellar_magnitude_scale(-1.0, 6.0)
    assert all(
        first > second
        for first, second in zip(scale.areas, scale.areas[1:])
    )


def test_empty_integer_range_produces_empty_scale():
    scale = stellar_magnitude_scale(2.2, 2.8)
    assert scale.entries == ()
    assert scale.magnitudes == ()
    assert scale.areas == ()


def test_invalid_area_scale_is_rejected():
    with pytest.raises(ValueError):
        stellar_magnitude_scale(0.0, 5.0, area_scale=0.0)
    with pytest.raises(ValueError):
        stellar_magnitude_scale(0.0, 5.0, area_scale=np.nan)


def test_contract_module_has_no_matplotlib_dependency():
    import wenu.charts.magnitude_legend as module

    source = Path(module.__file__).read_text().lower()
    assert "matplotlib" not in source

# Contracts consolidated from test_milestone40i_stellar_magnitude_legend.py.
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest
from matplotlib.legend import Legend

from wenu.charts.magnitude_legend import (
    StellarMagnitudeScale,
    stellar_magnitude_scale,
)
from wenu.charts.magnitude_legend_matplotlib import (
    draw_stellar_magnitude_legend,
    stellar_magnitude_handles,
)


def scale():
    return stellar_magnitude_scale(
        -1.2,
        4.8,
        area_scale=1.7,
        color="black",
        alpha=0.8,
        title="Stellar magnitude",
    )


def test_handles_use_integer_magnitude_labels():
    handles = stellar_magnitude_handles(scale())
    assert [handle.get_label() for handle in handles] == [
        "-1", "0", "1", "2", "3", "4"
    ]


def test_handle_sizes_are_square_roots_of_scatter_areas():
    current = scale()
    handles = stellar_magnitude_handles(current)
    for entry, handle in zip(current.entries, handles):
        assert handle.get_markersize() ** 2 == pytest.approx(entry.area)


def test_legend_uses_scale_title_and_requested_location():
    figure, ax = plt.subplots()
    legend = draw_stellar_magnitude_legend(
        ax,
        scale(),
        location="upper left",
    )
    assert isinstance(legend, Legend)
    assert legend.get_title().get_text() == "Stellar magnitude"
    assert [text.get_text() for text in legend.get_texts()] == [
        "-1", "0", "1", "2", "3", "4"
    ]
    plt.close(figure)


def test_magnitude_legend_preserves_existing_object_legend():
    figure, ax = plt.subplots()
    ax.plot([], [], marker="s", label="Galaxy")
    object_legend = ax.legend(loc="upper right")

    magnitude_legend = draw_stellar_magnitude_legend(
        ax,
        scale(),
        location="lower right",
    )

    assert ax.get_legend() is object_legend
    legends = [
        artist
        for artist in ax.get_children()
        if isinstance(artist, Legend)
    ]
    assert object_legend in legends
    assert magnitude_legend in legends
    assert magnitude_legend is not object_legend
    plt.close(figure)


def test_empty_scale_does_not_add_a_legend():
    figure, ax = plt.subplots()
    empty = StellarMagnitudeScale(
        entries=(),
        color="black",
        alpha=1.0,
        title="Stellar magnitude",
    )
    assert draw_stellar_magnitude_legend(ax, empty) is None
    assert not any(
        isinstance(artist, Legend)
        for artist in ax.get_children()
    )
    plt.close(figure)


def test_public_api_exports_renderer():
    from wenu import draw_stellar_magnitude_legend as exported

    assert exported is draw_stellar_magnitude_legend

# Contracts consolidated from test_milestone40i_styled_magnitude_legend.py.
from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.legend import Legend

from wenu import (
    StellarMagnitudeLegendStyle,
    draw_styled_stellar_magnitude_legend,
)


class m40i_styled_magnitude_legend_Viewport:
    x_min = -1.0
    x_max = 1.0
    y_min = -1.0
    y_max = 1.0


def m40i_styled_magnitude_legend_geometry():
    return (
        SimpleNamespace(
            metadata={"magnitude": np.asarray([-1.2, 0.2, 2.8])}
        ),
        SimpleNamespace(
            x=np.asarray([0.0, 0.2, 0.4]),
            y=np.asarray([0.0, 0.2, 0.4]),
        ),
    )


def test_default_style_is_separate_from_chart_style():
    style = StellarMagnitudeLegendStyle()
    assert style.enabled
    assert style.location == "lower right"
    assert style.title == "Stars"


def test_drawing_options_are_complete_and_stable():
    style = StellarMagnitudeLegendStyle(
        location="upper left",
        frame_on=False,
        font_size=8.0,
    )
    options = style.drawing_options()
    assert options["location"] == "upper left"
    assert options["frame_on"] is False
    assert options["font_size"] == 8.0
    assert "enabled" not in options


def test_styled_wrapper_draws_requested_legend():
    figure, ax = plt.subplots()
    spherical, projected = m40i_styled_magnitude_legend_geometry()
    result = draw_styled_stellar_magnitude_legend(
        ax,
        spherical,
        projected,
        m40i_styled_magnitude_legend_Viewport(),
        effective_limit=3.0,
        color="navy",
        legend_style=StellarMagnitudeLegendStyle(
            location="upper left",
            title="Magnitude",
        ),
    )
    assert isinstance(result.artist, Legend)
    assert result.artist.get_title().get_text() == "Magnitude"
    assert result.scale.color == "navy"
    plt.close(figure)


def test_disabled_style_calculates_statistics_but_draws_nothing():
    figure, ax = plt.subplots()
    spherical, projected = m40i_styled_magnitude_legend_geometry()
    result = draw_styled_stellar_magnitude_legend(
        ax,
        spherical,
        projected,
        m40i_styled_magnitude_legend_Viewport(),
        effective_limit=3.0,
        legend_style=StellarMagnitudeLegendStyle(enabled=False),
    )
    assert result.statistics.visible_count == 3
    assert result.scale is None
    assert result.artist is None
    plt.close(figure)


def test_two_legends_remain_present():
    figure, ax = plt.subplots()
    ax.plot([], [], marker="s", label="Galaxy")
    object_legend = ax.legend(loc="upper right")
    spherical, projected = m40i_styled_magnitude_legend_geometry()
    result = draw_styled_stellar_magnitude_legend(
        ax,
        spherical,
        projected,
        m40i_styled_magnitude_legend_Viewport(),
        effective_limit=3.0,
        legend_style=StellarMagnitudeLegendStyle(
            location="lower right"
        ),
    )
    legends = [
        artist for artist in ax.get_children()
        if isinstance(artist, Legend)
    ]
    assert object_legend in legends
    assert result.artist in legends
    plt.close(figure)


def test_visual_example_is_importable_and_writes_output(tmp_path):
    import importlib.util
    from pathlib import Path

    path = Path("tests/fixtures/example_regressions/stellar_magnitude_legend.py")
    specification = importlib.util.spec_from_file_location(
        "stellar_magnitude_legend_example",
        path,
    )
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)

    destination = tmp_path / "reference.png"
    figure, _, object_legend, result = module.draw_reference(
        destination,
        dpi=80,
    )
    assert destination.is_file()
    assert object_legend is not result.artist
    assert result.drawn
    plt.close(figure)

# Contracts consolidated from test_milestone40i_visible_star_statistics.py.
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from wenu import (
    VisibleStarStatistics,
    visible_star_mask,
    visible_star_statistics,
)
from wenu.geometry.viewport import Viewport


def geometries():
    spherical = SimpleNamespace(
        metadata={
            "magnitude": np.asarray(
                [-1.4, 0.2, 3.1, 5.8, 7.0, np.nan]
            )
        }
    )
    projected = SimpleNamespace(
        x=np.asarray([4.0, 0.0, 0.4, 0.8, 0.2, 0.0]),
        y=np.asarray([0.0, 0.0, 0.3, 0.8, 0.1, 0.0]),
    )
    viewport = Viewport.centered(width=2.0, height=2.0)
    return spherical, projected, viewport


def test_statistics_exclude_bright_star_outside_viewport():
    spherical, projected, viewport = geometries()
    result = visible_star_statistics(
        spherical,
        projected,
        viewport,
        effective_limit=6.0,
    )
    assert isinstance(result, VisibleStarStatistics)
    assert result.visible_count == 3
    assert result.brightest_magnitude == pytest.approx(0.2)
    assert result.faintest_magnitude == pytest.approx(5.8)
    assert result.effective_limit == pytest.approx(6.0)


def test_effective_limit_excludes_fainter_stars():
    spherical, projected, viewport = geometries()
    result = visible_star_statistics(
        spherical,
        projected,
        viewport,
        effective_limit=3.5,
    )
    assert result.visible_count == 2
    assert result.faintest_magnitude == pytest.approx(3.1)


def test_optional_footprint_supports_circular_charts():
    spherical, projected, viewport = geometries()
    result = visible_star_statistics(
        spherical,
        projected,
        viewport,
        effective_limit=6.0,
        footprint_contains=lambda x, y: np.hypot(x, y) <= 0.6,
    )
    assert result.visible_count == 2
    assert result.brightest_magnitude == pytest.approx(0.2)
    assert result.faintest_magnitude == pytest.approx(3.1)


def test_mask_is_inclusive_at_viewport_edges():
    spherical = SimpleNamespace(
        metadata={"magnitude": np.asarray([1.0, 2.0])}
    )
    projected = SimpleNamespace(
        x=np.asarray([-1.0, 1.0]),
        y=np.asarray([-1.0, 1.0]),
    )
    viewport = Viewport.centered(width=2.0, height=2.0)
    mask = visible_star_mask(
        spherical,
        projected,
        viewport,
        effective_limit=2.0,
    )
    assert mask.tolist() == [True, True]


def test_no_visible_stars_has_explicit_empty_statistics():
    spherical, projected, viewport = geometries()
    result = visible_star_statistics(
        spherical,
        projected,
        viewport,
        effective_limit=-2.0,
    )
    assert not result.has_visible_stars
    assert result.visible_count == 0
    assert result.brightest_magnitude is None
    assert result.faintest_magnitude is None


def test_mismatched_geometry_shapes_are_rejected():
    spherical, projected, viewport = geometries()
    projected.x = projected.x[:-1]
    with pytest.raises(ValueError):
        visible_star_mask(
            spherical,
            projected,
            viewport,
            effective_limit=6.0,
        )


def test_invalid_footprint_shape_is_rejected():
    spherical, projected, viewport = geometries()
    with pytest.raises(ValueError):
        visible_star_mask(
            spherical,
            projected,
            viewport,
            effective_limit=6.0,
            footprint_contains=lambda x, y: [True],
        )


def test_statistics_module_remains_backend_independent():
    import wenu.charts.magnitude_legend as module

    source = Path(module.__file__).read_text().lower()
    assert "matplotlib" not in source
