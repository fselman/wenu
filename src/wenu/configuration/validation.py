"""Strict validation for Wenu schema-version-1 configuration data."""

from __future__ import annotations

from copy import deepcopy
from importlib.resources import files
from math import isfinite
from pathlib import Path
import re
from typing import Any, Mapping

from matplotlib.colors import is_color_like

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10
    import tomli as tomllib


SCHEMA_VERSION = 1
LINE_STYLES = frozenset(
    {"solid", "dashed", "dotted", "dash_dot", "none"}
)
LEGEND_LOCATIONS = frozenset(
    {
        "none",
        "upper left",
        "upper right",
        "lower left",
        "lower right",
        "upper left outside",
        "upper right outside",
        "lower left outside",
        "lower right outside",
    }
)


class ConfigurationError(ValueError):
    """A configuration value failed schema-version-1 validation."""


_OPTIONAL_NUMBERS = frozenset(
    {
        "observer.elevation",
        "sequence.playback_duration",
        "sequence.frames_per_second",
        "families.regional_single.width",
        "families.regional_single.height",
        "families.regional_group.width",
        "families.regional_group.height",
        "families.regional_single.position_angle",
        "families.regional_group.position_angle",
        "families.binocular.position_angle",
        "detail.neutral.star_magnitude_limit",
        "detail.neutral.galaxy_magnitude_limit",
        "detail.neutral.open_cluster_minimum_size",
        "detail.neutral.globular_cluster_minimum_size",
        "detail.neutral.planetary_nebula_minimum_size",
        "detail.neutral.supernova_remnant_minimum_size",
        "modes.base.height",
        "furniture.magnitude_legend.font_size",
        "furniture.magnitude_legend.title_font_size",
    }
)
_OPTIONAL_INTEGERS = frozenset({
    "detail.neutral.extended_samples",
    "sequence.frames",
})
_OPTIONAL_LISTS = frozenset(
    {
        "detail.neutral.enabled_layers",
        "grids_references.coordinate_grid.requested_longitudes",
        "grids_references.coordinate_grid.requested_latitudes",
    }
)
_OPTIONAL_POINTS = frozenset({"grids_references.references.anchor"})
_STRING_LISTS = frozenset(
    {
        "detail.neutral.grid_label_layers",
        "detail.polar_planisphere.enabled_layers",
    }
)
_INTEGER_LISTS = frozenset(
    {"detail.neutral.extra_stars", "detail.cartoon.extra_stars"}
)
_NUMBER_LISTS = frozenset(
    {
        "grids_references.coordinate_grid.requested_longitudes",
        "grids_references.coordinate_grid.requested_latitudes",
    }
)
_POINTS = frozenset(
    {
        "modes.cartoon.label_offset",
        "modes.cartoon.clearance",
    }
)
_POSITIVE_NAMES = frozenset(
    {
        "dpi",
        "samples",
        "width",
        "height",
        "field_diameter",
        "reference_width",
        "span",
        "font_size",
        "title_font_size",
        "label_font_size",
        "symbol_size",
        "symbol_dot_size",
        "magnitude_scale",
        "scale",
        "minimum_area",
        "maximum_area",
        "label_density",
        "font_scale",
        "line_scale",
        "symbol_scale",
        "contrast_scale",
        "area_scale",
        "columns",
        "symbol_dots",
    }
)
_NONNEGATIVE_NAMES = frozenset(
    {
        "line_width",
        "edge_width",
        "z_order",
        "padding",
        "border_padding",
        "label_spacing",
        "handle_text_padding",
        "magnitude_exponent",
        "exponent",
        "magnitude_adjustment_per_octave",
        "maximum_adjustment",
    }
)
_ENUMS = {
    "sequence.restart_policy": {"restart", "resume"},
    "families.all_sky.projection": {"mollweide"},
    "families.all_sky.coordinate_frame": {"galactic"},
    "families.planisphere.projection": {"stereographic"},
    "families.planisphere.coordinate_frame": {"horizontal"},
    "families.regional_single.projection": {"stereographic"},
    "families.regional_single.coordinate_frame": {"horizontal"},
    "families.regional_group.projection": {"stereographic"},
    "families.regional_group.coordinate_frame": {"horizontal"},
    "families.circumpolar.projection": {"stereographic"},
    "families.circumpolar.coordinate_frame": {"horizontal"},
    "families.circumpolar.pole": {"north", "south"},
    "families.binocular.projection": {"stereographic"},
    "families.binocular.coordinate_frame": {"horizontal"},
    "detail.cartoon.star_mode": {"selected", "all", "none"},
    "detail.polar_planisphere.constellation_star_mode": {"none"},
    "detail.binocular_stellar_sizing.reference": {
        "fixed",
        "limiting_magnitude",
    },
    "products.default.style": {"atlas", "cartoon"},
    "products.default.mode": {"print", "presentation"},
    "products.default.language": {"en", "es"},
    "export.bounding_box": {"tight", "standard"},
    "grids_references.references.state": {"none", "line", "labeled"},
    "grids_references.poles.state": {"none", "visible", "both"},
}

