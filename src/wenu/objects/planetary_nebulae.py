"""Planetary-nebula catalogue represented by fixed chart symbols."""

from __future__ import annotations

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord

from wenu.geometry.spherical import SphericalPoints
from wenu.objects.nonstellar import NonStellar


class PlanetaryNebulae(NonStellar):
    """True and probable planetary nebulae from the packaged catalogue.

    Planetary nebulae are cartographic point symbols, not sampled angular
    outlines. Catalogue diameters and fluxes are retained as metadata.
    """

    layer_name = "planetary_nebulae"

    _ALIASES = {
        **NonStellar._ALIASES,
        "identifier": (
            "identifier",
            "name",
            "object",
            "designation",
            "pk_name",
        ),
    }

    def __init__(
        self,
        observer,
        *,
        selected=None,
        samples=None,
    ):
        super().__init__(
            observer,
            catalog="planetary_nebulae",
            magnitude_limit=None,
            samples=12,
        )
        self.selected = (
            None if selected is None else tuple(selected)
        )
        # Accepted during the curve-to-symbol migration. A fixed marker
        # requires no angular sampling.
        self.requested_samples = samples

    def _normalize(self, source):
        """Preserve planetary-nebula-specific catalogue metadata."""
        normalized = super()._normalize(source)
        names = {name.casefold(): name for name in source.colnames}
        for name in (
            "pk_name",
            "alternate_names",
            "log_hbeta_flux",
            "position_quality",
            "optical_diameter_limit",
            "optical_diameter_uncertain",
        ):
            actual = names.get(name.casefold())
            if actual is not None:
                normalized[name] = source[actual]
        return normalized

    def spherical_geometry(
        self,
        observer,
        *,
        selected=None,
        minimum_size_arcmin=None,
    ) -> SphericalPoints:
        """Return vectorized Alt/Az centers for fixed renderer symbols."""
        if self.catalog is None:
            raise RuntimeError(
                "The catalogue has not been loaded. "
                "Call planetary_nebulae.load() first."
            )
        resolved = self.observer if observer is None else observer
        if resolved is None or not hasattr(resolved, "altaz_frame"):
            raise ValueError(
                "An observer with an altaz_frame is required."
            )

        selection = self.selected if selected is None else selected
        if selection is None:
            table = self.catalog
        else:
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
                    catalogue_ids
                    == str(requested).strip().casefold()
                )
                if matches.size:
                    indices.append(int(matches[0]))
            table = self.catalog[np.asarray(indices, dtype=int)]
        if minimum_size_arcmin is not None:
            minimum = float(minimum_size_arcmin)
            if not np.isfinite(minimum) or minimum < 0.0:
                raise ValueError(
                    "minimum_size_arcmin must be finite and "
                    "non-negative."
                )
            major = np.asarray(table["major_axis_arcmin"], dtype=float)
            minor = np.asarray(table["minor_axis_arcmin"], dtype=float)
            sizes = np.fmax(major, minor)
            table = table[np.isfinite(sizes) & (sizes >= minimum)]
        identifiers = np.asarray(
            table["identifier"],
            dtype=object,
        )
        if len(table) == 0:
            return SphericalPoints(
                lon_deg=np.asarray([], dtype=float),
                lat_deg=np.asarray([], dtype=float),
                ids=identifiers,
                labels=identifiers,
                names=identifiers,
                metadata=self._point_metadata(table),
            )

        centers = SkyCoord(
            ra=np.asarray(table["ra_deg"], dtype=float) * u.deg,
            dec=np.asarray(table["dec_deg"], dtype=float) * u.deg,
            frame="icrs",
        )
        horizontal = centers.transform_to(resolved.altaz_frame)
        return SphericalPoints(
            lon_deg=horizontal.az.to_value(u.deg),
            lat_deg=horizontal.alt.to_value(u.deg),
            ids=identifiers,
            labels=identifiers,
            names=identifiers,
            metadata=self._point_metadata(table),
        )

    def _point_metadata(self, table):
        metadata = self._geometry_metadata(table)
        metadata.update(
            {
                "geometry_kind": "cartographic_symbol",
                "symbol": "planetary_nebula",
            }
        )
        for name in (
            "common_name",
            "pk_name",
            "alternate_names",
            "log_hbeta_flux",
            "position_quality",
        ):
            if name in table.colnames:
                metadata[name] = np.asarray(
                    table[name],
                    dtype=object,
                )
        return metadata
