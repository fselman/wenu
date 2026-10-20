"""Milky Way surface-brightness isophote layer."""

from __future__ import annotations

import json

import numpy as np

from wenu.coordinates import PositionStatus
from wenu.coordinates import observer_altaz_spec, icrs_catalogue_spec

from wenu_kernel.geometry.spherical import SphericalPolygons
from wenu.sky.isophote_sources import IsophoteSourceMetadata, source_receipt, packaged_evidence
from wenu_kernel.geometry.topology import ring_interior
from wenu.resources import milky_way_isophote_path
from wenu.sky.observed_cache import (
    icrs_curve_arrays_to_altaz,
    observed_polygon_arrays,
)
from wenu.sky.sky_layer import SkyLayer


class MilkyWayIsophotes(SkyLayer):
    """Nested Milky Way isophotes with GeoJSON ring topology preserved."""

    layer_name = "milky_way_isophotes"
    available_levels = ("ol1", "ol2", "ol3", "ol4", "ol5")
    # D3-Celestial OL1 is a very faint, full-longitude envelope whose two
    # principal boundaries produce an unnaturally broad band in ordinary
    # charts.  Retain it as explicit catalogue content, but start governed
    # defaults at OL2.
    default_levels = ("ol2", "ol3", "ol4", "ol5")

    def __init__(self, observer, *, levels=None):
        self.observer = observer
        self.levels = self._validate_levels(levels)
        self.catalogue_metadata = None
        self.features = None
        self.source = None
        self.sources = {}
        self._source_revision = 0
        self._observed_polygon_cache = {}

    @classmethod
    def _validate_levels(cls, levels):
        if levels is None:
            return cls.default_levels
        levels = tuple(str(level) for level in levels)
        unknown = set(levels).difference(cls.available_levels)
        if unknown:
            raise ValueError(
                "Unknown Milky Way isophote level(s): "
                + ", ".join(sorted(unknown))
            )
        if len(set(levels)) != len(levels):
            raise ValueError("Milky Way isophote levels must be unique.")
        return tuple(
            level for level in cls.available_levels if level in levels
        )

    def load(self, filename=None):
        """Load and validate the canonical GeoJSON snapshot."""
        features = {}
        receipts = {}
        sources = {}
        paths = (
            tuple(milky_way_isophote_path(level) for level in self.available_levels)
            if filename is None
            else (filename,)
        )
        for path in paths:
            with open(path, "rb") as stream:
                raw = stream.read()
            document = json.loads(raw)
            if document.get("type") != "FeatureCollection":
                raise ValueError("Milky Way data must be a FeatureCollection.")
            for feature in document.get("features", ()):
                level = str(
                    feature.get("id")
                    or feature.get("properties", {}).get("id")
                )
                geometry = feature.get("geometry", {})
                if level not in self.available_levels:
                    raise ValueError(f"Unexpected isophote level: {level!r}.")
                if level in features:
                    raise ValueError(f"Duplicate isophote level: {level!r}.")
                if geometry.get("type") != "MultiPolygon":
                    raise ValueError(
                        f"{level} must use GeoJSON MultiPolygon geometry."
                    )
                receipts[level] = source_receipt(raw, document, feature)
                features[level] = geometry["coordinates"]
                sources[level] = str(path)
        if tuple(level for level in self.available_levels if level in features) != self.available_levels:
            raise ValueError("Milky Way data must contain ol1 through ol5.")
        evidence = ()
        if filename is None:
            from pathlib import Path
            evidence = packaged_evidence(Path(paths[0]).parent / "milky_way_d3.provenance.json", receipts=receipts)
        metadata = IsophoteSourceMetadata.admit("milky_way", receipts, evidence=evidence)
        metadata.validate("milky_way", features)
        self.catalogue_metadata = metadata
        self.features = features
        self.sources = sources
        self.source = tuple(sources[level] for level in self.available_levels)
        self._source_revision += 1
        self._observed_polygon_cache.clear()
        return self

    def validate_source(self, *, source_digests=None):
        """Refuse mismatched data before native output or observed cache reuse."""
        if not isinstance(self.catalogue_metadata, IsophoteSourceMetadata):
            raise ValueError("Missing admitted isophote source metadata.")
        self.catalogue_metadata.validate("milky_way", self.features, source_digests=source_digests)

    def spherical_geometry(self, observer, *, levels=None):
        return self._spherical_geometry(observer, levels=levels)

    def realize(self, context, observer, **geometry_options):
        """Retain native ring topology for the static ICRS product."""
        if context.is_native_icrs:
            return self._spherical_geometry(observer, native_icrs=True, **geometry_options)
        return self.spherical_geometry(observer, **geometry_options)

    def _spherical_geometry(self, observer, *, levels=None, native_icrs=False):
        """Transform the selected ICRS isophote rings to observer Alt/Az."""
        if self.features is None:
            raise RuntimeError(
                "The isophotes have not been loaded. Call load() first."
            )
        self.validate_source()
        resolved = self.observer if observer is None else observer
        if not native_icrs and (resolved is None or not hasattr(resolved, "altaz_frame")):
            raise ValueError("An observer with an altaz_frame is required.")

        native_rings = []
        ids = []
        level_values = []
        compounds = []
        ring_indices = []
        holes = []
        projection_cap_topology_inversions = []
        interior_left = []
        interior_areas = []
        source_values = []

        selected_levels = (
            self.levels
            if levels is None
            else self._validate_levels(levels)
        )
        for level in self.available_levels:
            if level not in selected_levels:
                continue
            for polygon_index, polygon in enumerate(self.features[level]):
                compound = f"{level}:{polygon_index}"
                for ring_index, ring in enumerate(polygon):
                    coordinates = np.asarray(ring, dtype=float)
                    if coordinates.ndim != 2 or coordinates.shape[1] < 2:
                        raise ValueError(
                            f"{compound} ring {ring_index} is invalid."
                        )
                    if len(coordinates) > 1 and np.allclose(
                        coordinates[0, :2],
                        coordinates[-1, :2],
                    ):
                        coordinates = coordinates[:-1]
                    if len(coordinates) < 3:
                        raise ValueError(
                            f"{compound} ring {ring_index} is too short."
                        )
                    native_rings.append(coordinates[:, :2])
                    ring_id = f"{compound}:{ring_index}"
                    ids.append(ring_id)
                    level_values.append(level)
                    compounds.append(compound)
                    ring_indices.append(ring_index)
                    holes.append(ring_index > 0)
                    unwrapped_longitude = np.degrees(
                        np.unwrap(
                            np.radians(coordinates[:, 0]),
                            discont=np.pi,
                        )
                    )
                    projection_cap_topology_inversions.append(
                        abs(int(np.round(
                            (
                                unwrapped_longitude[-1]
                                - unwrapped_longitude[0]
                            )
                            / 360.0
                        )))
                        >= 1
                    )
                    left, area = _native_ring_interior(
                        coordinates[:, :2],
                        projection_cap_topology_inversions[-1],
                    )
                    # The equatorial and north/east/zenith horizontal
                    # coordinate triples have opposite handedness.
                    interior_left.append(left if native_icrs else not left)
                    interior_areas.append(area)
                    source_values.append(self.sources[level])

        if native_icrs:
            longitude = tuple(ring[:, 0].copy() for ring in native_rings)
            latitude = tuple(ring[:, 1].copy() for ring in native_rings)
        else:
            longitude, latitude = observed_polygon_arrays(
                self._observed_polygon_cache, resolved,
                source_key=(self.layer_name, self.source, self._source_revision,
                            self.catalogue_metadata.fingerprint, selected_levels),
                build=lambda: self._transform_rings(native_rings, resolved),
            )
        positions = list(range(len(level_values)))

        return SphericalPolygons(
            lon_deg=tuple(longitude[index] for index in positions),
            lat_deg=tuple(latitude[index] for index in positions),
            coordinate_spec=icrs_catalogue_spec(self.catalogue_metadata.provider, epoch=None)
            if native_icrs else observer_altaz_spec(
                resolved,
                position_status=PositionStatus.APPARENT,
                provider=f"astropy {self.catalogue_metadata.provider}"
            ),
            ids=[ids[index] for index in positions],
            metadata={
                "source": np.asarray(source_values, dtype=object)[positions],
                "source_metadata": self.catalogue_metadata.record_json,
                "coordinate_system": "icrs" if native_icrs else "altaz",
                "level": np.asarray(level_values, dtype=object)[positions],
                "compound_id": np.asarray(compounds, dtype=object)[positions],
                "ring_index": np.asarray(ring_indices, dtype=int)[positions],
                "is_hole": np.asarray(holes, dtype=bool)[positions],
                "spherical_interior_left": np.asarray(
                    interior_left, dtype=bool
                )[positions],
                "spherical_interior_area_sr": np.asarray(
                    interior_areas, dtype=float
                )[positions],
                "projection_cap_topology_inversion": np.asarray(
                    projection_cap_topology_inversions,
                    dtype=bool,
                )[positions],
                "semantic_entity_keys": np.asarray(
                    [f"isophote_{level}" for level in level_values],
                    dtype=object,
                )[positions],
                "semantic_entity_display_names": np.asarray(
                    [f"Isophote {str(level).upper()}" for level in level_values],
                    dtype=object,
                )[positions],
            },
        )

    def _transform_rings(self, rings, observer):
        if not rings:
            return (), ()
        return icrs_curve_arrays_to_altaz(
            tuple(np.asarray(ring[:, 0], dtype=float) for ring in rings),
            tuple(np.asarray(ring[:, 1], dtype=float) for ring in rings),
            observer,
            provider=self.catalogue_metadata.provider,
        )


def _native_ring_interior(coordinates, pole_winding):
    """Preserve the legacy source adapter seam for the shared ring math."""
    return ring_interior(coordinates, pole_winding)