for _family in (
    "all_sky", "planisphere", "regional_single", "regional_group",
    "circumpolar", "binocular",
):
    _ENUMS[f"families.{_family}.orientation"] = {
        "none", "celestial-north-up", "zenith-up"
    }


def _error(path: str, message: str) -> None:
    raise ConfigurationError(f"{path}: {message}")


def _resource_text() -> str:
    return files("wenu.configuration").joinpath("defaults.toml").read_text(
        encoding="utf-8"
    )


def _parse(text: str, *, source: str) -> dict[str, Any]:
    try:
        value = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        _error(source, f"invalid TOML: {error}")
    if not isinstance(value, dict):  # pragma: no cover - tomllib contract
        _error(source, "root must be a table")
    return value


def _path(parts: tuple[str, ...]) -> str:
    return ".".join(parts) if parts else "configuration"


def _is_number(value: Any) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and isfinite(float(value))
    )


def _validate_leaf_type(value: Any, exemplar: Any, parts: tuple[str, ...]):
    path = _path(parts)
    if path in _OPTIONAL_NUMBERS or path.endswith(".stars.maximum_area"):
        if value != "none" and not _is_number(value):
            _error(path, "expected a finite number or \"none\"")
        return
    if path in _OPTIONAL_INTEGERS:
        if value != "none" and (
            isinstance(value, bool) or not isinstance(value, int)
        ):
            _error(path, "expected an integer or \"none\"")
        return
    if path in _OPTIONAL_LISTS:
        if value != "none" and not isinstance(value, list):
            _error(path, "expected an array or \"none\"")
        if (
            value != "none"
            and path == "detail.neutral.enabled_layers"
            and not all(isinstance(item, str) for item in value)
        ):
            _error(path, "array values must be strings")
        if (
            value != "none"
            and path in _NUMBER_LISTS
            and not all(_is_number(item) for item in value)
        ):
            _error(path, "array values must be finite numbers")
        return
    if path in _OPTIONAL_POINTS:
        if value != "none" and not (
            isinstance(value, list)
            and len(value) == 2
            and all(_is_number(item) for item in value)
        ):
            _error(path, "expected a two-number point or \"none\"")
        return
    if isinstance(exemplar, bool):
        if not isinstance(value, bool):
            _error(path, "expected a boolean")
    elif isinstance(exemplar, int):
        if isinstance(value, bool) or not isinstance(value, int):
            _error(path, "expected an integer")
    elif isinstance(exemplar, float):
        if not _is_number(value):
            _error(path, "expected a finite number")
    elif isinstance(exemplar, str):
        if not isinstance(value, str):
            _error(path, "expected a string")
    else:  # pragma: no cover - the packaged schema uses known TOML types
        _error(path, f"unsupported schema exemplar {type(exemplar).__name__}")


def _validate_shape(
    value: Any,
    exemplar: Any,
    parts: tuple[str, ...],
    *,
    complete: bool,
) -> None:
    path = _path(parts)
    if isinstance(exemplar, dict):
        if not isinstance(value, dict):
            _error(path, "expected a table")
        if path == "export.metadata":
            for key, item in value.items():
                if not isinstance(key, str) or not isinstance(item, str):
                    _error(f"{path}.{key}", "expected a string")
            return
        for key in value:
            if key not in exemplar:
                _error(f"{path}.{key}", "unknown configuration key")
        if complete:
            for key in exemplar:
                if key not in value:
                    _error(f"{path}.{key}", "missing required key")
            if tuple(value) != tuple(exemplar):
                _error(path, "keys are not in deterministic schema order")
        for key, item in value.items():
            _validate_shape(
                item,
                exemplar[key],
                (*parts, key),
                complete=complete,
            )
        return
    if isinstance(exemplar, list):
        if not isinstance(value, list):
            _error(path, "expected an array")
        if exemplar:
            for index, item in enumerate(value):
                _validate_shape(
                    item,
                    exemplar[0],
                    (*parts, str(index)),
                    complete=complete,
                )
        if path in _STRING_LISTS and not all(
            isinstance(item, str) for item in value
        ):
            _error(path, "array values must be strings")
        if path in _NUMBER_LISTS and not all(
            _is_number(item) for item in value
        ):
            _error(path, "array values must be finite numbers")
        if path in _INTEGER_LISTS and not all(
            not isinstance(item, bool) and isinstance(item, int)
            for item in value
        ):
            _error(path, "array values must be integers")
        if path in _POINTS and len(value) != 2:
            _error(path, "must contain exactly two numbers")
        return
    _validate_leaf_type(value, exemplar, parts)


