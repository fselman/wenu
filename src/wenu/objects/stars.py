"""Stellar catalogue layer producing spherical point geometry."""

from __future__ import annotations

from importlib.resources import as_file
from io import BytesIO

import numpy as np
from skyfield.api import Star
from skyfield.data import hipparcos

from wenu.objects.astronomical_object import AstronomicalObject
from wenu.resources import catalog_path
from wenu.geometry.spherical import SphericalPoints
from wenu.sky.observed_cache import observer_geometry_key


_HIPPARCOS_SEMANTIC_DEFAULTS = {
    "variability_type": "",
    "variability_annex": "",
    "light_curve_annex": "",
    "is_variable": False,
    "ccdm_id": "",
    "ccdm_entry_count": 0,
    "component_count": 0,
    "multiple_annex": "",
    "component_position_angle_deg": np.nan,
    "component_separation_arcsec": np.nan,
    "component_magnitude_difference": np.nan,
    "is_multiple": False,
}


def _integer(text, default=0):
    text = text.strip()
    return default if not text else int(text)


def _floating(text):
    text = text.strip()
    return np.nan if not text else float(text)


def _hipparcos_semantics(payload):
    """Return H52--H67 classifications keyed by HIP identifier.

    Byte positions follow ESA (1997), Hipparcos Catalogue I/239.  Python
    slices are zero-based and therefore one less than the published byte
    numbers.
    """
    semantics = {}
    for raw_line in payload.splitlines():
        line = raw_line.decode("ascii") if isinstance(raw_line, bytes) else raw_line
        if len(line) < 14:
            continue
        hip_text = line[8:14].strip()
        if not hip_text.isdigit():
            continue
        line = line.ljust(383)
        variability_type = line[321:322].strip()
        ccdm_id = line[327:337].strip()
        component_count = _integer(line[343:345])
        multiple_annex = line[346:347].strip()
        semantics[int(hip_text)] = {
            "variability_type": variability_type,
            "variability_annex": line[323:324].strip(),
            "light_curve_annex": line[325:326].strip(),
            # C means constant; R only records a revised V-I colour.
            "is_variable": variability_type in {"D", "M", "P", "U"},
            "ccdm_id": ccdm_id,
            "ccdm_entry_count": _integer(line[340:342]),
            "component_count": component_count,
            "multiple_annex": multiple_annex,
            "component_position_angle_deg": _floating(line[355:358]),
            "component_separation_arcsec": _floating(line[359:366]),
            "component_magnitude_difference": _floating(line[373:378]),
            "is_multiple": bool(
                ccdm_id or component_count > 1 or multiple_annex
            ),
        }
    return semantics


def _attach_hipparcos_semantics(source, semantics):
    """Attach classification columns without changing Skyfield row order."""
    for name, default in _HIPPARCOS_SEMANTIC_DEFAULTS.items():
        source[name] = [
            semantics.get(int(hip_id), {}).get(name, default)
            for hip_id in source.index
        ]
    return source


