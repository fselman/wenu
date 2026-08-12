"""Canonical composition and export for declarative chart requests."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from wenu.observer import Observer
from wenu.rendering.matplotlib import MatplotlibRenderer
from wenu.sky.maximal_sphere import (
    CANONICAL_MAXIMAL_SPHERE_PROFILE,
    build_maximal_sphere,
)

from .composition import compose_chart
from .export_workflow import ChartExportResult
from .request import ChartRequest
from .request_chart import PreparedChartRequest, prepare_chart_request
from .request_grids import configure_chart_request_grids
from .request_furniture import resolve_request_furniture_context
from .request_resolver import resolve_chart_request


@dataclass(frozen=True)
class ChartRequestGeneration:
    """Completed exports produced from one immutable chart request."""

    exports: tuple[ChartExportResult, ...]

    @property
    def outputs(self):
        """Return the deterministic paths written by this request."""
        return tuple(result.output for result in self.exports)


@dataclass
class ChartRequestBuild:
    """Prepared request plus explicit ownership of its reusable sphere."""

    sky: object
    prepared: PreparedChartRequest
    owns_observer: bool = False
    _closed: bool = field(default=False, init=False, repr=False)

    @property
    def chart(self):
        return self.prepared.chart

    def close(self):
        """Close an owned observer once; leave supplied spheres untouched."""
        if self.owns_observer and not self._closed:
            self.sky.observer.close()
        self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        del exc_type, exc_value, traceback
        self.close()


def _request_stem(prepared):
    resolved = prepared.resolved
    if resolved.target is not None:
        subject = resolved.target.key
    elif resolved.constellations is not None:
        subject = resolved.constellations.key
    else:
        subject = None
    return (
        resolved.request.family
        if subject is None
        else f"{resolved.request.family}-{subject}"
    )


def _request_title(prepared):
    resolved = prepared.resolved
    request = resolved.request
    if request.title is not None:
        return request.title
    if resolved.target is not None:
        return resolved.target.display_name
    if resolved.constellations is not None:
        return resolved.constellations.display_name
    return {
        "planisphere": "Planisphere",
        "all_sky": "Galactic all-sky map",
        "circumpolar": "Circumpolar sky",
    }.get(request.family, request.family.title())


def export_prepared_chart(sky, prepared, *, observer=None):
    """Compose and export every requested product exactly once."""
    if not isinstance(prepared, PreparedChartRequest):
        raise TypeError("prepared must be a PreparedChartRequest.")
    resolved_observer = getattr(sky, "observer", None) if observer is None else observer
    if resolved_observer is None:
        raise TypeError("request export requires an observer.")

    from matplotlib import pyplot as plt

    chart = prepared.chart
    request = prepared.resolved.request
    detail = replace(
        request.detail,
        content_selection=request.content,
    )
    furniture_options = {}
    if observer is not None:
        furniture_options["observer"] = resolved_observer
    furniture = resolve_request_furniture_context(
        request.furniture, chart, sky, **furniture_options
    )
    title = _request_title(prepared)
    exports = []
    for product, output in request.product.outputs(
        stem=_request_stem(prepared)
    ):
        product_composition = request.composition_for(product)
        composition = compose_chart(
            chart,
            style=product.style,
            mode=product.mode,
            detail=(
                None
                if product_composition is None
                else product_composition.detail
            ),
            detail_overrides=detail,
            style_overrides=(
                None
                if product_composition is None
                else product_composition.style_overrides
            ),
            furniture=furniture,
        )
        figure, ax = plt.subplots(figsize=(
            composition.mode.width_inches,
            composition.mode.height_inches,
        ))
        try:
            composition.style.configure_axes(ax, title=title)
            export_options = {"composition": composition}
            if observer is not None:
                export_options["observer"] = resolved_observer
            result = chart.export(
                sky,
                MatplotlibRenderer(ax),
                output,
                **export_options,
            )
        finally:
            plt.close(figure)
        exports.append(result)
    return ChartRequestGeneration(exports=tuple(exports))


def _prepare_with_sphere(request, sky, profile, *, owns_observer):
    resolved = resolve_chart_request(request, profile)
    configure_chart_request_grids(
        sky,
        resolved.request,
        frame=getattr(resolved, "frame", None),
    )
    prepared = prepare_chart_request(sky, resolved)
    return ChartRequestBuild(
        sky=sky,
        prepared=prepared,
        owns_observer=owns_observer,
    )


def build_chart_request(request, *, sky=None, profile=None):
    """Prepare any chart request using an owned or supplied maximal sphere."""
    if not isinstance(request, ChartRequest):
        raise TypeError("request must be a ChartRequest.")
    if sky is not None:
        observer = getattr(sky, "observer", None)
        if observer is None:
            raise TypeError("sky must provide its scientific observer.")
        if not request.observer.matches(observer):
            raise ValueError(
                "The supplied sphere observer does not match the chart "
                "request."
            )
        available_profile = getattr(sky, "load_profile", None)
        if available_profile is None:
            raise ValueError(
                "The supplied sphere does not declare a load profile."
            )
        if profile is not None and profile != available_profile:
            raise ValueError(
                "The supplied sphere load profile does not match profile."
            )
        return _prepare_with_sphere(
            request, sky, available_profile, owns_observer=False
        )

    profile = (
        CANONICAL_MAXIMAL_SPHERE_PROFILE if profile is None else profile
    )
    observer = Observer(**request.observer.observer_kwargs())
    try:
        sky = build_maximal_sphere(observer, profile=profile)
        return _prepare_with_sphere(
            request, sky, profile, owns_observer=True
        )
    except BaseException:
        observer.close()
        raise


def generate_chart_request(
    request,
    *,
    sky=None,
    profile=None,
):
    """Resolve and export a request using an owned or supplied sphere."""
    build = build_chart_request(request, sky=sky, profile=profile)
    try:
        return export_prepared_chart(build.sky, build.prepared)
    finally:
        build.close()
