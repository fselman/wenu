"""Translate validated TOML furniture, product, and export values."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from types import MappingProxyType
from typing import Any, Mapping

from wenu.charts.furniture import (
    ChartContextOptions,
    ChartFurnitureOptions,
    FooterOptions,
    PoleAnnotations,
    ReferenceAnnotations,
    ReferencePlaneAnnotation,
)
from wenu.charts.legend_plan import (
    ChartLegendPlan,
    LegendOptions,
    LegendPlacement,
)
from wenu.charts.magnitude_legend_style import StellarMagnitudeLegendStyle
from wenu.charts.product_options import ChartProduct
from wenu.charts.regional import ExportOptions

from .validation import (
    ConfigurationError,
    load_packaged_defaults,
    validate_configuration,
)


@dataclass(frozen=True)
class FooterLayoutDefaults:
    """Validated footer appearance not yet represented by FooterOptions."""

    font_size: float
    y: float
    left_x: float
    right_x: float


@dataclass(frozen=True)
class ProductDefaults:
    """Validated default product values independent of an output path."""

    product: ChartProduct
    all_products: bool
    language: str
    title: str | None
    extension: str


@dataclass(frozen=True)
class FurnitureProductExportDefaults:
    """Immutable translation of the remaining Milestone 46D.3 values."""

    furniture_by_family: Mapping[str, ChartFurnitureOptions]
    legend_options: LegendOptions
    footer_layout: FooterLayoutDefaults
    magnitude_legend: StellarMagnitudeLegendStyle
    product: ProductDefaults
    export_options: ExportOptions
    export_padding: float


def _optional(value):
    return None if value == "none" else value


def _placement(value: str, *, enabled: bool = True) -> LegendPlacement:
    if value == "none":
        return LegendPlacement(enabled=False)
    suffix = " outside"
    outside = value.endswith(suffix)
    location = value[:-len(suffix)] if outside else value
    return LegendPlacement(
        enabled=enabled,
        location=location,
        outside=outside,
    )


def _legend_plans(table: Mapping[str, Any]):
    plans = {}
    for family in (
        "regional", "planisphere", "all_sky", "circumpolar", "binocular"
    ):
        values = table[family]
        objects_enabled = values.get("objects", table["objects"])
        plans[family] = ChartLegendPlan(
            chart_type=family,
            objects=_placement(
                values["objects_location"],
                enabled=objects_enabled,
            ),
            stars=_placement(
                values["stars_location"],
                enabled=table["stars"],
            ),
        )
    return MappingProxyType(plans)


def _references(configuration: Mapping[str, Any]) -> ReferenceAnnotations:
    table = configuration["grids_references"]["references"]
    anchor = _optional(table["anchor"])
    return ReferenceAnnotations(
        celestial_equator=ReferencePlaneAnnotation(
            state=table["state"],
            label=table["equatorial_label"],
            anchor=anchor,
        ),
        ecliptic=ReferencePlaneAnnotation(
            state=table["state"],
            label=table["ecliptic_label"],
            anchor=anchor,
        ),
        galactic_plane=ReferencePlaneAnnotation(
            state=table["state"],
            label=table["galactic_label"],
            anchor=anchor,
        ),
    )


def _footer(table: Mapping[str, Any]) -> FooterOptions:
    copyright_text = _optional(table["copyright"])
    if not table["enabled"] and copyright_text is not None:
        raise ConfigurationError(
            "furniture.footer.copyright: a disabled footer with copyright "
            "cannot translate until Milestone 46D.4 adds an overall "
            "footer switch to the runtime contract"
        )
    return FooterOptions(
        application=table["enabled"],
        application_name=table["application"],
        include_version=table["include_version"],
        copyright=copyright_text,
    )


def _magnitude_legend(table: Mapping[str, Any]):
    return StellarMagnitudeLegendStyle(
        enabled=table["enabled"],
        location=table["location"],
        title=table["title"],
        frame_on=table["frame"],
        font_size=_optional(table["font_size"]),
        title_font_size=_optional(table["title_font_size"]),
        marker=table["marker"],
        marker_edge_color=_optional(table["edge_color"]),
        marker_edge_width=table["edge_width"],
        label_spacing=table["label_spacing"],
        handle_text_pad=table["handle_text_padding"],
        border_pad=table["border_padding"],
        zorder=table["z_order"],
        text_color=_optional(table["text_color"]),
        facecolor=_optional(table["face_color"]),
        edgecolor=_optional(table["edge_color"]),
    )


def translate_furniture_product_export_defaults(
    configuration: Mapping[str, Any] | None = None,
) -> FurnitureProductExportDefaults:
    """Translate validated values without changing active runtime defaults."""
    values = (
        load_packaged_defaults()
        if configuration is None
        else validate_configuration(configuration)
    )
    furniture = values["furniture"]
    footer = furniture["footer"]
    context = ChartContextOptions(**furniture["context"])
    legends = furniture["legends"]
    legend_options = LegendOptions(
        objects=legends["objects"],
        stellar_magnitudes=legends["stars"],
        context=legends["context"],
        stellar_counts=legends["counts"],
        stellar_title=legends["title"],
    )
    plans = _legend_plans(legends)
    poles = values["grids_references"]["poles"]
    pole_annotations = PoleAnnotations(
        celestial=poles["state"],
        ecliptic=poles["state"],
        galactic=poles["state"],
        labels=poles["labels"],
    )
    common = {
        "references": _references(values),
        "poles": pole_annotations,
        "footer": _footer(footer),
        "context": context,
    }
    furniture_by_family = MappingProxyType({
        family: ChartFurnitureOptions(
            **common,
            legends=LegendOptions(
                objects=plan.objects.enabled,
                stellar_magnitudes=plan.stars.enabled,
                context=legend_options.context,
                stellar_counts=legend_options.stellar_counts,
                plan=plan,
                stellar_title=legend_options.stellar_title,
            ),
        )
        for family, plan in plans.items()
    })
    product = values["products"]["default"]
    export = values["export"]
    return FurnitureProductExportDefaults(
        furniture_by_family=furniture_by_family,
        legend_options=legend_options,
        footer_layout=FooterLayoutDefaults(
            font_size=footer["font_size"],
            y=footer["y"],
            left_x=footer["left_x"],
            right_x=footer["right_x"],
        ),
        magnitude_legend=_magnitude_legend(
            furniture["magnitude_legend"]
        ),
        product=ProductDefaults(
            product=ChartProduct(product["style"], product["mode"]),
            all_products=product["all_products"],
            language=product["language"],
            title=_optional(product["title"]),
            extension=product["extension"],
        ),
        export_options=ExportOptions(
            dpi=export["dpi"],
            bbox_inches=(
                "tight" if export["bounding_box"] == "tight" else None
            ),
            transparent=export["transparent"],
            facecolor=_optional(export["face_color"]),
            metadata=dict(export["metadata"]),
            padding=export["padding"],
        ),
        export_padding=export["padding"],
    )


@lru_cache(maxsize=1)
def packaged_furniture_product_export_defaults():
    """Return the process-local immutable packaged runtime authority."""
    return translate_furniture_product_export_defaults()