class Stars(AstronomicalObject):
    """A magnitude-limited stellar catalogue."""

    layer_name = "stars"

    def __init__(
        self,
        observer,
        catalog="hipparcos",
        magnitude_limit=5.5,
    ):
        self.observer = observer
        self.catalog_name = catalog
        self.magnitude_limit = magnitude_limit
        # Identifiers retained in addition to the magnitude cut.
        self.include_ids = frozenset()

        # Constellation vertices in the active sky line system.  Membership
        # is metadata; inclusion remains an explicit detail-policy choice.
        self.constellation_vertex_ids = frozenset()
        self.include_constellation_vertices = False

        # Stable magnitude-limited catalogue.
        self.catalog = None

        # Current observer/altitude selection.
        self.hip_df = None

        # Skyfield representation of the stable catalogue.
        self.skyfield_stars = None
        self._source_revision = 0
        self._observed_altaz_cache = {}

    def load(
        self,
        *,
        catalog=None,
        filename=None,
    ):
        """Load a stellar catalogue and apply the magnitude limit."""
        if catalog is not None:
            self.catalog_name = catalog

        if filename is not None:
            with open(filename, "rb") as file:
                payload = file.read()
        else:
            resource = catalog_path(self.catalog_name)

            with as_file(resource) as path:
                with open(path, "rb") as file:
                    payload = file.read()

        source = hipparcos.load_dataframe(BytesIO(payload))
        source = _attach_hipparcos_semantics(
            source,
            _hipparcos_semantics(payload),
        )
        source["is_constellation_vertex"] = source.index.isin(
            getattr(self, "constellation_vertex_ids", frozenset())
        )

        self.source_catalog = source.copy()
        magnitude_mask = (
            source["magnitude"] <= self.magnitude_limit
        )
        identifier_mask = source.index.isin(self.include_ids)
        vertex_mask = (
            source["is_constellation_vertex"]
            if self.include_constellation_vertices
            else np.zeros(len(source), dtype=bool)
        )
        self.catalog = source[
            magnitude_mask | identifier_mask | vertex_mask
        ].copy()
        self.hip_df = self.catalog.copy()

        self.skyfield_stars = Star(
            ra_hours=self.catalog["ra_hours"].to_numpy(),
            dec_degrees=self.catalog["dec_degrees"].to_numpy(),
        )
        self._source_revision += 1
        self._observed_altaz_cache.clear()

        return self.catalog

    def set_constellation_vertices(self, identifiers, *, reload=True):
        """Store vertices for the active constellation-line configuration."""
        identifiers = frozenset(int(value) for value in identifiers)
        changed = identifiers != getattr(
            self,
            "constellation_vertex_ids",
            frozenset(),
        )
        self.constellation_vertex_ids = identifiers
        if changed and reload:
            self.load()
        return changed

    def configure_selection(
        self,
        *,
        include_ids=(),
        include_constellation_vertices=None,
        reload=True,
    ):
        """Configure additions to the magnitude-limited stellar selection."""
        identifiers = frozenset(int(value) for value in include_ids)
        current_include_vertices = getattr(
            self,
            "include_constellation_vertices",
            False,
        )
        include_vertices = (
            current_include_vertices
            if include_constellation_vertices is None
            else bool(include_constellation_vertices)
        )
        changed = (
            identifiers != self.include_ids
            or include_vertices != current_include_vertices
        )
        self.include_ids = identifiers
        self.include_constellation_vertices = include_vertices
        if changed and reload:
            self.load()
        return changed

    def compute_altaz(
        self,
        alt_min=-10.0,
        *,
        observer=None,
    ):
        """Return apparent Alt/Az and select stars above ``alt_min``."""
        if self.catalog is None or self.skyfield_stars is None:
            raise RuntimeError(
                "Hipparcos has not been loaded. Call stars.load() first."
            )

        resolved_observer = self.observer if observer is None else observer

        if resolved_observer is None:
            raise ValueError(
                "An observer is required to compute stellar coordinates."
            )

        apparent = (
            resolved_observer.skyfield
            .at(resolved_observer.t)
            .observe(self.skyfield_stars)
            .apparent(deflectors=[])
        )

        alt, az, _ = apparent.altaz()
        alt_all = np.asarray(alt.degrees)
        az_all = np.asarray(az.degrees)
        mask = alt_all > alt_min

        # Always filter the stable catalogue, never the previous selection.
        self.hip_df = self.catalog.iloc[
            np.flatnonzero(mask)
        ].copy()

        return alt_all[mask], az_all[mask]

    def spherical_geometry(
        self,
        observer,
        *,
        alt_min=-10.0,
        magnitude_limit=None,
        include_ids=None,
        include_constellation_vertices=None,
    ) -> SphericalPoints:
        """Return observer-dependent stellar positions as spherical points."""
        if getattr(self, "source_catalog", None) is None:
            if any(
                value is not None
                for value in (
                    magnitude_limit,
                    include_ids,
                    include_constellation_vertices,
                )
            ):
                raise RuntimeError(
                    "Render-local stellar selection requires a loaded "
                    "source catalogue."
                )
            alt_deg, az_deg = self.compute_altaz(
                alt_min=alt_min,
                observer=observer,
            )
            selected = self.hip_df
        else:
            catalog = self._render_catalog(
                magnitude_limit=magnitude_limit,
                include_ids=include_ids,
                include_constellation_vertices=(
                    include_constellation_vertices
                ),
            )
            selected, alt_deg, az_deg = self._catalog_altaz(
                catalog,
                observer,
                alt_min,
            )

        magnitudes = selected["magnitude"].to_numpy(copy=True)
        hip_ids = selected.index.to_numpy(copy=True)

        vertex_membership = selected.get(
            "is_constellation_vertex"
        )
        if vertex_membership is None:
            vertex_membership = np.zeros(len(self.hip_df), dtype=bool)
        else:
            vertex_membership = vertex_membership.to_numpy(
                dtype=bool,
                copy=True,
            )
        metadata = {
            "catalog": self.catalog_name,
            "magnitude": magnitudes,
            "is_constellation_vertex": vertex_membership,
        }
        for name, default in _HIPPARCOS_SEMANTIC_DEFAULTS.items():
            if name in selected.columns:
                values = selected[name].to_numpy(copy=True)
            else:
                values = np.asarray(
                    [default] * len(selected)
                )
            metadata[name] = values

        # Preserve colour information when supplied by a catalogue. The
        # bundled Hipparcos table does not currently provide such a column.
        if "color" in selected.columns:
            metadata["color"] = selected[
                "color"
            ].to_numpy(copy=True)

        return SphericalPoints(
            lon_deg=az_deg,
            lat_deg=alt_deg,
            ids=hip_ids,
            metadata=metadata,
        )

    def _render_catalog(
        self,
        *,
        magnitude_limit=None,
        include_ids=None,
        include_constellation_vertices=None,
    ):
        """Return one render's stellar selection without changing the layer."""
        if getattr(self, "source_catalog", None) is None:
            raise RuntimeError(
                "Hipparcos has not been loaded. Call stars.load() first."
            )
        if (
            magnitude_limit is None
            and include_ids is None
            and include_constellation_vertices is None
        ):
            return self.catalog
        limit = (
            self.magnitude_limit
            if magnitude_limit is None
            else float(magnitude_limit)
        )
        identifiers = (
            self.include_ids
            if include_ids is None
            else frozenset(int(value) for value in include_ids)
        )
        include_vertices = (
            self.include_constellation_vertices
            if include_constellation_vertices is None
            else bool(include_constellation_vertices)
        )
        source = self.source_catalog
        keep = source["magnitude"] <= limit
        keep |= source.index.isin(identifiers)
        if include_vertices:
            keep |= source["is_constellation_vertex"]
        return source[keep].copy()

    def _catalog_altaz(self, catalog, observer, alt_min):
        """Transform a render-local catalogue without updating cached state."""
        resolved_observer = self.observer if observer is None else observer
        if resolved_observer is None:
            raise ValueError(
                "An observer is required to compute stellar coordinates."
            )
        source, source_altitude, source_azimuth = (
            self.observed_altaz(resolved_observer)
        )
        positions = source.index.get_indexer(catalog.index)
        if np.any(positions < 0):
            raise RuntimeError(
                "The render-local stellar selection is not contained in "
                "the loaded source catalogue."
            )
        altitude = source_altitude[positions]
        azimuth = source_azimuth[positions]
        keep = altitude > float(alt_min)
        return (
            catalog.iloc[np.flatnonzero(keep)].copy(),
            altitude[keep],
            azimuth[keep],
        )

    def observed_altaz(self, observer=None):
        """Return cached maximal-catalogue Alt/Az for one observer instant."""
        resolved = self.observer if observer is None else observer
        if resolved is None:
            raise ValueError(
                "An observer is required to compute stellar coordinates."
            )
        source = getattr(self, "source_catalog", None)
        if source is None:
            source = self.catalog
        if source is None:
            raise RuntimeError(
                "Hipparcos has not been loaded. Call stars.load() first."
            )
        key = (
            observer_geometry_key(resolved),
            self.catalog_name,
            self._source_revision,
        )
        cached = self._observed_altaz_cache.get(key)
        if cached is None:
            if source is self.catalog and self.skyfield_stars is not None:
                stars = self.skyfield_stars
            else:
                stars = Star(
                    ra_hours=source["ra_hours"].to_numpy(),
                    dec_degrees=source["dec_degrees"].to_numpy(),
                )
            apparent = (
                resolved.skyfield
                .at(resolved.t)
                .observe(stars)
                .apparent(deflectors=[])
            )
            altitude, azimuth, _ = apparent.altaz()
            altitude = np.asarray(altitude.degrees, dtype=float)
            azimuth = np.asarray(azimuth.degrees, dtype=float)
            altitude.setflags(write=False)
            azimuth.setflags(write=False)
            cached = (altitude, azimuth)
            self._observed_altaz_cache[key] = cached
        return source, cached[0], cached[1]

    @property
    def hip_index(self):
        """Map HIP identifier to row position in the active selection."""
        if self.hip_df is None:
            return {}

        return {
            int(hip_id): index
            for index, hip_id in enumerate(self.hip_df.index)
        }
