"""Backend-independent plans for composing chart legends."""

from __future__ import annotations

from dataclasses import dataclass, replace


_CHART_TYPES = frozenset(
    {
        "regional",
        "planisphere",
        "circumpolar",
        "binocular",
    }
)


@dataclass(frozen=True)
class LegendPlacement:
    """Placement of one independently rendered chart legend."""

    enabled: bool = True
    location: str = "upper right"
    outside: bool = False
    anchor: tuple[float, float] | None = None

    def __post_init__(self):
        if self.anchor is not None:
            if len(self.anchor) != 2:
                raise ValueError("Legend anchor must contain two values.")
            object.__setattr__(
                self,
                "anchor",
                tuple(float(value) for value in self.anchor),
            )


@dataclass(frozen=True)
class ChartLegendPlan:
    """Resolved independent placements for chart legend families."""

    chart_type: str
    objects: LegendPlacement
    stars: LegendPlacement

    def __post_init__(self):
        normalized = str(self.chart_type).strip().lower()
        if normalized not in _CHART_TYPES:
            raise ValueError(
                "chart_type must be one of: "
                + ", ".join(sorted(_CHART_TYPES))
            )
        object.__setattr__(self, "chart_type", normalized)

    def with_objects(self, **changes) -> "ChartLegendPlan":
        return replace(
            self,
            objects=replace(self.objects, **changes),
        )

    def with_stars(self, **changes) -> "ChartLegendPlan":
        return replace(
            self,
            stars=replace(self.stars, **changes),
        )


def default_chart_legend_plan(chart_type: str) -> ChartLegendPlan:
    """Return neutral defaults appropriate to a chart's geometry.

    These are layout defaults only. They do not select colors, symbols,
    magnitude limits, content, or output mode.
    """
    normalized = str(chart_type).strip().lower()
    if normalized == "regional":
        return ChartLegendPlan(
            chart_type=normalized,
            objects=LegendPlacement(location="upper right"),
            stars=LegendPlacement(location="lower right"),
        )
    if normalized == "planisphere":
        return ChartLegendPlan(
            chart_type=normalized,
            objects=LegendPlacement(location="upper right"),
            stars=LegendPlacement(location="lower right"),
        )
    if normalized == "circumpolar":
        return ChartLegendPlan(
            chart_type=normalized,
            objects=LegendPlacement(location="upper right"),
            stars=LegendPlacement(location="lower left"),
        )
    if normalized == "binocular":
        return ChartLegendPlan(
            chart_type=normalized,
            objects=LegendPlacement(enabled=False),
            stars=LegendPlacement(location="lower right"),
        )
    raise ValueError(
        "chart_type must be one of: "
        + ", ".join(sorted(_CHART_TYPES))
    )
