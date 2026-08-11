"""Canonical composition and export for declarative chart requests."""

from __future__ import annotations

from dataclasses import dataclass, replace

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
from .request_resolver import resolve_chart_request


@dataclass(frozen=True)
class ChartRequestGeneration:
    """Completed exports produced from one immutable chart request."""

    exports: tuple[ChartExportResult, ...]

    @property
    def outputs(self):
        """Return the deterministic paths written by this request."""
        return tuple(result.output for result in self.exports)


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
        "circumpolar": "Circumpolar sky",
    }.get(request.family, request.family.title())


def export_prepared_chart(sky, prepared):
    """Compose and export every requested product exactly once."""
    if not isinstance(prepared, PreparedChartRequest):
        raise TypeError("prepared must be a PreparedChartRequest.")
    if getattr(sky, "observer", None) is None:
        raise TypeError("sky must provide its scientific observer.")

    from matplotlib import pyplot as plt

    chart = prepared.chart
    request = prepared.resolved.request
    detail = replace(
        request.detail,
        content_selection=request.content,
    )
    title = _request_title(prepared)
    exports = []
    for product, output in request.product.outputs(
        stem=_request_stem(prepared)
    ):
        composition = compose_chart(
            chart,
            style=product.style,
            mode=product.mode,
            detail_overrides=detail,
            furniture=request.furniture,
        )
        figure, ax = plt.subplots(figsize=(
            composition.mode.width_inches,
            composition.mode.height_inches,
        ))
        try:
            composition.style.configure_axes(ax, title=title)
            result = chart.export(
                sky,
                MatplotlibRenderer(ax),
                output,
                composition=composition,
            )
        finally:
            plt.close(figure)
        exports.append(result)
    return ChartRequestGeneration(exports=tuple(exports))


def generate_chart_request(
    request,
    *,
    sky=None,
    profile=None,
):
    """Resolve and export a request using an owned or supplied sphere."""
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
        profile = available_profile
        resolved = resolve_chart_request(request, profile)
        prepared = prepare_chart_request(sky, resolved)
        return export_prepared_chart(sky, prepared)

    profile = (
        CANONICAL_MAXIMAL_SPHERE_PROFILE if profile is None else profile
    )
    observer = Observer(**request.observer.observer_kwargs())
    try:
        sky = build_maximal_sphere(observer, profile=profile)
        resolved = resolve_chart_request(request, profile)
        prepared = prepare_chart_request(sky, resolved)
        return export_prepared_chart(sky, prepared)
    finally:
        observer.close()
