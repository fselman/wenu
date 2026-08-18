"""Matplotlib-facing rendering of canonical figure-margin footers."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version


@dataclass(frozen=True)
class ChartFooterRendering:
    """Inspectable artists and resolved text for one chart footer."""

    copyright_text: str | None
    application_text: str | None
    artists: tuple[object, ...]


def installed_wenu_version() -> str:
    """Return installed package metadata without hard-coding a release."""
    try:
        return version("wenu")
    except PackageNotFoundError:
        return "0+unknown"


def resolved_footer_text(footer, *, package_version=None):
    """Resolve independent left and right footer strings."""
    application = None
    if footer.application:
        application = footer.application_name
        if footer.include_version:
            resolved_version = (
                installed_wenu_version()
                if package_version is None
                else str(package_version)
            )
            application = f"{application} {resolved_version}"
    return footer.copyright, application


def draw_chart_footer(
    renderer,
    footer,
    mode,
    *,
    color="black",
    package_version=None,
    layout=None,
) -> ChartFooterRendering | None:
    """Draw requested credits below the axes in the figure margin."""
    copyright_text, application_text = resolved_footer_text(
        footer,
        package_version=package_version,
    )
    if copyright_text is None and application_text is None:
        return None

    ax = renderer.ax
    figure = ax.figure
    if layout is None:
        from wenu.configuration import (
            packaged_furniture_product_export_defaults,
        )

        layout = packaged_furniture_product_export_defaults().footer_layout
    font_size = layout.font_size * float(
        getattr(mode, "font_scale", 1.0)
    )
    position = ax.get_position()
    left = float(position.x0)
    width = float(position.width)
    top = float(position.y1)
    figure_height = float(figure.get_size_inches()[1])
    text_height = font_size / 72.0 / figure_height
    clearance = 1.35 * text_height
    bottom = max(float(position.y0), float(layout.y) + clearance)
    if bottom < top and bottom != float(position.y0):
        ax.set_position([left, bottom, width, top - bottom])
    footer_y = max(float(layout.y), bottom - clearance)
    left_x = max(float(layout.left_x), left)
    right_x = min(float(layout.right_x), left + width)
    common = dict(
        y=footer_y,
        fontsize=font_size,
        color=str(color),
        va="bottom",
    )
    artists = []
    if copyright_text is not None:
        artists.append(
            figure.text(
                left_x,
                s=copyright_text,
                ha="left",
                **common,
            )
        )
    if application_text is not None:
        artists.append(
            figure.text(
                right_x,
                s=application_text,
                ha="right",
                **common,
            )
        )
    return ChartFooterRendering(
        copyright_text=copyright_text,
        application_text=application_text,
        artists=tuple(artists),
    )
