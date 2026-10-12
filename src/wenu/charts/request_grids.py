"""Request-time semantic coordinate-grid configuration."""

from __future__ import annotations

from math import floor

from wenu.sky.coordinate_grids import CoordinatesGrid

from .detail import COORDINATE_GRID_LAYERS
from .request import ChartRequest


def requested_coordinate_grids(detail):
    """Return the semantic grids explicitly requested by detail overrides."""
    requested = set(detail.grid_label_layers or ())
    if getattr(detail, "equatorial_grid_marks", None) is not None:
        requested.add("equatorial_grid")
    all_requested = False
    for names in (detail.enabled_layers, detail.enabled_layer_additions):
        if not names:
            continue
        if "coordinate_grids" in names:
            all_requested = True
        requested.update(set(names) & COORDINATE_GRID_LAYERS)
    disabled = set(detail.disabled_layers or ())
    if all_requested and "coordinate_grids" not in disabled:
        requested.update(COORDINATE_GRID_LAYERS)
    return frozenset(requested - disabled)


def _latitude_values(limit, step, *, include_zero=False):
    count = int(limit // step)
    values = {index * step for index in range(-count, count + 1)}
    if include_zero:
        values.add(0)
    else:
        values.discard(0)
    return tuple(sorted(values))


def _declination_values(step, *, include_zero=False):
    count = int(floor((90.0 - 1.0e-12) / float(step)))
    positive = tuple(float(step) * index for index in range(1, count + 1))
    values = {-value for value in positive} | set(positive)
    if include_zero:
        values.add(0.0)
    return tuple(sorted(values))


def _circumpolar_declinations(values, frame):
    limit = float(frame.limiting_declination_deg)
    if limit < 0.0:
        return tuple(value for value in values if -90.0 < value < limit)
    return tuple(value for value in values if limit < value < 90.0)


def _view_span_deg(family, frame):
    if frame is not None:
        diameter = getattr(frame, "field_diameter_deg", None)
        if diameter is not None:
            return float(diameter)
        dimensions = tuple(
            value for value in (
                getattr(frame, "field_width_deg", None),
                getattr(frame, "field_height_deg", None),
            ) if value is not None
        )
        if dimensions:
            return max(map(float, dimensions))
        limiting = getattr(frame, "limiting_declination_deg", None)
        if limiting is not None:
            return 2.0 * (90.0 - abs(float(limiting)))
    if family == "all_sky":
        return 360.0
    return 180.0 if family == "planisphere" else 60.0


def _grid_specifications(family, frame=None, detail=None, *, equinox="J2000"):
    span = _view_span_deg(family, frame)
    if family == "circumpolar":
        step = 30
    elif family == "regional" and span <= 60.0:
        step = 15
    else:
        step = 15 if span < 60.0 else 30
    longitudes = tuple(range(0, 360, step))
    latitudes = _latitude_values(
        75, step, include_zero=family == "all_sky"
    )
    galactic_longitudes = longitudes
    galactic_latitudes = latitudes
    declination_step = getattr(
        detail, "equatorial_declination_step_deg", None
    )
    equatorial_latitudes = _declination_values(
        step if declination_step is None else declination_step,
        include_zero=True,
    )
    equatorial_longitudes = longitudes
    marks = getattr(detail, "equatorial_grid_marks", None)
    if marks is not None:
        equatorial_longitudes = tuple(range(0, 360, 15))
        equatorial_latitudes = _declination_values(10, include_zero=True)
    if family == "circumpolar" and frame is not None:
        equatorial_latitudes = _circumpolar_declinations(
            equatorial_latitudes, frame
        )
    if family == "all_sky":
        galactic_longitudes = tuple(range(0, 360, 45))
        galactic_latitudes = tuple(range(-60, 61, 30))
    samples = 721 if step == 15 else 1441
    return {
        "equatorial_grid": {
            "ra": equatorial_longitudes,
            "dec": equatorial_latitudes,
            "frame": "fk5",
            "equinox": equinox,
            "samples": samples,
            "meridian_dec_min": -90.0 if marks is not None else -75.0,
            "meridian_dec_max": 90.0,
        },
        "ecliptic_grid": {
            "longitude": longitudes,
            "latitude": latitudes,
            "equinox": equinox,
            "samples": samples,
            "include_ecliptic": False,
        },
        "galactic_grid": {
            "longitude": galactic_longitudes,
            "latitude": galactic_latitudes,
            "samples": samples,
            "include_plane": False,
        },
        "altaz_grid": {
            "azimuth": longitudes,
            "altitude": tuple(range(step, 90, step)),
            "samples": samples,
            "include_horizon": False,
        },
    }


def validate_equatorial_grid_marks(request):
    """Reject unsupported presets before mutating a supplied sky or exporting."""
    if request.detail.equatorial_grid_marks is None:
        return
    if request.family != "regional" or request.coordinate_frame != "horizontal":
        raise ValueError("Equatorial edge marks require an ordinary regional or native atlas-sheet request.")
    if request.detail.equatorial_declination_step_deg not in (None, 10.0):
        raise ValueError("The edge-mark preset requires 10-degree declination lines.")
    # The preset is an explicit individual grid selection. Like other individual
    # additions, it takes precedence over the general coordinate_grids alias.
    if "equatorial_grid" in set(request.detail.disabled_layers or ()):
        raise ValueError("Equatorial edge marks cannot disable their grid layer.")


def configure_chart_request_grids(sky, request, *, frame=None, observer=None):
    """Replace request-time grids with the selected family configuration."""
    if not isinstance(request, ChartRequest):
        raise TypeError("request must be a ChartRequest.")
    validate_equatorial_grid_marks(request)
    if not hasattr(sky, "layers") or not callable(getattr(sky, "remove", None)):
        raise TypeError("sky must provide registered layers and remove().")

    for layer in tuple(sky.layers):
        if isinstance(layer, CoordinatesGrid):
            sky.remove(layer)

    requested = requested_coordinate_grids(request.detail)
    specifications = _grid_specifications(
        request.family, frame, request.detail,
        equinox=request.reference_policy.resolved_equinox(
            getattr(sky, "observer", None) if observer is None else observer
        ),
    )
    configured = []
    for name, method_name in (
        ("equatorial_grid", "add_equatorial_grid"),
        ("ecliptic_grid", "add_ecliptic_grid"),
        ("galactic_grid", "add_galactic_grid"),
        ("altaz_grid", "add_altaz_grid"),
    ):
        if name in requested:
            if (
                name == "equatorial_grid"
                and request.coordinate_frame == "ecliptic"
            ):
                from wenu.sky.frozen_earth_reference_grids import (
                    FrozenEarthEquatorialGrid,
                )
                from .request_realization import (
                    chart_request_realization_context,
                )

                resolved_observer = (
                    getattr(sky, "observer", None)
                    if observer is None else observer
                )
                context = chart_request_realization_context(
                    request, resolved_observer
                )
                layer = FrozenEarthEquatorialGrid(
                    resolved_observer,
                    product_coordinate_spec=(
                        context.product_coordinate_spec
                    ),
                    **specifications[name],
                )
                sky.add(layer)
                configured.append(layer)
                continue
            configured.append(
                getattr(sky, method_name)(**specifications[name])
            )
    return tuple(configured)



def equatorial_grid_tick_options(name, *, minor_scale):
    """Chart-owned coordinate typography; renderer consumes only mark records."""
    if name.startswith("right_ascension_"):
        minutes = round(float(name.removeprefix("right_ascension_")) * 4) % 1440
        hour, minute = divmod(minutes, 60)
        label = f"{hour}ʰ" if minute == 0 else f"{minute}ᵐ" if minute in (20, 40) else None
        scale = 1.0 if minute == 0 else minor_scale
        length = 4.0 if minute == 0 else 3.0 if label else 2.0
    else:
        value = float(name.removeprefix("declination_"))
        label, scale, length = f"{value:+g}°", 1.0, 4.0
    return dict(label=label, font_scale=scale, length_points=length,
                label_rotation="perpendicular" if name.startswith("declination_") else None,
                label_lane=2 if name.startswith("declination_") else 0 if minute == 0 else 1,
                style=dict(color="black", linewidth=0.8, alpha=1.0, linestyle="-", zorder=4))


def equatorial_grid_mark_options(chart, presentation):
    """Request-local grid definitions; saved source data remains unchanged."""
    from functools import partial
    from .boundaries import ExteriorGridLabelAnchor
    from wenu.geometry.projected import ProjectedCurve
    view = chart.viewport
    boundary = ProjectedCurve([view.x_min, view.x_max, view.x_max, view.x_min],
                             [view.y_min, view.y_min, view.y_max, view.y_max], closed=True)
    ticks = partial(equatorial_grid_tick_options, minor_scale=presentation.grid_minor_label_scale)
    return {"equatorial_grid": dict(
        geometry=dict(ra=tuple(range(0, 360, 15)), dec=tuple(range(-80, 81, 10)),
                      ra_ticks=tuple(index * 2.5 for index in range(144)),
                      dec_ticks=tuple(range(-80, 81, 10))),
        render=dict(draw_labels=False,
                    style=dict(color="black", alpha=0.9,
                               linewidth=0.65 if presentation.grid_lines_visible else 0),
                    label_style=dict(fontsize=presentation.grid_label_fontsize, color="black", alpha=1.0),
                    boundary_ticks=dict(tick_meridians=ticks, tick_parallels=ticks),
                    boundary_tick_anchor=ExteriorGridLabelAnchor(None, boundary, all_crossings=True)))}


def equatorial_grid_frame_layout(width_mm, height_mm, axes_bounds, style, presentation):
    """Uniform sky reduction reserves the wider physical coordinate frame."""
    from dataclasses import replace
    from types import SimpleNamespace
    left, bottom, width, height = axes_bounds
    page = SimpleNamespace(width_mm=width_mm, height_mm=height_mm,
        inner_mm=left*width_mm, bottom_mm=bottom*height_mm,
        useful_width_mm=width*width_mm, useful_height_mm=height*height_mm)
    canvas = style.canvas
    baseline = max(8.5, presentation.grid_label_fontsize) + 2 * (
        canvas.grid_label_band_padding_points + canvas.grid_label_band_linewidth / 2)
    width = baseline * presentation.grid_frame_width_scale
    padding = (width - max(8.5, presentation.grid_label_fontsize)) / 2 - canvas.grid_label_band_linewidth / 2
    if padding < 0:
        raise ValueError("grid_frame_width_scale is too small for the labels.")
    # Reserve a conservative two-label lane where RA and Dec cross together.
    # This is font measurement, not another sky realization or a changed viewport.
    from matplotlib.backends.backend_agg import RendererAgg
    from matplotlib.font_manager import FontProperties
    measure = RendererAgg(1, 1, 72)
    font = FontProperties(size=presentation.grid_label_fontsize)
    def text_width(text):
        return measure.get_text_width_height_descent(text, font, ismath=False)[0]
    ra_width = max(text_width(f"{hour}ʰ") for hour in range(24))
    dec_width = max(text_width(f"{value:+g}°") for value in range(-80,81,10))
    reserve = max(width, ra_width + dec_width + 2 + 2 * (
        canvas.grid_label_band_padding_points + canvas.grid_label_band_linewidth / 2))
    inset_mm = reserve * 25.4 / 72.0
    factor = min(1 - 2 * inset_mm / page.useful_width_mm,
                 1 - 2 * inset_mm / page.useful_height_mm)
    if factor <= 0:
        raise ValueError("Coordinate frame does not fit the useful page.")
    width_mm, height_mm = page.useful_width_mm * factor, page.useful_height_mm * factor
    bounds = ((page.inner_mm + (page.useful_width_mm - width_mm) / 2) / page.width_mm,
              (page.bottom_mm + (page.useful_height_mm - height_mm) / 2) / page.height_mm,
              width_mm / page.width_mm, height_mm / page.height_mm)
    return bounds, replace(style, canvas=replace(canvas,
        grid_label_band=True, grid_label_band_padding_points=padding))
