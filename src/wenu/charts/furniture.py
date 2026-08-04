"""Backend-independent options for canonical chart furniture."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .legend_plan import (
    ChartLegendPlan,
    LegendOptions,
    ResolvedLegendOptions,
)


_REFERENCE_STATES = frozenset({"none", "line", "labeled"})
_POLE_SELECTIONS = frozenset({"none", "visible", "both"})


def _anchor(value, name):
    """Return one normalized explicit chart-coordinate label anchor."""
    if value is None:
        return None
    if len(value) != 2:
        raise ValueError(f"{name} must contain two values.")
    result = tuple(float(component) for component in value)
    if not all(isfinite(component) for component in result):
        raise ValueError(f"{name} values must be finite.")
    return result


@dataclass(frozen=True)
class ReferencePlaneAnnotation:
    """Selection and semantic label policy for one reference plane.

    ``anchor=None`` requests automatic boundary-aware placement. A concrete
    anchor is expressed in prepared chart coordinates and is used only when
    ``state='labeled'``.
    """

    state: str = "none"
    label: str = ""
    anchor: tuple[float, float] | None = None

    def __post_init__(self):
        state = str(self.state).strip().lower()
        if state not in _REFERENCE_STATES:
            raise ValueError(
                "Reference-plane state must be 'none', 'line', or "
                "'labeled'."
            )
        label = str(self.label)
        if state == "labeled" and not label.strip():
            raise ValueError("A labeled reference plane requires text.")
        object.__setattr__(self, "state", state)
        object.__setattr__(self, "label", label)
        object.__setattr__(
            self,
            "anchor",
            _anchor(self.anchor, "Reference-plane anchor"),
        )

    @property
    def enabled(self) -> bool:
        return self.state != "none"

    @property
    def labeled(self) -> bool:
        return self.state == "labeled"


@dataclass(frozen=True)
class ReferenceAnnotations:
    """Independent principal coordinate-plane annotation policies."""

    celestial_equator: ReferencePlaneAnnotation = ReferencePlaneAnnotation(
        label="Celestial equator"
    )

    ecliptic: ReferencePlaneAnnotation = ReferencePlaneAnnotation(
        label="Ecliptic"
    )
    galactic_plane: ReferencePlaneAnnotation = ReferencePlaneAnnotation(
        label="Galactic plane"
    )

    def __post_init__(self):
        for name in (
            "celestial_equator",
            "ecliptic",
            "galactic_plane",
        ):
            if not isinstance(getattr(self, name), ReferencePlaneAnnotation):
                raise TypeError(
                    f"{name} must be a ReferencePlaneAnnotation value."
                )


@dataclass(frozen=True)
class PoleAnnotations:
    """Coordinate-system pole selections for canonical cross markers."""

    celestial: str = "none"
    ecliptic: str = "none"
    galactic: str = "none"
    labels: bool = True

    def __post_init__(self):
        for name in ("celestial", "ecliptic", "galactic"):
            selection = str(getattr(self, name)).strip().lower()
            if selection not in _POLE_SELECTIONS:
                raise ValueError(
                    f"{name} pole selection must be 'none', 'visible', "
                    "or 'both'."
                )
            object.__setattr__(self, name, selection)
        object.__setattr__(self, "labels", bool(self.labels))


@dataclass(frozen=True)
class FooterOptions:
    """Figure-margin application and copyright footer requests."""

    application: bool = False
    application_name: str = "Wenu"
    include_version: bool = True
    copyright: str | None = None

    def __post_init__(self):
        name = str(self.application_name).strip()
        if self.application and not name:
            raise ValueError("An application footer requires a name.")
        copyright_text = (
            None if self.copyright is None else str(self.copyright).strip()
        )
        object.__setattr__(self, "application", bool(self.application))
        object.__setattr__(self, "application_name", name)
        object.__setattr__(self, "include_version", bool(self.include_version))
        object.__setattr__(self, "copyright", copyright_text or None)


@dataclass(frozen=True)
class ResolvedChartFurnitureOptions:
    """Immutable chart-furniture policy resolved for one chart family."""

    references: ReferenceAnnotations
    poles: PoleAnnotations
    footer: FooterOptions
    legends: ResolvedLegendOptions | None = None


@dataclass(frozen=True)
class ChartFurnitureOptions:
    """User-facing, backend-independent chart-furniture options."""

    references: ReferenceAnnotations = ReferenceAnnotations()
    poles: PoleAnnotations = PoleAnnotations()
    footer: FooterOptions = FooterOptions()
    legends: LegendOptions | ChartLegendPlan | None = None

    def __post_init__(self):
        expected = (
            ("references", self.references, ReferenceAnnotations),
            ("poles", self.poles, PoleAnnotations),
            ("footer", self.footer, FooterOptions),
        )
        for name, value, kind in expected:
            if not isinstance(value, kind):
                raise TypeError(f"{name} must be a {kind.__name__} value.")
        if self.legends is not None and not isinstance(
            self.legends,
            (LegendOptions, ChartLegendPlan),
        ):
            raise TypeError(
                "legends must be LegendOptions, ChartLegendPlan, or None."
            )

    def resolve(self, chart_type: str) -> ResolvedChartFurnitureOptions:
        """Resolve the optional legend plan for one chart family."""
        legends = self.legends
        if isinstance(legends, ChartLegendPlan):
            legends = LegendOptions(plan=legends)
        resolved_legends = (
            None if legends is None else legends.resolve(chart_type)
        )
        return ResolvedChartFurnitureOptions(
            references=self.references,
            poles=self.poles,
            footer=self.footer,
            legends=resolved_legends,
        )
