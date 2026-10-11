"""Matplotlib rendering for stellar magnitude–size legends."""

from __future__ import annotations

from math import sqrt

from matplotlib import rcParams
from matplotlib.legend import Legend
from matplotlib.lines import Line2D
from matplotlib.legend_handler import HandlerLine2D

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
                    f" ≤ m < {entry.magnitude + 1}   N={entry.interval_count}"
                    if entry.interval_count is not None
                    else ""
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
    # Matplotlib handle boxes shrink height by 0.35*(handleheight-0.7).
    return max(0.7, (largest_marker / resolved_font_size + 0.35 - 0.245) / 0.65)


class _CenteredMagnitudeHandler(HandlerLine2D):
    """One centered marker with extents matching its physical handle box."""

    def create_artists(self, legend, original, xdescent, ydescent, width, height, fontsize, transform):
        artists = super().create_artists(legend, original, xdescent, ydescent,
                                         width, height, fontsize, transform)
        for artist in artists:
            artist.set_data([(width - xdescent) / 2], [(height - ydescent) / 2])
            artist.set_markevery(None)
        return artists


class _MagnitudeRangeLegend(Legend):
    """Draw range furniture from current row extents at every backend/DPI."""

    def draw(self, renderer):
        super().draw(renderer)
        if not getattr(self, '_wenu_report_range', False):
            return
        from matplotlib.patches import Rectangle
        from matplotlib.transforms import Bbox, IdentityTransform
        rows = self._legend_handle_box.get_children()[0].get_children()
        active = []
        for i, (row, entry) in enumerate(zip(rows, self._wenu_scale.entries)):
            bounds = row.get_window_extent(renderer)
            if entry.active:
                active.append(bounds)
            else:
                veil = Rectangle((bounds.x0, bounds.y0), bounds.width, bounds.height,
                    transform=IdentityTransform(), facecolor=self._wenu_veil_color,
                    alpha=self._wenu_veil_alpha, edgecolor='none')
                veil.set_gid(f'magnitude-veil-{_magnitude_semantic_key(entry.magnitude)}')
                veil.set_figure(self.figure)
                veil.draw(renderer)
        if active:
            bounds = Bbox.union(active).padded(renderer.points_to_pixels(2))
            box = Rectangle((bounds.x0, bounds.y0), bounds.width, bounds.height,
                transform=IdentityTransform(), fill=False, edgecolor=self._wenu_range_color,
                linewidth=.8, linestyle=':')
            box.set_gid('magnitude-chart-range')
            box.set_figure(self.figure)
            box.draw(renderer)


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
    report_range: bool = False,
    veil_color: str = "white",
    veil_alpha: float = 0.65,
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

    legend = _MagnitudeRangeLegend(
        ax,
        handles,
        [handle.get_label() for handle in handles],
        handler_map={Line2D: _CenteredMagnitudeHandler(numpoints=1)},
        loc=location,
        title=scale.title if title is None else title,
        frameon=frame_on,
        fontsize=font_size,
        title_fontsize=title_font_size,
        labelspacing=label_spacing,
        handletextpad=handle_text_pad,
        borderpad=border_pad,
        handleheight=resolved_handle_height,
        handlelength=max(2.0, max(h.get_markersize() for h in handles) / float(font_size or rcParams["font.size"]) + .4),
    )
    if handle_height is None:
        # Offset-box dimensions are points; resize each row to its own disk.
        # Keep one aligned handle column without reserving the largest disk's
        # height for every faint reference symbol.
        for row, handle in zip(legend._legend_handle_box.get_children()[0].get_children(),
                               legend.legend_handles):
            drawing = row.get_children()[0]
            drawing.height = max(float(font_size or rcParams['font.size']),
                                 handle.get_markersize() + 2)
            drawing.ydescent = 0
            handle.set_ydata([drawing.height / 2])
            row.align = 'center'
    legend._wenu_scale = scale
    legend._wenu_report_range = report_range
    legend._wenu_veil_color = veil_color
    legend._wenu_veil_alpha = veil_alpha
    legend._wenu_range_color = text_color or 'black'
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
