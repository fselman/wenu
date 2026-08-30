"""Bright-galaxy catalogue layer."""

from __future__ import annotations

import numpy as np

from wenu.coordinates import PositionStatus
from wenu.coordinates import observer_altaz_spec

from wenu.geometry.spherical import SphericalPolygons
from wenu.objects.nonstellar import NonStellar


class Galaxies(NonStellar):
    """OpenNGC galaxies represented by their catalogue ellipses.

    The Magellanic Clouds remain in the normalized catalogue but are
    withheld from ordinary polygon geometry because they are reserved for
    later isophote rendering.
    """

    layer_name = "galaxies"

    _ALIASES = {
        **NonStellar._ALIASES,
        "magnitude": (
            "selection_magnitude",
            "vmag",
            "magnitude",
            "mag",
        ),
        "common_name": ("common_names", "common_name"),
    }

    _FLOAT_FIELDS = (
        "b_magnitude",
        "v_magnitude",
        "selection_magnitude",
        "surface_brightness_b_mag_arcsec2",
    )
    _TEXT_FIELDS = (
        "selection_band",
        "morphology",
        "messier",
        "ngc",
        "ic",
        "identifiers",
        "common_names",
        "openngc_notes",
        "ned_notes",
        "sources",
        "source_file",
        "rendering_class",
    )

    def __init__(
        self,
        observer,
        catalog="galaxies",
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
        names = {
            column.casefold(): column
            for column in source.colnames
        }
        actual = names.get(name.casefold())
        return None if actual is None else source[actual]

    @staticmethod
    def _text_values(values, count, *, default=None):
        if values is None:
            return np.full(count, default, dtype=object)
        return np.asarray(
            [
                default
                if np.ma.is_masked(value)
                or str(value).strip() == ""
                else str(value).strip()
                for value in values
            ],
            dtype=object,
        )

    def _normalize(self, source):
        normalized = super()._normalize(source)
        count = len(source)

        for name in self._FLOAT_FIELDS:
            values = self._source_column(source, name)
            normalized[name] = (
                np.full(count, np.nan)
                if values is None
                else self._float_values(values)
            )

        for name in self._TEXT_FIELDS:
            default = "ellipse" if name == "rendering_class" else None
            normalized[name] = self._text_values(
                self._source_column(source, name),
                count,
                default=default,
            )
        return normalized

    def _geometry_table(self, selected=None, magnitude_limit=None):
        table = super()._geometry_table(
            selected,
            magnitude_limit=magnitude_limit,
        )
        rendering_class = np.asarray(
            table["rendering_class"],
            dtype=str,
        )
        return table[rendering_class == "ellipse"]

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
        for name in self._FLOAT_FIELDS:
            metadata[name] = np.asarray(table[name], dtype=float)
        for name in self._TEXT_FIELDS:
            metadata[name] = np.asarray(table[name], dtype=object)
        return metadata

    def spherical_geometry(
        self,
        observer,
        *,
        selected=None,
        magnitude_limit=None,
        minimum_size_arcmin=None,
        samples=None,
    ) -> SphericalPolygons:
        """Return galaxy ellipses as polygons transformed to Alt/Az."""
        if self.catalog is None:
            raise RuntimeError(
                "The catalogue has not been loaded. "
                "Call galaxies.load() first."
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

        return SphericalPolygons(
            lon_deg=tuple(longitude[index] for index in positions),
            lat_deg=tuple(latitude[index] for index in positions),
            coordinate_spec=observer_altaz_spec(
                resolved, position_status=PositionStatus.APPARENT, provider="astropy OpenNGC"
            ),
            ids=identifiers,
            names=identifiers,
            metadata=self._geometry_metadata(
                table,
                minimum_size_arcmin=minimum_size_arcmin,
            ),
        )