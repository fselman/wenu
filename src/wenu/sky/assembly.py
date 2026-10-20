"""Application-owned construction of concrete sky layers and restored facades.

Numerical services and chart orchestration stay with their existing owners.
The default assembly is stateless; callers may supply an assembly per sky/build.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from wenu.sky.celestial_sphere import CelestialSphere
from wenu.sky.maximal_sphere import (CelestialSphereLoadProfile,
    CANONICAL_MAXIMAL_SPHERE_PROFILE, _require_native_profile)
from wenu.sky.solar_system_bodies import SYMBOLIC_POINT
from wenu.sky.solar_system_catalog import SOLAR_SYSTEM_BODY_CATALOG
from wenu.objects.nonstellar import NonStellarCatalogueMetadata
from wenu.stellar_catalogue import ingest_stellar_catalogue
from wenu.objects.nonstellar import NonStellar
from wenu.objects.galaxies import Galaxies
from wenu.objects.globular_clusters import GlobularClusters
from wenu.objects.open_clusters import OpenClusters
from wenu.objects.supernova_remnants import SupernovaRemnants
from wenu.objects.planetary_nebulae import PlanetaryNebulae
from wenu.objects.stars import Stars
from wenu.sky.milky_way import MilkyWayIsophotes
from wenu.sky.magellanic_clouds import MagellanicCloudIsophotes
from wenu.sky.constellation_boundaries import ConstellationBoundaries
from wenu.sky.constellation_labels import ConstellationLabels
from wenu.sky.constellations import Constellations
from wenu.sky.constellation_lines import ConstellationLines
from wenu.sky.horizon import HorizonReference
from wenu.sky.coordinate_grids import (
    AltAzGrid,
    EclipticGrid,
    EquatorialGrid,
    GalacticGrid,
)
from wenu.sky.moon import MoonLayer
from wenu.sky.points import CelestialPoints
from wenu.sky.sky_layer import SkyLayer
from wenu.sky.solar_system_bodies import SolarSystemBodyDescriptor
from wenu.sky.solar_system_points import SolarSystemPointLayer
from wenu.sky.venus import VENUS_POINT, VenusLayer

class _NativeOnly:
    def load(self, *args, **kwargs):
        raise RuntimeError("Frozen snapshot layers cannot reload source catalogues.")

    def spherical_geometry(self, observer, **options):
        raise ValueError("A persisted native sky requires native ICRS realization.")


class _SnapshotStars(_NativeOnly, Stars):
    def _render_catalog(self, *, magnitude_limit=None, **options):
        limit = self.magnitude_limit if magnitude_limit is None else magnitude_limit
        if isinstance(limit, bool) or not np.isfinite(limit) or limit > self.magnitude_limit:
            raise ValueError("Insufficient snapshot stellar magnitude coverage; prepare a new revision.")
        identifiers = options.get("include_ids")
        if identifiers is not None and not set(identifiers) <= set(self.source_catalog.index):
            raise ValueError("Requested stellar identities are absent from the snapshot.")
        return super()._render_catalog(magnitude_limit=magnitude_limit, **options)


class _SnapshotLines(_NativeOnly, ConstellationLines):
    pass


class _SnapshotMilkyWay(_NativeOnly, MilkyWayIsophotes):
    pass


class _SnapshotCloud(_NativeOnly, MagellanicCloudIsophotes):
    pass


class _SnapshotLabels(_NativeOnly, ConstellationLabels):
    pass


_CATALOGUES = {"nonstellar": NonStellar, "galaxies": Galaxies,
    "open_clusters": OpenClusters, "globular_clusters": GlobularClusters,
    "supernova_remnants": SupernovaRemnants, "planetary_nebulae": PlanetaryNebulae}
_REFERENCES = {"equatorial_grid": EquatorialGrid, "ecliptic_grid": EclipticGrid,
               "galactic_grid": GalacticGrid}


def _restore_fixed(sky, data, source_digests):
    from wenu.sky.native_snapshot import _table_from_records, _plain_mapping
    fixed = data["fixed"]
    profile = fixed["profile"]
    sky.load_profile = CelestialSphereLoadProfile(star_magnitude_limit=sky.stars.magnitude_limit, **dict(profile))
    for name, owner in _CATALOGUES.items():
        content = fixed["catalogues"][name]
        kwargs = (dict(catalog=profile["nonstellar_catalog"], magnitude_limit=profile["nonstellar_magnitude_limit"], samples=profile["extended_object_samples"])
                  if name == "nonstellar" else dict(magnitude_limit=profile["galaxy_magnitude_limit" if name == "galaxies" else "globular_cluster_magnitude_limit"], samples=profile["extended_object_samples"])
                  if name in {"galaxies", "globular_clusters"} else dict(samples=profile["extended_object_samples"])
                  if name == "supernova_remnants" else {})
        layer = owner(None, **kwargs)
        table = _table_from_records(content["table"])
        layer.source = content["source"]
        layer.catalog = table
        if name == 'open_clusters':
            layer._source_sha256 = source_digests[name]
        if name != "open_clusters":
            layer.source_catalog = table
            if 'metadata' in content:
                layer._catalogue_metadata = NonStellarCatalogueMetadata.from_record(_plain_mapping(content['metadata']))
            if layer.magnitude_limit is not None:
                magnitude = np.asarray(table["magnitude"], dtype=float)
                layer.catalog = table[~np.isfinite(magnitude) | (magnitude <= layer.magnitude_limit)]
        setattr(sky, name, sky.add(layer))
    content = fixed["boundaries"]
    boundary = object.__new__(ConstellationBoundaries)
    boundary.observer, boundary.boundaries_name, boundary.semantic_system_key = None, "iau", "iau"
    boundary.filename, boundary.constellations = None, None
    boundary.sampling_step_deg = content["sampling_step_deg"]
    boundary.vertices, boundary.sampled_vertices = dict(content["vertices"]), {}
    boundary._source_revision, boundary._observed_polygon_cache = 1, {}
    sky.constellation_boundaries = sky.add(boundary)
    sky.constellations.set_boundaries(boundary)
    sky.constellation_labels.set_boundaries(boundary)
    for name, owner in _REFERENCES.items():
        sky.add(owner(None, **dict(fixed["references"][name])))
    from astropy.coordinates import SkyCoord, BarycentricMeanEcliptic
    from astropy.time import Time
    import astropy.units as u
    points = sky.add_points()
    for record in fixed["points"]:
        name = record["frame"]
        frame = BarycentricMeanEcliptic(equinox=Time(record["equinox"])) if name == "barycentricmeanecliptic" else name
        coord = SkyCoord(record["lon"] * u.deg, record["lat"] * u.deg, frame=frame)
        points._append_point(coord, record["label"], record["marker"], record["size"], record["color"],
                             record["zorder"], **dict(record["style"]))


class SkyAssembly:
    """Construct the existing application layers without owning chart policy."""

    def add_stars(
        self, sky,
        catalog="hipparcos",
        magnitude_limit=5.5,
        *,
        filename=None,
    ) -> Stars:
        """Load and register a stellar catalogue layer."""
        sky.stars = Stars(
            observer=sky.observer,
            catalog=catalog,
            magnitude_limit=magnitude_limit,
        )
        sky.stars.load(filename=filename)
        sky.add(sky.stars)
        return sky.stars

    def add_venus(self, sky) -> VenusLayer:
        """Register the opt-in apparent Venus layer."""
        sky.venus = sky.add_solar_system_body(VENUS_POINT)
        return sky.venus

    def add_solar_system_body(
        self, sky, descriptor: SolarSystemBodyDescriptor
    ) -> SolarSystemPointLayer:
        """Register one descriptor-driven apparent moving-body layer."""
        if not isinstance(descriptor, SolarSystemBodyDescriptor):
            raise TypeError("descriptor must be a SolarSystemBodyDescriptor.")
        layer = SolarSystemPointLayer(descriptor)
        sky.solar_system_bodies[descriptor.selection_key] = layer
        setattr(sky, descriptor.entity_key, layer)
        sky.add(layer)
        return layer

    def add_moon(self, sky) -> MoonLayer:
        """Register the opt-in apparent Moon symbolic-point layer."""
        sky.moon = MoonLayer()
        sky.add(sky.moon)
        return sky.moon

    def add_nonstellar(
        self, sky,
        catalog="messier",
        *,
        filename=None,
        magnitude_limit=None,
        samples=73,
    ) -> NonStellar:
        """Load and register a non-stellar catalogue layer."""
        sky.nonstellar = NonStellar(
            observer=sky.observer,
            catalog=catalog,
            magnitude_limit=magnitude_limit,
            samples=samples,
        )
        sky.nonstellar.load(filename=filename)
        sky.add(sky.nonstellar)
        return sky.nonstellar

    def add_galaxies(
        self, sky,
        *,
        filename=None,
        magnitude_limit=12.0,
        samples=73,
    ) -> Galaxies:
        """Load and register the bright-galaxy catalogue layer."""
        sky.galaxies = Galaxies(
            observer=sky.observer,
            magnitude_limit=magnitude_limit,
            samples=samples,
        )
        sky.galaxies.load(filename=filename)
        sky.add(sky.galaxies)
        return sky.galaxies

    def add_milky_way_isophotes(
        self, sky,
        *,
        filename=None,
        levels=None,
    ) -> MilkyWayIsophotes:
        """Load and register nested Milky Way isophotes."""
        sky.milky_way_isophotes = MilkyWayIsophotes(
            observer=sky.observer,
            levels=levels,
        )
        sky.milky_way_isophotes.load(filename=filename)
        sky.add(sky.milky_way_isophotes)
        return sky.milky_way_isophotes

    def add_magellanic_cloud_isophotes(
        self, sky,
        cloud,
        *,
        filename=None,
        levels=None,
    ) -> MagellanicCloudIsophotes:
        """Load and register one Magellanic Cloud isophote layer."""
        layer = MagellanicCloudIsophotes(
            observer=sky.observer,
            cloud=cloud,
            levels=levels,
        )
        if layer.cloud in sky.magellanic_cloud_isophotes:
            raise ValueError(
                f"{layer.cloud.upper()} isophotes are already registered."
            )
        layer.load(filename=filename)
        sky.magellanic_cloud_isophotes[layer.cloud] = layer
        sky.add(layer)
        return layer

    def add_open_clusters(
        self, sky,
        *,
        filename=None,
        selected=None,
    ) -> OpenClusters:
        """Load and register established/likely Galactic open clusters."""
        sky.open_clusters = OpenClusters(
            observer=sky.observer,
            selected=selected,
        )
        sky.open_clusters.load(filename=filename)
        sky.add(sky.open_clusters)
        return sky.open_clusters

    def add_globular_clusters(
        self, sky,
        *,
        filename=None,
        magnitude_limit=12.0,
        samples=73,
    ) -> GlobularClusters:
        """Load and register Galactic globular clusters."""
        sky.globular_clusters = GlobularClusters(
            observer=sky.observer,
            magnitude_limit=magnitude_limit,
            samples=samples,
        )
        sky.globular_clusters.load(filename=filename)
        sky.add(sky.globular_clusters)
        return sky.globular_clusters

    def add_supernova_remnants(
        self, sky,
        *,
        selected=None,
        filename=None,
        samples=73,
    ) -> SupernovaRemnants:
        """Load and register confirmed Galactic supernova remnants."""
        sky.supernova_remnants = SupernovaRemnants(
            observer=sky.observer,
            selected=selected,
            samples=samples,
        )
        sky.supernova_remnants.load(filename=filename)
        sky.add(sky.supernova_remnants)
        return sky.supernova_remnants

    def add_planetary_nebulae(
        self, sky,
        *,
        selected=None,
        filename=None,
        samples=73,
    ) -> PlanetaryNebulae:
        """Load and register true/probable Galactic planetary nebulae."""
        sky.planetary_nebulae = PlanetaryNebulae(
            observer=sky.observer,
            samples=samples,
            selected=selected,
        )
        sky.planetary_nebulae.load(filename=filename)
        sky.add(sky.planetary_nebulae)
        return sky.planetary_nebulae

    def add_points(self, sky) -> CelestialPoints:
        """Create and register a celestial-reference-point layer."""
        sky.points = CelestialPoints(obs=sky.observer)
        sky.add(sky.points)
        return sky.points

    def add_constellations(
        self, sky,
        system="western",
        lines_file=None,
        selected=None,
    ) -> Constellations:
        """Create and register constellation lines and label anchors."""
        if sky.stars is None:
            raise RuntimeError(
                "Stars must be added before constellations."
            )
        sky.constellations = Constellations(
            stars=sky.stars,
            observer=sky.observer,
            system=system,
            lines_file=lines_file,
            selected=selected,
        )
        sky.constellation_lines = sky.constellations.lines
        sky.stars.set_constellation_vertices(
            sky.constellation_lines.star_ids
        )
        sky.constellation_labels = ConstellationLabels(
            sky.stars,
            selected=selected,
            boundaries=sky.constellation_boundaries,
            system=system,
        )
        sky.add(sky.constellation_lines)
        sky.add(sky.constellation_labels)
        return sky.constellations

    def add_constellation_boundaries(
        self, sky,
        boundaries="iau",
        filename=None,
        *,
        constellations=None,
        **kwargs,
    ) -> ConstellationBoundaries:
        """Create and register IAU constellation-boundary geometry."""
        if sky.constellations is None:
            raise RuntimeError(
                "Call add_constellations() before "
                "add_constellation_boundaries()."
            )
        layer = ConstellationBoundaries(
            observer=sky.observer,
            boundaries=boundaries,
            filename=filename,
            constellations=constellations,
            **kwargs,
        )
        sky.constellation_boundaries = layer
        sky.constellations.set_boundaries(layer)
        if sky.constellation_labels is not None:
            sky.constellation_labels.set_boundaries(layer)
        sky.add(layer)
        return layer

    def add_equatorial_grid(
        self, sky,
        *,
        ra=None,
        dec=None,
        include_equator=False,
        frame="fk5",
        equinox="of_date",
        samples=721,
        meridian_dec_min=-90.0,
        meridian_dec_max=90.0,
    ) -> EquatorialGrid:
        """Create and register an equatorial coordinate grid."""
        layer = EquatorialGrid(
            observer=sky.observer,
            frame=frame,
            equinox=equinox,
            samples=samples,
            ra=ra,
            dec=dec,
            include_equator=include_equator,
            meridian_dec_min=meridian_dec_min,
            meridian_dec_max=meridian_dec_max,
        )
        sky.add(layer)
        return layer

    def add_altaz_grid(
        self, sky,
        *,
        azimuth=None,
        altitude=None,
        include_horizon=False,
        samples=721,
    ) -> AltAzGrid:
        """Create and register an observer-local AltAz coordinate grid."""
        layer = AltAzGrid(
            observer=sky.observer,
            samples=samples,
            azimuth=azimuth,
            altitude=altitude,
            include_horizon=include_horizon,
        )
        sky.add(layer)
        return layer

    def add_horizon_reference(self, sky, *, samples=721) -> HorizonReference:
        """Create and register the semantic observer horizon."""
        layer = HorizonReference(
            observer=sky.observer,
            samples=samples,
        )
        sky.horizon_reference = layer
        sky.add(layer)
        return layer

    def add_ecliptic_grid(
        self, sky,
        *,
        longitude=None,
        latitude=None,
        include_ecliptic=False,
        equinox="of_date",
        samples=721,
    ) -> EclipticGrid:
        """Create and register an ecliptic coordinate grid."""
        layer = EclipticGrid(
            observer=sky.observer,
            equinox=equinox,
            samples=samples,
            longitude=longitude,
            latitude=latitude,
            include_ecliptic=include_ecliptic,
        )
        sky.add(layer)
        return layer

    def add_galactic_grid(
        self, sky,
        *,
        longitude=None,
        latitude=None,
        include_plane=False,
        samples=721,
    ) -> GalacticGrid:
        """Create and register a galactic coordinate grid."""
        layer = GalacticGrid(
            observer=sky.observer,
            samples=samples,
            longitude=longitude,
            latitude=latitude,
            include_plane=include_plane,
        )
        sky.add(layer)
        return layer

    def generate_native_icrs_sphere(self, *, profile=CANONICAL_MAXIMAL_SPHERE_PROFILE):
        """Prepare the currently admitted static whole-sky layers once.

        This is the fixed-content profile: all installed static catalogues,
        boundaries and reference definitions. Moving bodies remain excluded. Connectivity is loaded before the single stellar
        load, so vertices require no catalogue reload.
        """
        from wenu.objects.stars import Stars
        from wenu.sky.constellations import Constellations
        from wenu.sky.constellation_labels import ConstellationLabels
        from wenu.star_designations import load_effective_star_designations
        from wenu.stellar_research import load_stellar_research
        _require_native_profile(profile)
        sky = CelestialSphere(None, assembly=self)
        sky.load_profile = profile
        sky.stellar_research = load_stellar_research()
        sky.add_milky_way_isophotes(filename=profile.milky_way_filename,
                                  levels=MilkyWayIsophotes.available_levels)
        for cloud, filename in (("lmc", profile.lmc_filename), ("smc", profile.smc_filename)):
            sky.add_magellanic_cloud_isophotes(cloud, filename=filename,
                                              levels=MagellanicCloudIsophotes.available_levels)
        stars = Stars(None, magnitude_limit=profile.star_magnitude_limit)
        constellation = Constellations(stars, lines_file=profile.constellation_lines_filename)
        stars.set_constellation_vertices(constellation.lines.star_ids, reload=False)
        stars.load(filename=profile.star_filename)
        stars.designation_catalogue = load_effective_star_designations(stars.designation_catalogue)
        stars.source_catalog["star_designations"] = [
            stars.designation_catalogue.get(int(hip)) for hip in stars.source_catalog.index]
        stars.catalog["star_designations"] = [
            stars.designation_catalogue.get(int(hip)) for hip in stars.catalog.index]
        stars.hip_df = stars.catalog.copy()
        sky.stars = sky.add(stars)
        sky.constellations = constellation
        sky.constellation_lines = sky.add(constellation.lines)
        sky.constellation_labels = sky.add(ConstellationLabels(stars))
        sky.add_nonstellar(catalog=profile.nonstellar_catalog, filename=profile.nonstellar_filename,
                           magnitude_limit=profile.nonstellar_magnitude_limit, samples=profile.extended_object_samples)
        sky.add_galaxies(filename=profile.galaxy_filename, magnitude_limit=profile.galaxy_magnitude_limit,
                         samples=profile.extended_object_samples)
        sky.add_open_clusters(filename=profile.open_cluster_filename)
        sky.add_globular_clusters(filename=profile.globular_cluster_filename,
                                 magnitude_limit=profile.globular_cluster_magnitude_limit,
                                 samples=profile.extended_object_samples)
        sky.add_supernova_remnants(filename=profile.supernova_remnant_filename, samples=profile.extended_object_samples)
        sky.add_planetary_nebulae(filename=profile.planetary_nebula_filename)
        sky.add_constellation_boundaries(filename=profile.constellation_boundaries_filename)
        sky.add_equatorial_grid(frame="icrs", equinox="J2000", include_equator=True)
        sky.add_ecliptic_grid(equinox="J2000", include_ecliptic=True)
        sky.add_galactic_grid(include_plane=True)
        points = sky.add_points()
        from astropy.coordinates import BarycentricMeanEcliptic
        from astropy.time import Time
        ecliptic = BarycentricMeanEcliptic(equinox=Time("J2000"))
        for pole in ("north", "south"):
            points.add_equatorial_pole(pole)
            points.add_galactic_pole(pole)
            points.add_ecliptic_pole(pole, frame=ecliptic)
        points.add_galactic_center()
        points.add_galactic_anticenter()
        points.add_ecliptic_cardinal_points(frame=ecliptic)
        return sky

    def build_maximal_sphere(self,
        observer,
        *,
        profile=CANONICAL_MAXIMAL_SPHERE_PROFILE,
    ):
        """Load and register the complete reusable canonical sky content."""
        if not isinstance(profile, CelestialSphereLoadProfile):
            raise TypeError("profile must be a CelestialSphereLoadProfile.")

        sky = CelestialSphere(observer, assembly=self)
        sky.load_profile = profile
        sky.add_venus()
        for descriptor in SOLAR_SYSTEM_BODY_CATALOG.supporting(SYMBOLIC_POINT):
            if descriptor.selection_key not in {"venus", "moon"}:
                sky.add_solar_system_body(descriptor)
        sky.add_moon()
        sky.add_milky_way_isophotes(
            filename=profile.milky_way_filename,
            levels=MilkyWayIsophotes.available_levels,
        )
        for cloud, filename in (
            ("lmc", profile.lmc_filename),
            ("smc", profile.smc_filename),
        ):
            sky.add_magellanic_cloud_isophotes(
                cloud,
                filename=filename,
                levels=MagellanicCloudIsophotes.available_levels,
            )
        sky.add_stars(
            catalog=profile.star_catalog,
            magnitude_limit=profile.star_magnitude_limit,
            filename=profile.star_filename,
        )
        sky.add_nonstellar(
            catalog=profile.nonstellar_catalog,
            filename=profile.nonstellar_filename,
            magnitude_limit=profile.nonstellar_magnitude_limit,
            samples=profile.extended_object_samples,
        )
        sky.add_galaxies(
            filename=profile.galaxy_filename,
            magnitude_limit=profile.galaxy_magnitude_limit,
            samples=profile.extended_object_samples,
        )
        sky.add_open_clusters(filename=profile.open_cluster_filename)
        sky.add_globular_clusters(
            filename=profile.globular_cluster_filename,
            magnitude_limit=profile.globular_cluster_magnitude_limit,
            samples=profile.extended_object_samples,
        )
        sky.add_supernova_remnants(
            filename=profile.supernova_remnant_filename,
            samples=profile.extended_object_samples,
        )
        sky.add_planetary_nebulae(
            filename=profile.planetary_nebula_filename,
            samples=profile.extended_object_samples,
        )
        sky.add_constellations(
            system="western",
            lines_file=profile.constellation_lines_filename,
        )
        sky.add_constellation_boundaries(
            boundaries="iau",
            filename=profile.constellation_boundaries_filename,
        )
        return sky

    def restore_snapshot(self, snapshot):
        """Reconstruct local native facades, never original catalogue loading."""
        from wenu.sky.native_snapshot import _diffuse_metadata
        data = snapshot._records
        sky = CelestialSphere(None, assembly=self)
        sky.stellar_research = data["research"]
        sky.load_profile = CelestialSphereLoadProfile(star_magnitude_limit=snapshot.star_magnitude_limit)
        mw = _SnapshotMilkyWay(None, levels=MilkyWayIsophotes.available_levels)
        mw.features, mw.source, mw.sources = (
            data["milky_way"][key] for key in ("features", "source", "sources"))
        mw.catalogue_metadata = _diffuse_metadata(data["milky_way"], "milky_way",
            snapshot._manifest["schema_version"], snapshot.source_digests)
        sky.milky_way_isophotes = sky.add(mw)
        for cloud, content in data["clouds"].items():
            layer = _SnapshotCloud(None, cloud=cloud)
            layer.features, layer.fractions, layer.source = (
                content[key] for key in ("features", "fractions", "source"))
            layer.catalogue_metadata = _diffuse_metadata(content, cloud,
                snapshot._manifest["schema_version"], snapshot.source_digests)
            sky.magellanic_cloud_isophotes[cloud] = sky.add(layer)
        stars = _SnapshotStars(None, magnitude_limit=snapshot.star_magnitude_limit)
        stars.designation_catalogue = data["designation_catalogue"]
        source = pd.DataFrame(dict(data["columns"]), index=data["star_ids"], copy=False)
        source = ingest_stellar_catalogue(source, snapshot.stellar_metadata).table
        source["star_designations"] = [stars.designation_catalogue.get(int(hip)) for hip in source.index]
        stars.source_catalog = source
        stars.catalog = source[source["magnitude"] <= stars.magnitude_limit].copy()
        stars.hip_df = stars.catalog.copy()
        stars.constellation_vertex_ids = frozenset(
            hip for edges in data["edges"].values() for edge in edges for hip in edge)
        sky.stars = sky.add(stars)
        lines = object.__new__(_SnapshotLines)
        lines.stars, lines.system, lines.semantic_system_key = stars, "western", "western"
        lines.filename, lines.constellations = None, None
        lines.edges_by_constellation = dict(data["edges"])
        lines.edges = [edge for edges in lines.edges_by_constellation.values() for edge in edges]
        sky.constellation_lines = sky.add(lines)
        constellation = object.__new__(Constellations)
        constellation.stars, constellation.observer, constellation.system = stars, None, "western"
        constellation.selected, constellation.lines, constellation.boundaries = None, lines, None
        sky.constellations = constellation
        sky.constellation_labels = sky.add(_SnapshotLabels(stars))
        if "fixed" in data:
            _restore_fixed(sky, data, snapshot.source_digests)
        return sky


DEFAULT_SKY_ASSEMBLY = SkyAssembly()
