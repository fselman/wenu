"""Vectorized fixed-symbol layer for Galactic open clusters."""

from __future__ import annotations

from importlib.resources import as_file
from pathlib import Path
from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from io import StringIO
import json

import numpy as np
from astropy.table import Table

from wenu.coordinates import PositionStatus
from wenu.coordinates import icrs_catalogue_spec, observer_altaz_spec
from wenu.geometry.spherical import SphericalPoints
from wenu.objects.astronomical_object import AstronomicalObject
from wenu.resources import nonstellar_catalog_path
from wenu.sky.observed_cache import catalogue_point_altaz


@dataclass(frozen=True)
class OpenClusterCatalogueMetadata:
    """Source-bound immutable facts for lookup, not a motion solution.

    Raw columns, units and masks remain in the table. Their canonical ECSV
    digest binds all fields, including uninterpreted proper motions, to the
    copied provider resource. Unqualified epoch labels are never made TT.
    """

    document_json: str
    source_epochs: tuple

    @classmethod
    def from_table(cls, table, *, source=None, source_sha256=None):
        from astropy.time import Time
        from wenu_kernel.records import TimePoint

        def text(value):
            if value is None or np.ma.is_masked(value):
                return None
            if not isinstance(value, str):
                raise ValueError("Open-cluster source declarations must be text.")
            return value.strip() or None

        def optional_epoch(value):
            value = text(value)
            return None if value is None or value.casefold() == 'unknown' else value

        metadata = deepcopy(table.meta)
        source_metadata = metadata.get('input_catalogue_metadata', {})
        facts, epochs, parsed = [], [], {}
        identifiers = table['wenu_id'] if 'wenu_id' in table.colnames else table['identifier']
        for index, identifier in enumerate(identifiers):
            source_name = text(table['RA_source'][index]) if 'RA_source' in table.colnames else None
            profile = source_metadata.get(source_name + '_metadata', {}) if source_name else {}
            def declaration(column, key):
                return text(table[column][index]) if column in table.colnames else text(profile.get(key, metadata.get(key)))
            label = optional_epoch(declaration('position_epoch', 'coordinate_epoch'))
            scale = declaration('position_epoch_scale', 'coordinate_epoch_scale')
            frame = declaration('coordinate_frame', 'coordinate_frame')
            origin = declaration('coordinate_origin', 'coordinate_origin')
            if frame is not None:
                parts = frame.casefold().split('/', 1)
                if parts[0].strip() != 'icrs' or (len(parts) == 2 and
                        (not parts[1].split() or parts[1].split()[0] not in ('j2000', 'j2000.0'))):
                    raise ValueError('Unsupported declared open-cluster frame; transform before ingestion.')
            if origin not in (None, 'solar-system-barycenter'):
                raise ValueError('Unsupported declared open-cluster origin.')
            if scale is not None and (label is None or scale not in ('tai', 'tt', 'tdb', 'tcb')):
                raise ValueError('Open-cluster epoch requires a declared label and supported time scale.')
            epoch = None
            if label is not None:
                if not label.startswith(('J', 'B')):
                    raise ValueError('Invalid declared open-cluster coordinate epoch.')
                key = label, scale
                if key not in parsed:
                    try:
                        date = Time(label, **({} if scale is None else {'scale': scale}))
                        if not np.isfinite(date.jd):
                            raise ValueError('Nonfinite epoch.')
                        parsed[key] = (None if scale is None else
                            TimePoint(float(date.jd1), float(date.jd2), scale))
                    except (TypeError, ValueError) as error:
                        raise ValueError('Invalid declared open-cluster coordinate epoch.') from error
                epoch = parsed[key]
            facts.append(dict(identifier=str(identifier), position_source=source_name,
                epoch_label=label, epoch_scale=scale, frame=frame, origin=origin))
            epochs.append(epoch)
        for name in ('ra_deg', 'dec_deg', 'RA', 'Dec'):
            if name in table.colnames and table[name].unit is not None and str(table[name].unit) != 'deg':
                raise ValueError('Open-cluster directions must be normalized to declared degrees before ingestion.')
        canonical = table.copy(copy_data=True)
        canonical.meta = json.loads(json.dumps(metadata, sort_keys=True, allow_nan=False))
        stream = StringIO()
        canonical.write(stream, format='ascii.ecsv')
        document = dict(schema='wenu-open-cluster-catalogue/1', source=None if source is None else str(source),
            source_sha256=source_sha256, derived_table_sha256=sha256(stream.getvalue().encode()).hexdigest(),
            source_metadata=metadata, rows=facts,
            column_units={name: None if table[name].unit is None else str(table[name].unit) for name in table.colnames})
        return cls(json.dumps(document, sort_keys=True, allow_nan=False), tuple(epochs))

    def to_record(self):
        return json.loads(self.document_json)

    def coordinate_spec(self):
        record = self.to_record()
        labels = [row['epoch_label'] for row in record['rows']]
        common = labels[0] if labels and all(label == labels[0] for label in labels) else None
        meta = record['source_metadata']
        return icrs_catalogue_spec(str(meta.get('database') or meta.get('catalog') or 'open-cluster catalogue'),
            epoch=common, provenance=() if record['source'] is None else (record['source'],))


