# src/wenu/sky/constellation_boundaries.py

from collections import OrderedDict
from importlib.resources import as_file
from pathlib import Path

import numpy as np

import astropy.units as u
from astropy.coordinates import AltAz, FK4, SkyCoord, EarthLocation
from astropy.time import Time
from matplotlib.path import Path as MatplotlibPath

from wenu.projected import ProjectedCurve
from wenu.renderers import render_curve
from wenu.resources import boundary_path


class ConstellationBoundaries:
    """
    Official IAU constellation boundaries defined in FK4/B1875.

    The expected input is the Davenhall ``bound_18.dat`` file. Each
    non-empty line has four fields:

        RA_hours  Dec_degrees  constellation_code  boundary_type

    The vertices for each constellation occur contiguously and are
    ordered around its boundary. The first vertex is not repeated at
    the end, so each polygon is closed internally by this class.

    Long B1875 meridian and parallel segments are sampled before
    transformation. This preserves the official boundary geometry
    when the coordinates are precessed and projected.

    Parameters
    ----------
    filename : str or pathlib.Path
        Path to ``bound_18.dat``.

    observer : wenu.observer.Observer
        Observer providing ``t_astropy`` and location attributes.

    constellations : iterable of str, optional
        Boundary identifiers to load. These are normally three-letter
        IAU abbreviations. Serpens is represented by ``SER1`` and
        ``SER2`` in this catalogue.

    sampling_step_deg : float, optional
        Maximum angular sampling interval, in degrees, along each
        B1875 boundary segment.

    color : matplotlib color, optional
        Boundary line color.

    linewidth : float, optional
        Boundary line width.

    alpha : float, optional
        Boundary transparency.

    zorder : float, optional
        Matplotlib drawing order.

    horizon_altitude : float, optional
        Minimum visible altitude in degrees.
    """

    def __init__(
        self,
        observer,
        boundaries="iau",
        filename=None,
        constellations=None,
        *,
        sampling_step_deg=0.5,
        color="white",
        linewidth=0.3,
        alpha=0.4,
        zorder=1,
        horizon_altitude=0.0,
    ):
        self.observer = observer
        self.boundaries_name = boundaries

        self.filename = (
            None
            if filename is None
            else Path(filename)
        )

        self.constellations = self._expand_constellation_names(
            constellations
        )

        self.sampling_step_deg = float(sampling_step_deg)

        if self.sampling_step_deg <= 0.0:
            raise ValueError(
                "sampling_step_deg must be positive."
            )

        self.color = color
        self.linewidth = linewidth
        self.alpha = alpha
        self.zorder = zorder
        self.horizon_altitude = float(horizon_altitude)

        self.vertices = OrderedDict()
        self.sampled_vertices = OrderedDict()
        self.altaz = OrderedDict()
        self.projected = OrderedDict()
        self.artists = []

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

    # ============================================================
    # Loading
    # ============================================================

    def load(self):
        """
        Load the ordered B1875 boundary vertices.

        If ``filename`` was supplied explicitly, that file is used.
        Otherwise the packaged boundary resource selected by
        ``boundaries_name`` is used.

        Returns
        -------
        collections.OrderedDict
            Mapping from boundary identifier to an ``(N, 2)`` array
            containing RA in hours and declination in degrees.
        """

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
        """
        Parse one Davenhall-style constellation-boundary file.
        """

        path = Path(path)

        blocks = OrderedDict()

        previous_abbreviation = None
        completed_abbreviations = set()

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            for line_number, raw_line in enumerate(
                file,
                start=1,
            ):
                line = raw_line.strip()

                if not line or line.startswith("#"):
                    continue

                fields = line.split()

                if len(fields) != 4:
                    raise ValueError(
                        "Expected four fields at "
                        f"{path}:{line_number}, "
                        f"found {len(fields)}:\n"
                        f"{raw_line.rstrip()}"
                    )

                ra_text, dec_text, abbreviation, boundary_type = fields
                abbreviation = abbreviation.upper()

                try:
                    ra_hours = float(ra_text)
                    dec_degrees = float(dec_text)

                except ValueError as error:
                    raise ValueError(
                        "Invalid boundary coordinate at "
                        f"{path}:{line_number}:\n"
                        f"{raw_line.rstrip()}"
                    ) from error

                if boundary_type != "O":
                    raise ValueError(
                        "Unsupported boundary type "
                        f"{boundary_type!r} at "
                        f"{path}:{line_number}."
                    )

                if abbreviation != previous_abbreviation:
                    if abbreviation in completed_abbreviations:
                        raise ValueError(
                            "Boundary identifier "
                            f"{abbreviation!r} occurs in more than "
                            "one non-contiguous block."
                        )

                    if previous_abbreviation is not None:
                        completed_abbreviations.add(
                            previous_abbreviation
                        )

                    previous_abbreviation = abbreviation

                if (
                    self.constellations is not None
                    and abbreviation not in self.constellations
                ):
                    continue

                blocks.setdefault(
                    abbreviation,
                    [],
                ).append(
                    (
                        ra_hours,
                        dec_degrees,
                    )
                )

        self.vertices = OrderedDict(
            (
                abbreviation,
                np.asarray(points, dtype=float),
            )
            for abbreviation, points in blocks.items()
        )

        if not self.vertices:
            if self.constellations is not None:
                self.sampled_vertices.clear()
                self.altaz.clear()
                self.projected.clear()
                return self.vertices

            raise ValueError(
                "No constellation boundaries were loaded from "
                f"{path}."
            )

        self.sampled_vertices.clear()
        self.altaz.clear()
        self.projected.clear()

        return self.vertices

    # ============================================================
    # Boundary membership
    # ============================================================

    def region_of(
        self,
        ra_deg,
        dec_deg,
        *,
        candidates=None,
    ):
        """
        Return the B1875 boundary identifier containing an ICRS point.

        This is primarily useful for constellations represented by more
        than one polygon in ``bound_18.dat``. In particular, Serpens is
        represented by ``SER1`` (Caput) and ``SER2`` (Cauda).

        Parameters
        ----------
        ra_deg, dec_deg : float
            ICRS right ascension and declination in degrees.

        candidates : iterable of str, optional
            Restrict the containment test to these boundary identifiers.
            For example, ``{"SER1", "SER2"}``.

        Returns
        -------
        str or None
            Boundary identifier containing the point, or None if no
            loaded candidate polygon contains it.
        """

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
        dec_degrees = float(
            b1875.dec.to_value(u.deg)
        )

        if candidates is None:
            identifiers = self.vertices.keys()
        else:
            identifiers = (
                abbreviation.upper()
                for abbreviation in candidates
            )

        for abbreviation in identifiers:
            vertices = self.vertices.get(abbreviation)

            if vertices is None or len(vertices) < 3:
                continue

            if self._contains_b1875_point(
                vertices=vertices,
                ra_hours=ra_hours,
                dec_degrees=dec_degrees,
            ):
                return abbreviation

        return None

    @staticmethod
    def _contains_b1875_point(
        vertices,
        ra_hours,
        dec_degrees,
    ):
        """
        Test point containment while handling the 0h/24h RA seam.

        The polygon RA values are shifted to the shortest offsets from
        the test point. The test point therefore lies at x=0 in this
        local unwrapped coordinate system.
        """

        vertices = np.asarray(vertices, dtype=float)

        ra_offsets = (
            (
                vertices[:, 0]
                - float(ra_hours)
                + 12.0
            )
            % 24.0
        ) - 12.0

        polygon = np.column_stack(
            (
                ra_offsets,
                vertices[:, 1],
            )
        )

        path = MatplotlibPath(
            polygon,
            closed=True,
        )

        # A tiny positive radius includes points lying numerically on
        # an official boundary edge.
        return bool(
            path.contains_point(
                (0.0, float(dec_degrees)),
                radius=1.0e-10,
            )
        )

    # ============================================================
    # B1875 boundary sampling
    # ============================================================

    def sample(self):
        """
        Sample all B1875 boundary segments.
        """

        sampled = OrderedDict()

        for abbreviation, vertices in self.vertices.items():
            sampled[abbreviation] = self._sample_closed_polygon(
                vertices
            )

        self.sampled_vertices = sampled
        self.altaz.clear()
        self.projected.clear()

        return self.sampled_vertices

    def _sample_closed_polygon(self, vertices):
        """
        Sample all segments of one closed boundary polygon.
        """

        vertices = np.asarray(vertices, dtype=float)

        if vertices.ndim != 2 or vertices.shape[1] != 2:
            raise ValueError(
                "Boundary vertices must have shape (N, 2)."
            )

        if len(vertices) < 3:
            raise ValueError(
                "A boundary polygon requires at least "
                "three vertices."
            )

        sampled_parts = []
        number_of_vertices = len(vertices)

        for index in range(number_of_vertices):
            start = vertices[index]
            end = vertices[
                (index + 1) % number_of_vertices
            ]

            segment = self._sample_segment(
                start,
                end,
            )

            if index > 0:
                segment = segment[1:]

            sampled_parts.append(segment)

        return np.vstack(sampled_parts)

    def _sample_segment(
        self,
        start,
        end,
    ):
        """
        Sample one B1875 meridian or parallel segment.
        """

        ra_start_hours = float(start[0])
        dec_start_deg = float(start[1])

        ra_end_hours = float(end[0])
        dec_end_deg = float(end[1])

        same_ra = np.isclose(
            ra_start_hours,
            ra_end_hours,
            atol=1e-5,
        )

        same_dec = np.isclose(
            dec_start_deg,
            dec_end_deg,
            atol=1e-5,
        )

        if same_ra and same_dec:
            return np.asarray(
                [[ra_start_hours, dec_start_deg]],
                dtype=float,
            )

        if same_ra:
            angular_length_deg = abs(
                dec_end_deg - dec_start_deg
            )

            number_of_intervals = max(
                1,
                int(
                    np.ceil(
                        angular_length_deg
                        / self.sampling_step_deg
                    )
                ),
            )

            declination = np.linspace(
                dec_start_deg,
                dec_end_deg,
                number_of_intervals + 1,
            )

            right_ascension = np.full_like(
                declination,
                ra_start_hours,
            )

        elif same_dec:
            ra_end_unwrapped = self._unwrap_ra_endpoint(
                ra_start_hours,
                ra_end_hours,
            )

            ra_length_deg = (
                abs(
                    ra_end_unwrapped - ra_start_hours
                )
                * 15.0
            )

            spherical_length_deg = (
                ra_length_deg
                * abs(
                    np.cos(
                        np.deg2rad(dec_start_deg)
                    )
                )
            )

            number_of_intervals = max(
                1,
                int(
                    np.ceil(
                        spherical_length_deg
                        / self.sampling_step_deg
                    )
                ),
            )

            right_ascension = np.linspace(
                ra_start_hours,
                ra_end_unwrapped,
                number_of_intervals + 1,
            )

            right_ascension = right_ascension % 24.0

            declination = np.full_like(
                right_ascension,
                dec_start_deg,
            )

        else:
            raise ValueError(
                "A bound_18.dat edge is neither constant "
                "RA nor constant declination:\n"
                f"start={start}, end={end}"
            )

        return np.column_stack(
            (
                right_ascension,
                declination,
            )
        )

    @staticmethod
    def _unwrap_ra_endpoint(
        ra_start_hours,
        ra_end_hours,
    ):
        """
        Choose the shortest continuous RA interval across 0h/24h.
        """

        difference = ra_end_hours - ra_start_hours

        if difference > 12.0:
            return ra_end_hours - 24.0

        if difference < -12.0:
            return ra_end_hours + 24.0

        return ra_end_hours

    # ============================================================
    # Coordinate transformation
    # ============================================================

    def compute_altaz(self):
        """
        Transform sampled FK4/B1875 coordinates to Alt/Az.
        """

        self._validate_observer()

        if not self.sampled_vertices:
            self.sample()

        b1875 = FK4(
            equinox=Time("B1875.0"),
        )

        earth_location = EarthLocation.from_geodetic(
            lon=self.observer.lon_deg * u.deg,
            lat=self.observer.lat_deg * u.deg,
            height=self.observer.elevation_m * u.m,
        )

        altaz_frame = AltAz(
            obstime=self.observer.t_astropy,
            location=earth_location,
        )

        transformed = OrderedDict()

        for abbreviation, vertices in (
            self.sampled_vertices.items()
        ):
            coordinates = SkyCoord(
                ra=vertices[:, 0] * u.hourangle,
                dec=vertices[:, 1] * u.deg,
                frame=b1875,
            )

            horizontal = coordinates.transform_to(
                altaz_frame
            )

            transformed[abbreviation] = np.column_stack(
                (
                    horizontal.alt.to_value(u.deg),
                    horizontal.az.to_value(u.deg),
                )
            )

        self.altaz = transformed
        self.projected.clear()

        return self.altaz

    def project(self, projection):
        """
        Project transformed altitude and azimuth coordinates.
        """

        if not self.altaz:
            self.compute_altaz()

        projected = OrderedDict()

        for abbreviation, altaz in self.altaz.items():
            altitude = altaz[:, 0]
            azimuth = altaz[:, 1]

            x, y = projection.project(
                altitude,
                azimuth,
            )

            projected[abbreviation] = np.column_stack(
                (
                    np.asarray(x, dtype=float),
                    np.asarray(y, dtype=float),
                )
            )

        self.projected = projected

        return self.projected

    # ============================================================
    # Drawing
    # ============================================================

    def draw(self, ax, projection):
        """
        Draw the visible constellation boundaries.
        """

        self.compute_altaz()
        self.project(projection)

        self.artists = []

        for abbreviation in self.projected:
            altitude = self.altaz[
                abbreviation
            ][:, 0]

            x = self.projected[
                abbreviation
            ][:, 0]

            y = self.projected[
                abbreviation
            ][:, 1]

            for segment_x, segment_y in self._visible_segments(
                x=x,
                y=y,
                altitude=altitude,
            ):
                curve = ProjectedCurve(
                    x=segment_x,
                    y=segment_y,
                )

                artist = render_curve(
                    ax,
                    curve,
                    color=self.color,
                    linewidth=self.linewidth,
                    alpha=self.alpha,
                    zorder=self.zorder,
                )
            
                self.artists.append(artist)

        return self.artists

    # ============================================================
    # Visibility segmentation
    # ============================================================

    def _visible_segments(
        self,
        x,
        y,
        altitude,
    ):
        """
        Split a curve into contiguous visible sections.
        """

        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        altitude = np.asarray(
            altitude,
            dtype=float,
        )

        visible = (
            np.isfinite(x)
            & np.isfinite(y)
            & np.isfinite(altitude)
            & (
                altitude >= self.horizon_altitude
            )
        )

        segments = []
        start = None

        for index, is_visible in enumerate(visible):
            if is_visible and start is None:
                start = index

            if not is_visible and start is not None:
                if index - start >= 2:
                    segments.append(
                        (
                            x[start:index],
                            y[start:index],
                        )
                    )

                start = None

        if start is not None:
            if len(x) - start >= 2:
                segments.append(
                    (
                        x[start:],
                        y[start:],
                    )
                )

        return segments

    # ============================================================
    # Validation
    # ============================================================

    def _validate_observer(self):
        if self.observer is None:
            raise RuntimeError(
                "ConstellationBoundaries has no Observer."
            )

        missing = [
            attribute
            for attribute in (
                "t_astropy",
                "lat_deg",
                "lon_deg",
                "elevation_m",
            )
            if getattr(
                self.observer,
                attribute,
                None,
            )
            is None
        ]

        if missing:
            raise RuntimeError(
                "Observer is missing required attributes: "
                + ", ".join(missing)
            )
