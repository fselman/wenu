"""Canonical rendering of celestial reference chart furniture."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from wenu.charts.context import BoundaryKind
from wenu.rendering import layers
from wenu.rendering.preparation import project_geometry_for_viewport
from wenu.sky import CelestialSphere
from wenu.sky.coordinate_grids import EclipticGrid, GalacticGrid


@dataclass(frozen=True)
class CelestialReferenceRendering:
    """Inspectable result of one render-local reference overlay."""

    sky: CelestialSphere
    rendering: object


@dataclass(frozen=True)
class BoundaryAwareReferenceAnchor:
    """Choose a finite curve point inside the final chart footprint."""

    context: object
    inset: float = 0.88

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
        inside = (
            (x >= viewport.x_min)
            & (x <= viewport.x_max)
            & (y >= viewport.y_min)
            & (y <= viewport.y_max)
        )
        boundary = self.context.clip_boundary
        if (
            self.context.boundary_kind == BoundaryKind.CIRCULAR
            and boundary is not None
        ):
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
            if not np.any(inside):
                return None
            indices = np.flatnonzero(inside)
            target = radius * float(self.inset)
            index = indices[np.argmin(np.abs(radial[indices] - target))]
        else:
            if not np.any(inside):
                return None
            indices = np.flatnonzero(inside)
            target = (
                viewport.y_min
                + float(self.inset) * viewport.height
            )
            index = indices[np.argmin(np.abs(y[indices] - target))]
        return float(x[index]), float(y[index])


def _explicit_anchor(position):
    def anchor(curve, ax=None):
        return position

    return anchor


def _label_anchor(annotation, context):
    if annotation.anchor is not None:
        return _explicit_anchor(annotation.anchor)
    return BoundaryAwareReferenceAnchor(context)


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
        references.ecliptic.enabled
        or references.galactic_plane.enabled
        or any(
            value != "none"
            for value in (poles.celestial, poles.ecliptic, poles.galactic)
        )
    )
    if not requested:
        return None

    reference_sky = CelestialSphere(sky.observer)
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
        if system not in {"ecliptic", "galactic"}:
            continue
        annotation = (
            annotations.ecliptic
            if system == "ecliptic"
            else annotations.galactic_plane
        )
        configured = dict(options[layer])
        render = dict(configured["render"])
        render["draw_labels"] = annotation.labeled
        render["label_formatter"] = lambda name, text=annotation.label: text
        render["label_anchor"] = _label_anchor(
            annotation,
            composition.context,
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
