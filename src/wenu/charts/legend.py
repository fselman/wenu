"""Configurable informational legends for static sky charts."""

from __future__ import annotations

from matplotlib.legend_handler import HandlerPatch
from matplotlib.lines import Line2D
from matplotlib.patches import Ellipse, Patch

from wenu.rendering.symbols import DEFAULT_SYMBOLS

from .legend_metadata import resolve_legend_metadata
from .legend_symbols import legend_symbol_descriptors


def _legend_ellipse(
    legend,
    orig_handle,
    xdescent,
    ydescent,
    width,
    height,
    fontsize,
):
    """Create an elongated ellipse inside a legend handle box."""
    return Ellipse(
        (width / 2.0 - xdescent, height / 2.0 - ydescent),
        width=width,
        height=height * 0.58,
    )


def _legend_handler_map():
    return {
        Ellipse: HandlerPatch(patch_func=_legend_ellipse),
    }


def _legend_handle(descriptor):
    if descriptor.key == "galaxy":
        return Ellipse(
            (0.0, 0.0),
            width=1.7,
            height=0.75,
            facecolor=descriptor.face_color,
            edgecolor=descriptor.edge_color,
            alpha=descriptor.alpha,
            linewidth=descriptor.linewidth,
            label=descriptor.label,
        )
    if descriptor.kind == "patch":
        return Patch(
            facecolor=descriptor.face_color,
            edgecolor=descriptor.edge_color,
            alpha=descriptor.alpha,
            linewidth=descriptor.linewidth,
            label=descriptor.label,
        )
    marker = descriptor.marker
    if descriptor.symbol_name is not None:
        marker = DEFAULT_SYMBOLS[descriptor.symbol_name]
    return Line2D(
        [],
        [],
        color=descriptor.edge_color,
        marker=marker,
        markerfacecolor=descriptor.face_color,
        markeredgecolor=descriptor.edge_color,
        markeredgewidth=descriptor.linewidth,
        linestyle="None",
        alpha=descriptor.alpha,
        label=descriptor.label,
    )


def draw_chart_legend(
    ax,
    chart,
    sky,
    style,
    *,
    grid=None,
    title=None,
    context_lines=None,
    include_objects=True,
    include_context=True,
    resolved_detail=None,
    symbol_labels=None,
):
    """Draw a configurable symbol key with coordinate and context metadata."""
    config = style.legend
    if not config.visible:
        return None

    descriptors = (
        tuple(legend_symbol_descriptors(
            sky,
            style,
            resolved_detail=resolved_detail,
            labels=symbol_labels,
        ))
        if include_objects
        else ()
    )
    handles = [_legend_handle(descriptor) for descriptor in descriptors]
    title_lines = []
    if include_context:
        title_lines = (
            resolve_legend_metadata(
                chart,
                sky,
                grid=grid,
            ).title.splitlines()
            if title is None
            else [str(title)]
        )
    if context_lines is not None:
        title_lines.extend(str(line) for line in context_lines)
    if not handles and not title_lines:
        return None
    resolved_title = "\n".join(title_lines)
    legend = ax.legend(
        handles=handles,
        handler_map=_legend_handler_map(),
        loc=config.location,
        fontsize=config.fontsize,
        title=resolved_title or None,
        title_fontsize=config.title_fontsize,
        frameon=config.frame,
        facecolor=config.facecolor,
        edgecolor=config.edgecolor,
        framealpha=config.alpha,
        ncols=config.columns,
    )
    if config.text_color is not None:
        for text in legend.get_texts():
            text.set_color(config.text_color)
        legend.get_title().set_color(config.text_color)
    legend.set_zorder(100)
    setattr(
        legend,
        "_wenu_legend_entry_keys",
        tuple(descriptor.key for descriptor in descriptors),
    )
    return legend


def add_legend_heading(legend, text, *, fontsize, family, weight, color,
                       separator_width=0.8, gap_mm=3, gid=None):
    """Pack a prominent heading and rule inside the existing legend frame.

    Matplotlib exposes no public multi-font title packer. Keep this optional
    offset-box adaptation here, alongside legend construction; ordinary keys
    retain their original layout and get_title() metadata accessor.
    """
    from matplotlib.offsetbox import TextArea, DrawingArea, VPacker
    renderer = legend.figure.canvas.get_renderer()
    original = legend._legend_title_box
    heading = TextArea(text, textprops=dict(size=fontsize, family=family,
        weight=weight, color=color))
    heading.set_figure(legend.figure)
    width_px = max(child.get_window_extent(renderer).width for child in
                   (heading, original, legend._legend_handle_box))
    width = width_px / renderer.points_to_pixels(1)
    rule = DrawingArea(width, separator_width, 0, 0)
    line = Line2D([0, width], [separator_width / 2] * 2,
                  color=color, linewidth=separator_width)
    rule.add_artist(line)
    title = VPacker(children=[heading, rule, original], align="left", pad=0,
                    sep=gap_mm * 72 / 25.4)
    title._text = original._text
    legend._legend_box.get_children()[0] = title
    legend._legend_title_box = title
    title.set_figure(legend.figure)
    if gid is not None:
        heading._text.set_gid(gid + "-heading")
        line.set_gid(gid + "-separator")
    legend._wenu_heading = heading._text
    legend._wenu_separator = line
    return heading._text, line
