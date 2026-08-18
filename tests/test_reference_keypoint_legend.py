"""Visible ecliptic-keypoint legend contracts."""

from types import SimpleNamespace

import matplotlib.pyplot as plt
import numpy as np

from wenu import MatplotlibRenderer, Viewport
from wenu.charts.furniture import ReferenceAnnotations
from wenu.charts.reference_keypoint_legend import (
    draw_ecliptic_keypoint_legend,
)
from wenu.geometry.projected import ProjectedPoints


def composition(references):
    style = SimpleNamespace(
        ecliptic_color="gold",
        foreground_color="white",
        label_fontsize=20.0,
    )
    return SimpleNamespace(
        furniture=SimpleNamespace(references=references),
        context=SimpleNamespace(viewport=Viewport(-1.0, 1.0, -1.0, 1.0)),
        style=style,
        mode=SimpleNamespace(symbol_scale=1.0, line_scale=1.0),
    )


def test_keypoint_legend_lists_only_symbols_inside_the_viewport():
    points = object()
    projected = ProjectedPoints(
        x=np.asarray([0.0, 2.0, np.nan, -2.0]),
        y=np.asarray([0.0, 0.0, np.nan, 0.0]),
        labels=np.asarray(["♈", "♋", "♎", "♑"], dtype=object),
    )
    rendering = SimpleNamespace(layers=(SimpleNamespace(
        layer=points,
        projected=projected,
    ),))
    references = ReferenceAnnotations(
        ecliptic_keypoints="labeled",
        ecliptic_keypoint_legend=True,
        ecliptic_keypoint_names=(
            "Equinoccio de marzo",
            "Solsticio de junio",
            "Equinoccio de septiembre",
            "Solsticio de diciembre",
        ),
    )
    figure, ax = plt.subplots()
    try:
        legend = draw_ecliptic_keypoint_legend(
            MatplotlibRenderer(ax),
            rendering,
            SimpleNamespace(points=points),
            composition(references),
        )

        assert [text.get_text() for text in legend.get_texts()] == [
            "♈ (Aries): Equinoccio de marzo"
        ]
        assert legend._loc == 3
    finally:
        plt.close(figure)


def test_keypoint_legend_is_absent_when_no_keypoint_is_visible():
    points = object()
    projected = ProjectedPoints(
        x=np.asarray([2.0]),
        y=np.asarray([2.0]),
        labels=np.asarray(["♈"], dtype=object),
    )
    rendering = SimpleNamespace(layers=(SimpleNamespace(
        layer=points,
        projected=projected,
    ),))
    references = ReferenceAnnotations(
        ecliptic_keypoint_legend=True,
    )
    figure, ax = plt.subplots()
    try:
        assert draw_ecliptic_keypoint_legend(
            MatplotlibRenderer(ax),
            rendering,
            SimpleNamespace(points=points),
            composition(references),
        ) is None
    finally:
        plt.close(figure)
