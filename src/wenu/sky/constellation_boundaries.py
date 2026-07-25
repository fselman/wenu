"""Official IAU constellation boundaries as spherical domain geometry."""

from __future__ import annotations

from collections import OrderedDict
from importlib.resources import as_file
from pathlib import Path

import astropy.units as u
import numpy as np
from astropy.coordinates import AltAz, EarthLocation, FK4, SkyCoord
from astropy.time import Time

from wenu.objects.astronomical_object import AstronomicalObject
from wenu.resources import boundary_path
from wenu.spherical import SphericalPolygons


class ConstellationBoundaries(AstronomicalObject):
    """IAU boundaries whose authoritative geometry is FK4/B1875."""

    layer_name = "constellation_boundaries"

    def __init__(
        self,
        observer,
        boundaries="iau",
        filename=None,
        constellations=None,
        *,
        sampling_step_deg=0.5,
    ):
        self.observer = observer
        self.boundaries_name = boundaries
        self.filename = None if filename is None else Path(filename)
        self.constellations = self._expand_constellation_names(
            constellations
        )
        self.sampling_step_deg = float(sampling_step_deg)

        if self.sampling_step_deg <= 0.0:
            raise ValueError("sampling_step_deg must be positive.")

        # Native, authoritative B1875 vertices and their sampled realization.
        self.vertices = OrderedDict()
        self.sampled_vertices = OrderedDict()
        self.load()

    @staticmethod
    def _expand_constellation_names(constellations):
        if constellations is None:
            return None

        normalized = set()
        for abbreviation in constellations:
            key = abbreviation.strip().upper()
            if key == "SER":
                normalized.update({"SER1", "SER2"})
            elif key == "SERCAP":
                normalized.add("SER1")
            elif key == "SERCAU":
                normalized.add("SER2")
            else:
                normalized.add(key)
        return normalized

    def load(self):
        """Load ordered native FK4/B1875 boundary vertices."""
        if self.filename is not None:
            if not self.filename.exists():
                raise FileNotFoundError(
                    "Constellation boundary file not found: "
                    f"{self.filename}"
                )
            return self._load_file(self.filename)

        resource = boundary_path(self.boundaries_name)
        with as_file(resource) as path:
            return self._load_file(path)

    def _load_file(self, path):
        path = Path(path)
        blocks = OrderedDict()
        previous_abbreviation = None
        completed_abbreviations = set()

        with path.open("r", encoding="utf-8") as file:
            for line_number, raw_line in enumerate(file, start=1):
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue

                fields = line.split()
                if len(fields) != 4:
                    raise ValueError(
                        f"Expected four fields at {path}:{line_number}, "
                        f"found {len(fields)}:\n{raw_line.rstrip()}"
                    )

                ra_text, dec_text, abbreviation, boundary_type = fields
                abbreviation = abbreviation.upper()

                try:
                    ra_hours = float(ra_text)
                    dec_degrees = float(dec_text)
                except ValueError as error:
                    raise ValueError(
                        f"Invalid boundary coordinate at "
                        f"{path}:{line_number}:\n{raw_line.rstrip()}"
                    ) from error

                if boundary_type != "O":
                    raise ValueError(
                        f"Unsupported boundary type {boundary_type!r} at "
                        f"{path}:{line_number}."
                    )

                if abbreviation != previous_abbreviation:
                    if abbreviation in completed_abbreviations:
                        raise ValueError(
                            f"Boundary identifier {abbreviation!r} occurs "
                            "in more than one non-contiguous block."
                        )
                    if previous_abbreviation is not None:
                        completed_abbreviations.add(previous_abbreviation)
                    previous_abbreviation = abbreviation

                if (
                    self.constellations is not None
                    and abbreviation not in self.constellations
                ):
                    continue

                blocks.setdefault(abbreviation, []).append(
                    (ra_hours, dec_degrees)
                )

        self.vertices = OrderedDict(
            (
                abbreviation,
                np.asarray(points, dtype=float),
            )
            for abbreviation, points in blocks.items()
        )
        self.sampled_vertices.clear()

        if not self.vertices and self.constellations is None:
            raise ValueError(
                f"No constellation boundaries were loaded from {path}."
            )

        return self.vertices

    def sample(self):
        """Sample official segments in native B1875 before transformation."""
        self.sampled_vertices = OrderedDict(
            (
                abbreviation,
                self._sample_closed_polygon(
                    self._rendering_vertices(vertices)
                ),
            )
            for abbreviation, vertices in self.vertices.items()
        )
        return self.sampled_vertices

    @staticmethod
    def _rendering_vertices(vertices):
        """Remove pole-only closure vertices from a rendering contour.

        At either celestial pole every right ascension denotes the same
        physical point. Pole vertices used to close a tabular RA/Dec polygon
        are therefore not celestial boundary edges and must not be rendered.
        The authoritative vertices retained for membership tests are not
        changed.
        """
        vertices = np.asarray(vertices, dtype=float)
        nonpolar = ~np.isclose(
            np.abs(vertices[:, 1]),
            90.0,
            atol=1.0e-8,
        )

        if np.count_nonzero(nonpolar) >= 3:
            return vertices[nonpolar]

        return vertices

    def _sample_closed_polygon(self, vertices):
        vertices = np.asarray(vertices, dtype=float)
        if vertices.ndim != 2 or vertices.shape[1] != 2:
            raise ValueError(
                "Boundary vertices must have shape (N, 2)."
            )
        if len(vertices) < 3:
            raise ValueError(
                "A boundary polygon requires at least three vertices."
            )

        parts = []
        for index in range(len(vertices)):
            segment = self._sample_segment(
                vertices[index],
                vertices[(index + 1) % len(vertices)],
            )
            if index > 0:
                segment = segment[1:]
            parts.append(segment)
        return np.vstack(parts)

    def _sample_segment(self, start, end):
        ra_start_hours, dec_start_deg = map(float, start)
        ra_end_hours, dec_end_deg = map(float, end)
        ra_difference_hours = (
            (ra_end_hours - ra_start_hours + 12.0)
            % 24.0
        ) - 12.0
        same_ra = np.isclose(
            ra_difference_hours,
            0.0,
            atol=1e-5,
        )
        same_dec = np.isclose(
            dec_start_deg, dec_end_deg, atol=1e-5
        )

        if same_ra and same_dec:
            return np.asarray(
                [[ra_start_hours, dec_start_deg]],
                dtype=float,
            )

        if same_ra:
            length_deg = abs(dec_end_deg - dec_start_deg)
            intervals = max(
                1,
                int(np.ceil(length_deg / self.sampling_step_deg)),
            )
            dec = np.linspace(
                dec_start_deg,
                dec_end_deg,
                intervals + 1,
            )
            ra = np.full_like(dec, ra_start_hours)
        elif same_dec:
            ra_end_unwrapped = self._unwrap_ra_endpoint(
                ra_start_hours,
                ra_end_hours,
            )
            ra_length_deg = (
                abs(ra_end_unwrapped - ra_start_hours) * 15.0
            )
            length_deg = ra_length_deg * abs(
                np.cos(np.deg2rad(dec_start_deg))
            )
            intervals = max(
                1,
                int(np.ceil(length_deg / self.sampling_step_deg)),
            )
            ra = np.linspace(
                ra_start_hours,
                ra_end_unwrapped,
                intervals + 1,
            ) % 24.0
            dec = np.full_like(ra, dec_start_deg)
        else:
            raise ValueError(
                "A bound_18.dat edge is neither constant RA nor "
                f"constant declination: start={start}, end={end}"
            )

        return np.column_stack((ra, dec))

    @staticmethod
    def _unwrap_ra_endpoint(ra_start_hours, ra_end_hours):
        difference = ra_end_hours - ra_start_hours
        if difference > 12.0:
            return ra_end_hours - 24.0
        if difference < -12.0:
            return ra_end_hours + 24.0
        return ra_end_hours

    def spherical_geometry(self, observer) -> SphericalPolygons:
        """Transform sampled native B1875 polygons to observer Alt/Az."""
        resolved_observer = self.observer if observer is None else observer
        self._validate_observer(resolved_observer)

        if not self.sampled_vertices:
            self.sample()

        b1875 = FK4(equinox=Time("B1875.0"))
        location = EarthLocation.from_geodetic(
            lon=resolved_observer.lon_deg * u.deg,
            lat=resolved_observer.lat_deg * u.deg,
            height=resolved_observer.elevation_m * u.m,
        )
        altaz_frame = AltAz(
            obstime=resolved_observer.t_astropy,
            location=location,
        )

        identifiers = list(self.sampled_vertices)
        lon_deg = []
        lat_deg = []

        for vertices in self.sampled_vertices.values():
            native = SkyCoord(
                ra=vertices[:, 0] * u.hourangle,
                dec=vertices[:, 1] * u.deg,
                frame=b1875,
            )
            horizontal = native.transform_to(altaz_frame)
            lon_deg.append(horizontal.az.to_value(u.deg))
            lat_deg.append(horizontal.alt.to_value(u.deg))

        return SphericalPolygons(
            lon_deg=tuple(lon_deg),
            lat_deg=tuple(lat_deg),
            ids=identifiers,
            names=identifiers,
            metadata={
                "boundaries": self.boundaries_name,
                "source_frame": "fk4",
                "source_equinox": "B1875.0",
                "coordinate_system": "altaz",
            },
        )

    def region_of(
        self,
        ra_deg,
        dec_deg,
        *,
        candidates=None,
    ):
        """Return the native B1875 boundary containing an ICRS point."""
        if not np.all(np.isfinite([ra_deg, dec_deg])):
            return None

        coordinate = SkyCoord(
            ra=float(ra_deg) * u.deg,
            dec=float(dec_deg) * u.deg,
            frame="icrs",
        )
        b1875 = coordinate.transform_to(
            FK4(equinox=Time("B1875.0"))
        )
        ra_hours = float(
            b1875.ra.to_value(u.hourangle) % 24.0
        )
        dec_degrees = float(b1875.dec.to_value(u.deg))

        identifiers = (
            self.vertices.keys()
            if candidates is None
            else (item.upper() for item in candidates)
        )
        for abbreviation in identifiers:
            vertices = self.vertices.get(abbreviation)
            if vertices is None or len(vertices) < 3:
                continue
            if self._contains_b1875_point(
                vertices,
                ra_hours,
                dec_degrees,
            ):
                return abbreviation
        return None

    @classmethod
    def _contains_b1875_point(
        cls,
        vertices,
        ra_hours,
        dec_degrees,
    ):
        """Renderer-independent containment across the 0h/24h seam."""
        vertices = np.asarray(vertices, dtype=float)
        native_ra = vertices[:, 0]
        x = np.empty_like(native_ra)
        x[0] = native_ra[0]

        # Follow each official boundary edge through its shortest RA
        # displacement. This unwraps the polygon independently of the
        # query point and therefore preserves which side of the 0h seam
        # is its interior.
        for index in range(1, len(native_ra)):
            delta = (
                (native_ra[index] - native_ra[index - 1] + 12.0)
                % 24.0
            ) - 12.0
            x[index] = x[index - 1] + delta

        polygon_center = float(np.mean(x))
        point_x = float(ra_hours)
        point_x += 24.0 * round(
            (polygon_center - point_x) / 24.0
        )
        y = vertices[:, 1]
        point_y = float(dec_degrees)
        inside = False

        for index in range(len(vertices)):
            next_index = (index + 1) % len(vertices)
            x1, y1 = x[index], y[index]
            x2, y2 = x[next_index], y[next_index]

            if cls._point_on_segment(
                point_x, point_y, x1, y1, x2, y2
            ):
                return True

            if (y1 > point_y) != (y2 > point_y):
                crossing_x = (
                    x1
                    + (point_y - y1)
                    * (x2 - x1)
                    / (y2 - y1)
                )
                if crossing_x > point_x:
                    inside = not inside

        return inside

    @staticmethod
    def _point_on_segment(px, py, x1, y1, x2, y2):
        tolerance = 1.0e-10
        cross = (px - x1) * (y2 - y1) - (
            py - y1
        ) * (x2 - x1)
        if abs(cross) > tolerance:
            return False
        return (
            min(x1, x2) - tolerance
            <= px
            <= max(x1, x2) + tolerance
            and min(y1, y2) - tolerance
            <= py
            <= max(y1, y2) + tolerance
        )

    @staticmethod
    def _validate_observer(observer):
        if observer is None:
            raise RuntimeError(
                "ConstellationBoundaries has no Observer."
            )
        missing = [
            name
            for name in (
                "t_astropy",
                "lat_deg",
                "lon_deg",
                "elevation_m",
            )
            if getattr(observer, name, None) is None
        ]
        if missing:
            raise RuntimeError(
                "Observer is missing required attributes: "
                + ", ".join(missing)
            )
