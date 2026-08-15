"""Canonical rendering of celestial reference chart furniture."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from wenu.charts.context import BoundaryKind
from wenu.charts.coordinate_frames import horizontal_to_equatorial
from wenu.geometry.projected import ProjectedCurve, ProjectedCurves
from wenu.geometry.spherical import SphericalGrid
from wenu.rendering import layers
from wenu.rendering.label_placement import tangent_label_placement
from wenu.rendering.preparation import project_geometry_for_viewport
from wenu.sky import CelestialSphere
from wenu.sky.coordinate_grids import (
    EclipticGrid,
    EquatorialGrid,
    GalacticGrid,
)


class _PolarEquatorialGrid(EquatorialGrid):
    """Four RA meridians; declination ticks remain disk furniture."""

    def spherical_geometry(self, observer):
        self._resolve_observer(observer)
        meridians = self._combine(
            [self.meridian(value) for value in self.ra]
        )
        return SphericalGrid(
            components={"meridians": meridians},
            metadata=self._grid_metadata(),
        )


def polar_declination_tick_geometry(
    chart,
    *,
    right_ascensions_deg=(0.0, 90.0, 180.0, 270.0),
    declinations_deg=tuple(float(value) for value in range(-80, 81, 20)),
    half_width_deg=1.5,
):
    """Return short projected declination marks on selected RA meridians."""
    lower = min(
        chart.pole_declination_deg,
        chart.limiting_declination_deg,
    )
    upper = max(
        chart.pole_declination_deg,
        chart.limiting_declination_deg,
    )
    curves = []
    for right_ascension in right_ascensions_deg:
        for declination in declinations_deg:
            if not lower <= declination <= upper:
                continue
            longitude = np.asarray(
                (
                    float(right_ascension) - float(half_width_deg),
                    float(right_ascension) + float(half_width_deg),
                )
            )
            latitude = np.full(2, float(declination))
            x, y = chart.projection.project_spherical(longitude, latitude)
            curves.append(
                ProjectedCurve(
                    x,
                    y,
                    name=(
                        f"declination_tick_{right_ascension:g}_"
                        f"{declination:g}"
                    ),
                )
            )
    return ProjectedCurves(curves)


@dataclass(frozen=True)
class CelestialReferenceRendering:
    """Inspectable result of one render-local reference overlay."""

    sky: CelestialSphere
    rendering: object
    declination_tick_artists: tuple[object, ...] = ()


@dataclass(frozen=True)
class BoundaryAwareReferenceAnchor:
    """Choose a finite curve point in an unoccupied interior region."""

    context: object
    inset: float = 0.68
    avoid_locations: tuple[str, ...] = ()
    reservations: object | None = None

    def __post_init__(self):
        if not 0.0 < float(self.inset) <= 1.0:
            raise ValueError("inset must be in the interval (0, 1].")

    def __call__(self, curve, ax=None):
        finite = curve.finite
        if not np.any(finite):
            return None
        x = np.asarray(curve.x[finite], dtype=float)
        y = np.asarray(curve.y[finite], dtype=float)
        viewport = self.context.viewport
        normalized_x = (x - viewport.x_min) / viewport.width
        normalized_y = (y - viewport.y_min) / viewport.height
        margin = (1.0 - float(self.inset)) / 2.0
        inside = (
            (normalized_x >= margin)
            & (normalized_x <= 1.0 - margin)
            & (normalized_y >= margin)
            & (normalized_y <= 1.0 - margin)
        )
        boundary = self.context.clip_boundary
        circular = (
            self.context.boundary_kind == BoundaryKind.CIRCULAR
            and boundary is not None
        )
        if circular:
            boundary_finite = boundary.finite
            radius = float(
                np.nanmedian(
                    np.hypot(
                        boundary.x[boundary_finite],
                        boundary.y[boundary_finite],
                    )
                )
            )
            radial = np.hypot(x, y)
            inside = radial <= radius * (
                1.0 - margin + 1.0e-6
            )
        for location in self.avoid_locations:
            horizontal = str(location).lower()
            if "right" in horizontal:
                horizontal_mask = normalized_x >= 0.50
            elif "left" in horizontal:
                horizontal_mask = normalized_x <= 0.50
            else:
                horizontal_mask = np.ones_like(inside)
            if "upper" in horizontal:
                vertical_mask = normalized_y >= 0.58
            elif "lower" in horizontal:
                vertical_mask = normalized_y <= 0.46
            else:
                vertical_mask = np.ones_like(inside)
            inside &= ~(horizontal_mask & vertical_mask)
        if not np.any(inside):
            return None
        indices = np.flatnonzero(inside)
        if circular:
            target = radius * 0.78
            order = indices[
                np.argsort(np.abs(radial[indices] - target))
            ]
        else:
            edge_distance = np.minimum.reduce(
                (
                    normalized_x[indices],
                    1.0 - normalized_x[indices],
                    normalized_y[indices],
                    1.0 - normalized_y[indices],
                )
            )
            order = indices[np.argsort(edge_distance)]
        for index in order:
            anchor = float(x[index]), float(y[index])
            if self.reservations is None or self.reservations.claim(anchor):
                return anchor
        return None


class _ReferenceLabelReservations:
    """Reserve separated normalized positions during one reference render."""

    def __init__(self, context, minimum_separation=0.10):
        self.context = context
        self.minimum_separation = float(minimum_separation)
        self.positions = []

    def _normalized(self, anchor):
        viewport = self.context.viewport
        return (
            (float(anchor[0]) - viewport.x_min) / viewport.width,
            (float(anchor[1]) - viewport.y_min) / viewport.height,
        )

    def claim(self, anchor, *, force=False):
        normalized = self._normalized(anchor)
        separated = all(
            np.hypot(
                normalized[0] - occupied[0],
                normalized[1] - occupied[1],
            )
            >= self.minimum_separation
            for occupied in self.positions
        )
        if separated or force:
            self.positions.append(normalized)
            return True
        return False


def _explicit_anchor(position, reservations=None):
    def anchor(curve, ax=None):
        if reservations is not None:
            reservations.claim(position, force=True)
        return position

    return anchor


class _SingleReferenceLabelAnchor:
    """Return at most one successful anchor for a semantic reference."""

    def __init__(self, delegate, *, down_toward=None):
        self.delegate = delegate
        self.down_toward = down_toward
        self.used = False

    def __call__(self, curve, ax=None):
        if self.used:
            return None
        anchor = self.delegate(curve, ax)
        if anchor is not None:
            self.used = True
            return tangent_label_placement(
                curve,
                anchor,
                normal_offset_em=0.75,
                down_toward=self.down_toward,
            )
        return None


def _occupied_legend_locations(composition):
    legends = composition.legends
    if legends is None:
        return ()
    placements = (legends.plan.objects, legends.plan.stars)
    return tuple(
        placement.location
        for placement in placements
        if placement.enabled and not placement.outside
    )


def _label_anchor(
    annotation,
    composition,
    reservations,
    *,
    down_toward=None,
):
    if annotation.anchor is not None:
        delegate = _explicit_anchor(annotation.anchor, reservations)
    else:
        delegate = BoundaryAwareReferenceAnchor(
            composition.context,
            avoid_locations=_occupied_legend_locations(composition),
            reservations=reservations,
        )
    return _SingleReferenceLabelAnchor(
        delegate,
        down_toward=down_toward,
    )


def _publication_style(style):
    converter = getattr(style, "as_publication_style", None)
    return converter() if callable(converter) else style


def _add_selected_poles(points, system, selection, **style):
    if selection == "none":
        return
    add = getattr(points, f"add_{system}_pole")
    if selection in {"visible", "north", "south"}:
        poles = (selection,)
    else:
        poles = ("north", "south")
    marker = "+" if system == "equatorial" else "x"
    for pole in poles:
        add(pole=pole, marker=marker, **style)


def build_celestial_reference_sky(
    sky, composition, *, observer=None, chart=None
):
    """Build an unregistered reference-only sky for one composition."""
    furniture = composition.furniture
    if furniture is None:
        return None
    references = furniture.references
    poles = furniture.poles
    target = (
        None
        if chart is None or getattr(chart, "target_ra_deg", None) is None
        else (chart.target_ra_deg, chart.target_dec_deg)
    )
    polar = getattr(chart, "chart_type", None) == "polar_planisphere"
    polar_grid = polar and composition.detail.layer_enabled(
        "equatorial_grid"
    )
    requested = (
        polar_grid
        or references.celestial_equator.enabled
        or references.ecliptic.enabled
        or references.galactic_plane.enabled
        or any(
            value != "none"
            for value in (poles.celestial, poles.ecliptic, poles.galactic)
        )
        or target is not None
    )
    if not requested:
        return None

    resolved_observer = getattr(sky, "observer", None) if observer is None else observer
    if resolved_observer is None:
        raise TypeError("celestial reference furniture requires an observer.")
    reference_sky = CelestialSphere(resolved_observer)
    if polar_grid:
        reference_sky.add(
            _PolarEquatorialGrid(
                resolved_observer,
                ra=(0.0, 90.0, 180.0, 270.0),
                dec=tuple(float(value) for value in range(-80, 81, 20)),
                include_equator=False,
                frame="fk5",
                equinox="J2000",
            )
        )
    if references.celestial_equator.enabled:
        reference_sky.add(
            EquatorialGrid(
                resolved_observer,
                ra=(),
                dec=(),
                include_equator=True,
                frame="fk5",
                equinox="J2000",
            )
        )
    if references.ecliptic.enabled:
        reference_sky.add(
            EclipticGrid(
                resolved_observer,
                longitude=(),
                latitude=(),
                include_ecliptic=True,
            )
        )
    if references.galactic_plane.enabled:
        reference_sky.add(
            GalacticGrid(
                resolved_observer,
                longitude=(),
                latitude=(),
                include_plane=True,
            )
        )

    if any(
        value != "none"
        for value in (poles.celestial, poles.ecliptic, poles.galactic)
    ):
        style = _publication_style(composition.style)
        points = reference_sky.add_points()
        size = 45.0 * composition.mode.symbol_scale
        _add_selected_poles(
            points,
            "equatorial",
            poles.celestial,
            size=size,
            color=style.equatorial_color,
        )
        _add_selected_poles(
            points,
            "ecliptic",
            poles.ecliptic,
            size=size,
            color=style.ecliptic_color,
        )
        _add_selected_poles(
            points,
            "galactic",
            poles.galactic,
            size=size,
            color=style.galactic_color,
        )
        if polar:
            points.add_ecliptic_keypoints(
                marker="x",
                size=18.0 * composition.mode.symbol_scale,
                color=style.ecliptic_color,
                zorder=layers.POINTS,
            )
    if target is not None:
        style = _publication_style(composition.style)
        points = (
            reference_sky.add_points()
            if reference_sky.points is None
            else reference_sky.points
        )
        points.add_equatorial_point(
            target[0],
            target[1],
            marker="+",
            size=80.0 * composition.mode.symbol_scale,
            color=style.foreground_color,
            zorder=layers.LABELS,
            linewidths=1.1 * composition.mode.line_scale,
        )
    return reference_sky


def _reference_layer_options(reference_sky, composition, chart):
    style = _publication_style(composition.style)
    minimum = getattr(chart, "horizon_altitude_deg", None)
    options = style.layer_options(
        reference_sky,
        horizon_altitude_deg=minimum,
    )
    annotations = composition.furniture.references
    reservations = _ReferenceLabelReservations(composition.context)
    down_toward = (
        (0.0, 0.0)
        if getattr(chart, "chart_type", None) == "polar_planisphere"
        else None
    )
    for layer in reference_sky.layers:
        system = getattr(layer, "coordinate_system", None)
        if system not in {"equatorial", "ecliptic", "galactic"}:
            continue
        annotation = {
            "equatorial": annotations.celestial_equator,
            "ecliptic": annotations.ecliptic,
            "galactic": annotations.galactic_plane,
        }[system]
        configured = dict(options[layer])
        render = dict(configured["render"])
        unlabeled_polar_grid = (
            getattr(chart, "chart_type", None) == "polar_planisphere"
            and system == "equatorial"
            and bool(getattr(layer, "ra", ()))
        )
        render["draw_labels"] = (
            annotation.labeled and not unlabeled_polar_grid
        )
        render["label_formatter"] = lambda name, text=annotation.label: text
        render["label_anchor"] = _label_anchor(
            annotation,
            composition,
            reservations,
            down_toward=down_toward,
        )
        label_style = dict(render["label_style"])
        label_style["zorder"] = layers.LABELS
        render["label_style"] = label_style
        configured["render"] = render
        options[layer] = configured

    if reference_sky.points is not None:
        configured = dict(options[reference_sky.points])
        render_callback = configured["render"]

        def render_points(spherical, projected):
            render = dict(render_callback(spherical, projected))
            render["draw_labels"] = composition.furniture.poles.labels
            label_style = dict(render["label_style"])
            label_style.update(
                {
                    "color": style.foreground_color,
                    "fontsize": style.label_fontsize,
                    "zorder": layers.LABELS,
                }
            )
            render["label_style"] = label_style
            return render

        configured["render"] = render_points
        options[reference_sky.points] = configured
    return options


def draw_celestial_reference_furniture(
    chart,
    sky,
    renderer,
    composition,
    *,
    observer=None,
):
    """Draw requested references through the canonical geometry pipeline."""
    reference_sky = build_celestial_reference_sky(
        sky, composition, observer=observer, chart=chart
    )
    if reference_sky is None:
        return None
    projection = chart.projection
    viewport = chart.viewport
    polar = getattr(chart, "chart_type", None) == "polar_planisphere"

    def project(spherical):
        geometry = (
            horizontal_to_equatorial(spherical, observer)
            if polar
            else spherical
        )
        if polar:
            return chart.project_equatorial_geometry(geometry)
        return project_geometry_for_viewport(
            geometry,
            projection=projection,
            viewport=viewport,
        )

    rendering = reference_sky.draw_chart(
        projection=projection,
        renderer=renderer,
        observer=observer,
        viewport=viewport,
        layer_options=_reference_layer_options(
            reference_sky,
            composition,
            chart,
        ),
        project_geometry=project,
    )
    tick_artists = ()
    if polar and composition.detail.layer_enabled("equatorial_grid"):
        style = _publication_style(composition.style)
        tick_artists = tuple(
            renderer.draw(
                polar_declination_tick_geometry(chart),
                style={
                    "color": style.equatorial_color,
                    "linewidth": style.grid_linewidth,
                    "linestyle": style.equatorial_linestyle,
                    "alpha": style.grid_alpha,
                    "zorder": 3,
                },
            )
        )
    return CelestialReferenceRendering(
        sky=reference_sky,
        rendering=rendering,
        declination_tick_artists=tick_artists,
    )
