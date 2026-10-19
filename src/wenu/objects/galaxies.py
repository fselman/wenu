"""Bright-galaxy catalogue layer."""

from __future__ import annotations

import numpy as np

from wenu.geometry.spherical import SphericalPolygons
from wenu.objects.nonstellar import NonStellar


class Galaxies(NonStellar):
    """OpenNGC galaxies represented by their catalogue ellipses.

    The Magellanic Clouds remain in the normalized catalogue but are
    withheld from ordinary polygon geometry because they are reserved for
    later isophote rendering.
    """

    layer_name = "galaxies"

    @property
    def position_model(self):
        """Fixed ICRS chart directions, independent of the requested epoch.

        Any source measurement epoch remains provenance. This model makes
        no exact physical proper-motion or uncertainty claim.
        """
        return "static-direction"

    def _direction_provider(self, rows, scale):
        """Construct a source-bound provider; shared mechanics own no galaxy facts."""
        from astropy.time import Time
        from wenu.catalogue_state import CatalogueDirectionProvider
        from wenu_kernel.records import ReferenceSpec, TimePoint, UnboundedCoverage
        metadata = self.catalogue_metadata
        lookup_missing = metadata.missing_fields_for("catalogue-lookup")
        if not lookup_missing:
            metadata = self.require_catalogue_lookup_metadata()
        record = metadata.to_record()
        source_epoch = None
        # A static lookup does not turn an unqualified source date into a
        # numerical epoch. The complete original declaration stays in metadata.
        if record["epoch"] is not None and record["epoch_scale"] in ("tai", "tt", "tdb", "tcb"):
            source = Time(record["epoch"], scale=record["epoch_scale"])
            source_epoch = TimePoint(float(source.jd1), float(source.jd2), source.scale)
        missing = tuple(dict.fromkeys((*self.admission_missing_fields, *lookup_missing)))
        status = "legacy-unverified-catalogue-encoding" if missing else "static-catalogue-model"
        reference = ReferenceSpec(record["frame"] or "icrs",
            record["origin"] or "legacy-unverified-origin", status, "direction", "rad",
            "static chart model; missing source declarations: " + (",".join(missing) or "none"))
        provenance = tuple(record["provenance"]) + (
            "Wenu static chart model; physical uncertainty not evaluated; " + status,
            "catalogue-lookup admission: " + ("source-bound" if not lookup_missing
                else "legacy compatibility; missing lookup facts: " + ",".join(lookup_missing)),)
        return CatalogueDirectionProvider(rows,
            namespace=record["catalogue"] or self.catalog_name,
            source_epoch=source_epoch, provenance=provenance,
            catalogue_edition=record["edition"] or "unidentified-source-edition",
            reference=reference, capability="static_direction", semantic_type="galaxy",
            provider_id="wenu.static-galaxies", resource_id="derived-static-galaxy-table",
            model_id="static-galaxy-chart-directions", coverage=UnboundedCoverage(scale),
            source_identity=(metadata.document_json,))

    def _native_centres(self, table, instant=None):
        """Obtain static directions through the kernel, preserving source facts."""
        from astropy.time import Time
        from wenu.catalogue_state import (
            catalogue_direction_states, catalogue_direction_angles,
        )
        from wenu_kernel.records import TimePoint
        self.catalogue_metadata.validate_table(table)
        if instant is None:
            # Deterministic evaluation anchor for an undated static lookup.
            # This is software policy, never a source measurement epoch.
            time = TimePoint(0, 0, "tt")
        elif type(instant) is TimePoint:
            time = instant
        else:
            requested = Time(instant).tt
            time = TimePoint(float(requested.jd1), float(requested.jd2), "tt")
        longitude = np.asarray(table["ra_deg"], dtype=float).copy()
        latitude = np.asarray(table["dec_deg"], dtype=float).copy()
        valid = np.isfinite(longitude) & np.isfinite(latitude)
        rows = tuple((str(identifier), float(ra), float(dec)) for identifier, ra, dec in zip(
            table["identifier"][valid], longitude[valid], latitude[valid], strict=True))
        provider = self._direction_provider(rows, time.scale)
        states = catalogue_direction_states(provider, time)
        angles = catalogue_direction_angles(states, rows)
        if angles:
            longitude[valid], latitude[valid] = np.asarray(angles).T
        return longitude, latitude

    def _state_table(self, table, instant=None):
        longitude, latitude = self._native_centres(table, instant)
        state_table = table.copy(copy_data=True)
        state_table["ra_deg"] = longitude
        state_table["dec_deg"] = latitude
        return state_table

    def _outline_state(self, table, instant):
        """Query before the observed-outline cache, including its warm path."""
        return self._native_centres(table, instant)

    def _observed_point_source_key(self, table):
        return (super()._observed_point_source_key(table),
                tuple(str(value) for value in table["identifier"]),
                np.asarray(table["ra_deg"], dtype=float).tobytes(),
                np.asarray(table["dec_deg"], dtype=float).tobytes(),
                self.catalogue_metadata.document_json)

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
            coordinate_spec=self.observed_coordinate_spec(resolved),
            ids=identifiers,
            names=identifiers,
            metadata=self._geometry_metadata(
                table,
                minimum_size_arcmin=minimum_size_arcmin,
            ),
        )
