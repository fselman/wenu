"""Extract legend inputs from completed chart-rendering results."""

from __future__ import annotations

from dataclasses import dataclass


class RenderedStarsNotFoundError(LookupError):
    """Raised when a stellar legend is requested without rendered stars."""


@dataclass(frozen=True)
class RenderedStarGeometry:
    """The rendered Stars layer and geometry needed by its legend."""

    layer: object
    spherical: object
    projected: object
    viewport: object


def _candidate_star_layer(sky=None, star_layer=None):
    if star_layer is not None:
        return star_layer
    if sky is not None:
        return getattr(sky, "stars", None)
    return None


def rendered_star_geometry(
    rendering_result,
    *,
    sky=None,
    star_layer=None,
) -> RenderedStarGeometry:
    """Return the Stars geometry already produced for a chart.

    Identity with an explicitly supplied layer or ``sky.stars`` is
    preferred. A conservative class-name fallback supports stored or
    reconstructed rendering results without importing object-layer
    packages into this adapter.
    """
    expected = _candidate_star_layer(
        sky=sky,
        star_layer=star_layer,
    )
    matches = []
    for result in tuple(rendering_result.layers):
        layer = result.layer
        if expected is not None:
            if layer is expected:
                matches.append(result)
        elif type(layer).__name__ == "Stars":
            matches.append(result)

    if not matches:
        raise RenderedStarsNotFoundError(
            "The chart rendering result contains no matching Stars layer."
        )
    if len(matches) > 1:
        raise RenderedStarsNotFoundError(
            "The chart rendering result contains multiple matching "
            "Stars layers; pass star_layer explicitly."
        )

    match = matches[0]
    metadata = getattr(match.spherical, "metadata", {})
    if "magnitude" not in metadata:
        raise ValueError(
            "Rendered stellar spherical geometry has no magnitude "
            "metadata."
        )
    return RenderedStarGeometry(
        layer=match.layer,
        spherical=match.spherical,
        projected=match.projected,
        viewport=rendering_result.viewport,
    )
