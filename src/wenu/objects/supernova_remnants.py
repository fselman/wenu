"""Green Galactic supernova-remnant catalogue layer."""

from __future__ import annotations

import numpy as np

from wenu.objects.nonstellar import NonStellar


class SupernovaRemnants(NonStellar):
    """Confirmed Galactic supernova remnants from Green's catalogue.

    Green supplies radio major and minor angular diameters but does not
    supply celestial position angles. Consequently, unequal axes are drawn
    as equal-area circles by :class:`NonStellar`; Wenu does not invent an
    orientation. The measured axes remain available in geometry metadata.

    The catalogue's 1 GHz flux density is radio metadata. It is not an
    optical magnitude or visibility measure.
    """

    layer_name = "supernova_remnants"

    _ALIASES = {
        **NonStellar._ALIASES,
        "identifier": (
            "identifier",
            "snr",
            "name",
            "object",
            "designation",
        ),
    }

    _FLOAT_FIELDS = (
        "galactic_longitude_deg",
        "galactic_latitude_deg",
        "flux_1ghz_jy",
        "spectral_index",
    )
    _TEXT_FIELDS = (
        "morphology",
        "flux_limit_flag",
        "flux_uncertain",
        "spectral_index_flag",
        "alternate_names",
    )

    def __init__(
        self,
        observer,
        catalog="supernova_remnants",
        *,
        selected=None,
        samples=73,
    ):
        super().__init__(
            observer=observer,
            catalog=catalog,
            magnitude_limit=None,
            samples=samples,
        )
        self.selected = None if selected is None else tuple(selected)

    def spherical_geometry(self, observer, *, selected=None, **kwargs):
        selection = self.selected if selected is None else selected
        return super().spherical_geometry(
            observer,
            selected=selection,
            **kwargs,
        )

    @staticmethod
    def semantic_entity_key(identifier):
        """Preserve the signed Galactic latitude in Green designations."""
        return (
            str(identifier)
            .replace("+", "_plus_")
            .replace("-", "_minus_")
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

        for name in self._FLOAT_FIELDS:
            values = self._source_column(source, name)
            normalized[name] = (
                np.full(count, np.nan)
                if values is None
                else self._float_values(values)
            )

        for name in self._TEXT_FIELDS:
            normalized[name] = self._text_values(
                self._source_column(source, name),
                count,
            )

        normalized["object_type"] = np.asarray(
            [
                "supernova remnant"
                if morphology is None
                else f"supernova remnant ({morphology})"
                for morphology in normalized["morphology"]
            ],
            dtype=object,
        )
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
        for name in self._FLOAT_FIELDS:
            metadata[name] = np.asarray(table[name], dtype=float)
        for name in self._TEXT_FIELDS:
            metadata[name] = np.asarray(table[name], dtype=object)
        metadata.update(
            {
                "size_definition": "green_radio_angular_diameter",
                "position_angle_available": False,
                "shape_representation": (
                    "circle_for_single_diameter_or_equal_area_circle_"
                    "for_unequal_axes_without_position_angle"
                ),
                "flux_1ghz_is_optical_visibility": False,
            }
        )
        return metadata
