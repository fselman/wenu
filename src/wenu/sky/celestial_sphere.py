"""Celestial-sphere layer ownership and chart orchestration."""

from __future__ import annotations

from collections.abc import Iterable

from wenu.sky.rendering_results import ChartRenderingResult, LayerRenderingResult
from wenu.objects.nonstellar import NonStellar
from wenu.objects.galaxies import Galaxies
from wenu.objects.globular_clusters import GlobularClusters
from wenu.objects.supernova_remnants import SupernovaRemnants
from wenu.objects.planetary_nebulae import PlanetaryNebulae
from wenu.objects.stars import Stars
from wenu.sky.milky_way import MilkyWayIsophotes
from wenu.sky.magellanic_clouds import MagellanicCloudIsophotes
from wenu.sky.constellation_boundaries import ConstellationBoundaries
from wenu.sky.constellation_labels import ConstellationLabels
from wenu.sky.constellations import Constellations
from wenu.sky.coordinate_grids import (
    EclipticGrid,
    EquatorialGrid,
    GalacticGrid,
)
from wenu.sky.points import CelestialPoints
from wenu.sky.sky_layer import SkyLayer


class CelestialSphere:
    """The ordered collection of sky layers for one observer."""

    def __init__(self, observer) -> None:
        self.observer = observer
        self.stars = None
        self.nonstellar = None
        self.galaxies = None
        self.globular_clusters = None
        self.supernova_remnants = None
        self.planetary_nebulae = None
        self.milky_way_isophotes = None
        self.magellanic_cloud_isophotes = {}
        self.points = None
        self.constellations = None
        self.constellation_boundaries = None
        self.constellation_lines = None
        self.constellation_labels = None
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
        viewport=None,
        layer_options=None,
    ) -> ChartRenderingResult:
        """Render all registered layers through the canonical pipeline."""
        if not callable(getattr(projection, "project_geometry", None)):
            raise TypeError(
                "projection must provide project_geometry()."
            )
        if not callable(getattr(renderer, "draw", None)):
            raise TypeError("renderer must provide draw().")

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
            configured = self._layer_render_options(layer, options)
            geometry_options, prepare, render_options = (
                self._pipeline_options(configured)
            )
            spherical = layer.spherical_geometry(
                self.observer,
                **geometry_options,
            )
            projected = projection.project_geometry(spherical)
            if prepare is not None:
                projected = prepare(spherical, projected)
            if callable(render_options):
                render_options = render_options(spherical, projected)
            artists = renderer.draw(
                projected,
                **dict(render_options),
            )
            rendered_layers.append(
                LayerRenderingResult(
                    layer=layer,
                    spherical=spherical,
                    projected=projected,
                    artists=artists,
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

    def add_stars(
        self,
        catalog="hipparcos",
        magnitude_limit=5.5,
    ) -> Stars:
        """Load and register a stellar catalogue layer."""
        self.stars = Stars(
            observer=self.observer,
            catalog=catalog,
            magnitude_limit=magnitude_limit,
        )
        self.stars.load()
        self.add(self.stars)
        return self.stars

    def add_nonstellar(
        self,
        catalog="messier",
        *,
        filename=None,
        magnitude_limit=None,
        samples=73,
    ) -> NonStellar:
        """Load and register a non-stellar catalogue layer."""
        self.nonstellar = NonStellar(
            observer=self.observer,
            catalog=catalog,
            magnitude_limit=magnitude_limit,
            samples=samples,
        )
        self.nonstellar.load(filename=filename)
        self.add(self.nonstellar)
        return self.nonstellar

    def add_galaxies(
        self,
        *,
        filename=None,
        magnitude_limit=12.0,
        samples=73,
    ) -> Galaxies:
        """Load and register the bright-galaxy catalogue layer."""
        self.galaxies = Galaxies(
            observer=self.observer,
            magnitude_limit=magnitude_limit,
            samples=samples,
        )
        self.galaxies.load(filename=filename)
        self.add(self.galaxies)
        return self.galaxies

    def add_milky_way_isophotes(
        self,
        *,
        filename=None,
        levels=None,
    ) -> MilkyWayIsophotes:
        """Load and register nested Milky Way isophotes."""
        self.milky_way_isophotes = MilkyWayIsophotes(
            observer=self.observer,
            levels=levels,
        )
        self.milky_way_isophotes.load(filename=filename)
        self.add(self.milky_way_isophotes)
        return self.milky_way_isophotes

    def add_magellanic_cloud_isophotes(
        self,
        cloud,
        *,
        filename=None,
        levels=None,
    ) -> MagellanicCloudIsophotes:
        """Load and register one Magellanic Cloud isophote layer."""
        layer = MagellanicCloudIsophotes(
            observer=self.observer,
            cloud=cloud,
            levels=levels,
        )
        if layer.cloud in self.magellanic_cloud_isophotes:
            raise ValueError(
                f"{layer.cloud.upper()} isophotes are already registered."
            )
        layer.load(filename=filename)
        self.magellanic_cloud_isophotes[layer.cloud] = layer
        self.add(layer)
        return layer

    def add_globular_clusters(
        self,
        *,
        filename=None,
        magnitude_limit=12.0,
        samples=73,
    ) -> GlobularClusters:
        """Load and register Galactic globular clusters."""
        self.globular_clusters = GlobularClusters(
            observer=self.observer,
            magnitude_limit=magnitude_limit,
            samples=samples,
        )
        self.globular_clusters.load(filename=filename)
        self.add(self.globular_clusters)
        return self.globular_clusters

    def add_supernova_remnants(
        self,
        *,
        filename=None,
        samples=73,
    ) -> SupernovaRemnants:
        """Load and register confirmed Galactic supernova remnants."""
        self.supernova_remnants = SupernovaRemnants(
            observer=self.observer,
            samples=samples,
        )
        self.supernova_remnants.load(filename=filename)
        self.add(self.supernova_remnants)
        return self.supernova_remnants

    def add_planetary_nebulae(
        self,
        *,
        selected=None,
        filename=None,
        samples=73,
    ) -> PlanetaryNebulae:
        """Load and register true/probable Galactic planetary nebulae."""
        self.planetary_nebulae = PlanetaryNebulae(
            observer=self.observer,
            samples=samples,
            selected=selected,
        )
        self.planetary_nebulae.load(filename=filename)
        self.add(self.planetary_nebulae)
        return self.planetary_nebulae

    def add_points(self) -> CelestialPoints:
        """Create and register a celestial-reference-point layer."""
        self.points = CelestialPoints(obs=self.observer)
        self.add(self.points)
        return self.points

    def add_constellations(
        self,
        system="western",
        lines_file=None,
        selected=None,
    ) -> Constellations:
        """Create and register constellation lines and label anchors."""
        if self.stars is None:
            raise RuntimeError(
                "Stars must be added before constellations."
            )
        self.constellations = Constellations(
            stars=self.stars,
            observer=self.observer,
            system=system,
            lines_file=lines_file,
            selected=selected,
        )
        self.constellation_lines = self.constellations.lines
        self.constellation_labels = ConstellationLabels(
            self.stars,
            selected=selected,
            boundaries=self.constellation_boundaries,
        )
        self.add(self.constellation_lines)
        self.add(self.constellation_labels)
        return self.constellations

    def add_constellation_boundaries(
        self,
        boundaries="iau",
        filename=None,
        *,
        constellations=None,
        **kwargs,
    ) -> ConstellationBoundaries:
        """Create and register IAU constellation-boundary geometry."""
        if self.constellations is None:
            raise RuntimeError(
                "Call add_constellations() before "
                "add_constellation_boundaries()."
            )
        layer = ConstellationBoundaries(
            observer=self.observer,
            boundaries=boundaries,
            filename=filename,
            constellations=constellations,
            **kwargs,
        )
        self.constellation_boundaries = layer
        self.constellations.set_boundaries(layer)
        if self.constellation_labels is not None:
            self.constellation_labels.set_boundaries(layer)
        self.add(layer)
        return layer

    def add_equatorial_grid(
        self,
        *,
        ra=None,
        dec=None,
        include_equator=False,
        frame="fk5",
        equinox="of_date",
        samples=721,
    ) -> EquatorialGrid:
        """Create and register an equatorial coordinate grid."""
        layer = EquatorialGrid(
            observer=self.observer,
            frame=frame,
            equinox=equinox,
            samples=samples,
            ra=ra,
            dec=dec,
            include_equator=include_equator,
        )
        self.add(layer)
        return layer

    def add_ecliptic_grid(
        self,
        *,
        longitude=None,
        latitude=None,
        include_ecliptic=False,
        equinox="of_date",
        samples=721,
    ) -> EclipticGrid:
        """Create and register an ecliptic coordinate grid."""
        layer = EclipticGrid(
            observer=self.observer,
            equinox=equinox,
            samples=samples,
            longitude=longitude,
            latitude=latitude,
            include_ecliptic=include_ecliptic,
        )
        self.add(layer)
        return layer

    def add_galactic_grid(
        self,
        *,
        longitude=None,
        latitude=None,
        include_plane=False,
        samples=721,
    ) -> GalacticGrid:
        """Create and register a galactic coordinate grid."""
        layer = GalacticGrid(
            observer=self.observer,
            samples=samples,
            longitude=longitude,
            latitude=latitude,
            include_plane=include_plane,
        )
        self.add(layer)
        return layer
