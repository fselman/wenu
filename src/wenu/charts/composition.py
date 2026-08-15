"""Composition of chart geometry, style, mode, and content detail."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from .context import ChartContext
from .detail import (
    DetailOverrides,
    DetailPolicy,
    FixedDetailPolicy,
    ResolvedDetail,
    apply_detail_overrides,
)
from .modes import ChartMode, PrintMode, ResolvedMode
from .legend_plan import (
    ChartLegendPlan,
    LegendOptions,
    ResolvedLegendOptions,
    chart_type_name,
)
from .furniture import (
    ChartFurnitureOptions,
    ResolvedChartFurnitureOptions,
)
from .style_overrides import ChartStyleOverrides


ATLAS_STYLE = "atlas"
CARTOON_STYLE = "cartoon"
PRINT_MODE = "print"
PRESENTATION_MODE = "presentation"


def _style_mode_defaults(configuration=None):
    if configuration is not None:
        return configuration.style_mode
    from wenu.configuration.style_mode_translation import (
        packaged_style_mode_defaults,
    )

    return packaged_style_mode_defaults()


def _geometry_detail_defaults(configuration=None):
    if configuration is not None:
        return configuration.geometry_detail
    from wenu.configuration.geometry_detail_translation import (
        packaged_geometry_detail_defaults,
    )

    return packaged_geometry_detail_defaults()


def _resolved_style_mode_defaults(configuration):
    return (
        _style_mode_defaults()
        if configuration is None
        else _style_mode_defaults(configuration)
    )


def _resolved_geometry_detail_defaults(configuration):
    return (
        _geometry_detail_defaults()
        if configuration is None
        else _geometry_detail_defaults(configuration)
    )


def _family_atlas_policy(chart, geometry_defaults):
    try:
        family = chart_type_name(chart)
    except ValueError:
        return FixedDetailPolicy(geometry_defaults.neutral_detail)
    if family == "binocular":
        return geometry_defaults.binocular_other_policy
    if family == "polar_planisphere":
        return geometry_defaults.polar_planisphere_policy
    return geometry_defaults.family_atlas_policies.get(
        family,
        FixedDetailPolicy(geometry_defaults.neutral_detail),
    )


def _resolve_style(style, *, configuration=None):
    """Return the stable style identifier and concrete style value."""
    if isinstance(style, str):
        name = style.strip().lower()
        if name not in {ATLAS_STYLE, CARTOON_STYLE}:
            raise ValueError(
                f"Unknown chart style {style!r}. Use 'atlas', 'cartoon', "
                "or pass a chart-style object."
            )
        if name == ATLAS_STYLE:
            return ATLAS_STYLE, _resolved_style_mode_defaults(
                configuration
            ).atlas
        return CARTOON_STYLE, _resolved_style_mode_defaults(
            configuration
        ).cartoon

    from .presets import AtlasChartStyle, CartoonChartStyle

    if isinstance(style, AtlasChartStyle):
        name = ATLAS_STYLE
    elif isinstance(style, CartoonChartStyle):
        name = CARTOON_STYLE
    else:
        name = "custom"
    return name, style


def _resolve_mode(mode, *, configuration=None):
    """Return the stable mode identifier and concrete mode policy."""
    if mode is None:
        return PRINT_MODE, _resolved_style_mode_defaults(
            configuration
        ).print_mode
    if isinstance(mode, str):
        name = mode.strip().lower()
        if name in {PRINT_MODE, "paper"}:
            return PRINT_MODE, _resolved_style_mode_defaults(
                configuration
            ).print_mode
        if name == PRESENTATION_MODE:
            return (
                PRESENTATION_MODE,
                _resolved_style_mode_defaults(
                    configuration
                ).presentation_mode,
            )
        raise ValueError(
            f"Unknown chart mode {mode!r}. Use 'print', 'paper', or "
            "'presentation'."
        )

    from .modes import PresentationMode

    if isinstance(mode, PresentationMode):
        name = PRESENTATION_MODE
    elif isinstance(mode, PrintMode):
        name = PRINT_MODE
    else:
        name = "custom"
    return name, mode


@dataclass(frozen=True)
class ChartComposition:
    """Resolved, output-neutral inputs for a chart rendering operation."""

    context: ChartContext
    style: Any
    mode: ResolvedMode
    detail: ResolvedDetail
    style_name: str = "custom"
    mode_name: str = "custom"
    legends: ResolvedLegendOptions | None = None
    furniture: ResolvedChartFurnitureOptions | None = None
    configuration: Any | None = None

    def layer_options(
        self,
        sky,
        *,
        overrides=None,
        reload_catalogues=True,
    ):
        """Apply detail and return options ready for ``draw_chart``."""
        from .detail_application import composition_layer_options

        return composition_layer_options(
            self,
            sky,
            layer_options=overrides,
            reload_catalogues=reload_catalogues,
        )


def compose_chart(
    chart,
    *,
    style,
    mode: ChartMode | str | None = None,
    detail: DetailPolicy | None = None,
    detail_overrides: DetailOverrides | None = None,
    style_overrides: ChartStyleOverrides | None = None,
    legends: LegendOptions | ChartLegendPlan | None = None,
    furniture: ChartFurnitureOptions | None = None,
    configuration=None,
) -> ChartComposition:
    """Resolve independent chart concerns without rendering the chart."""
    if configuration is not None:
        from wenu.configuration import ConfigurationDefaults

        if not isinstance(configuration, ConfigurationDefaults):
            raise TypeError(
                "configuration must be a ConfigurationDefaults value."
            )
    style_defaults = _resolved_style_mode_defaults(configuration)
    geometry_defaults = _resolved_geometry_detail_defaults(configuration)
    context = chart.chart_context
    named_style = isinstance(style, str)
    style_name, resolved_style = _resolve_style(
        style,
        configuration=configuration,
    )
    mode_name, mode_policy = _resolve_mode(
        mode,
        configuration=configuration,
    )
    if not callable(getattr(mode_policy, "resolve", None)):
        raise TypeError("mode must provide resolve() or be a known mode name.")
    resolved_mode = mode_policy.resolve(context)
    if style_name == ATLAS_STYLE and mode_name in {
        PRINT_MODE,
        PRESENTATION_MODE,
    }:
        from .atlas_modes import atlas_chart_style

        resolved_style = atlas_chart_style(
            resolved_mode,
            base=resolved_style,
            mode_name=mode_name,
            presentation_palette=(
                style_defaults.atlas_presentation_palette
            ),
        )
    elif style_name == CARTOON_STYLE and mode_name in {
        PRINT_MODE,
        PRESENTATION_MODE,
    }:
        from .cartoon_modes import (
            CartoonModeChartStyle,
            cartoon_chart_style,
        )

        already_resolved = (
            isinstance(resolved_style, CartoonModeChartStyle)
            and resolved_style.output_mode_name == mode_name
        )
        if not already_resolved:
            resolved_style = cartoon_chart_style(
                resolved_mode,
                base=resolved_style,
                mode_name=mode_name,
                palette=(
                    style_defaults.cartoon_presentation_palette
                    if mode_name == PRESENTATION_MODE
                    else style_defaults.cartoon_print_palette
                ),
                constellation_label_offset=(
                    style_defaults.cartoon_label_offset
                ),
                constellation_label_clearance=(
                    style_defaults.cartoon_label_clearance
                ),
                constellation_label_halo_opacity=(
                    style_defaults.cartoon_label_halo_opacity
                ),
            )
    if (
        getattr(chart, "chart_type", None) == "polar_planisphere"
        and style_name == ATLAS_STYLE
        and mode_name == PRINT_MODE
    ):
        from .polar_planisphere_style import polar_planisphere_chart_style

        resolved_style = polar_planisphere_chart_style(
            resolved_style,
            style_defaults.polar_planisphere_palette,
        )
    if (
        getattr(chart, "chart_type", None) == "all_sky"
        and style_name in {ATLAS_STYLE, CARTOON_STYLE}
    ):
        resolved_style = replace(
            resolved_style,
            stars=replace(
                resolved_style.stars,
                area_scale=resolved_style.stars.area_scale * 0.25,
            ),
        )
    if (
        type(chart).__name__ == "BinocularChart"
        and named_style
    ):
        resolved_style = replace(
            resolved_style,
            stars=replace(
                resolved_style.stars,
                magnitude_sizing=(
                    geometry_defaults.binocular_stellar_sizing
                ),
            ),
        )
    if style_overrides is not None:
        if not isinstance(style_overrides, ChartStyleOverrides):
            raise TypeError(
                "style_overrides must be a ChartStyleOverrides value."
            )
        resolved_style = style_overrides.apply(resolved_style)
    family_atlas_default = False
    if detail is None and style_name == CARTOON_STYLE:
        policy = geometry_defaults.cartoon_policy
    elif detail is None and named_style and style_name == ATLAS_STYLE:
        policy = _family_atlas_policy(chart, geometry_defaults)
        family_atlas_default = True
    else:
        policy = (
            FixedDetailPolicy(geometry_defaults.neutral_detail)
            if detail is None
            else detail
        )
    detail_mode = (
        replace(resolved_mode, font_scale=1.0, symbol_scale=1.0)
        if family_atlas_default
        else resolved_mode
    )
    resolved_detail = apply_detail_overrides(
        policy.resolve(context, detail_mode),
        detail_overrides,
        default_content_layers=(
            geometry_defaults.default_content_layers
        ),
    )
    if furniture is not None and legends is not None:
        raise ValueError("Pass legends through furniture or legends, not both.")
    if furniture is not None:
        if not isinstance(furniture, ChartFurnitureOptions):
            raise TypeError("furniture must be a ChartFurnitureOptions value.")
        resolved_furniture = furniture.resolve(chart_type_name(chart))
        resolved_legends = resolved_furniture.legends
    else:
        resolved_furniture = None
        if legends is None:
            resolved_legends = None
        else:
            if isinstance(legends, ChartLegendPlan):
                legends = LegendOptions(plan=legends)
            resolved_legends = legends.resolve(chart_type_name(chart))
    return ChartComposition(
        context=context,
        style=resolved_style,
        mode=resolved_mode,
        detail=resolved_detail,
        style_name=style_name,
        mode_name=mode_name,
        legends=resolved_legends,
        furniture=resolved_furniture,
        configuration=configuration,
    )
