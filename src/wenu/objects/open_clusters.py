"""Vectorized fixed-symbol layer for Galactic open clusters."""

from __future__ import annotations

from importlib.resources import as_file
from pathlib import Path

import numpy as np
from astropy.table import Table

from wenu.coordinates import PositionStatus
from wenu.coordinates import icrs_catalogue_spec, observer_altaz_spec
from wenu.geometry.spherical import SphericalPoints
from wenu.objects.astronomical_object import AstronomicalObject
from wenu.resources import nonstellar_catalog_path
from wenu.sky.observed_cache import catalogue_point_altaz


class OpenClusters(AstronomicalObject):
    """Established and likely optically visible Galactic open clusters."""

    layer_name = "open_clusters"

    def __init__(self, observer, *, selected=None):
        self.observer = observer
        self.selected = None if selected is None else tuple(selected)
        self.catalog = None
        self.source = None
        self._source_revision = 0
        self._observed_point_cache = {}

    def load(self, *, filename=None):
        """Load the packaged snapshot or an explicit curated open-cluster ECSV."""
        if filename is None:
            resource = nonstellar_catalog_path("open_clusters")
            with as_file(resource) as path:
                self.source = resource
                table = Table.read(path)
        else:
            self.source = Path(filename)
            table = Table.read(self.source)
        table = self.normalize_catalogue(table)
        self._validate(table)
        table = self.mark_amateur_exclusions(table)
        self.catalog = table
        self._source_revision += 1
        self._observed_point_cache.clear()
        return self.catalog

    @staticmethod
    def mark_amateur_exclusions(table):
        """Retain every row and mark only explicit Dias IR/E classifications."""
        marked = table.copy(copy_data=True)
        flags = (np.asarray([str(v).strip().upper() for v in table['source_type_flag']])
                 if 'source_type_flag' in table.colnames else np.full(len(table), ''))
        marked['excluded_ir_embedded'] = np.isin(flags, ('IR', 'E'))
        marked['amateur_exclusion_reason'] = np.where(flags == 'IR', 'infrared_discovery',
            np.where(flags == 'E', 'embedded', ''))
        return marked

    @classmethod
    def _amateur_filtered(cls, table, exclude):
        if type(exclude) is not bool:
            raise ValueError('exclude_infrared_embedded must be boolean.')
        if not exclude:
            return table
        marked = cls.mark_amateur_exclusions(table)
        return marked[~np.asarray(marked['excluded_ir_embedded'], dtype=bool)]

    def position(self, instant=None) -> SphericalPoints:
        """Return selected native open-cluster catalogue centres in ICRS."""
        del instant
        if self.catalog is None:
            raise RuntimeError(
                "The catalogue has not been loaded. "
                "Call open_clusters.load() first."
            )
        table = self._selected_table(None)
        identifiers = np.asarray(table["identifier"], dtype=object)
        metadata = {
            "catalog": "openclust",
            "coordinate_system": "icrs",
        }
        for name in table.colnames:
            if name not in ("identifier", "ra_deg", "dec_deg"):
                metadata[name] = np.asarray(table[name])
        provenance = () if self.source is None else (str(self.source),)
        return SphericalPoints(
            lon_deg=np.asarray(table["ra_deg"], dtype=float),
            lat_deg=np.asarray(table["dec_deg"], dtype=float),
            coordinate_spec=icrs_catalogue_spec(
                str(table.meta.get("database", "Dias/HEASARC open-cluster catalogue")),
                provenance=provenance,
            ),
            ids=np.asarray(table["wenu_id"], dtype=object) if "wenu_id" in table.colnames else identifiers,
            labels=identifiers,
            names=identifiers,
            metadata=metadata,
        )

    @staticmethod
    def normalize_catalogue(table):
        """Adapt the curated union at the layer boundary, retaining source columns.

        V10 is a selection statistic, never an integrated V magnitude.
        Only Hunt type o and Dias-only rows belong in this layer.
        """
        if "wenu_id" not in table.colnames:
            return table
        from astropy.table import MaskedColumn
        from astropy import units as u
        required = {"wenu_id", "RA", "Dec", "has_hunt", "has_dias",
                    "hunt_type", "hunt_name", "dias_id"}
        if required.difference(table.colnames):
            raise ValueError("Incomplete curated open-cluster catalogue.")
        if len(set(map(str, table["wenu_id"]))) != len(table):
            raise ValueError("Duplicate wenu_id values in active catalogue.")
        if any(not (bool(r["has_hunt"]) or bool(r["has_dias"])) for r in table):
            raise ValueError("A curated row has neither source catalogue.")
        if any(bool(row["has_hunt"]) and str(row["hunt_type"]).strip() != "o"
               for row in table):
            raise ValueError("Remove globular clusters/moving groups before atlas installation.")
        output = table.copy(copy_data=True)
        # Astropy JSON text columns can hide numeric fill values under masks.
        # Canonicalize those unavailable slots to null before snapshot encoding.
        for name in output.colnames:
            column = output[name]
            if column.dtype.hasobject:
                values = np.asarray(column, dtype=object).copy()
                values[np.ma.getmaskarray(column)] = None
                output.replace_column(name, MaskedColumn(values, mask=np.ma.getmaskarray(column),
                    unit=column.unit, description=column.description))
        output["identifier"] = [str(r["hunt_name"] if r["has_hunt"] else r["dias_id"]).replace("_", " ") for r in table]
        output["ra_deg"] = MaskedColumn(table["RA"], unit=u.deg)
        output["dec_deg"] = MaskedColumn(table["Dec"], unit=u.deg)
        for name, unit in (("apparent_diameter_arcmin", u.arcmin),
                           ("member_count", None), ("distance_pc", u.pc),
                           ("reddening_e_bv", None)):
            values = [r[("hunt_" if r["has_hunt"] else "dias_") + name] for r in table]
            output[name] = MaskedColumn([np.nan if np.ma.is_masked(v) else float(v) for v in values],
                mask=[np.ma.is_masked(v) for v in values], unit=unit)
        output["object_type"] = ["Open Cluster"] * len(output)
        # The accepted curated selection bypasses the original Dias IR/E flag.
        # Preserve that flag under dias_source_type_flag for review.
        output["source_type_flag"] = [""] * len(output)
        if (np.any(np.ma.getmaskarray(output["ra_deg"])) or
                np.any(np.ma.getmaskarray(output["dec_deg"])) or
                not np.all(np.isfinite(np.asarray(output["ra_deg"], float))) or
                not np.all(np.isfinite(np.asarray(output["dec_deg"], float))) or
                np.any(np.abs(np.asarray(output["dec_deg"], float)) > 90)):
            raise ValueError("Invalid curated ICRS centres.")
        return output

    @staticmethod
    def _validate(table):
        required = {
            "identifier",
            "ra_deg",
            "dec_deg",
            "apparent_diameter_arcmin",
            "object_type",
        }
        missing = required.difference(table.colnames)
        if missing:
            raise ValueError(
                "Open-cluster catalogue is missing columns: "
                + ", ".join(sorted(missing))
            )

    def _selected_table(self, selected):
        selection = self.selected if selected is None else selected
        if selection is None:
            return self.catalog
        catalogue_ids = np.asarray(
            [
                str(value).strip().casefold()
                for value in self.catalog["identifier"]
            ],
            dtype=object,
        )
        indices = []
        for requested in selection:
            matches = np.flatnonzero(
                (catalogue_ids == str(requested).strip().casefold()) |
                (np.asarray([str(v).strip().casefold() for v in self.catalog["wenu_id"]]) == str(requested).strip().casefold()
                 if "wenu_id" in self.catalog.colnames else False)
            )
            if matches.size:
                indices.append(int(matches[0]))
        return self.catalog[np.asarray(indices, dtype=int)]

    def realize(self, context, observer, **options):
        from copy import copy
        from wenu.sky.realization import LayerRealizationContext
        if not isinstance(context, LayerRealizationContext) or not context.is_native_icrs:
            return super().realize(context, observer, **options)
        table = self._selected_table(options.pop("selected", None))
        table = self._amateur_filtered(table, options.pop('exclude_infrared_embedded', False))
        minimum = options.pop("minimum_size_arcmin", None)
        if options:
            raise TypeError(f"Unsupported native cluster options: {sorted(options)}")
        if minimum is not None:
            minimum = float(minimum)
            if not np.isfinite(minimum) or minimum < 0:
                raise ValueError("minimum_size_arcmin must be finite and non-negative.")
            sizes = np.asarray(table["apparent_diameter_arcmin"], dtype=float)
            table = table[np.isfinite(sizes) & (sizes >= minimum)]
        local = copy(self)
        local.catalog, local.selected = table, None
        geometry = local.position()
        geometry.metadata.update(geometry_kind="cartographic_symbol", symbol="open_cluster")
        return geometry

    def spherical_geometry(
        self,
        observer,
        *,
        selected=None,
        minimum_size_arcmin=None,
        exclude_infrared_embedded=False,
    ) -> SphericalPoints:
        """Return vectorized Alt/Az centers for open-cluster symbols."""
        if self.catalog is None:
            raise RuntimeError(
                "The catalogue has not been loaded. "
                "Call open_clusters.load() first."
            )
        resolved = self.observer if observer is None else observer
        if resolved is None or not hasattr(resolved, "altaz_frame"):
            raise ValueError(
                "An observer with an altaz_frame is required."
            )
        table = self._selected_table(selected)
        table = self._amateur_filtered(table, exclude_infrared_embedded)
        if minimum_size_arcmin is not None:
            minimum = float(minimum_size_arcmin)
            if not np.isfinite(minimum) or minimum < 0.0:
                raise ValueError(
                    "minimum_size_arcmin must be finite and "
                    "non-negative."
                )
            sizes = np.asarray(
                table["apparent_diameter_arcmin"],
                dtype=float,
            )
            table = table[np.isfinite(sizes) & (sizes >= minimum)]
        identifiers = np.asarray(table["identifier"], dtype=object)
        metadata = {
            "catalog": "openclust",
            "coordinate_system": "altaz",
            "geometry_kind": "cartographic_symbol",
            "symbol": "open_cluster",
        }
        for name in table.colnames:
            if name not in ("identifier", "ra_deg", "dec_deg"):
                metadata[name] = np.asarray(table[name])

        if len(table) == 0:
            return SphericalPoints(
                lon_deg=np.asarray([], dtype=float),
                lat_deg=np.asarray([], dtype=float),
                coordinate_spec=observer_altaz_spec(
                    resolved,
                    position_status=PositionStatus.APPARENT,
                    provider="astropy OpenClust"
                ),
                ids=np.asarray(table["wenu_id"], dtype=object) if "wenu_id" in table.colnames else identifiers,
                labels=identifiers,
                names=identifiers,
                metadata=metadata,
            )

        azimuth, altitude = catalogue_point_altaz(
            self._observed_point_cache,
            resolved,
            source_table=self.catalog,
            selected_table=table,
            source_key=("open_clusters", self._source_revision),
        )
        return SphericalPoints(
            lon_deg=azimuth,
            lat_deg=altitude,
            coordinate_spec=observer_altaz_spec(
                resolved,
                position_status=PositionStatus.APPARENT,
                provider="astropy OpenClust"
            ),
            ids=np.asarray(table["wenu_id"], dtype=object) if "wenu_id" in table.colnames else identifiers,
            labels=identifiers,
            names=identifiers,
            metadata=metadata,
        )

