# src/wenu/sky/constellations.py

from collections import defaultdict

import numpy as np

from astropy.coordinates import SkyCoord
import astropy.units as u

from wenu.sky.constellation_lines import ConstellationLines
from wenu.renderers import render_text
from wenu.renderers.constellation_lines import (
    ConstellationLinesRenderingAdapter,
)


class Constellations:
    """
    Manage constellation lines, labels, and boundaries.
    """

    LABEL_OVERRIDES = {
        "SER1": "SerCap",
        "SER2": "SerCau",
    }

    def __init__(
        self,
        stars,
        system="western",
        lines_file=None,
        selected=None,
        observer=None,
        star_renderer=None,
    ):
        line_stars = getattr(stars, "stars", stars)
        self.stars = (
            stars if star_renderer is None else star_renderer
        )
        self.observer = (
            getattr(stars, "observer", None)
            if observer is None
            else observer
        )
        self.system = system
    
        self.selected = (
            None
            if selected is None
            else set(selected)
        )

        self.lines = ConstellationLines(
            stars=line_stars,
            system=self.system,
            filename=lines_file,
            constellations=self.selected,
        )
        self.line_renderer = ConstellationLinesRenderingAdapter(
            lines=self.lines,
            observer=self.observer,
        )

        self.boundaries = None
        self.boundary_renderer = None

        self.line_artists = []
        self.label_artists = []
        self.boundary_artists = []

    # =====================================================
    # Unified drawing interface
    # =====================================================

    def draw(
        self,
        ax,
        projection,
        *,
        draw_lines=True,
        draw_labels=True,
        draw_boundaries=False,
        line_kwargs=None,
        label_kwargs=None,
        boundary_kwargs=None,
    ):
        line_kwargs = (
            {}
            if line_kwargs is None
            else dict(line_kwargs)
        )

        label_kwargs = (
            {}
            if label_kwargs is None
            else dict(label_kwargs)
        )

        boundary_kwargs = (
            {}
            if boundary_kwargs is None
            else dict(boundary_kwargs)
        )

        artists = {}

        if draw_boundaries:
            artists["boundaries"] = self.draw_boundaries(
                ax=ax,
                projection=projection,
                **boundary_kwargs,
            )

        if draw_lines:
            artists["lines"] = self.draw_lines(
                ax=ax,
                projection=projection,
                **line_kwargs,
            )

        if draw_labels:
            artists["labels"] = self.draw_labels(
                ax=ax,
                **label_kwargs,
            )

        return artists

    # =====================================================
    # Lines
    # =====================================================

    def draw_lines(
        self,
        ax,
        projection,
        **kwargs,
    ):
        if self.lines is None:
            self.line_artists = []
            return self.line_artists

        self.line_artists = self.line_renderer.draw(
            ax=ax,
            projection=projection,
            **kwargs,
        )

        return self.line_artists

    # =====================================================
    # Labels
    # =====================================================

    def draw_labels(
        self,
        ax,
        *,
        selected=None,
        min_stars=3,
        radial_cut=None,
        fontsize=10,
        color="white",
        alpha=0.85,
        outward_offset=0.04,
        zorder=5,
    ):
        """
        Draw constellation labels.

        Serpens stars are divided between the two official boundary
        polygons, SER1 and SER2, and labelled SerCap and SerCau.
        """

        self._validate_stars()

        selected = self._resolve_selected(selected)
        stars = self.stars

        hip_to_constellation = self._build_hip_to_constellation(
            stars.hip_df
        )

        points = defaultdict(list)

        for hip_id in stars.hip_df.index:
            hip_id = int(hip_id)

            iau_constellation = hip_to_constellation.get(
                hip_id
            )

            if iau_constellation is None:
                continue

            index = stars.hip_index.get(hip_id)

            if index is None:
                continue

            if stars.alt[index] <= 0.0:
                continue

            x = stars.x[index]
            y = stars.y[index]

            if not np.all(np.isfinite([x, y])):
                continue

            label_group = self._label_group_for_star(
                hip_id=hip_id,
                iau_constellation=iau_constellation,
            )

            # Accept either the ordinary IAU abbreviation or the
            # resolved label group. Thus:
            #
            #   {"Ser"}    selects both SerCap and SerCau
            #   {"SerCap"} selects only Serpens Caput
            #   {"SerCau"} selects only Serpens Cauda
            if (
                selected is not None
                and iau_constellation not in selected
                and label_group not in selected
            ):
                continue

            points[label_group].append(
                (x, y)
            )

        self.label_artists = []

        for constellation, constellation_points in points.items():
            if len(constellation_points) < min_stars:
                continue

            coordinates = np.asarray(
                constellation_points,
                dtype=float,
            )

            cx = np.mean(coordinates[:, 0])
            cy = np.mean(coordinates[:, 1])

            radius = np.hypot(cx, cy)

            if (
                radial_cut is not None
                and radius > radial_cut
            ):
                continue

            if radius > 1.0e-12:
                dx = outward_offset * cx / radius
                dy = outward_offset * cy / radius
            else:
                dx = 0.0
                dy = 0.0

            artist = render_text(
                ax,
                cx + dx,
                cy + dy,
                constellation,
                color=color,
                fontsize=fontsize,
                ha="center",
                va="center",
                alpha=alpha,
                zorder=zorder,
            )

            self.label_artists.append(artist)

        return self.label_artists

    def _label_group_for_star(
        self,
        hip_id,
        iau_constellation,
    ):
        """
        Return the label group used for one catalogue star.
        """

        if iau_constellation != "Ser":
            return iau_constellation

        if self.boundaries is None:
            return iau_constellation

        row = self.stars.hip_df.loc[hip_id]

        boundary_identifier = self.boundaries.region_of(
            ra_deg=float(row["ra_degrees"]),
            dec_deg=float(row["dec_degrees"]),
            candidates={"SER1", "SER2"},
        )

        return self.LABEL_OVERRIDES.get(
            boundary_identifier,
            iau_constellation,
        )

    # =====================================================
    # Boundaries
    # =====================================================

    def draw_boundaries(
        self,
        ax,
        projection,
        **kwargs,
    ):
        if self.boundary_renderer is None:
            raise RuntimeError(
                "No constellation-boundary data has been configured."
            )

        self.boundary_artists = self.boundary_renderer.draw(
            ax=ax,
            projection=projection,
            **kwargs,
        )

        return self.boundary_artists

    def set_boundaries(
        self,
        boundaries,
        *,
        renderer=None,
    ):
        self.boundaries = boundaries
        self.boundary_renderer = renderer
        return self.boundaries

    # =====================================================
    # Helpers
    # =====================================================

    def _resolve_selected(self, selected):
        if selected is None:
            return self.selected

        return set(selected)

    @staticmethod
    def _build_hip_to_constellation(hip_df):
        """
        Map each active HIP star to its IAU constellation.
        """

        coordinates = SkyCoord(
            ra=hip_df[
                "ra_degrees"
            ].to_numpy() * u.deg,
            dec=hip_df[
                "dec_degrees"
            ].to_numpy() * u.deg,
            frame="icrs",
        )

        abbreviations = coordinates.get_constellation(
            short_name=True
        )

        return {
            int(hip_id): abbreviation
            for hip_id, abbreviation in zip(
                hip_df.index,
                abbreviations,
            )
        }

    def _validate_stars(self):
        stars = self.stars

        if stars is None:
            raise RuntimeError(
                "No Stars object has been assigned."
            )

        if stars.hip_df is None:
            raise RuntimeError(
                "The Stars catalogue has not been loaded."
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
                "Stars must be prepared or drawn first. "
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
                "Stars catalogue and projected arrays "
                f"are not aligned: {lengths}"
            )
