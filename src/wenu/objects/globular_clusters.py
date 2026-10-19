"""Milky Way globular-cluster catalogue layer."""

from __future__ import annotations

import numpy as np
import astropy.units as u

from wenu.objects.nonstellar import NonStellar


class GlobularClusters(NonStellar):
    """Harris Milky Way globular clusters drawn as circular outlines.

    Catalogue size is represented by the measured half-light diameter,
    twice the Harris half-light radius. The original structural parameters
    remain available in geometry metadata.
    """

    layer_name = "globular_clusters"
    _ANGULAR_SOURCE_FIELDS = ("core_radius", "half_light_radius")

    @property
    def _uses_catalogue_lookup(self):
        return True

    def _direction_provider(self, rows, scale):
        """Globular source identity; shared owner supplies lookup mechanics."""
        return self._catalogue_direction_provider(rows, scale,
            capability="catalogue_lookup", semantic_type="globular-cluster",
            provider_id="wenu.globular-lookup", resource_id="derived-globular-table",
            model_id="globular-catalogue-lookup")

    _FLOAT_FIELDS = (
        "lii",
        "bii",
        "helio_distance",
        "galcen_distance",
        "metallicity",
        "reddening",
        "abs_vmag",
        "ellipticity",
        "central_concentration",
        "core_radius",
        "half_light_radius",
        "cent_surf_brightness",
    )

    def __init__(
        self,
        observer,
        catalog="globular_clusters",
        *,
        magnitude_limit=12.0,
        samples=73,
    ):
        super().__init__(
            observer=observer,
            catalog=catalog,
            magnitude_limit=magnitude_limit,
            samples=samples,
        )

    @staticmethod
    def _source_column(source, name):
        names = {column.casefold(): column for column in source.colnames}
        actual = names.get(name.casefold())
        return None if actual is None else source[actual]

    @staticmethod
    def _text_values(values, count):
        if values is None:
            return np.full(count, None, dtype=object)
        return np.asarray(
            [
                None
                if np.ma.is_masked(value) or str(value).strip() == ""
                else str(value).strip()
                for value in values
            ],
            dtype=object,
        )

    def _normalize(self, source):
        normalized = super()._normalize(source)
        count = len(source)

        alternate = self._text_values(
            self._source_column(source, "alt_name"),
            count,
        )
        normalized["common_name"] = alternate
        normalized["object_type"] = np.full(
            count,
            "globular cluster",
            dtype=object,
        )

        for name in self._FLOAT_FIELDS:
            values = self._source_column(source, name)
            unit = u.arcmin if name in ("core_radius", "half_light_radius") else None
            normalized[name] = (
                np.full(count, np.nan)
                if values is None
                else self._float_values(values, unit=unit)
            )
            if unit is not None:
                normalized[name].unit = unit

        # Normalized radii are in arcminutes. The plotted circle represents
        # the half-light diameter, not a catalogue major/minor ellipse.
        diameter = 2.0 * np.asarray(
            normalized["half_light_radius"],
            dtype=float,
        )
        normalized["major_axis_arcmin"] = diameter
        normalized["minor_axis_arcmin"] = diameter
        normalized["position_angle_deg"] = np.full(count, np.nan)
        normalized["major_axis_arcmin"].unit = u.arcmin
        normalized["minor_axis_arcmin"].unit = u.arcmin
        normalized["position_angle_deg"].unit = u.deg
        return normalized

    def _geometry_metadata(
        self,
        table,
        *,
        minimum_size_arcmin=None,
    ):
        metadata = super()._geometry_metadata(
            table,
            minimum_size_arcmin=minimum_size_arcmin,
        )
        metadata["size_definition"] = "half_light_diameter"
        metadata["common_name"] = np.asarray(
            table["common_name"],
            dtype=object,
        )
        for name in self._FLOAT_FIELDS:
            metadata[name] = np.asarray(table[name], dtype=float)
        return metadata

    def spherical_geometry(
        self,
        observer,
        *,
        selected=None,
        minimum_size_arcmin=None,
        samples=None,
        labels_only=False,
    ):
        geometry = super().spherical_geometry(
            observer,
            selected=selected,
            minimum_size_arcmin=minimum_size_arcmin,
            samples=samples,
            labels_only=labels_only,
        )
        table = self._geometry_table(selected)
        geometry.names = np.asarray(
            [
                str(identifier)
                if common_name is None
                else str(common_name)
                for identifier, common_name in zip(
                    table["identifier"],
                    table["common_name"],
                )
            ],
            dtype=object,
        )
        return geometry

