"""Resolution and load-profile validation for declarative chart requests."""

from __future__ import annotations

from dataclasses import dataclass, fields, replace

from wenu.sky.maximal_sphere import CelestialSphereLoadProfile
from wenu.sky.milky_way import MilkyWayIsophotes

from .constellation_resolver import (
    ResolvedConstellationSubject,
    resolve_constellation_subject,
)
from .detail import SkyContentSelection
from .request import EXCLUDABLE_CATALOGUE_FAMILIES, ChartRequest
from .target_resolver import ResolvedTarget, resolve_target
from .view_defaults import chart_view_defaults


SUPPORTED_TARGET_FAMILIES = frozenset(
    {
        "nonstellar_objects",
        "galaxies",
        "open_clusters",
        "globular_clusters",
        "planetary_nebulae",
        "supernova_remnants",
    }
)


@dataclass(frozen=True)
class ResolvedChartRequest:
    """One request with resolved subject and validated content selection."""

    request: ChartRequest
    target: ResolvedTarget | None = None
    constellations: ResolvedConstellationSubject | None = None
    frame: "ResolvedChartFrame | None" = None


@dataclass(frozen=True)
class ResolvedChartFrame:
    """Effective family framing, retaining whether geometry must derive it."""

    field_diameter_deg: float | None = None
    field_width_deg: float | None = None
    field_height_deg: float | None = None
    position_angle_deg: float = 0.0
    pole: str | None = None
    limiting_declination_deg: float | None = None
    automatic_from_geometry: bool = False
    source: str = "request"


def _resolve_frame(request, constellations):
    frame = request.frame
    if request.family == "binocular":
        return ResolvedChartFrame(
            field_diameter_deg=(
                chart_view_defaults("binocular").field_diameter_deg
                if frame.field_diameter_deg is None
                else frame.field_diameter_deg
            ),
            position_angle_deg=frame.position_angle_deg,
            source=(
                "family-default" if frame.field_diameter_deg is None
                else "request"
            ),
        )
    if request.family == "regional":
        if frame.field_width_deg is not None:
            return ResolvedChartFrame(
                field_width_deg=frame.field_width_deg,
                field_height_deg=frame.field_height_deg,
                position_angle_deg=frame.position_angle_deg,
            )
        if constellations.field_width_deg is not None:
            return ResolvedChartFrame(
                field_width_deg=constellations.field_width_deg,
                field_height_deg=constellations.field_height_deg,
                position_angle_deg=frame.position_angle_deg,
                source="packaged-group",
            )
        return ResolvedChartFrame(
            position_angle_deg=frame.position_angle_deg,
            automatic_from_geometry=True,
            source="constellation-geometry",
        )
    if request.family == "circumpolar":
        return ResolvedChartFrame(
            position_angle_deg=frame.position_angle_deg,
            pole=frame.pole,
            limiting_declination_deg=frame.limiting_declination_deg,
            source="chart-family",
        )
    return ResolvedChartFrame(
        position_angle_deg=frame.position_angle_deg,
        source="chart-family",
    )


def _union(current, additions):
    if not additions:
        return current
    return frozenset(additions) if current is None else current | additions


def _resolved_content(request, *, target=None, constellations=None):
    values = {
        field.name: getattr(request.content, field.name)
        for field in fields(SkyContentSelection)
    }
    if values["milky_way_levels"] is None:
        values["milky_way_levels"] = frozenset(
            MilkyWayIsophotes.default_levels
        )
    if target is not None:
        for component in target.components:
            values[component.family] = _union(
                values[component.family], {component.identifier}
            )
    if constellations is not None:
        values["constellation_lines"] = _union(
            values["constellation_lines"],
            constellations.line_constellations,
        )
        values["constellation_boundaries"] = _union(
            values["constellation_boundaries"],
            constellations.boundary_constellations,
        )
        values["constellation_labels"] = _union(
            values["constellation_labels"],
            constellations.label_constellations,
        )
        for name in (
            "open_clusters",
            "planetary_nebulae",
            "supernova_remnants",
        ):
            values[name] = _union(
                values[name], getattr(constellations, name)
            )
    for name in EXCLUDABLE_CATALOGUE_FAMILIES:
        selected = values[name]
        excluded = getattr(request.exclusions, name)
        if selected is not None:
            values[name] = selected - excluded
    return SkyContentSelection(**values)


def _validate_exclusions(request, target):
    for name in EXCLUDABLE_CATALOGUE_FAMILIES:
        included = getattr(request.content, name)
        excluded = getattr(request.exclusions, name)
        overlap = frozenset() if included is None else included & excluded
        if overlap:
            identifiers = ", ".join(sorted(overlap))
            raise ValueError(
                f"{name} cannot both include and exclude: {identifiers}."
            )
    if target is not None:
        for component in target.components:
            if component.identifier in getattr(
                request.exclusions, component.family
            ):
                raise ValueError(
                    "The central target cannot be excluded from its "
                    f"catalogue family: {component.identifier}."
                )


def resolve_chart_request(request, profile):
    """Resolve a request and reject content unavailable to its load profile."""
    if not isinstance(request, ChartRequest):
        raise TypeError("request must be a ChartRequest.")
    if not isinstance(profile, CelestialSphereLoadProfile):
        raise TypeError("profile must be a CelestialSphereLoadProfile.")

    target = None
    constellations = None
    if request.subject.target is not None or request.subject.ra_deg is not None:
        target = resolve_target(request.subject)
        if request.subject.target is not None and not target.components:
            raise ValueError(
                f"Target {target.display_name!r} has no drawable catalogue "
                "representation."
            )
        unsupported = target.required_families - SUPPORTED_TARGET_FAMILIES
        if unsupported:
            names = ", ".join(sorted(unsupported))
            raise ValueError(
                f"Target requires unsupported catalogue family: {names}."
            )
    elif (
        request.subject.constellations is not None
        or request.subject.group is not None
    ):
        constellations = resolve_constellation_subject(request.subject)

    profile.require(
        star_magnitude_limit=request.detail.star_magnitude_limit,
        galaxy_magnitude_limit=request.detail.galaxy_magnitude_limit,
        extended_object_samples=request.detail.extended_object_samples,
    )
    _validate_exclusions(request, target)
    content = _resolved_content(
        request,
        target=target,
        constellations=constellations,
    )
    return ResolvedChartRequest(
        request=replace(request, content=content),
        target=target,
        constellations=constellations,
        frame=_resolve_frame(request, constellations),
    )
