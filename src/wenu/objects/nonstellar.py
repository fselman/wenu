"""Catalogue layer for non-stellar astronomical objects."""

from __future__ import annotations

from importlib.resources import as_file
from pathlib import Path
import re

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord, concatenate
from astropy.table import Table

from wenu.geometry.spherical import SphericalCurves, SphericalPoints
from wenu.objects.astronomical_object import AstronomicalObject
from wenu.resources import nonstellar_catalog_path
from wenu.sky.observed_cache import (
    catalogue_point_altaz,
    observed_polygon_arrays,
)


class NonStellar(AstronomicalObject):
    """A catalogue of extended and other non-stellar objects.

    Catalogue coordinates and dimensions remain in their native ICRS
    representation until ``spherical_geometry()`` is called. Ellipse
    position angles follow the astronomical convention: north through east.
    """

    layer_name = "nonstellar"

    _ALIASES = {
        "identifier": ("name", "object", "designation", "messier"),
        "ra": ("ra", "ra_deg"),
        "dec": ("dec", "dec_deg"),
        "dimension": ("dimension", "dimensions", "size"),
        "major": ("major_axis", "major_axis_arcmin", "major"),
        "minor": ("minor_axis", "minor_axis_arcmin", "minor"),
        "position_angle": (
            "position_angle",
            "position_angle_deg",
            "pa",
        ),
        "magnitude": ("vmag", "magnitude", "mag"),
        "object_type": ("object_type", "type"),
        "common_name": ("common_name",),
        "constellation": ("constellation", "const"),
    }

    def __init__(
        self,
        observer,
        catalog="messier",
        *,
        magnitude_limit=None,
        samples=73,
    ):
        self.observer = observer
        self.catalog_name = str(catalog)
        self.magnitude_limit = (
            None
            if magnitude_limit is None
            else float(magnitude_limit)
        )
        self.samples = int(samples)
        if self.samples < 12:
            raise ValueError("samples must be at least 12.")
        self.catalog = None
        self.source_catalog = None
        self.source = None
        self._source_revision = 0
        self._observed_point_cache = {}
        self._observed_outline_cache = {}

    def load(self, *, catalog=None, filename=None):
        """Load and normalize a non-stellar catalogue."""
        if catalog is not None:
            self.catalog_name = str(catalog)

        if filename is not None:
            self.source = Path(filename)
            table = Table.read(self.source)
        else:
            resource = nonstellar_catalog_path(self.catalog_name)
            with as_file(resource) as path:
                self.source = resource
                table = Table.read(path)

        self.source_catalog = self._normalize(table)
        self.catalog = self.source_catalog
        if self.magnitude_limit is not None:
            magnitude = self.catalog["magnitude"]
            keep = (
                ~np.isfinite(magnitude)
                | (magnitude <= self.magnitude_limit)
            )
            self.catalog = self.source_catalog[keep]
        self._source_revision += 1
        self._observed_point_cache.clear()
        self._observed_outline_cache.clear()
        return self.catalog

    def _normalize(self, source):
        names = {
            name.casefold(): name
            for name in source.colnames
        }

        def column(key, *, required=False):
            for alias in self._ALIASES[key]:
                actual = names.get(alias.casefold())
                if actual is not None:
                    return source[actual]
            if required:
                raise ValueError(
                    f"Catalogue requires a {key!r} column."
                )
            return None

        ra = self._float_values(column("ra", required=True))
        dec = self._float_values(column("dec", required=True))
        count = len(source)
        identifier_source = column("identifier")
        identifiers = (
            np.asarray(
                [f"object-{index + 1}" for index in range(count)],
                dtype=object,
            )
            if identifier_source is None
            else np.asarray(identifier_source, dtype=str)
        )

        major_source = column("major")
        minor_source = column("minor")
        if major_source is not None:
            major = self._float_values(major_source)
            minor = (
                major.copy()
                if minor_source is None
                else self._float_values(minor_source)
            )
        else:
            dimensions = column("dimension")
            major = np.full(count, np.nan)
            minor = np.full(count, np.nan)
            if dimensions is not None:
                for index, value in enumerate(dimensions):
                    major[index], minor[index] = (
                        self.parse_dimension(value)
                    )

        angle_source = column("position_angle")
        position_angle = (
            np.full(count, np.nan)
            if angle_source is None
            else self._float_values(angle_source)
        )

        magnitude_source = column("magnitude")
        magnitude = (
            np.full(count, np.nan)
            if magnitude_source is None
            else self._float_values(magnitude_source)
        )

        def text_values(key):
            values = column(key)
            if values is None:
                return np.full(count, None, dtype=object)
            return np.asarray(
                [
                    None
                    if np.ma.is_masked(value)
                    or str(value).strip() == ""
                    else str(value).strip()
                    for value in values
                ],
                dtype=object,
            )

        normalized = Table()
        normalized["identifier"] = identifiers
        normalized["ra_deg"] = ra
        normalized["dec_deg"] = dec
        normalized["major_axis_arcmin"] = major
        normalized["minor_axis_arcmin"] = minor
        normalized["position_angle_deg"] = position_angle
        normalized["magnitude"] = magnitude
        normalized["object_type"] = text_values("object_type")
        normalized["common_name"] = text_values("common_name")
        normalized["constellation"] = text_values("constellation")
        return normalized

    @staticmethod
    def _float_values(values):
        result = np.full(len(values), np.nan, dtype=float)
        for index, value in enumerate(values):
            if np.ma.is_masked(value):
                continue
            try:
                result[index] = float(value)
            except (TypeError, ValueError):
                continue
        return result

    @staticmethod
    def parse_dimension(value):
        """Return major and minor dimensions in arcminutes."""
        if value is None or np.ma.is_masked(value):
            return np.nan, np.nan
        numbers = [
            float(item)
            for item in re.findall(
                r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)",
                str(value),
            )
        ]
        if not numbers:
            return np.nan, np.nan
        if len(numbers) == 1:
            return numbers[0], numbers[0]
        return max(numbers[:2]), min(numbers[:2])

    @staticmethod
    def _ellipse(
        center,
        major,
        minor,
        position_angle,
        samples,
        *,
        minimum_size_arcmin=None,
    ):
        """Sample one angular ellipse around an ICRS center."""
        major = float(major)
        minor = float(minor)
        known_angle = np.isfinite(position_angle)
        if not np.isfinite(major) or major <= 0.0:
            major = 1.0
        if not np.isfinite(minor) or minor <= 0.0:
            minor = major

        # Without a measured orientation, use an equal-area circle. This
        # preserves scale without inventing a celestial position angle.
        if not known_angle and not np.isclose(major, minor):
            diameter = np.sqrt(major * minor)
            major = diameter
            minor = diameter

        if minimum_size_arcmin is not None:
            minimum = float(minimum_size_arcmin)
            if not np.isfinite(minimum) or minimum <= 0.0:
                raise ValueError(
                    "minimum_size_arcmin must be positive and finite."
                )
            scale = max(1.0, minimum / min(major, minor))
            major *= scale
            minor *= scale

        phase = np.linspace(
            0.0,
            2.0 * np.pi,
            int(samples),
            endpoint=False,
        )
        north = 0.5 * major * np.cos(phase)
        east = 0.5 * minor * np.sin(phase)
        if known_angle:
            angle = np.deg2rad(float(position_angle))
            north, east = (
                north * np.cos(angle) - east * np.sin(angle),
                north * np.sin(angle) + east * np.cos(angle),
            )
        separation = np.hypot(north, east) * u.arcmin
        bearing = np.arctan2(east, north) * u.rad
        return center.directional_offset_by(bearing, separation)

    def _geometry_table(self, selected=None, magnitude_limit=None):
        """Return the catalogue rows participating in geometry."""
        table = (
            self.catalog
            if magnitude_limit is None
            else self.source_catalog
        )
        if magnitude_limit is not None:
            magnitude = np.asarray(table["magnitude"], dtype=float)
            keep = (
                ~np.isfinite(magnitude)
                | (magnitude <= float(magnitude_limit))
            )
            table = table[keep]
        if selected is None:
            return table
        wanted = {
            str(identifier).strip().casefold()
            for identifier in selected
        }
        keep = np.asarray(
            [
                str(value).strip().casefold() in wanted
                for value in table["identifier"]
            ]
        )
        return table[keep]

    def _resolved_samples(self, samples):
        """Return render-local outline samples within loaded quality."""
        if samples is None:
            return self.samples
        resolved = int(samples)
        if resolved < 12:
            raise ValueError("samples must be at least 12.")
        if resolved > self.samples:
            raise ValueError(
                "samples cannot exceed the layer's maximum sampling "
                f"quality ({self.samples})."
            )
        return resolved

    @staticmethod
    def semantic_category(object_type, *, identifier=None):
        """Normalize one catalog row to Wenu's shared sky taxonomy."""
        if object_type is None or np.ma.is_masked(object_type):
            return "other_objects"
        value = re.sub(
            r"[^a-z0-9]+",
            " ",
            str(object_type).casefold(),
        ).strip()
        identifier_key = re.sub(
            r"[^a-z0-9]+",
            "",
            "" if identifier is None else str(identifier).casefold(),
        )
        if identifier_key == "m1":
            return "supernova_remnants"
        aliases = {
            "gal": "galaxies",
            "galaxy": "galaxies",
            "galaxies": "galaxies",
            "s": "galaxies",
            "e": "galaxies",
            "e?": "galaxies",
            "ir": "galaxies",
            "oc": "open_clusters",
            "open cluster": "open_clusters",
            "gc": "globular_clusters",
            "gb": "globular_clusters",
            "globular cluster": "globular_clusters",
            "pn": "planetary_nebulae",
            "pl": "planetary_nebulae",
            "planetary nebula": "planetary_nebulae",
            "snr": "supernova_remnants",
            "supernova remnant": "supernova_remnants",
            "di": "nebulae",
            "hii": "nebulae",
            "h ii": "nebulae",
            "nebula": "nebulae",
            "diffuse nebula": "nebulae",
            "emission nebula": "nebulae",
            "reflection nebula": "nebulae",
        }
        if value in aliases:
            return aliases[value]
        if "supernova remnant" in value:
            return "supernova_remnants"
        if "planetary nebula" in value:
            return "planetary_nebulae"
        if "globular cluster" in value:
            return "globular_clusters"
        if "open cluster" in value:
            return "open_clusters"
        if "galaxy" in value:
            return "galaxies"
        if "nebula" in value or value.startswith("h ii"):
            return "nebulae"
        return "other_objects"

    def _geometry_metadata(
        self,
        table,
        *,
        minimum_size_arcmin=None,
    ):
        """Return per-object metadata accompanying generated geometry."""
        identifiers = tuple(
            str(value) for value in table["identifier"]
        )
        return {
            "catalog": self.catalog_name,
            "coordinate_system": "altaz",
            "semantic_entity_keys": identifiers,
            "semantic_entity_display_names": identifiers,
            "semantic_entity_categories": tuple(
                self.semantic_category(
                    object_type,
                    identifier=identifier,
                )
                for object_type, identifier in zip(
                    table["object_type"],
                    table["identifier"],
                    strict=True,
                )
            ),
            "magnitude": np.asarray(table["magnitude"], dtype=float),
            "object_type": np.asarray(
                table["object_type"],
                dtype=object,
            ),
            "major_axis_arcmin": np.asarray(
                table["major_axis_arcmin"],
                dtype=float,
            ),
            "minor_axis_arcmin": np.asarray(
                table["minor_axis_arcmin"],
                dtype=float,
            ),
            "position_angle_deg": np.asarray(
                table["position_angle_deg"],
                dtype=float,
            ),
            "position_angle_known": np.isfinite(
                np.asarray(
                    table["position_angle_deg"],
                    dtype=float,
                )
            ),
            "minimum_size_arcmin": minimum_size_arcmin,
        }

    def _maximal_geometry_table(self):
        """Return every loaded row capable of producing an outline."""
        return self._geometry_table(selected=None)

    def _transform_outline_table(
        self,
        table,
        observer,
        *,
        samples,
        minimum_size_arcmin,
    ):
        """Transform one complete outline table in one AltAz operation."""
        if len(table) == 0:
            return (), ()
        outlines = []
        for row in table:
            center = SkyCoord(
                ra=float(row["ra_deg"]) * u.deg,
                dec=float(row["dec_deg"]) * u.deg,
                frame="icrs",
            )
            outlines.append(
                self._ellipse(
                    center,
                    row["major_axis_arcmin"],
                    row["minor_axis_arcmin"],
                    row["position_angle_deg"],
                    samples,
                    minimum_size_arcmin=minimum_size_arcmin,
                )
            )
        native = concatenate(outlines)
        horizontal = native.transform_to(observer.altaz_frame)
        splits = np.arange(1, len(table)) * samples
        return (
            np.split(horizontal.az.to_value(u.deg), splits),
            np.split(horizontal.alt.to_value(u.deg), splits),
        )

    def _observed_outlines(
        self,
        observer,
        *,
        samples,
        minimum_size_arcmin,
    ):
        """Return the maximal cached outline realization and its table."""
        maximal = self._maximal_geometry_table()
        minimum = (
            None
            if minimum_size_arcmin is None
            else float(minimum_size_arcmin)
        )
        longitude, latitude = observed_polygon_arrays(
            self._observed_outline_cache,
            observer,
            source_key=(
                self.layer_name,
                self.catalog_name,
                str(self.source),
                self._source_revision,
                int(samples),
                minimum,
            ),
            build=lambda: self._transform_outline_table(
                maximal,
                observer,
                samples=samples,
                minimum_size_arcmin=minimum,
            ),
        )
        return maximal, longitude, latitude

    @staticmethod
    def _outline_positions(maximal, selected):
        positions = {
            str(identifier): index
            for index, identifier in enumerate(maximal["identifier"])
        }
        try:
            return [
                positions[str(identifier)]
                for identifier in selected["identifier"]
            ]
        except KeyError as error:
            raise RuntimeError(
                "The outline selection is not contained in the loaded "
                "source catalogue."
            ) from error

    def spherical_geometry(
        self,
        observer,
        *,
        selected=None,
        magnitude_limit=None,
        minimum_size_arcmin=None,
        samples=None,
    ) -> SphericalCurves:
        """Return sampled outlines transformed from ICRS to Alt/Az."""
        if self.catalog is None:
            raise RuntimeError(
                "The catalogue has not been loaded. "
                "Call nonstellar.load() first."
            )
        resolved = self.observer if observer is None else observer
        if resolved is None or not hasattr(resolved, "altaz_frame"):
            raise ValueError(
                "An observer with an altaz_frame is required."
            )

        table = self._geometry_table(
            selected,
            magnitude_limit=magnitude_limit,
        )
        resolved_samples = self._resolved_samples(samples)

        maximal, longitude, latitude = self._observed_outlines(
            resolved,
            samples=resolved_samples,
            minimum_size_arcmin=minimum_size_arcmin,
        )
        positions = self._outline_positions(maximal, table)
        identifiers = [str(value) for value in table["identifier"]]

        return SphericalCurves(
            lon_deg=tuple(longitude[index] for index in positions),
            lat_deg=tuple(latitude[index] for index in positions),
            closed=np.ones(len(table), dtype=bool),
            ids=identifiers,
            names=identifiers,
            metadata=self._geometry_metadata(
                table,
                minimum_size_arcmin=minimum_size_arcmin,
            ),
        )

    def spherical_centers(
        self,
        observer,
        *,
        selected=None,
        magnitude_limit=None,
    ) -> SphericalPoints:
        """Return cached AltAz catalogue centers for spatial selection."""
        if self.catalog is None:
            raise RuntimeError(
                "The catalogue has not been loaded. Call load() first."
            )
        resolved = self.observer if observer is None else observer
        if resolved is None or not hasattr(resolved, "altaz_frame"):
            raise ValueError(
                "An observer with an altaz_frame is required."
            )
        table = self._geometry_table(
            selected,
            magnitude_limit=magnitude_limit,
        )
        identifiers = np.asarray(table["identifier"], dtype=object)
        if len(table) == 0:
            longitude = latitude = np.asarray([], dtype=float)
        else:
            longitude, latitude = catalogue_point_altaz(
                self._observed_point_cache,
                resolved,
                source_table=self.source_catalog,
                selected_table=table,
                source_key=(self.catalog_name, self._source_revision),
            )
        semantic_identifiers = tuple(
            str(value) for value in identifiers
        )
        return SphericalPoints(
            lon_deg=longitude,
            lat_deg=latitude,
            ids=identifiers,
            names=identifiers,
            metadata={
                "coordinate_system": "altaz",
                "semantic_entity_keys": semantic_identifiers,
                "semantic_entity_display_names": semantic_identifiers,
                "semantic_entity_categories": tuple(
                    self.semantic_category(
                        object_type,
                        identifier=identifier,
                    )
                    for object_type, identifier in zip(
                        table["object_type"],
                        table["identifier"],
                        strict=True,
                    )
                ),
            },
        )
