"""Constellation layer grouping without projection or rendering state."""

from __future__ import annotations

from wenu.sky.constellation_lines import ConstellationLines


class Constellations:
    """Group constellation line and boundary domain objects."""

    def __init__(
        self,
        stars,
        system="western",
        lines_file=None,
        selected=None,
        observer=None,
    ):
        self.stars = stars
        self.observer = (
            getattr(stars, "observer", None)
            if observer is None
            else observer
        )
        self.system = system
        self.selected = (
            None if selected is None else set(selected)
        )
        self.lines = ConstellationLines(
            stars=stars,
            system=system,
            filename=lines_file,
            constellations=self.selected,
        )
        self.boundaries = None

    def set_boundaries(self, boundaries):
        """Associate boundary geometry used by constellation labels."""
        self.boundaries = boundaries
        return boundaries
