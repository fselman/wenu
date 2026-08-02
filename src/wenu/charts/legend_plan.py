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


@dataclass(frozen=True)
class ResolvedLegendOptions:
    """Backend-independent legend policy resolved for one chart type."""

    plan: ChartLegendPlan
    context: bool = True


@dataclass(frozen=True)
class LegendOptions:
    """User-facing switches for canonical chart furniture."""

    objects: bool = True
    stellar_magnitudes: bool = True
    context: bool = True
    plan: ChartLegendPlan | None = None

    def resolve(self, chart_type: str) -> ResolvedLegendOptions:
        """Resolve family switches into the established placement plan."""
        plan = (
            default_chart_legend_plan(chart_type)
            if self.plan is None
            else self.plan
        )
        if plan.chart_type != str(chart_type).strip().lower():
            raise ValueError(
                "Legend plan chart_type does not match the chart."
            )
        plan = plan.with_objects(enabled=bool(self.objects))
        plan = plan.with_stars(enabled=bool(self.stellar_magnitudes))
        return ResolvedLegendOptions(
            plan=plan,
            context=bool(self.context),
        )


def chart_type_name(chart) -> str:
    """Return the stable semantic type used by legend layout policy."""
    explicit = getattr(chart, "chart_type", None)
    if explicit is not None:
        normalized = str(explicit).strip().lower()
        if normalized in _CHART_TYPES:
            return normalized
    names = {
        "RegionalChart": "regional",
        "FullSkyChart": "planisphere",
        "CircumpolarChart": "circumpolar",
        "BinocularChart": "binocular",
    }
    try:
        return names[type(chart).__name__]
    except KeyError as error:
        raise ValueError(
            f"Cannot infer a legend plan for chart class "
            f"{type(chart).__name__!r}; pass plan explicitly or use "
            "a chart with a stable chart_type."
        ) from error


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
