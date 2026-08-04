"""Backend-independent descriptions of symbols used by chart legends."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal


LegendSymbolKind = Literal["marker", "patch"]


@dataclass(frozen=True)
class LegendSymbolDescriptor:
    """Semantic symbol and appearance for one active chart layer."""

    key: str
    label: str
    kind: LegendSymbolKind
    layer_attribute: str
    symbol_name: str | None = None
    marker: str | None = None
    edge_color: str | None = None
    face_color: str | None = None
    alpha: float | None = None
    linewidth: float | None = None


def legend_symbol_descriptors(
    sky,
    style,
    *,
    resolved_detail=None,
    labels=None,
):
    """Return descriptors for active layers in conventional legend order."""
    deep = style.deep_sky
    iso = style.isophotes
    candidates = (
        LegendSymbolDescriptor(
            key="open_cluster",
            label="Open cluster",
            kind="marker",
            layer_attribute="open_clusters",
            symbol_name="open_cluster",
            edge_color=deep.open_cluster_color,
            face_color="none",
            alpha=deep.open_cluster_alpha,
            linewidth=deep.open_cluster_linewidth,
        ),
        LegendSymbolDescriptor(
            key="globular_cluster",
            label="Globular cluster",
            kind="marker",
            layer_attribute="globular_clusters",
            marker="o",
            edge_color=deep.globular_cluster_color,
            face_color=deep.globular_cluster_color,
            alpha=deep.globular_cluster_alpha,
            linewidth=deep.globular_cluster_linewidth,
        ),
        LegendSymbolDescriptor(
            key="planetary_nebula",
            label="Planetary nebula",
            kind="marker",
            layer_attribute="planetary_nebulae",
            symbol_name="planetary_nebula",
            edge_color=deep.planetary_nebula_color,
            face_color=deep.planetary_nebula_face_color,
            alpha=deep.planetary_nebula_alpha,
            linewidth=deep.planetary_nebula_linewidth,
        ),
        LegendSymbolDescriptor(
            key="supernova_remnant",
            label="Supernova remnant",
            kind="marker",
            layer_attribute="supernova_remnants",
            marker="o",
            edge_color=deep.supernova_remnant_color,
            face_color="none",
            alpha=deep.supernova_remnant_alpha,
            linewidth=deep.supernova_remnant_linewidth,
        ),
        LegendSymbolDescriptor(
            key="galaxy",
            label="Galaxy",
            kind="patch",
            layer_attribute="galaxies",
            edge_color=deep.galaxy_edge_color,
            face_color=(
                deep.galaxy_face_color or deep.galaxy_edge_color
            ),
            alpha=deep.galaxy_edge_alpha,
            linewidth=deep.galaxy_linewidth,
        ),
        LegendSymbolDescriptor(
            key="milky_way",
            label="Milky Way",
            kind="patch",
            layer_attribute="milky_way_isophotes",
            edge_color=iso.milky_way_contour_color or "none",
            face_color=iso.milky_way_color,
            alpha=iso.milky_way_alpha,
            linewidth=(
                0.0
                if iso.milky_way_contour_color is None
                else iso.milky_way_contour_linewidth
            ),
        ),
    )
    detail_names = {
        "milky_way_isophotes": "milky_way",
    }
    labels = {} if labels is None else dict(labels)
    return tuple(
        replace(
            descriptor,
            label=labels.get(descriptor.key, descriptor.label),
        )
        for descriptor in candidates
        if getattr(sky, descriptor.layer_attribute, None) is not None
        and (
            resolved_detail is None
            or resolved_detail.layer_enabled(
                detail_names.get(
                    descriptor.layer_attribute,
                    descriptor.layer_attribute,
                )
            )
        )
    )
