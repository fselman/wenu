"""Celestial-sphere layer ownership and chart orchestration."""

from __future__ import annotations

from collections.abc import Iterable

from wenu.sky.rendering_results import ChartRenderingResult, LayerRenderingResult
from wenu.sky.semantic_identity import semantic_layer_identity
from wenu.sky.realization import LayerRealizationContext
from wenu.sky.sky_layer import SkyLayer


class CelestialSphere:
    """The ordered collection of sky layers, optionally bound to an observer."""

    def __init__(self, observer, *, assembly=None) -> None:
        self.observer = observer
        self._assembly = assembly
        self.load_profile = None
        self.stars = None
        self.nonstellar = None
        self.galaxies = None
        self.globular_clusters = None
        self.open_clusters = None
        self.supernova_remnants = None
        self.planetary_nebulae = None
        self.milky_way_isophotes = None
        self.magellanic_cloud_isophotes = {}
        self.points = None
        self.constellations = None
        self.constellation_boundaries = None
        self.constellation_lines = None
        self.constellation_labels = None
        self.horizon_reference = None
        self.venus = None
        self.moon = None
        self.solar_system_bodies = {}
        self._layers: list[SkyLayer] = []

    @property
    def layers(self) -> tuple[SkyLayer, ...]:
        """Return registered layers in drawing order."""
        return tuple(self._layers)

    def add(self, layer: SkyLayer) -> SkyLayer:
        """Register and return one sky layer."""
        if not isinstance(layer, SkyLayer):
            raise TypeError(
                f"{type(layer).__name__} cannot be added to "
                "CelestialSphere because it does not implement the "
                "SkyLayer contract."
            )
        self._layers.append(layer)
        return layer

    def extend(self, layers: Iterable[SkyLayer]) -> None:
        """Register several layers in iteration order."""
        for layer in layers:
            self.add(layer)

    def remove(self, layer: SkyLayer) -> None:
        """Remove a registered layer."""
        self._layers.remove(layer)

    def clear(self) -> None:
        """Remove every registered layer."""
        self._layers.clear()

    def draw_chart(
        self,
        *,
        projection,
        renderer,
        observer=None,
        realization_context=None,
        viewport=None,
        layer_options=None,
        project_geometry=None,
    ) -> ChartRenderingResult:
        """Render all registered layers through the canonical pipeline.

        An explicit observer overrides the compatibility observer bound at
        construction time.
        """
        if not callable(getattr(projection, "project_geometry", None)):
            raise TypeError(
                "projection must provide project_geometry()."
            )
        if not callable(getattr(renderer, "draw", None)):
            raise TypeError("renderer must provide draw().")
        if project_geometry is not None and not callable(project_geometry):
            raise TypeError("project_geometry must be callable or None.")
        resolved_observer = self.observer if observer is None else observer
        native_icrs = (
            isinstance(realization_context, LayerRealizationContext)
            and realization_context.is_native_icrs
        )
        if (resolved_observer is None and not native_icrs
                and not (isinstance(realization_context, LayerRealizationContext)
                         and realization_context.reception is not None)):
            raise TypeError("draw_chart requires an observer.")
        if (
            realization_context is not None
            and not isinstance(
                realization_context,
                LayerRealizationContext,
            )
        ):
            raise TypeError(
                "realization_context must be a "
                "LayerRealizationContext or None."
            )

        if viewport is not None:
            apply = getattr(renderer, "apply_viewport", None)
            if not callable(apply):
                raise TypeError(
                    "renderer must provide apply_viewport() when a "
                    "viewport is supplied."
                )
            apply(viewport)

        options = {} if layer_options is None else layer_options
        rendered_layers = []
        for layer in self._layers:
            identity = semantic_layer_identity(layer)
            configured = self._layer_render_options(layer, options)
            enabled = configured.pop("enabled", True)
            if not isinstance(enabled, bool):
                raise TypeError("layer enabled option must be boolean.")
            if not enabled:
                continue
            geometry_options, prepare, render_options = (
                self._pipeline_options(configured)
            )
            spherical = (
                layer.spherical_geometry(
                    resolved_observer,
                    **geometry_options,
                )
                if realization_context is None
                else layer.realize(
                    realization_context,
                    resolved_observer,
                    **geometry_options,
                )
            )
            if native_icrs:
                spec = spherical.coordinate_spec
                if (spec.frame != "icrs" or spec.origin != "solar-system-barycenter"
                        or spec.position_status.value != "astrometric"
                        or (spec.instant is not None and (
                            spec.instant != realization_context.evaluation_instant
                            or spec.time_scale != realization_context.evaluation_time_scale))):
                    raise ValueError("Native ICRS layers must return matching barycentric astrometry.")
            if realization_context is not None and realization_context.reception is not None:
                spec = spherical.coordinate_spec
                expected = realization_context.product_coordinate_spec
                if (any(getattr(spec, key) != getattr(expected, key) for key in
                        ("frame", "origin", "position_status", "instant", "time_scale",
                         "longitude_unit", "latitude_unit", "corrections"))
                        or realization_context.reception.identity not in spec.provenance):
                    raise ValueError("Observed layers must return matching reception-bound vacuum geometry.")
            project = (
                projection.project_geometry
                if project_geometry is None
                else project_geometry
            )
            resolved_prepare = prepare
            if prepare is not None:
                bind = getattr(prepare, "bind_project_geometry", None)
                if callable(bind):
                    resolved_prepare = bind(project)
                    if not callable(resolved_prepare):
                        raise TypeError(
                            "bind_project_geometry() must return a callable."
                        )
            projected = project(spherical)
            if resolved_prepare is not None:
                projected = resolved_prepare(spherical, projected)
            if callable(render_options):
                render_options = render_options(spherical, projected)
            artists = renderer.draw(
                projected,
                **dict(render_options),
            )
            semantic_artists = ()
            assign_identity = getattr(
                renderer, "assign_semantic_identity", None
            )
            if identity is not None and callable(assign_identity):
                semantic_artists = tuple(
                    assign_identity(artists, identity)
                )
            rendered_layers.append(
                LayerRenderingResult(
                    layer=layer,
                    semantic_identity=identity,
                    spherical=spherical,
                    projected=projected,
                    artists=artists,
                    semantic_artists=semantic_artists,
                )
            )

        return ChartRenderingResult(
            projection=projection,
            renderer=renderer,
            viewport=viewport,
            layers=tuple(rendered_layers),
        )

    @staticmethod
    def _pipeline_options(configured):
        configured = dict(configured)
        structured = any(
            name in configured
            for name in ("geometry", "prepare", "render")
        )
        if not structured:
            return {}, None, configured
        geometry = dict(configured.pop("geometry", {}))
        prepare = configured.pop("prepare", None)
        render = configured.pop("render", configured)
        if prepare is not None and not callable(prepare):
            raise TypeError("prepare must be callable or None.")
        if not callable(render):
            render = dict(render)
        return geometry, prepare, render

    @staticmethod
    def _layer_render_options(layer, options):
        for key, value in options.items():
            if key is layer:
                return dict(value)
        name = getattr(layer, "layer_name", None)
        if name in options:
            return dict(options[name])
        return {}

    def _assemble(self, operation, *args, **kwargs):
        assembly = self._assembly
        if assembly is None:
            from wenu.sky.assembly import DEFAULT_SKY_ASSEMBLY
            assembly = DEFAULT_SKY_ASSEMBLY
        return getattr(assembly, operation)(self, *args, **kwargs)

    def add_stars(self, catalog='hipparcos', magnitude_limit=5.5, *, filename=None):
        """Load and register a stellar catalogue layer."""
        return self._assemble('add_stars', catalog, magnitude_limit, filename=filename)

    def add_venus(self):
        """Register the opt-in apparent Venus layer."""
        return self._assemble('add_venus')

    def add_solar_system_body(self, descriptor):
        """Register one descriptor-driven apparent moving-body layer."""
        return self._assemble('add_solar_system_body', descriptor)

    def add_moon(self):
        """Register the opt-in apparent Moon symbolic-point layer."""
        return self._assemble('add_moon')

    def add_nonstellar(self, catalog='messier', *, filename=None, magnitude_limit=None, samples=73):
        """Load and register a non-stellar catalogue layer."""
        return self._assemble('add_nonstellar', catalog, filename=filename, magnitude_limit=magnitude_limit, samples=samples)

    def add_galaxies(self, *, filename=None, magnitude_limit=12.0, samples=73):
        """Load and register the bright-galaxy catalogue layer."""
        return self._assemble('add_galaxies', filename=filename, magnitude_limit=magnitude_limit, samples=samples)

    def add_milky_way_isophotes(self, *, filename=None, levels=None):
        """Load and register nested Milky Way isophotes."""
        return self._assemble('add_milky_way_isophotes', filename=filename, levels=levels)

    def add_magellanic_cloud_isophotes(self, cloud, *, filename=None, levels=None):
        """Load and register one Magellanic Cloud isophote layer."""
        return self._assemble('add_magellanic_cloud_isophotes', cloud, filename=filename, levels=levels)

    def add_open_clusters(self, *, filename=None, selected=None):
        """Load and register established/likely Galactic open clusters."""
        return self._assemble('add_open_clusters', filename=filename, selected=selected)

    def add_globular_clusters(self, *, filename=None, magnitude_limit=12.0, samples=73):
        """Load and register Galactic globular clusters."""
        return self._assemble('add_globular_clusters', filename=filename, magnitude_limit=magnitude_limit, samples=samples)

    def add_supernova_remnants(self, *, selected=None, filename=None, samples=73):
        """Load and register confirmed Galactic supernova remnants."""
        return self._assemble('add_supernova_remnants', selected=selected, filename=filename, samples=samples)

    def add_planetary_nebulae(self, *, selected=None, filename=None, samples=73):
        """Load and register true/probable Galactic planetary nebulae."""
        return self._assemble('add_planetary_nebulae', selected=selected, filename=filename, samples=samples)

    def add_points(self):
        """Create and register a celestial-reference-point layer."""
        return self._assemble('add_points')

    def add_constellations(self, system='western', lines_file=None, selected=None):
        """Create and register constellation lines and label anchors."""
        return self._assemble('add_constellations', system, lines_file, selected)

    def add_constellation_boundaries(self, boundaries='iau', filename=None, *, constellations=None, **kwargs):
        """Create and register IAU constellation-boundary geometry."""
        return self._assemble('add_constellation_boundaries', boundaries, filename, constellations=constellations, **kwargs)

    def add_equatorial_grid(self, *, ra=None, dec=None, include_equator=False, frame='fk5', equinox='of_date', samples=721, meridian_dec_min=-90.0, meridian_dec_max=90.0):
        """Create and register an equatorial coordinate grid."""
        return self._assemble('add_equatorial_grid', ra=ra, dec=dec, include_equator=include_equator, frame=frame, equinox=equinox, samples=samples, meridian_dec_min=meridian_dec_min, meridian_dec_max=meridian_dec_max)

    def add_altaz_grid(self, *, azimuth=None, altitude=None, include_horizon=False, samples=721):
        """Create and register an observer-local AltAz coordinate grid."""
        return self._assemble('add_altaz_grid', azimuth=azimuth, altitude=altitude, include_horizon=include_horizon, samples=samples)

    def add_horizon_reference(self, *, samples=721):
        """Create and register the semantic observer horizon."""
        return self._assemble('add_horizon_reference', samples=samples)

    def add_ecliptic_grid(self, *, longitude=None, latitude=None, include_ecliptic=False, equinox='of_date', samples=721):
        """Create and register an ecliptic coordinate grid."""
        return self._assemble('add_ecliptic_grid', longitude=longitude, latitude=latitude, include_ecliptic=include_ecliptic, equinox=equinox, samples=samples)

    def add_galactic_grid(self, *, longitude=None, latitude=None, include_plane=False, samples=721):
        """Create and register a galactic coordinate grid."""
        return self._assemble('add_galactic_grid', longitude=longitude, latitude=latitude, include_plane=include_plane, samples=samples)
