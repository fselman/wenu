"""Canonical loading profile and maximal celestial-sphere factory."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from wenu.sky.celestial_sphere import CelestialSphere
from wenu.sky.magellanic_clouds import MagellanicCloudIsophotes
from wenu.sky.milky_way import MilkyWayIsophotes
from wenu.sky.solar_system_bodies import SYMBOLIC_POINT
from wenu.sky.solar_system_catalog import SOLAR_SYSTEM_BODY_CATALOG


def _source(value):
    return None if value is None else Path(value)


@dataclass(frozen=True)
class CelestialSphereLoadProfile:
    """Immutable declaration of content available in a loaded sphere."""

    star_catalog: str = "hipparcos"
    star_magnitude_limit: float = 11.0
    nonstellar_catalog: str = "messier"
    nonstellar_magnitude_limit: float | None = None
    galaxy_magnitude_limit: float = 12.0
    globular_cluster_magnitude_limit: float = 12.0
    extended_object_samples: int = 97
    star_filename: Path | None = None
    nonstellar_filename: Path | None = None
    galaxy_filename: Path | None = None
    open_cluster_filename: Path | None = None
    globular_cluster_filename: Path | None = None
    supernova_remnant_filename: Path | None = None
    planetary_nebula_filename: Path | None = None
    milky_way_filename: Path | None = None
    lmc_filename: Path | None = None
    smc_filename: Path | None = None
    constellation_lines_filename: Path | None = None
    constellation_boundaries_filename: Path | None = None

    def __post_init__(self):
        for name in (
            "star_filename",
            "nonstellar_filename",
            "galaxy_filename",
            "open_cluster_filename",
            "globular_cluster_filename",
            "supernova_remnant_filename",
            "planetary_nebula_filename",
            "milky_way_filename",
            "lmc_filename",
            "smc_filename",
            "constellation_lines_filename",
            "constellation_boundaries_filename",
        ):
            object.__setattr__(self, name, _source(getattr(self, name)))
        if self.star_magnitude_limit <= 0:
            raise ValueError("star_magnitude_limit must be positive.")
        if self.galaxy_magnitude_limit <= 0:
            raise ValueError("galaxy_magnitude_limit must be positive.")
        if self.globular_cluster_magnitude_limit <= 0:
            raise ValueError(
                "globular_cluster_magnitude_limit must be positive."
            )
        if self.extended_object_samples < 12:
            raise ValueError("extended_object_samples must be at least 12.")

    def require(
        self,
        *,
        star_magnitude_limit=None,
        nonstellar_magnitude_limit=None,
        galaxy_magnitude_limit=None,
        globular_cluster_magnitude_limit=None,
        extended_object_samples=None,
    ):
        """Reject a request that exceeds content loaded by this profile."""
        requested = {
            "star_magnitude_limit": star_magnitude_limit,
            "nonstellar_magnitude_limit": nonstellar_magnitude_limit,
            "galaxy_magnitude_limit": galaxy_magnitude_limit,
            "globular_cluster_magnitude_limit": (
                globular_cluster_magnitude_limit
            ),
            "extended_object_samples": extended_object_samples,
        }
        for name, value in requested.items():
            if value is None:
                continue
            available = getattr(self, name)
            if available is not None and value > available:
                raise ValueError(
                    f"Requested {name}={value!r} exceeds the loaded "
                    f"maximum {available!r}."
                )
            if available is None and name == "nonstellar_magnitude_limit":
                continue
        return self


CANONICAL_MAXIMAL_SPHERE_PROFILE = CelestialSphereLoadProfile()


def generate_celestial_sphere(
    *,
    profile=CANONICAL_MAXIMAL_SPHERE_PROFILE,
):
    """Load reusable canonical content without binding an observer."""
    return build_maximal_sphere(None, profile=profile)


def build_maximal_sphere(
    observer,
    *,
    profile=CANONICAL_MAXIMAL_SPHERE_PROFILE,
):
    """Load and register the complete reusable canonical sky content."""
    if not isinstance(profile, CelestialSphereLoadProfile):
        raise TypeError("profile must be a CelestialSphereLoadProfile.")

    sky = CelestialSphere(observer)
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
