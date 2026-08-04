"""Canonical rendering of celestial reference chart furniture."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from wenu.charts.context import BoundaryKind
from wenu.rendering import layers
from wenu.rendering.preparation import project_geometry_for_viewport
from wenu.sky import CelestialSphere
from wenu.sky.coordinate_grids import (
    EclipticGrid,
    EquatorialGrid,
    GalacticGrid,
)


@dataclass(frozen=True)
class CelestialReferenceRendering:
    """Inspectable result of one render-local reference overlay."""

    sky: CelestialSphere
    rendering: object


@dataclass(frozen=True)
class BoundaryAwareReferenceAnchor:
    """Choose a finite curve point in an unoccupied interior region."""

    context: object
    inset: float = 0.68
    avoid_locations: tuple[str, ...] = ()

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
            inside &= radial <= radius * (1.0 + 1.0e-6)
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
            target = radius * 0.62
            index = indices[np.argmin(np.abs(radial[indices] - target))]
        else:
            distance = (
                (normalized_x[indices] - 0.5) ** 2
                + (normalized_y[indices] - 0.5) ** 2
            )
            index = indices[np.argmin(distance)]
        return float(x[index]), float(y[index])


def _explicit_anchor(position):
    def anchor(curve, ax=None):
        return position

    return anchor


class _SingleReferenceLabelAnchor:
    """Return at most one successful anchor for a semantic reference."""

    def __init__(self, delegate):
        self.delegate = delegate
        self.used = False

    def __call__(self, curve, ax=None):
        if self.used:
            return None
        anchor = self.delegate(curve, ax)
        if anchor is not None:
            self.used = True
        return anchor


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


def _label_anchor(annotation, composition):
    if annotation.anchor is not None:
        delegate = _explicit_anchor(annotation.anchor)
    else:
        delegate = BoundaryAwareReferenceAnchor(
            composition.context,
            avoid_locations=_occupied_legend_locations(composition),
        )
    return _SingleReferenceLabelAnchor(
        delegate,
    )


def _publication_style(style):
    converter = getattr(style, "as_publication_style", None)
    return converter() if callable(converter) else style


def _add_selected_poles(points, system, selection, **style):
    if selection == "none":
        return
    add = getattr(points, f"add_{system}_pole")
    poles = ("visible",) if selection == "visible" else ("north", "south")
    for pole in poles:
        add(pole=pole, marker="x", **style)


def build_celestial_reference_sky(sky, composition):
    """Build an unregistered reference-only sky for one composition."""
    furniture = composition.furniture
    if furniture is None:
        return None
    references = furniture.references
    poles = furniture.poles
    requested = (
        references.celestial_equator.enabled
        or references.ecliptic.enabled
        or references.galactic_plane.enabled
        or any(
            value != "none"
            for value in (poles.celestial, poles.ecliptic, poles.galactic)
        )
    )
    if not requested:
        return None

    reference_sky = CelestialSphere(sky.observer)
    if references.celestial_equator.enabled:
        reference_sky.add(
            EquatorialGrid(
                sky.observer,
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
                sky.observer,
                longitude=(),
                latitude=(),
                include_ecliptic=True,
            )
        )
    if references.galactic_plane.enabled:
        reference_sky.add(
            GalacticGrid(
                sky.observer,
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
    return reference_sky


def _reference_layer_options(reference_sky, composition, chart):
    style = _publication_style(composition.style)
    minimum = getattr(chart, "horizon_altitude_deg", None)
    options = style.layer_options(
        reference_sky,
        horizon_altitude_deg=minimum,
    )
    annotations = composition.furniture.references
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
        render["draw_labels"] = annotation.labeled
        render["label_formatter"] = lambda name, text=annotation.label: text
        render["label_anchor"] = _label_anchor(
            annotation,
            composition,
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
):
    """Draw requested references through the canonical geometry pipeline."""
    reference_sky = build_celestial_reference_sky(sky, composition)
    if reference_sky is None:
        return None
    projection = chart.projection
    viewport = chart.viewport
    rendering = reference_sky.draw_chart(
        projection=projection,
        renderer=renderer,
        viewport=viewport,
        layer_options=_reference_layer_options(
            reference_sky,
            composition,
            chart,
        ),
        project_geometry=lambda spherical: project_geometry_for_viewport(
            spherical,
            projection=projection,
            viewport=viewport,
        ),
    )
    return CelestialReferenceRendering(
        sky=reference_sky,
        rendering=rendering,
    )
