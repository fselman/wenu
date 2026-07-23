# src/wenu/sky/constellation_lines.py

from importlib.resources import as_file
from pathlib import Path

import numpy as np

from wenu.projected import ProjectedCurve
from wenu.renderers import render_curve
from wenu.resources import constellation_lines_path


class ConstellationLines:
    """
    Constellation line segments loaded from a Stellarium-style .fab file.

    The class uses the Hipparcos indexing, altitudes, and projected
    coordinates already calculated by a Stars object.

    Expected .fab format
    --------------------
    Each non-comment line has the form:

        CONSTELLATION  N  hip1 hip2 hip3 ...

    Consecutive HIP identifiers define segments:

        hip1 -- hip2
        hip2 -- hip3
        ...

    Parameters
    ----------
    filename : str or pathlib.Path
        Path to the .fab file.

    stars : wenu.objects.stars.Stars
        Stars object used to resolve HIP identifiers and obtain projected
        coordinates.

    constellations : iterable of str, optional
        IAU constellation abbreviations to include.
        If None, all constellations are loaded.

    color : matplotlib color, optional
        Line color.

    linewidth : float, optional
        Line width.

    alpha : float, optional
        Line transparency.

    zorder : float, optional
        Matplotlib drawing order.

    horizon_altitude : float, optional
        Both endpoint stars must have an altitude greater than this value.

    max_segment_length : float, optional
        Maximum allowed projected segment length. If None, no length
        filtering is applied.
    """

    def __init__(
        self,
        stars,
        system="western",
        filename=None,
        constellations=None,
        *,
        color="white",
        linewidth=0.4,
        alpha=0.7,
        zorder=2,
        horizon_altitude=0.0,
        max_segment_length=None,
    ):
        self.stars = stars
        self.system = system
        
        # An explicit filename overrides the packaged resource.
        self.filename = (
            None
            if filename is None
            else Path(filename)
        )

        self.constellations = (
            None
            if constellations is None
            else set(constellations)
        )

        self.color = color
        self.linewidth = linewidth
        self.alpha = alpha
        self.zorder = zorder
        self.horizon_altitude = horizon_altitude
        self.max_segment_length = max_segment_length

        self.edges = []
        self.edges_by_constellation = {}

        self.artists = []

        self.load()

    # =====================================================
    # Data loading
    # =====================================================
    def load(self):
        """
        Read constellation segments from a .fab file.
    
        If ``filename`` was supplied explicitly, that file is used.
        Otherwise the packaged resource selected by ``system`` is used.

        Returns
        -------
        list of tuple
            All loaded ``(hip1, hip2)`` edges.
        """

        if self.filename is not None:
            if not self.filename.exists():
                raise FileNotFoundError(
                    f"Constellation file not found: {self.filename}"
                )
    
            return self._load_file(self.filename)

        resource = constellation_lines_path(self.system)

        with as_file(resource) as path:
            return self._load_file(path)

    def _load_file(self, path):
        """
        Parse one Stellarium-style .fab file.
        """

        path = Path(path)

        self.edges.clear()
        self.edges_by_constellation.clear()

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

                parts = line.split()

                if len(parts) < 4:
                    continue

                abbreviation = parts[0]

                if (
                    self.constellations is not None
                    and abbreviation not in self.constellations
                ):
                    continue

                try:
                    declared_count = int(parts[1])

                    hip_ids = [
                        int(value)
                        for value in parts[2:]
                    ]

                except ValueError as error:
                    raise ValueError(
                        f"Invalid .fab line at "
                        f"{path}:{line_number}\n"
                        f"{raw_line.rstrip()}"
                    ) from error

                if len(hip_ids) < 2:
                    continue

                # Retain the declared value for possible future validation.
                # Different .fab files do not always use this field in
                # precisely the same way.
                _ = declared_count

                constellation_edges = [
                    (int(hip1), int(hip2))
                    for hip1, hip2 in zip(
                        hip_ids[:-1],
                        hip_ids[1:],
                    )
                ]

                self.edges.extend(constellation_edges)

                self.edges_by_constellation.setdefault(
                    abbreviation,
                    [],
                ).extend(constellation_edges)

        return self.edges

    # =====================================================
    # Unified drawing interface
    # =====================================================

    def draw(self, ax, projection):
        """
        Draw all loaded constellation line segments.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            Axes on which to draw.

        projection
            Projection associated with the chart. The Stars object already
            contains projected coordinates, so this argument is not used
            directly here. It is accepted to preserve Wenu's unified
            ``draw(ax, projection)`` interface.


        Returns
        -------
        list
            Matplotlib Line2D artists.
        """

        del projection

        self._validate_stars()

        self.artists = self._draw_edges(
            ax=ax,
            edges=self.edges,
        )

        return self.artists

    # =====================================================
    # Individual constellations
    # =====================================================

    def draw_constellation(
        self,
        ax,
        projection,
        abbreviation,
    ):
        """
        Draw one constellation by its IAU abbreviation.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            Axes on which to draw.

        projection
            Projection associated with the chart.

        abbreviation : str
            IAU constellation abbreviation.

        Returns
        -------
        list
            Matplotlib Line2D artists.
        """

        del projection

        self._validate_stars()

        edges = self.edges_by_constellation.get(
            abbreviation,
            [],
        )

        return self._draw_edges(
            ax=ax,
            edges=edges,
        )

    # =====================================================
    # Internal drawing
    # =====================================================

    def _draw_edges(
        self,
        ax,
        edges,
    ):
        """
        Draw a supplied sequence of HIP-to-HIP edges.
        """

        stars = self.stars

        hip_index = stars.hip_index

        x = np.asarray(stars.x)
        y = np.asarray(stars.y)
        alt = np.asarray(stars.alt)

        artists = []

        for hip1, hip2 in edges:
            if hip1 not in hip_index or hip2 not in hip_index:
                continue

            i = hip_index[hip1]
            j = hip_index[hip2]

            if (
                alt[i] <= self.horizon_altitude
                or alt[j] <= self.horizon_altitude
            ):
                continue

            x1 = x[i]
            y1 = y[i]
            x2 = x[j]
            y2 = y[j]

            if not np.all(
                np.isfinite([x1, y1, x2, y2])
            ):
                continue

            if self.max_segment_length is not None:
                segment_length = np.hypot(
                    x2 - x1,
                    y2 - y1,
                )

                if segment_length > self.max_segment_length:
                    continue

            curve = ProjectedCurve(
                x=[x1, x2],
                y=[y1, y2],
            )

            artist = render_curve(
                ax,
                curve,
                color=self.color,
                linewidth=self.linewidth,
                alpha=self.alpha,
                zorder=self.zorder,
            )

            artists.append(artist)

        return artists

    # =====================================================
    # Validation
    # =====================================================

    def _validate_stars(self):
        """
        Confirm that the Stars object has been loaded and projected.
        """

        stars = self.stars

        if stars is None:
            raise RuntimeError(
                "ConstellationLines has no Stars object."
            )

        if stars.hip_df is None:
            raise RuntimeError(
                "Stars has no active Hipparcos catalogue. "
                "Call stars.load() first."
            )

        if stars.hip_index is None:
            raise RuntimeError(
                "Stars has no HIP index."
            )

        required = {
            "alt": stars.alt,
            "x": stars.x,
            "y": stars.y,
        }

        missing = [
            name
            for name, value in required.items()
            if value is None
        ]

        if missing:
            raise RuntimeError(
                "Stars has not yet been prepared or drawn. "
                "Constellation lines require projected stellar "
                "coordinates. "
                f"Missing: {', '.join(missing)}"
            )

        lengths = {
            "hip_df": len(stars.hip_df),
            "alt": len(stars.alt),
            "x": len(stars.x),
            "y": len(stars.y),
        }

        if len(set(lengths.values())) != 1:
            raise RuntimeError(
                "Stars catalogue and projected coordinates "
                f"are not aligned: {lengths}"
            )
