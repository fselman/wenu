"""Atlas presentation context and circular frame regression tests."""

import matplotlib.pyplot as plt

from wenu import CircumpolarChart, MatplotlibRenderer, Observer, compose_chart


def chart():
    return CircumpolarChart(
        Observer(location="La Ligua", time="2026-08-15 21:00"),
        limiting_declination_deg=-69.75,
        pole="south",
    )


def test_atlas_presentation_title_uses_foreground_palette():
    composition = compose_chart(
        chart(), style="atlas", mode="presentation"
    )
    figure, ax = plt.subplots()
    composition.style.configure_axes(ax, title="Circumpolar")

    assert ax.title.get_color() == composition.style.canvas.foreground_color
    plt.close(figure)


def test_circular_renderer_suppresses_rectangular_axes_frame():
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)

    renderer.set_axes_frame_visible(False)

    assert all(not spine.get_visible() for spine in ax.spines.values())
    plt.close(figure)