class OpenClusters(AstronomicalObject):
    """Established and likely optically visible Galactic open clusters."""

    layer_name = "open_clusters"

    def __init__(self, observer, *, selected=None):
        self.observer = observer
        self.selected = None if selected is None else tuple(selected)
        self.catalog = None
        self.source = None
        self._source_sha256 = None
        self._source_revision = 0
        self._observed_point_cache = {}

    def load(self, *, filename=None):
        """Load the packaged snapshot or an explicit curated open-cluster ECSV."""
        def read(path):
            digest = sha256(Path(path).read_bytes()).hexdigest()
            table = Table.read(path)
            if sha256(Path(path).read_bytes()).hexdigest() != digest:
                raise ValueError('Open-cluster source changed during ingestion.')
            return table, digest
        if filename is None:
            resource = nonstellar_catalog_path("open_clusters")
            with as_file(resource) as path:
                source = resource
                table, digest = read(path)
        else:
            source = Path(filename)
            table, digest = read(source)
        table = self.normalize_catalogue(table)
        self._validate(table)
        OpenClusterCatalogueMetadata.from_table(table, source=source, source_sha256=digest)
        table = self.mark_amateur_exclusions(table)
        self.source = source
        self._source_sha256 = digest
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

    def position(self, instant=None, *, motion=None, reception=None) -> SphericalPoints:
        """Return lookup centres, or an explicit admitted nominal motion query."""
        if self.catalog is None:
            raise RuntimeError(
                "The catalogue has not been loaded. "
                "Call open_clusters.load() first."
            )
        if reception is not None and motion is None:
            raise ValueError('Explicit reception requires an admitted cluster motion model.')
        table = self._selected_table(None, strict=reception is not None)
        admitted = self.catalogue_metadata_for(table)
        if motion is None:
            longitude, latitude = self._native_centres(table, instant, admitted=admitted)
            spec, state_metadata = admitted.coordinate_spec(), {}
        else:
            longitude, latitude, spec, state_metadata = self._motion_centres(table, motion, instant, reception=reception)
        identifiers = np.asarray(table["identifier"], dtype=object)
        metadata = {
            "catalog": "openclust",
            "coordinate_system": "altaz" if reception is not None else "icrs",
            "catalogue_metadata": deepcopy(table.meta),
        }
        for name in table.colnames:
            if name not in ("identifier", "ra_deg", "dec_deg"):
                metadata[name] = self._column_metadata(table[name])
        metadata['catalogue_admission'] = admitted.to_record()
        metadata['catalogue_position_model'] = 'catalogue_lookup'
        metadata.update(state_metadata)
        return SphericalPoints(
            lon_deg=longitude,
            lat_deg=latitude,
            coordinate_spec=spec,
            ids=np.asarray(table["wenu_id"], dtype=object) if "wenu_id" in table.colnames else identifiers,
            labels=identifiers,
            names=identifiers,
            metadata=metadata,
        )

    def catalogue_metadata_for(self, table):
        """Mirror preserved source facts without acquisition or epoch guessing."""
        return OpenClusterCatalogueMetadata.from_table(table, source=self.source,
            source_sha256=self._source_sha256)

    def native_coordinate_spec(self, table=None):
        """Mirror row epoch labels; a frame/equinox is not a measurement date."""
        return self.catalogue_metadata_for(self._selected_table(None) if table is None else table).coordinate_spec()

    @staticmethod
    def _column_metadata(column):
        return (np.ma.array(column, copy=True) if np.ma.isMaskedArray(column)
                else np.array(column, copy=True))

    def _direction_provider(self, rows, epochs, admitted, scale):
        from wenu.catalogue_state import CatalogueDirectionProvider
        from wenu_kernel.records import ReferenceSpec, UnboundedCoverage
        record = admitted.to_record()
        facts = record['rows']
        origin = ('solar-system-barycenter' if facts and all(
            fact['origin'] == 'solar-system-barycenter' for fact in facts) else 'legacy-unverified-origin')
        reference = ReferenceSpec('icrs', origin, 'catalogue-lookup', 'direction', 'rad',
            'encoded source directions; unqualified epochs and missing frame/origin remain in source record')
        meta = record['source_metadata']
        return CatalogueDirectionProvider(rows,
            namespace=str(meta.get('database') or meta.get('catalog') or meta.get('catalogue') or 'unidentified-open-clusters'),
            catalogue_edition=str(meta.get('version') or meta.get('release') or meta.get('catalog_version') or 'unidentified-source-edition'),
            source_epoch=None, source_epochs=epochs,
            provenance=((str(self.source),) if self.source is not None else ()) + (
                'Wenu source lookup compatibility; no propagation or physical epoch accuracy',),
            reference=reference, capability='catalogue_lookup', semantic_type='open-cluster',
            provider_id='wenu.catalogue-open-clusters', resource_id='derived-open-cluster-table',
            model_id='unpropagated-open-cluster-lookup', coverage=UnboundedCoverage(scale),
            source_identity=(admitted.document_json,))

    def _native_centres(self, table, instant=None, *, admitted=None):
        """Use returned kernel directions; no direct-source fallback on failure."""
        from astropy.time import Time
        from wenu.catalogue_state import catalogue_direction_states, catalogue_direction_angles
        from wenu_kernel.records import TimePoint
        admitted = self.catalogue_metadata_for(table) if admitted is None else admitted
        if instant is None:
            # Undated lookup bookkeeping, never a source measurement epoch.
            time = TimePoint(0, 0, 'tt')
        elif type(instant) is TimePoint:
            time = instant
        else:
            requested = Time(instant).tt
            time = TimePoint(float(requested.jd1), float(requested.jd2), 'tt')
        longitude, latitude = (np.asarray(table[name], dtype=float).copy() for name in ('ra_deg', 'dec_deg'))
        valid = (np.isfinite(longitude) & np.isfinite(latitude)
                 & ~np.ma.getmaskarray(table['ra_deg']) & ~np.ma.getmaskarray(table['dec_deg']))
        longitude[~valid], latitude[~valid] = np.nan, np.nan
        identifiers = table['wenu_id'] if 'wenu_id' in table.colnames else table['identifier']
        unique = {}
        for index in np.flatnonzero(valid):
            key = str(identifiers[index])
            value = float(longitude[index]), float(latitude[index]), admitted.source_epochs[index]
            if key in unique and unique[key] != value:
                raise ValueError('Conflicting open-cluster identities in selected source rows.')
            unique[key] = value
        rows = tuple((key, lon, lat) for key, (lon, lat, _) in unique.items())
        epochs = tuple(value[2] for value in unique.values())
        states = catalogue_direction_states(self._direction_provider(rows, epochs, admitted, time.scale), time)
        angles = dict(zip(unique, catalogue_direction_angles(states, rows), strict=True))
        for index in np.flatnonzero(valid):
            longitude[index], latitude[index] = angles[str(identifiers[index])]
        return longitude, latitude

    def _motion_centres(self, table, motion, instant, *, reception=None):
        """Compose the accepted provider and kernel; never fall back to lookup."""
        from wenu.cluster_state import ClusterMotionCatalogue, ClusterMotionProvider
        from wenu.coordinates import CoordinateSpec
        from wenu_kernel import Kernel
        from wenu_kernel.records import AccuracyRequest, SessionPolicy, StateQuery, TimePoint
        if type(motion) is not ClusterMotionCatalogue:
            raise TypeError('motion must be an admitted ClusterMotionCatalogue.')
        if type(instant) is not TimePoint or instant.scale != motion.coverage.start.scale:
            raise ValueError('Nominal cluster motion requires an explicit matching-scale TimePoint.')
        if not motion.coverage.contains(instant):
            raise ValueError('Cluster evaluation instant is outside the nominal model domain.')
        metadata = motion.to_record()
        source = metadata['source_metadata']
        if self._source_sha256 is None or self._source_sha256 != source['selected_catalogue_sha256']:
            raise ValueError('Cluster motion is bound to a different source catalogue.')
        identifiers = tuple(map(str, table['wenu_id'] if 'wenu_id' in table.colnames else table['identifier']))
        # Validate the complete layer identity set, not only the visible subset.
        full_ids = tuple(map(str, self.catalog['wenu_id'] if 'wenu_id' in self.catalog.colnames else self.catalog['identifier']))
        if set(full_ids) != {row.identifier for row in motion.rows}:
            raise ValueError('Cluster motion and source catalogue identity sets differ.')
        if reception is not None:
            from wenu.astrometric_observation import ReceptionContext
            if type(reception) is not ReceptionContext or instant != reception.tcb:
                raise ValueError('Cluster evaluation must match the explicit reception TCB event.')
        provider = ClusterMotionProvider(motion,
            **({} if reception is None else {'representation': 'cartesian'}))
        try:
            admission = provider.describe().admissions[0]
            records = provider.catalogue(admission.catalogue).objects
            keys = {row.external_ids[0].identifier: row.key for row in records}
            selected_keys = tuple(keys[value] for value in dict.fromkeys(identifiers))
            if selected_keys:
                with Kernel(references=(admission.reference,)) as kernel:
                    kernel.register(provider, ownership='borrowed')
                    with kernel.open_session(SessionPolicy((admission.catalogue,))) as session:
                        batch = session.evaluate(StateQuery(admission.catalogue, admission.model,
                            selected_keys, (instant,), admission.reference,
                            AccuracyRequest(**({} if reception is None else {'metric': 'euclidean_norm'})),
                            require_velocity=reception is not None))
                states = {state.object_key: state for state in batch.states}
            else:
                states = {}
            if reception is not None:
                from dataclasses import replace
                from wenu.astrometric_observation import NominalObservationAdmission, realize_astrometric_batch
                if not selected_keys:
                    # The SDK requires a non-empty query. Refuse rather than
                    # manufacture an unvalidated observed receipt for an empty batch.
                    raise ValueError('Explicit observed cluster selection must be non-empty.')
                observed = realize_astrometric_batch(batch, reception,
                    admission=NominalObservationAdmission(admission, reception.model))
                by_key = {state.object_key: state for state in observed.states}
                ordered_observed = tuple(by_key[keys[value]] for value in identifiers)
                spec = replace(observed.coordinate_spec, longitude_unit='deg', latitude_unit='deg')
                return (np.rad2deg([state.azimuth_rad for state in ordered_observed]),
                    np.rad2deg([state.altitude_rad for state in ordered_observed]), spec,
                    dict(catalogue_position_model=admission.model.model_id,
                         cluster_motion_admission=metadata,
                         cluster_motion_states=tuple(states[keys[value]] for value in identifiers),
                         cluster_motion_model=admission.model, cluster_motion_reference=admission.reference,
                         astrometric_observation=observed, observed_states=ordered_observed))
            ordered = tuple(states[keys[value]] for value in identifiers)
            vectors = np.asarray([state.vector for state in ordered], dtype=float).reshape(-1, 3)
            longitude = np.rad2deg(np.arctan2(vectors[:, 1], vectors[:, 0])) % 360
            latitude = np.rad2deg(np.arctan2(vectors[:, 2], np.hypot(vectors[:, 0], vectors[:, 1])))
            spec = CoordinateSpec(frame=admission.reference.frame_id,
                origin=admission.reference.origin_id, position_status=PositionStatus.ASTROMETRIC,
                instant=f'JD {instant.jd1} {instant.jd2:+}', time_scale=instant.scale,
                provider='wenu.cluster-motion', model=admission.model.model_id,
                provenance=(source['provenance'],))
            return longitude, latitude, spec, dict(catalogue_position_model=admission.model.model_id,
                cluster_motion_admission=metadata, cluster_motion_states=ordered,
                cluster_motion_model=admission.model, cluster_motion_reference=admission.reference)
        finally:
            provider.close()

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

    def _selected_table(self, selected, *, strict=False):
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
            elif strict:
                raise ValueError(f'Unknown observed cluster identity: {requested!r}')
        return self.catalog[np.asarray(indices, dtype=int)]

    def realize(self, context, observer, **options):
        from copy import copy
        from wenu.sky.realization import LayerRealizationContext
        motion = options.pop('motion', None)
        reception = context.reception if isinstance(context, LayerRealizationContext) else None
        if reception is not None and motion is None:
            raise ValueError('Explicit reception requires an admitted cluster motion model.')
        if reception is None and (not isinstance(context, LayerRealizationContext) or not context.is_native_icrs):
            if motion is not None:
                raise ValueError('Nominal cluster motion currently requires native ICRS realization.')
            return super().realize(context, observer, **options)
        instant = None
        if reception is not None:
            instant = reception.tcb
        elif motion is not None:
            from astropy.time import Time
            from wenu_kernel.records import TimePoint
            if context.evaluation_instant is None or context.evaluation_time_scale != 'tcb':
                raise ValueError('Nominal cluster motion requires an explicit TCB evaluation context.')
            time = Time(context.evaluation_instant, scale=context.evaluation_time_scale)
            carry = int(time.jd2 >= .5)
            instant = TimePoint(int(time.jd1) + carry, float(time.jd2) - carry, time.scale)
        table = self._selected_table(options.pop("selected", None), strict=reception is not None)
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
        if motion is None:
            local.catalog, local.selected = table, None
        else:
            local.selected = tuple(map(str, table['wenu_id'] if 'wenu_id' in table.colnames else table['identifier']))
        geometry = local.position(instant, motion=motion, reception=reception)
        if motion is not None and reception is None:
            from dataclasses import replace
            geometry.coordinate_spec = replace(geometry.coordinate_spec, instant=context.evaluation_instant)
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
            "catalogue_metadata": deepcopy(table.meta),
            "geometry_kind": "cartographic_symbol",
            "symbol": "open_cluster",
        }
        for name in table.colnames:
            if name not in ("identifier", "ra_deg", "dec_deg"):
                metadata[name] = self._column_metadata(table[name])
        metadata['catalogue_admission'] = self.catalogue_metadata_for(table).to_record()
        metadata['catalogue_position_model'] = 'catalogue_lookup'

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

        instant = getattr(resolved, 't_astropy', None)
        if instant is None:
            instant = getattr(resolved.altaz_frame, 'obstime', None)
        longitude, latitude = self._native_centres(self.catalog, instant)
        source = self.catalog.copy(copy_data=True)
        source['ra_deg'], source['dec_deg'] = longitude, latitude
        # Changed provider output must never reuse a previous observed frame.
        state_digest = sha256(longitude.tobytes() + latitude.tobytes()).hexdigest()
        azimuth, altitude = catalogue_point_altaz(
            self._observed_point_cache,
            resolved,
            source_table=source,
            selected_table=table,
            source_key=("open_clusters", self._source_revision, state_digest),
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

