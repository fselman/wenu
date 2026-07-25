import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

from wenu.regional_chart import draw_regional_chart


class StubStarRenderer:
    def __init__(self):
        self.calls = []

    def draw(self, ax, projection, **kwargs):
        self.calls.append((ax, projection, kwargs))
        return ax.scatter([0.0], [0.0])


class StubConstellations:
    def __init__(self):
        self.calls = []

    def draw(self, ax, projection, **kwargs):
        self.calls.append((ax, projection, kwargs))
        labels = []
        if kwargs["draw_labels"]:
            labels.append(ax.text(0.0, 0.0, "Cru"))
        return {
            "lines": [ax.plot([-1.0, 1.0], [0.0, 0.0])[0]],
            "labels": labels,
            "boundaries": (
                [ax.plot([0.0, 0.0], [-1.0, 1.0])[0]]
                if kwargs["draw_boundaries"]
                else []
            ),
        }


class StubSky:
    def __init__(self, *, constellations=True):
        # The domain layer and transitional renderer are deliberately
        # distinct after Milestone 7.
        self.stars = object()
        self.star_renderer = StubStarRenderer()
        self.constellations = (
            StubConstellations() if constellations else None
        )


def test_regional_chart_configures_center_projection_and_viewport():
    figure, ax = plt.subplots()
    sky = StubSky()

    result = draw_regional_chart(
        sky,
        ax,
        center_alt_deg=35.0,
        center_az_deg=210.0,
        angular_radius_deg=20.0,
        position_angle_deg=12.0,
    )

    center = result.projection.project_point(210.0, 35.0)
    assert center.x == pytest.approx(0.0, abs=1e-7)
    assert center.y == pytest.approx(0.0, abs=1e-7)
    assert ax.get_xlim() == pytest.approx(result.viewport.xlim)
    assert ax.get_ylim() == pytest.approx(result.viewport.ylim)
    assert float(ax.get_aspect()) == 1.0
    plt.close(figure)


def test_regional_chart_draws_stars_before_constellations():
    figure, ax = plt.subplots()
    sky = StubSky()

    result = draw_regional_chart(
        sky,
        ax,
        center_alt_deg=45.0,
        center_az_deg=180.0,
        angular_radius_deg=15.0,
    )

    assert list(result.artists) == ["stars", "constellations"]
    assert len(sky.star_renderer.calls) == 1
    assert len(sky.constellations.calls) == 1
    plt.close(figure)


@pytest.mark.parametrize(
    "selected",
    [
        ["Cru"],
        ["Cru", "Cen"],
    ],
)
def test_single_and_multiple_constellation_selection(selected):
    figure, ax = plt.subplots()
    sky = StubSky()

    result = draw_regional_chart(
        sky,
        ax,
        center_alt_deg=45.0,
        center_az_deg=180.0,
        angular_radius_deg=15.0,
        selected_constellations=selected,
    )

    kwargs = sky.constellations.calls[0][2]
    assert kwargs["label_kwargs"]["selected"] == selected
    assert kwargs["label_kwargs"]["radial_cut"] == pytest.approx(
        result.projection.projected_radius(15.0)
    )
    plt.close(figure)


def test_optional_boundaries_and_clipped_labels():
    figure, ax = plt.subplots()
    sky = StubSky()

    result = draw_regional_chart(
        sky,
        ax,
        center_alt_deg=45.0,
        center_az_deg=180.0,
        angular_radius_deg=15.0,
        draw_boundaries=True,
    )

    kwargs = sky.constellations.calls[0][2]
    assert kwargs["draw_boundaries"] is True
    labels = result.artists["constellations"]["labels"]
    assert labels
    assert all(label.get_clip_on() for label in labels)
    plt.close(figure)


def test_chart_can_be_saved_as_static_output(tmp_path):
    figure, ax = plt.subplots()
    sky = StubSky(constellations=False)
    output = tmp_path / "regional-chart.png"

    draw_regional_chart(
        sky,
        ax,
        center_alt_deg=45.0,
        center_az_deg=180.0,
        angular_radius_deg=15.0,
        save_path=output,
        savefig_kwargs={"dpi": 72},
    )

    assert output.exists()
    assert output.stat().st_size > 0
    plt.close(figure)


def test_regional_chart_requires_stars():
    figure, ax = plt.subplots()

    class EmptySky:
        stars = None
        star_renderer = None
        constellations = None

    with pytest.raises(RuntimeError, match="sky.stars"):
        draw_regional_chart(
            EmptySky(),
            ax,
            center_alt_deg=45.0,
            center_az_deg=180.0,
            angular_radius_deg=15.0,
        )

    plt.close(figure)
