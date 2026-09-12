"""Explicit named-center parsing and offline namespace resolution."""

from __future__ import annotations

from dataclasses import dataclass
import argparse
import re

from wenu.sky.solar_system_bodies import SolarSystemBodyDescriptor
from wenu.sky.solar_system_catalog import SOLAR_SYSTEM_BODY_CATALOG

from .constellation_resolver import (
    IAU_CONSTELLATIONS,
    ResolvedConstellationSubject,
    resolve_constellation_subject,
)
from .request import ChartSubjectRequest
from .target_resolver import ResolvedTarget, resolve_target


_TARGET_FAMILIES = {
    "star": frozenset({"stars"}),
    "galaxy": frozenset({"galaxies"}),
    "cluster": frozenset({"open_clusters", "globular_clusters"}),
    "nebula": frozenset({
        "nonstellar_objects",
        "planetary_nebulae",
        "supernova_remnants",
    }),
}
_QUALIFIERS = frozenset({
    "constellation", "group", "planet", "moon", "asteroid", "target",
    *_TARGET_FAMILIES,
})


def _angle(value, *, right_ascension=False):
    from astropy import units as u
    from astropy.coordinates import Angle

    text = str(value).strip()
    if not text:
        raise argparse.ArgumentTypeError("center angle cannot be empty")
    hour_angle = bool(re.search(r"[hms]", text, re.IGNORECASE))
    degree_angle = text.casefold().endswith(("deg", "degree", "degrees"))
    if right_ascension:
        if not hour_angle and not degree_angle:
            raise argparse.ArgumentTypeError(
                "ICRS right ascension requires hour-angle or degree units"
            )
    elif not degree_angle:
        raise argparse.ArgumentTypeError(
            "center angle requires explicit degree units"
        )
    try:
        return float(Angle(text, unit=u.hourangle if hour_angle else u.deg).degree)
    except (TypeError, ValueError) as error:
        raise argparse.ArgumentTypeError(str(error)) from error


def parse_icrs_ra(value):
    """Parse an explicitly unit-bearing ICRS right ascension."""
    return _angle(value, right_ascension=True) % 360.0


def parse_degree_angle(value):
    """Parse an explicitly degree-bearing spherical angle."""
    return _angle(value)


@dataclass(frozen=True)
class ResolvedNamedCenter:
    """One uniquely resolved named center from an explicit namespace."""

    kind: str
    identifier: str
    value: ResolvedConstellationSubject | ResolvedTarget | SolarSystemBodyDescriptor

    @property
    def is_constellation(self):
        return isinstance(self.value, ResolvedConstellationSubject)

    @property
    def is_point(self):
        return isinstance(
            self.value, (ResolvedTarget, SolarSystemBodyDescriptor)
        )


def _parts(specification):
    text = str(specification).strip()
    if not text:
        raise ValueError("center-on identifier cannot be empty.")
    if ":" not in text:
        return None, text
    qualifier, identifier = text.split(":", 1)
    qualifier = qualifier.strip().casefold()
    identifier = identifier.strip()
    if qualifier not in _QUALIFIERS:
        raise ValueError(f"unknown center namespace {qualifier!r}.")
    if not identifier:
        raise ValueError("center-on identifier cannot be empty.")
    return qualifier, identifier


def _constellation(identifier, *, group=False):
    values = None if group else tuple(
        item.strip() for item in identifier.split(",") if item.strip()
    )
    return resolve_constellation_subject(ChartSubjectRequest(
        constellations=values,
        group=identifier if group else None,
    ))


def _target(identifier, qualifier="target"):
    target = resolve_target(ChartSubjectRequest(target=identifier))
    families = _TARGET_FAMILIES.get(qualifier)
    if families is not None and not (target.required_families & families):
        raise ValueError(
            f"{identifier!r} is not a packaged {qualifier} target."
        )
    return target


def _body(identifier, qualifier, minor_body_collection=None):
    descriptor = None
    try:
        descriptor = SOLAR_SYSTEM_BODY_CATALOG.resolve(identifier)
    except KeyError:
        if minor_body_collection is not None:
            try:
                descriptor = minor_body_collection.resolve(identifier)
            except KeyError:
                pass
    if descriptor is None:
        raise ValueError(f"unknown {qualifier} center {identifier!r}.")
    expected = {
        "planet": "planet",
        "moon": "natural_satellite",
        "asteroid": "asteroid",
    }[qualifier]
    if descriptor.body_class != expected:
        raise ValueError(f"{identifier!r} is not a {qualifier}.")
    if descriptor.selection_key == "earth":
        raise ValueError("Earth is the observer origin, not a chart center.")
    return descriptor


def _qualified(qualifier, identifier, minor_body_collection=None):
    if qualifier == "constellation":
        return _constellation(identifier)
    if qualifier == "group":
        return _constellation(identifier, group=True)
    if qualifier in {"planet", "moon", "asteroid"}:
        return _body(identifier, qualifier, minor_body_collection)
    return _target(identifier, qualifier)


def resolve_named_center(specification, *, minor_body_collection=None):
    """Resolve one qualified or globally unique offline center name."""
    qualifier, identifier = _parts(specification)
    if qualifier is not None:
        return ResolvedNamedCenter(
            qualifier,
            identifier,
            _qualified(qualifier, identifier, minor_body_collection),
        )

    matches = []
    if identifier.casefold() in {
        value.casefold() for value in IAU_CONSTELLATIONS
    }:
        matches.append(("constellation", _constellation(identifier)))
    for kind, resolver in (
        ("group", lambda: _constellation(identifier, group=True)),
        ("target", lambda: _target(identifier)),
        ("planet", lambda: _body(identifier, "planet")),
        ("moon", lambda: _body(identifier, "moon")),
        ("asteroid", lambda: _body(
            identifier, "asteroid", minor_body_collection
        )),
    ):
        try:
            value = resolver()
        except (KeyError, ValueError):
            continue
        if all(value != prior for _, prior in matches):
            matches.append((kind, value))
    if not matches:
        raise ValueError(f"unknown center identifier {identifier!r}.")
    if len(matches) > 1:
        alternatives = ", ".join(
            f"{kind}:{identifier}" for kind, _ in matches
        )
        raise ValueError(
            f"ambiguous center {identifier!r}; use one of: {alternatives}."
        )
    kind, value = matches[0]
    return ResolvedNamedCenter(kind, identifier, value)
