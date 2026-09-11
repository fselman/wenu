"""Canonical composition and export for declarative chart requests."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace

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
from .request_furniture import (
    binocular_product_title,
    resolve_request_furniture_context,
)
from .request_grids import configure_chart_request_grids
from .request_disks import configure_chart_request_disks
from .request_horizon import configure_chart_request_horizon
from .request_realization import chart_request_realization_context
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
    minor_body_session: object | None = None
    prior_source_resolvers: tuple = ()
    request_minor_body_layers: tuple = ()
    _closed: bool = field(default=False, init=False, repr=False)

    @property
    def chart(self):
        return self.prepared.chart

    def close(self):
        """Close an owned observer once; leave supplied spheres untouched."""
        if not self._closed:
            if self.prior_source_resolvers:
                from wenu.minor_body_resources import (
                    restore_sky_source_resolvers,
                )

                restore_sky_source_resolvers(self.prior_source_resolvers)
            if self.minor_body_session is not None:
                self.minor_body_session.close()
            for layer in self.request_minor_body_layers:
                self.sky.remove(layer)
                self.sky.solar_system_bodies.pop(
                    layer.descriptor.selection_key, None
                )
            if self.owns_observer:
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
        if request.family == "binocular":
            return binocular_product_title(
                resolved.target,
                resolved.frame.field_diameter_deg,
            )
        return resolved.target.display_name
    if resolved.constellations is not None:
        return resolved.constellations.display_name
    return {
        "planisphere": "Planisphere",
        "all_sky": "Galactic all-sky map",
        "circumpolar": "Circumpolar sky",
    }.get(request.family, request.family.title())


def export_prepared_chart(
    sky,
    prepared,
    *,
    observer=None,
    configuration=None,
):
    """Compose and export every requested product exactly once."""
    if not isinstance(prepared, PreparedChartRequest):
        raise TypeError("prepared must be a PreparedChartRequest.")
    resolved_observer = (
        getattr(sky, "observer", None) if observer is None else observer
    )
    if resolved_observer is None:
        raise TypeError("request export requires an observer.")

    from matplotlib import pyplot as plt

    chart = prepared.chart
    request = prepared.resolved.request
    realization_context = chart_request_realization_context(
        request,
        resolved_observer,
    )
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
        composition_options = dict(
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
            reference_policy=request.reference_policy,
        )
        if configuration is not None:
            composition_options["configuration"] = configuration
        composition = compose_chart(chart, **composition_options)
        figure, ax = plt.subplots(figsize=(
            composition.mode.width_inches,
            composition.mode.height_inches,
        ))
        try:
            composition.style.configure_axes(ax, title=title)
            export_options = {
                "composition": composition,
                "horizon_mask": request.horizon_mask,
                "realization_context": realization_context,
            }
            if observer is not None:
                export_options["observer"] = resolved_observer
            from wenu.output_policy import SvgProvenance

            copyright_text = getattr(
                getattr(request.furniture, "footer", None),
                "copyright",
                None,
            )
            provenance = SvgProvenance(
                product_name=request.family,
                title=title,
                parameters=asdict(request),
                copyright=copyright_text,
            )
            export_options["svg_provenance"] = provenance
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


def _prepare_with_sphere(
    request,
    sky,
    profile,
    *,
    owns_observer,
    observer=None,
):
    resolved_observer = getattr(sky, "observer", None) or observer
    session = None
    prior = ()
    request_layers = []
    from wenu.minor_body_resources import (
        MinorBodyResourceSession,
        bind_sky_source_resolver,
        request_minor_body_descriptors,
    )

    if request_minor_body_descriptors(request):
        for descriptor in request.minor_body_descriptors:
            if descriptor.selection_key not in sky.solar_system_bodies:
                request_layers.append(sky.add_solar_system_body(descriptor))
        session = MinorBodyResourceSession(
            request.minor_body_resource_directory,
            resolved_observer,
        )
        prior = bind_sky_source_resolver(sky, session.source_binding)
    try:
        resolved = resolve_chart_request(request, profile)
        grid_options = {"frame": getattr(resolved, "frame", None)}
        if observer is not None:
            grid_options["observer"] = observer
        configure_chart_request_grids(
            sky,
            resolved.request,
            **grid_options,
        )
        configure_chart_request_horizon(sky, resolved.request)
        configure_chart_request_disks(sky, resolved.request)
        from .request_tracks import configure_chart_request_track

        configure_chart_request_track(
            sky,
            resolved.request,
            source_resolver=(
                None if session is None else session.source_binding
            ),
        )
        prepare_options = {}
        if observer is not None:
            prepare_options["observer"] = observer
        prepared = prepare_chart_request(sky, resolved, **prepare_options)
    except BaseException:
        if prior:
            from wenu.minor_body_resources import restore_sky_source_resolvers

            restore_sky_source_resolvers(prior)
        if session is not None:
            session.close()
        raise
    return ChartRequestBuild(
        sky=sky,
        prepared=prepared,
        owns_observer=owns_observer,
        minor_body_session=session,
        prior_source_resolvers=prior,
        request_minor_body_layers=tuple(request_layers),
    )


def build_chart_request(request, *, sky=None, profile=None, observer=None):
    """Prepare any chart request using an owned or supplied maximal sphere."""
    if not isinstance(request, ChartRequest):
        raise TypeError("request must be a ChartRequest.")
    if sky is not None:
        bound_observer = getattr(sky, "observer", None)
        if bound_observer is not None and observer is not None:
            raise ValueError(
                "an explicit observer requires an observer-independent sky."
            )
        resolved_observer = (
            bound_observer if observer is None else observer
        )
        if resolved_observer is None:
            raise TypeError(
                "an observer-independent sky requires an explicit observer."
            )
        if not request.observer.matches(resolved_observer):
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
            request,
            sky,
            available_profile,
            owns_observer=False,
            observer=observer,
        )

    if observer is not None:
        raise ValueError(
            "an explicit observer may be supplied only with a reusable sky."
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
    configuration=None,
    observer=None,
):
    """Resolve and export a request using an owned or supplied sphere."""
    build = build_chart_request(
        request,
        sky=sky,
        profile=profile,
        observer=observer,
    )
    try:
        export_options = {}
        if configuration is not None:
            export_options["configuration"] = configuration
        if observer is not None:
            export_options["observer"] = observer
        return export_prepared_chart(
            build.sky,
            build.prepared,
            **export_options,
        )
    finally:
        build.close()
