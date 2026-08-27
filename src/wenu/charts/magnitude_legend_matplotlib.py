"""Matplotlib rendering for stellar magnitude–size legends."""

from __future__ import annotations

from math import sqrt

from matplotlib import rcParams
from matplotlib.legend import Legend
from matplotlib.lines import Line2D

from .magnitude_legend import StellarMagnitudeScale


def _magnitude_semantic_key(magnitude: int) -> str:
    """Return an unambiguous ID token independent of displayed counts."""
    magnitude = int(magnitude)
    return (
        f"mag-minus-{abs(magnitude)}"
        if magnitude < 0
        else f"mag-{magnitude}"
    )


def stellar_magnitude_handles(
    scale: StellarMagnitudeScale,
    *,
    marker: str = "o",
    marker_edge_color: str | None = None,
    marker_edge_width: float = 0.0,
    label_suffix: str = "",
) -> tuple[Line2D, ...]:
    """Return legend handles that reproduce the chart's stellar areas."""
    edge_color = (
        scale.color
        if marker_edge_color is None
        else marker_edge_color
    )
    return tuple(
        Line2D(
            [],
            [],
            linestyle="None",
            marker=marker,
            markersize=sqrt(max(0.0, entry.area)),
            markerfacecolor=scale.color,
            markeredgecolor=edge_color,
            markeredgewidth=marker_edge_width,
            alpha=scale.alpha,
            label=(
                (
                    f"{entry.magnitude:+d}"
                    if entry.magnitude < 0
                    else str(entry.magnitude)
                )
                + (
                    ""
                    if entry.cumulative_count is None
                    else f" ({entry.cumulative_count})"
                )
                + str(label_suffix)
            ),
        )
        for entry in scale.entries
    )


def _required_handle_height(handles, font_size):
    """Return a text-relative row height large enough for every marker."""
    if not handles:
        return 0.7
    resolved_font_size = float(
        rcParams["legend.fontsize"]
        if font_size is None
        and isinstance(rcParams["legend.fontsize"], (int, float))
        else (
            rcParams["font.size"]
            if font_size is None
            else font_size
        )
    )
    largest_marker = max(handle.get_markersize() for handle in handles)
    # A small allowance prevents antialiasing at adjacent row boundaries.
    return max(0.7, largest_marker / resolved_font_size + 0.18)


def draw_stellar_magnitude_legend(
    ax,
    scale: StellarMagnitudeScale,
    *,
    location: str = "lower right",
    title: str | None = None,
    frame_on: bool = True,
    frame_alpha: float | None = None,
    font_size: float | None = None,
    title_font_size: float | None = None,
    marker: str = "o",
    marker_edge_color: str | None = None,
    marker_edge_width: float = 0.0,
    label_spacing: float = 0.35,
    handle_text_pad: float = 0.8,
    border_pad: float = 0.5,
    handle_height: float | None = None,
    zorder: float = 1000.0,
    text_color: str | None = None,
    facecolor: str | None = None,
    edgecolor: str | None = None,
    label_suffix: str = "",
) -> Legend | None:
    """Draw an independent, non-overlapping stellar magnitude legend."""
    handles = stellar_magnitude_handles(
        scale,
        marker=marker,
        marker_edge_color=marker_edge_color,
        marker_edge_width=marker_edge_width,
        label_suffix=label_suffix,
    )
    if not handles:
        return None

    resolved_handle_height = (
        _required_handle_height(handles, font_size)
        if handle_height is None
        else float(handle_height)
    )
    if resolved_handle_height <= 0.0:
        raise ValueError("handle_height must be positive.")

    legend = Legend(
        ax,
        handles,
        [handle.get_label() for handle in handles],
        loc=location,
        title=scale.title if title is None else title,
        frameon=frame_on,
        fontsize=font_size,
        title_fontsize=title_font_size,
        labelspacing=label_spacing,
        handletextpad=handle_text_pad,
        borderpad=border_pad,
        handleheight=resolved_handle_height,
    )
    legend.set_zorder(zorder)
    if text_color is not None:
        for text in legend.get_texts():
            text.set_color(text_color)
        legend.get_title().set_color(text_color)
    frame = legend.get_frame()
    if frame_alpha is not None:
        frame.set_alpha(float(frame_alpha))
    if facecolor is not None:
        frame.set_facecolor(facecolor)
    if edgecolor is not None:
        frame.set_edgecolor(edgecolor)
    setattr(
        legend,
        "_wenu_legend_entry_keys",
        tuple(
            _magnitude_semantic_key(entry.magnitude)
            for entry in scale.entries
        ),
    )
    ax.add_artist(legend)
    return legend
