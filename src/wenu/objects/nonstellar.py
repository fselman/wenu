"""Catalogue layer for non-stellar astronomical objects."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from importlib.resources import as_file
from pathlib import Path
import re

import astropy.units as u
import numpy as np

from wenu.coordinates import PositionStatus
from wenu.coordinates import observer_altaz_spec
from astropy.coordinates import SkyCoord, concatenate
from astropy.table import Column, Table

from wenu.geometry.spherical import SphericalCurves, SphericalPoints
from wenu.objects.astronomical_object import AstronomicalObject
from wenu.resources import nonstellar_catalog_path
from wenu.sky.observed_cache import (
    catalogue_point_altaz,
    icrs_curve_arrays_to_altaz,
    observed_polygon_arrays,
)


@dataclass(frozen=True)
class NonStellarCatalogueMetadata:
    """Immutable admitted facts; missing facts remain explicit.

    Legacy charts can retain their existing ICRS encoding, but that policy
    is not evidence of a source frame/origin and cannot pass strict admission.
    """

    document_json: str

    def __post_init__(self):
        record = json.loads(self.document_json)
        required = {"schema", "catalogue", "edition", "frame", "origin", "epoch",
                    "epoch_scale", "provenance", "source_sha256", "source_units",
                    "normalized_units", "source_metadata"}
        if not isinstance(record, dict) or set(record) != required:
            raise ValueError("Invalid nonstellar metadata record.")
        expected = self._record(record["source_metadata"], record["source_units"],
                                record["normalized_units"], record["source_sha256"])
        if record != expected:
            raise ValueError("Nonstellar metadata disagrees with preserved source declarations.")
        object.__setattr__(self, "document_json", json.dumps(record, sort_keys=True, allow_nan=False))

    @staticmethod
    def _record(meta, source_units, normalized_units, source_sha256):
        from astropy.time import Time
        if not isinstance(meta, dict) or not isinstance(source_units, dict) or not isinstance(normalized_units, dict):
            raise ValueError("Invalid nonstellar metadata mappings.")
        def text(value):
            if value is None:
                return None
            if not isinstance(value, str) or not value.strip():
                raise ValueError("Invalid nonstellar metadata text.")
            return value.strip()
        def source_text(*keys):
            # General source metadata can also contain structured fields.
            # Preserve them without treating a dictionary as a source name.
            return next((meta[key].strip() for key in keys
                         if isinstance(meta.get(key), str) and meta[key].strip()), None)
        declared = text(meta.get("coordinate_frame"))
        if declared is not None:
            parts = declared.casefold().split("/", 1)
            if parts[0].strip() != "icrs" or (len(parts) == 2 and
                    (not parts[1].split() or parts[1].split()[0] not in ("j2000", "j2000.0"))):
                raise ValueError("Unsupported declared nonstellar frame; transform before ingestion.")
        origin = text(meta.get("coordinate_origin"))
        if origin not in (None, "solar-system-barycenter"):
            raise ValueError("Unsupported declared nonstellar origin.")
        if meta.get("coordinate_equinox") is not None:
            raise ValueError("ICRS has no defining equinox.")
        epoch, scale = text(meta.get("coordinate_epoch")), text(meta.get("coordinate_epoch_scale"))
        if epoch is not None:
            if not epoch.startswith(("J", "B")):
                raise ValueError("Invalid nonstellar coordinate epoch.")
            try:
                time = Time(epoch, **({} if scale is None else {"scale": scale}))
                if not np.isfinite(time.jd):
                    raise ValueError("Non-finite epoch.")
            except (TypeError, ValueError) as error:
                raise ValueError("Invalid nonstellar coordinate epoch/time scale.") from error
        elif scale is not None:
            raise ValueError("Epoch time scale requires a declared epoch.")
        if source_sha256 is not None and (not isinstance(source_sha256, str) or re.fullmatch(r"[0-9a-f]{64}", source_sha256) is None):
            raise ValueError("Invalid nonstellar source digest.")
        for name, unit in source_units.items():
            if not isinstance(name, str) or unit is not None and not isinstance(unit, str):
                raise ValueError("Invalid nonstellar source units.")
            if unit is not None:
                u.Unit(unit).to(u.deg)
        canonical = {"ra_deg": "deg", "dec_deg": "deg", "major_axis_arcmin": "arcmin",
                     "minor_axis_arcmin": "arcmin", "position_angle_deg": "deg"}
        if normalized_units != canonical:
            raise ValueError("Invalid normalized nonstellar angular units.")
        def source_urls(value):
            if isinstance(value, dict):
                for key, item in sorted(value.items()):
                    if key == "url" or key.endswith("_url"):
                        yield text(item)
                    elif isinstance(item, (dict, list)):
                        yield from source_urls(item)
            elif isinstance(value, list):
                for item in value:
                    yield from source_urls(item)
        provenance = sorted({value for value in source_urls(meta) if value is not None})
        return dict(schema="wenu-nonstellar-catalogue/1",
                    catalogue=source_text("catalog", "source"),
                    edition=source_text("release", "catalog_version", "catalog_reference", "catalogue_reference"),
                    frame=None if declared is None else "icrs", origin=origin,
                    epoch=epoch, epoch_scale=scale, provenance=provenance,
                    source_sha256=source_sha256, source_units=source_units,
                    normalized_units=normalized_units, source_metadata=meta)

    @classmethod
    def from_table(cls, table, *, source_units, source_sha256=None):
        canonical = {"ra_deg": "deg", "dec_deg": "deg", "major_axis_arcmin": "arcmin",
                     "minor_axis_arcmin": "arcmin", "position_angle_deg": "deg"}
        normalized_units = {name: str(table[name].unit) if name in table.colnames and table[name].unit is not None else unit
                            for name, unit in canonical.items()}
        record = cls._record(deepcopy(table.meta), deepcopy(source_units), normalized_units, source_sha256)
        return cls(json.dumps(record, sort_keys=True, allow_nan=False))

    @classmethod
    def from_record(cls, record):
        return cls(json.dumps(record, sort_keys=True, allow_nan=False))

    def to_record(self):
        return json.loads(self.document_json)

    @property
    def missing_fields(self):
        """Gaps for the default source-epoch model; no facts are invented."""
        return self.missing_fields_for("source-epoch")

    def missing_fields_for(self, position_model):
        """Required facts follow the explicitly selected provider model."""
        if position_model not in ("source-epoch", "static-direction", "catalogue-lookup"):
            raise ValueError("Unsupported catalogue position model.")
        record = self.to_record()
        required = ("catalogue", "edition", "source_sha256")
        if position_model != "catalogue-lookup":
            required += ("frame", "origin")
        if position_model == "source-epoch":
            required += ("epoch", "epoch_scale")
        missing = [key for key in required if record[key] is None]
        if not record["provenance"]:
            missing.append("provenance")
        missing.extend(f"source_units.{key}" for key in sorted({"ra", "dec"} | set(record["source_units"]))
                       if record["source_units"].get(key) is None)
        return tuple(missing)

    def require_complete(self, *, position_model="source-epoch"):
        missing = self.missing_fields_for(position_model)
        if missing:
            raise ValueError("Incomplete nonstellar metadata: " + ", ".join(missing))
        return self

    def validate_table(self, table, *, require_units=False):
        record = self.to_record()
        if record["source_metadata"] != table.meta:
            raise ValueError("Nonstellar metadata disagrees with table metadata.")
        for name, unit in record["normalized_units"].items():
            if name not in table.colnames:
                if require_units:
                    raise ValueError("Missing normalized nonstellar column.")
                continue
            actual = table[name].unit
            if (actual is None and require_units) or (actual is not None and str(actual) != unit):
                raise ValueError("Nonstellar metadata disagrees with normalized column units.")
        return self

    def coordinate_spec(self, provider, *, position_model="source-epoch"):
        record = self.to_record()
        from wenu.coordinates import CoordinateSpec
        missing = self.missing_fields_for(position_model)
        unqualified_lookup = (position_model == "catalogue-lookup" and
                              (record["frame"] is None or record["origin"] is None))
        if position_model == "catalogue-lookup":
            model = ("catalogue-lookup-legacy-unverified-encoding"
                     if missing or unqualified_lookup else "catalogue-lookup")
        else:
            model = ("legacy-unverified-catalogue-encoding" if missing
                     else "static-direction" if position_model == "static-direction" else None)
        return CoordinateSpec(frame=record["frame"] or "icrs",
                              origin=record["origin"] or ("legacy-unverified-origin"
                                  if position_model == "catalogue-lookup" else "solar-system-barycenter"),
                              epoch=record["epoch"], position_status=PositionStatus.ASTROMETRIC,
                              provider=record["catalogue"] or provider,
                              provenance=tuple(record["provenance"]),
                              model=model)


class NonStellar(AstronomicalObject):
    """A catalogue of extended and other non-stellar objects.

    Catalogue coordinates and dimensions remain in their native ICRS
    representation until ``spherical_geometry()`` is called. Ellipse
    position angles follow the astronomical convention: north through east.
    """

    layer_name = "nonstellar"
    _ANGULAR_SOURCE_FIELDS = ()

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

    def load(self, *, catalog=None, filename=None, require_complete_metadata=False):
        """Load and normalize a non-stellar catalogue."""
        catalog_name = self.catalog_name if catalog is None else str(catalog)
        if type(require_complete_metadata) is not bool:
            raise ValueError("require_complete_metadata must be boolean.")

        def read(path):
            digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
            table = Table.read(path)
            if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest:
                raise ValueError("Nonstellar source changed during ingestion.")
            return table, digest

        if filename is not None:
            source = Path(filename)
            table, digest = read(source)
        else:
            resource = nonstellar_catalog_path(catalog_name)
            with as_file(resource) as path:
                source = resource
                table, digest = read(path)

        source_catalog = self._normalize(table)
        names = {name.casefold(): name for name in table.colnames}
        source_units = {}
        for key in ("ra", "dec", "major", "minor", "position_angle", "dimension"):
            actual = next((names[alias.casefold()] for alias in self._ALIASES[key] if alias.casefold() in names), None)
            if actual is not None:
                unit = table[actual].unit
                source_units[key] = None if unit is None else str(unit)
        for key in self._ANGULAR_SOURCE_FIELDS:
            if key.casefold() in names:
                unit = table[names[key.casefold()]].unit
                source_units[key] = None if unit is None else str(unit)
        metadata = NonStellarCatalogueMetadata.from_table(source_catalog, source_units=source_units, source_sha256=digest)
        if require_complete_metadata:
            metadata.require_complete(position_model=self.position_model)
        active_catalog = source_catalog
        if self.magnitude_limit is not None:
            magnitude = active_catalog["magnitude"]
            keep = (
                ~np.isfinite(magnitude)
                | (magnitude <= self.magnitude_limit)
            )
            active_catalog = source_catalog[keep]
        self.catalog_name = catalog_name
        self.source = source
        self.source_catalog = source_catalog
        self.catalog = active_catalog
        self._catalogue_metadata = metadata
        self._source_revision += 1
        self._observed_point_cache.clear()
        self._observed_outline_cache.clear()
        return self.catalog

    @property
    def catalogue_metadata(self):
        if self.catalog is None:
            raise RuntimeError("The catalogue has not been loaded.")
        table = self.source_catalog if self.source_catalog is not None else self.catalog
        metadata = getattr(self, "_catalogue_metadata", None)
        if metadata is None:
            # Constructed/legacy tables have no proof of original input units
            # or source bytes. Do not manufacture that evidence on restore.
            metadata = NonStellarCatalogueMetadata.from_table(table, source_units={})
        return metadata.validate_table(table)

    @property
    def position_model(self):
        """Default model admission still requires source epoch metadata."""
        return "source-epoch"

    @property
    def admission_missing_fields(self):
        return self.catalogue_metadata.missing_fields_for(self.position_model)

    def require_complete_metadata(self):
        return self.catalogue_metadata.require_complete(position_model=self.position_model)

    def require_catalogue_lookup_metadata(self):
        """Admit preserved chart lookup without claiming physical qualification.

        Source identity, edition/provenance and angular units remain required.
        Missing physical reference/epoch facts stay in the immutable record;
        require_complete_metadata() retains its stricter model requirements.
        """
        return self.catalogue_metadata.require_complete(position_model="catalogue-lookup")

    def native_coordinate_spec(self, table=None):
        """Describe admitted source facts, with explicit legacy uncertainty."""
        metadata = self.catalogue_metadata
        if table is not None:
            metadata.validate_table(table)
        return metadata.coordinate_spec(self.catalog_name, position_model=self.position_model)

    def observed_coordinate_spec(self, observer):
        spec = self.native_coordinate_spec()
        return observer_altaz_spec(observer, position_status=PositionStatus.APPARENT,
                                   provider=spec.provider, model=spec.model,
                                   provenance=spec.provenance)

    def _native_centres(self, table, instant=None):
        """State boundary: unmigrated families retain source coordinates."""
        return (np.asarray(table["ra_deg"], dtype=float),
                np.asarray(table["dec_deg"], dtype=float))

    def _state_table(self, table, instant=None):
        """Source table for legacy observation; migrated families override."""
        return table

    def position(self, instant=None) -> SphericalPoints:
        """Return active native non-stellar catalogue centres in ICRS."""
        if self.catalog is None:
            raise RuntimeError(
                "The catalogue has not been loaded. "
                "Call nonstellar.load() first."
            )
        table = self.catalog
        identifiers = np.asarray(table["identifier"], dtype=object)
        metadata = {
            "catalog": self.catalog_name,
            "coordinate_system": "icrs",
            "catalogue_metadata": deepcopy(table.meta),
        }
        for name in table.colnames:
            if name not in ("identifier", "ra_deg", "dec_deg"):
                metadata[name] = np.asarray(table[name])
        # Provider admission/model metadata cannot be overwritten by a source
        # column with the same spelling; the original column stays in the table.
        metadata["catalogue_admission"] = self.catalogue_metadata.to_record()
        metadata["catalogue_position_model"] = self.position_model
        longitude, latitude = self._native_centres(table, instant)
        return SphericalPoints(
            lon_deg=longitude,
            lat_deg=latitude,
            coordinate_spec=self.native_coordinate_spec(table),
            ids=identifiers,
            names=identifiers,
            metadata=metadata,
        )

    def realize(self, context, observer, **options):
        """Realize original catalogue outlines directly in static ICRS."""
        from wenu.sky.realization import LayerRealizationContext
        from wenu.geometry.spherical import SphericalPolygons
        if not isinstance(context, LayerRealizationContext) or not context.is_native_icrs:
            return super().realize(context, observer, **options)
        selected = options.pop("selected", None)
        if selected is None:
            selected = getattr(self, "selected", None)
        limit = options.pop("magnitude_limit", None)
        minimum = options.pop("minimum_size_arcmin", None)
        samples = self._resolved_samples(options.pop("samples", None))
        excluded = options.pop("excluded_categories", ())
        labels_only = options.pop("labels_only", False)
        if type(labels_only) is not bool:
            raise ValueError("labels_only must be boolean.")
        if labels_only:
            excluded = ()
        if options:
            raise TypeError(f"Unsupported native outline options: {sorted(options)}")
        table_options = {"excluded_categories": excluded} if excluded else {}
        table = self._geometry_table(selected, magnitude_limit=limit, **table_options)
        if labels_only:
            from copy import copy
            local = copy(self)
            local.catalog = table
            geometry = local.position()
            geometry.metadata.update(self._geometry_metadata(table))
            geometry.metadata["coordinate_system"] = "icrs"
            return geometry
        lon, lat = [], []
        longitude, latitude = self._native_centres(table)
        for row, ra, dec in zip(table, longitude, latitude, strict=True):
            outline = self._ellipse(
                SkyCoord(ra=float(ra) * u.deg,
                         dec=float(dec) * u.deg, frame="icrs"),
                row["major_axis_arcmin"], row["minor_axis_arcmin"],
                row["position_angle_deg"], samples,
                minimum_size_arcmin=minimum)
            lon.append(outline.icrs.ra.to_value(u.deg))
            lat.append(outline.icrs.dec.to_value(u.deg))
        identifiers = [str(v) for v in table["identifier"]]
        metadata = self._geometry_metadata(table, minimum_size_arcmin=minimum)
        metadata["coordinate_system"] = "icrs"
        geometry = SphericalPolygons if self.layer_name == "galaxies" else SphericalCurves
        names = identifiers
        if self.layer_name == "globular_clusters":
            names = [str(i) if n is None else str(n)
                     for i, n in zip(table["identifier"], table["common_name"], strict=True)]
        return geometry(lon_deg=tuple(lon), lat_deg=tuple(lat),
                        coordinate_spec=self.native_coordinate_spec(table),
                        ids=identifiers, names=names,
                        **({"closed": np.ones(len(table), dtype=bool)} if geometry is SphericalCurves else {}),
                        metadata=metadata)

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

        ra_source = column("ra", required=True)
        dec_source = column("dec", required=True)
        ra = self._float_values(ra_source, unit=u.deg)
        dec = self._float_values(dec_source, unit=u.deg)
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
            major = self._float_values(major_source, unit=u.arcmin)
            minor = (
                major.copy()
                if minor_source is None
                else self._float_values(minor_source, unit=u.arcmin)
            )
        else:
            dimensions = column("dimension")
            major = np.full(count, np.nan)
            minor = np.full(count, np.nan)
            if dimensions is not None:
                factor = self._unit_factor(dimensions, u.arcmin)
                for index, value in enumerate(dimensions):
                    major[index], minor[index] = (
                        self.parse_dimension(value)
                    )
                major *= factor
                minor *= factor

        angle_source = column("position_angle")
        position_angle = (
            np.full(count, np.nan)
            if angle_source is None
            else self._float_values(angle_source, unit=u.deg)
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

        # Retain source fields, masks and column descriptors, including fields
        # this consumer does not yet understand. Canonical columns below own
        # their output encoding; no source epoch or frame is invented here.
        normalized = source.copy(copy_data=True)
        normalized.meta = deepcopy(source.meta)
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
        for name, original, unit in (
            ("ra_deg", ra_source, u.deg),
            ("dec_deg", dec_source, u.deg),
            ("major_axis_arcmin", major_source, u.arcmin),
            ("minor_axis_arcmin", minor_source if minor_source is not None else major_source, u.arcmin),
            ("position_angle_deg", angle_source, u.deg),
        ):
            normalized[name] = Column(
                normalized[name], unit=unit,
                description=None if original is None else original.description,
                meta={} if original is None else deepcopy(original.meta),
            )
        return normalized

    @staticmethod
    def _unit_factor(values, unit):
        """Convert explicit source units; retain the legacy unitless encoding.

        Unitless inputs still use this loader's historical column contract.
        This compatibility policy is not evidence of source unit metadata.
        """
        source_unit = getattr(values, "unit", None)
        return 1.0 if source_unit is None else u.Unit(source_unit).to(unit)

    @staticmethod
    def _float_values(values, *, unit=None):
        factor = 1.0 if unit is None else NonStellar._unit_factor(values, unit)
        result = np.full(len(values), np.nan, dtype=float)
        for index, value in enumerate(values):
            if np.ma.is_masked(value):
                continue
            try:
                result[index] = float(value)
            except (TypeError, ValueError):
                continue
        return Column(result * factor,
                      unit=getattr(values, "unit", None) if unit is None else unit,
                      description=getattr(values, "description", None),
                      meta=deepcopy(getattr(values, "meta", {})))

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

    def _geometry_table(self, selected=None, magnitude_limit=None, *, excluded_categories=()):
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
        if excluded_categories:
            excluded = frozenset(excluded_categories)
            table = table[np.asarray([self.semantic_category(row["object_type"],
                identifier=row["identifier"]) not in excluded for row in table], dtype=bool)]
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

    @staticmethod
    def semantic_entity_key(identifier):
        """Return the source-owned semantic key for one catalogue entity."""
        return str(identifier)

    def _geometry_metadata(
        self,
        table,
        *,
        minimum_size_arcmin=None,
    ):
        """Return per-object metadata accompanying generated geometry."""
        identifiers = tuple(str(value) for value in table["identifier"])
        semantic_keys = tuple(
            self.semantic_entity_key(value) for value in identifiers
        )
        return {
            "catalog": self.catalog_name,
            "catalogue_metadata": deepcopy(table.meta),
            "catalogue_admission": self.catalogue_metadata.to_record(),
            "catalogue_position_model": self.position_model,
            "coordinate_system": "altaz",
            "semantic_entity_keys": semantic_keys,
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
        longitude, latitude = self._native_centres(table, getattr(observer.altaz_frame, "obstime", None))
        for row, ra, dec in zip(table, longitude, latitude, strict=True):
            center = SkyCoord(
                ra=float(ra) * u.deg,
                dec=float(dec) * u.deg,
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
        native = outlines[0].icrs if len(outlines) == 1 else concatenate(outlines).icrs
        splits = np.arange(1, len(table)) * samples
        return icrs_curve_arrays_to_altaz(
            np.split(native.ra.to_value(u.deg), splits),
            np.split(native.dec.to_value(u.deg), splits),
            observer,
            provider=f"astropy {self.catalog_name} outlines",
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
        excluded_categories=(),
        labels_only=False,
    ) -> SphericalCurves:
        """Return sampled outlines transformed from ICRS to Alt/Az."""
        if self.catalog is None:
            raise RuntimeError(
                "The catalogue has not been loaded. "
                "Call nonstellar.load() first."
            )
        if type(labels_only) is not bool:
            raise ValueError("labels_only must be boolean.")
        if labels_only:
            return self.spherical_centers(observer, selected=selected, magnitude_limit=magnitude_limit)
        resolved = self.observer if observer is None else observer
        if resolved is None or not hasattr(resolved, "altaz_frame"):
            raise ValueError(
                "An observer with an altaz_frame is required."
            )

        table = self._geometry_table(
            selected,
            magnitude_limit=magnitude_limit,
            excluded_categories=excluded_categories,
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
            coordinate_spec=self.observed_coordinate_spec(resolved),
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
                source_table=self._state_table(self.source_catalog, getattr(resolved.altaz_frame, "obstime", None)),
                selected_table=table,
                source_key=(self.catalog_name, self._source_revision),
            )
        semantic_identifiers = tuple(str(value) for value in identifiers)
        semantic_keys = tuple(
            self.semantic_entity_key(value)
            for value in semantic_identifiers
        )
        return SphericalPoints(
            lon_deg=longitude,
            lat_deg=latitude,
            coordinate_spec=self.observed_coordinate_spec(resolved),
            ids=identifiers,
            names=identifiers,
            metadata={
                "coordinate_system": "altaz",
                "catalogue_metadata": deepcopy(table.meta),
                "catalogue_admission": self.catalogue_metadata.to_record(),
                "catalogue_position_model": self.position_model,
                "semantic_entity_keys": semantic_keys,
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

