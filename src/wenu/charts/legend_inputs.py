"""Resolve stellar-legend inputs from chart detail and visual style."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class ResolvedStellarLegendInputs:
    """Effective scientific and visual inputs for a stellar legend."""

    effective_limit: float
    area_scale: float
    color: str
    alpha: float = 1.0

    def __post_init__(self):
        if not isfinite(float(self.effective_limit)):
            raise ValueError("effective_limit must be finite.")
        if not isfinite(float(self.area_scale)) or self.area_scale <= 0.0:
            raise ValueError("area_scale must be finite and positive.")
        if not isfinite(float(self.alpha)):
            raise ValueError("alpha must be finite.")


def _publication_style(chart_style):
    converter = getattr(chart_style, "as_publication_style", None)
    return converter() if callable(converter) else chart_style


def resolve_stellar_legend_inputs(
    resolved_detail,
    chart_style,
    *,
    effective_limit=None,
    area_scale=None,
    color=None,
    alpha=None,
) -> ResolvedStellarLegendInputs:
    """Resolve legend inputs while allowing deliberate call-site overrides.

    ``resolved_detail`` owns scientific content.  ``chart_style`` owns
    appearance.  This adapter accepts either a composed ``ChartStyle`` or
    its renderer-facing ``PublicationStyle``.
    """
    publication = _publication_style(chart_style)

    if effective_limit is None:
        if resolved_detail is None:
            raise ValueError(
                "resolved_detail is required when effective_limit is not "
                "supplied."
            )
        effective_limit = getattr(
            resolved_detail,
            "star_magnitude_limit",
            None,
        )
        if effective_limit is None:
            raise ValueError(
                "Resolved detail has no stellar magnitude limit."
            )

    if area_scale is None:
        area_scale = getattr(publication, "star_area_scale", None)
        if area_scale is None:
            stars = getattr(chart_style, "stars", None)
            area_scale = getattr(stars, "area_scale", 1.0)

    if color is None:
        color = getattr(publication, "star_color", None)
        if color is None:
            stars = getattr(chart_style, "stars", None)
            color = getattr(stars, "color", "black")

    if alpha is None:
        # Base stars currently default to opaque in PublicationStyle.
        alpha = getattr(publication, "star_alpha", 1.0)

    return ResolvedStellarLegendInputs(
        effective_limit=float(effective_limit),
        area_scale=float(area_scale),
        color=str(color),
        alpha=float(alpha),
    )
