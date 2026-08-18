"""Backend realization of visible celestial-reference legend entries."""

from __future__ import annotations

import numpy as np

from wenu.rendering import layers


ECLIPTIC_KEYPOINT_SYMBOLS = ("♈", "♋", "♎", "♑")


def _publication_style(style):
    converter = getattr(style, "as_publication_style", None)
    return converter() if callable(converter) else style


def draw_ecliptic_keypoint_legend(
    renderer,
    rendering,
    reference_sky,
    composition,
):
    """Draw names only for canonical keypoints visible in this viewport."""
    annotations = composition.furniture.references
    if (
        not annotations.ecliptic_keypoint_legend
        or reference_sky.points is None
    ):
        return None
    point_result = next(
        (
            result
            for result in rendering.layers
            if result.layer is reference_sky.points
        ),
        None,
    )
    if point_result is None:
        return None
    projected = point_result.projected
    viewport = composition.context.viewport
    labels = np.asarray(projected.labels, dtype=object)
    visible = (
        projected.finite
        & (projected.x >= viewport.x_min)
        & (projected.x <= viewport.x_max)
        & (projected.y >= viewport.y_min)
        & (projected.y <= viewport.y_max)
    )
    present = tuple(
        symbol
        for symbol in ECLIPTIC_KEYPOINT_SYMBOLS
        if np.any(visible & (labels == symbol))
    )
    if not present:
        return None

    from matplotlib.legend import Legend
    from matplotlib.lines import Line2D

    style = _publication_style(composition.style)
    names = dict(zip(
        ECLIPTIC_KEYPOINT_SYMBOLS,
        annotations.ecliptic_keypoint_names,
        strict=True,
    ))
    zodiac_names = dict(zip(
        ECLIPTIC_KEYPOINT_SYMBOLS,
        annotations.ecliptic_keypoint_zodiac_names,
        strict=True,
    ))
    handles = tuple(
        Line2D(
            [],
            [],
            linestyle="None",
            marker="x",
            markersize=4.0 * composition.mode.symbol_scale,
            markeredgewidth=0.8 * composition.mode.line_scale,
            color=style.ecliptic_color,
            label=(
                f"{symbol} ({zodiac_names[symbol]}): {names[symbol]}"
            ),
        )
        for symbol in present
    )
    legend = Legend(
        renderer.ax,
        handles,
        [handle.get_label() for handle in handles],
        loc="lower left",
        bbox_to_anchor=(0.01, 0.095),
        bbox_transform=renderer.ax.transAxes,
        frameon=False,
        fontsize=0.42 * style.label_fontsize,
        borderpad=0.25,
        handletextpad=0.35,
        labelspacing=0.2,
    )
    for text in legend.get_texts():
        text.set_color(style.foreground_color)
    legend.set_zorder(layers.LABELS)
    renderer.ax.add_artist(legend)
    return legend