def _walk(value: Any, parts: tuple[str, ...] = ()):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _walk(item, (*parts, key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk(item, (*parts, str(index)))
    else:
        yield parts, value


def _is_color_path(parts: tuple[str, ...]) -> bool:
    if not parts or "styles" not in parts:
        return False
    leaf = parts[-1]
    if leaf in {"background", "foreground", "sky"}:
        return True
    if leaf == "color" or leaf.endswith("_color"):
        return True
    return "palettes" in parts and len(parts) >= 4


def _validate_color(value: Any, parts: tuple[str, ...]) -> None:
    path = _path(parts)
    if not isinstance(value, str):
        _error(path, "expected a color string")
    if value in {"none", "inherit_canvas"}:
        return
    if not is_color_like(value):
        _error(path, f"invalid color {value!r}")


def _validate_semantics(configuration: Mapping[str, Any]) -> None:
    if configuration.get("schema_version") != SCHEMA_VERSION:
        _error(
            "schema_version",
            f"unsupported value {configuration.get('schema_version')!r}; "
            f"expected {SCHEMA_VERSION}",
        )

    for parts, value in _walk(configuration):
        path = _path(parts)
        leaf = parts[-1]
        if leaf == "line_style" and value not in LINE_STYLES:
            expected = ", ".join(sorted(LINE_STYLES))
            _error(path, f"unsupported value {value!r}; expected {expected}")
        if _is_color_path(parts):
            _validate_color(value, parts)
        if path in _ENUMS and value not in _ENUMS[path]:
            expected = ", ".join(sorted(_ENUMS[path]))
            _error(path, f"unsupported value {value!r}; expected {expected}")
        if _is_number(value):
            number = float(value)
            if (
                leaf in {"opacity", "halo_opacity"}
                and not 0.0 <= number <= 1.0
            ):
                _error(path, "must be in the interval [0, 1]")
            if leaf in _POSITIVE_NAMES and number <= 0.0:
                _error(path, "must be positive")
            if (
                leaf.endswith("_samples")
                or leaf.endswith("_minimum_size")
                or leaf == "minimum_size_arcmin"
            ) and number <= 0.0:
                _error(path, "must be positive")
            if leaf in _NONNEGATIVE_NAMES and number < 0.0:
                _error(path, "cannot be negative")
            if leaf in {
                "limiting_declination",
                "meridian_declination_minimum",
                "meridian_declination_maximum",
            } and not -90.0 <= number <= 90.0:
                _error(path, "must be in the interval [-90, 90]")

    sequence = configuration["sequence"]
    enabled = sequence["stop"] != "none"
    if enabled != (sequence["frames"] != "none"):
        _error(
            "sequence.frames",
            "stop and frames must both be \"none\" or both be configured",
        )
    playback_enabled = sequence["playback_duration"] != "none"
    if playback_enabled != (sequence["frames_per_second"] != "none"):
        _error(
            "sequence.frames_per_second",
            "playback duration and frame rate must both be \"none\" or "
            "both be configured",
        )
    if not enabled and playback_enabled:
        _error(
            "sequence.playback_duration",
            "playback requires a configured observer-time sequence",
        )
    if sequence["frames"] != "none" and sequence["frames"] < 2:
        _error("sequence.frames", "must be at least 2")
    for name in ("playback_duration", "frames_per_second"):
        value = sequence[name]
        if value != "none" and value <= 0:
            _error(f"sequence.{name}", "must be positive")
    if playback_enabled and round(
        sequence["playback_duration"] * sequence["frames_per_second"]
    ) != sequence["frames"]:
        _error(
            "sequence.frames_per_second",
            "playback duration and frame rate must imply sequence frames",
        )

    samples = configuration["grids_references"]["coordinate_grid"]["samples"]
    if samples % 2 == 0:
        _error("grids_references.coordinate_grid.samples", "must be odd")

    field = configuration["families"]["binocular"]["field_diameter"]
    if field > 180.0:
        _error("families.binocular.field_diameter", "cannot exceed 180")

    extension = configuration["products"]["default"]["extension"]
    if not re.fullmatch(r"\.[A-Za-z0-9]+", extension):
        _error(
            "products.default.extension",
            "must begin with '.' and contain only letters or digits",
        )

    for family in ("regional_single", "regional_group"):
        geometry = configuration["families"][family]
        width_none = geometry["width"] == "none"
        height_none = geometry["height"] == "none"
        if width_none != height_none:
            _error(
                f"families.{family}.height",
                "width and height must both be \"none\" or both be numbers",
            )

    for family in ("regional_single", "regional_group", "binocular"):
        geometry = configuration["families"][family]
        named = geometry["orientation"] != "none"
        angled = geometry["position_angle"] != "none"
        if named == angled:
            _error(
                f"families.{family}.orientation",
                "specify exactly one of orientation or position_angle",
            )

    for family in ("all_sky", "planisphere", "circumpolar"):
        geometry = configuration["families"][family]
        if geometry["orientation"] != "none":
            _error(
                f"families.{family}.orientation",
                "named orientation is not supported by this family",
            )

    circumpolar = configuration["families"]["circumpolar"]
    declination = circumpolar["limiting_declination"]
    if circumpolar["pole"] == "south" and declination >= 0.0:
        _error(
            "families.circumpolar.limiting_declination",
            "must be negative for the south pole",
        )
    if circumpolar["pole"] == "north" and declination <= 0.0:
        _error(
            "families.circumpolar.limiting_declination",
            "must be positive for the north pole",
        )

    for name, subject in configuration["subjects"].items():
        kind = subject["kind"]
        allowed = {
            "all_sky": {"none"},
            "planisphere": {"none"},
            "regional_single": {"constellations"},
            "regional_group": {"constellations", "group"},
            "circumpolar": {"none"},
            "binocular": {"target"},
        }[name]
        if kind not in allowed:
            _error(
                f"subjects.{name}.kind",
                f"unsupported value {kind!r}; expected "
                f"{', '.join(sorted(allowed))}",
            )
        constellations = subject.get("constellations")
        if constellations is not None:
            if len(constellations) != len(set(constellations)):
                _error(
                    f"subjects.{name}.constellations",
                    "identifiers must be unique",
                )
            if kind == "constellations" and not constellations:
                _error(
                    f"subjects.{name}.constellations",
                    "must not be empty for kind \"constellations\"",
                )
        if name == "regional_group":
            group = subject["group"]
            if kind == "group" and group == "none":
                _error("subjects.regional_group.group", "must name a group")
            if kind == "group" and constellations:
                _error(
                    "subjects.regional_group.constellations",
                    "must be empty when kind is \"group\"",
                )
            if kind == "constellations" and group != "none":
                _error(
                    "subjects.regional_group.group",
                    "must be \"none\" when kind is \"constellations\"",
                )

    levels = configuration["detail"]["adaptive"]["levels"]
    spans = [float(level["span"]) for level in levels]
    if spans != sorted(spans) or len(spans) != len(set(spans)):
        _error(
            "detail.adaptive.levels",
            "span values must be strictly increasing",
        )

    sizing = configuration["detail"]["binocular_stellar_sizing"]
    if sizing["maximum_area"] != "none" and (
        sizing["maximum_area"] < sizing["minimum_area"]
    ):
        _error(
            "detail.binocular_stellar_sizing.maximum_area",
            "must be at least minimum_area",
        )

    for style_name in ("atlas", "cartoon"):
        stars = configuration["styles"][style_name]["stars"]
        maximum = stars["maximum_area"]
        if maximum != "none" and maximum < stars["minimum_area"]:
            _error(
                f"styles.{style_name}.stars.maximum_area",
                "must be at least minimum_area",
            )
        legend = configuration["styles"][style_name]["legend"]
        if legend["visible"] and legend["location"] == "none":
            _error(
                f"styles.{style_name}.legend.location",
                "must name a location when the legend is visible",
            )

    magnitude_legend = configuration["furniture"]["magnitude_legend"]
    if magnitude_legend["location"] not in LEGEND_LOCATIONS:
        _error(
            "furniture.magnitude_legend.location",
            f"unsupported value {magnitude_legend['location']!r}",
        )
    if magnitude_legend["enabled"] and magnitude_legend["location"] == "none":
        _error(
            "furniture.magnitude_legend.location",
            "must name a location when the legend is enabled",
        )

    legends = configuration["furniture"]["legends"]
    for family in (
        "regional", "planisphere", "all_sky", "circumpolar", "binocular"
    ):
        for name in ("objects_location", "stars_location"):
            location = legends[family][name]
            if location not in LEGEND_LOCATIONS:
                _error(
                    f"furniture.legends.{family}.{name}",
                    f"unsupported value {location!r}",
                )

    references = configuration["grids_references"]["references"]
    if references["state"] == "labeled":
        for name in (
            "equatorial_label",
            "ecliptic_label",
            "galactic_label",
        ):
            if not references[name].strip():
                _error(
                    f"grids_references.references.{name}",
                    "must not be empty when references are labeled",
                )

    grid = configuration["grids_references"]["coordinate_grid"]
    if grid["meridian_declination_minimum"] >= grid[
        "meridian_declination_maximum"
    ]:
        _error(
            "grids_references.coordinate_grid.meridian_declination_maximum",
            "must exceed meridian_declination_minimum",
        )

    footer = configuration["furniture"]["footer"]
    for name in ("y", "left_x", "right_x"):
        if not 0.0 <= footer[name] <= 1.0:
            _error(f"furniture.footer.{name}", "must be in [0, 1]")
    if footer["left_x"] >= footer["right_x"]:
        _error("furniture.footer.right_x", "must exceed left_x")


def validate_configuration(
    configuration: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate and return one schema-version-1 configuration mapping."""
    if not isinstance(configuration, Mapping):
        _error("configuration", "root must be a table")
    value = dict(configuration)
    exemplar = _parse(_resource_text(), source="packaged defaults")
    _validate_shape(value, exemplar, (), complete=True)
    _validate_semantics(value)
    return value


def validate_configuration_overlay(
    overlay: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate and return one partial schema-version-1 overlay mapping."""
    if not isinstance(overlay, Mapping):
        _error("configuration", "root must be a table")
    value = dict(overlay)
    exemplar = _parse(_resource_text(), source="packaged defaults")
    _validate_shape(value, exemplar, (), complete=False)
    if "schema_version" not in value:
        _error("schema_version", "missing required overlay key")
    if value["schema_version"] != SCHEMA_VERSION:
        _error(
            "schema_version",
            f"unsupported value {value['schema_version']!r}; "
            f"expected {SCHEMA_VERSION}",
        )
    return value


def merge_configuration_overlay(
    packaged: Mapping[str, Any],
    overlay: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a validated recursive merge without mutating either input."""
    base = validate_configuration(packaged)
    partial = validate_configuration_overlay(overlay)

    def merge(left, right):
        result = deepcopy(left)
        for key, value in right.items():
            if isinstance(value, dict):
                result[key] = merge(result[key], value)
            else:
                result[key] = deepcopy(value)
        return result

    return validate_configuration(merge(base, partial))


def parse_configuration(
    text: str,
    *,
    source: str = "configuration",
) -> dict[str, Any]:
    """Parse and strictly validate one complete TOML configuration."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    return validate_configuration(_parse(text, source=source))


def parse_configuration_overlay(
    text: str,
    *,
    source: str = "user configuration",
) -> dict[str, Any]:
    """Parse and validate one partial schema-version-1 TOML overlay."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    return validate_configuration_overlay(_parse(text, source=source))


def load_packaged_defaults() -> dict[str, Any]:
    """Load and strictly validate a fresh packaged default mapping."""
    return parse_configuration(_resource_text(), source="packaged defaults")


def load_configuration(path=None) -> dict[str, Any]:
    """Load packaged defaults with an optional partial user TOML overlay."""
    packaged = load_packaged_defaults()
    if path is None:
        return packaged
    source = Path(path)
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as error:
        raise ConfigurationError(
            f"user configuration {source}: {error}"
        ) from error
    overlay = parse_configuration_overlay(
        text,
        source=f"user configuration {source}",
    )
    return merge_configuration_overlay(packaged, overlay)
