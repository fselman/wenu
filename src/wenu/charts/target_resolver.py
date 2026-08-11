"""Offline resolution of packaged and explicit chart targets."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
import json
import re

from .request import ChartSubjectRequest


class TargetResolutionError(ValueError):
    """Base error for user-facing target resolution failures."""


class UnknownTargetError(TargetResolutionError):
    """Raised when no packaged alias identifies a requested target."""


class AmbiguousTargetError(TargetResolutionError):
    """Raised when one normalized alias identifies multiple targets."""


@dataclass(frozen=True)
class TargetComponent:
    """One catalogue family and identifier needed to depict a target."""

    family: str
    identifier: str

    @property
    def display_identifier(self):
        """Return a compact catalogue identifier in publication form."""
        match = re.fullmatch(r"NGC\s*(\d+)", self.identifier)
        if match:
            return f"NGC {match.group(1)}"
        return self.identifier


@dataclass(frozen=True)
class ResolvedTarget:
    """Canonical target identity, coordinate, components, and provenance."""

    key: str
    display_name: str
    ra_deg: float
    dec_deg: float
    components: tuple[TargetComponent, ...]
    provenance: str
    matched_alias: str | None = None

    @property
    def required_families(self):
        return frozenset(component.family for component in self.components)

    @property
    def primary_identifier(self):
        """Return the first drawable catalogue identity, when available."""
        if not self.components:
            return None
        return self.components[0].display_identifier

    @property
    def coordinate(self):
        """Return the resolved center as an ICRS coordinate."""
        from astropy import units as u
        from astropy.coordinates import SkyCoord

        return SkyCoord(
            ra=self.ra_deg * u.deg,
            dec=self.dec_deg * u.deg,
            frame="icrs",
        )


def _alias_key(value):
    return "".join(
        character
        for character in str(value).casefold()
        if character.isalnum()
    )


def target_catalogue_path():
    """Return the packaged target cross-identification resource."""
    resource = files("wenu.data") / "targets.json"
    if not resource.is_file():
        raise FileNotFoundError("Packaged target catalogue is missing.")
    return resource


def load_target_catalogue():
    """Load and validate packaged target declarations."""
    resource = target_catalogue_path()
    with resource.open("r", encoding="utf-8") as stream:
        document = json.load(stream)
    provenance = str(document.get("provenance", "")).strip()
    if not provenance:
        raise ValueError("Target catalogue provenance is required.")
    targets = tuple(document.get("targets", ()))
    if not targets:
        raise ValueError("Target catalogue must contain targets.")
    return provenance, targets


def resolve_target(subject: ChartSubjectRequest) -> ResolvedTarget:
    """Resolve one named or explicit-coordinate subject offline."""
    if not isinstance(subject, ChartSubjectRequest):
        raise TypeError("subject must be a ChartSubjectRequest.")
    if subject.ra_deg is not None:
        name = subject.display_name or (
            f"RA {subject.ra_deg:g}°, Dec {subject.dec_deg:g}°"
        )
        return ResolvedTarget(
            key="explicit-coordinate",
            display_name=name,
            ra_deg=subject.ra_deg,
            dec_deg=subject.dec_deg,
            components=(),
            provenance="user-supplied ICRS coordinate",
        )
    if subject.target is None:
        raise TargetResolutionError(
            "Target resolution requires a name or explicit coordinates."
        )

    provenance, declarations = load_target_catalogue()
    requested_key = _alias_key(subject.target)
    matches = []
    for declaration in declarations:
        aliases = (
            declaration["key"],
            declaration["name"],
            *declaration.get("aliases", ()),
        )
        if requested_key in {_alias_key(alias) for alias in aliases}:
            matches.append(declaration)
    if not matches:
        raise UnknownTargetError(
            f"Unknown packaged target {subject.target!r}."
        )
    if len(matches) > 1:
        names = ", ".join(sorted(item["name"] for item in matches))
        raise AmbiguousTargetError(
            f"Ambiguous target {subject.target!r}: {names}."
        )
    declaration = matches[0]
    components = tuple(
        TargetComponent(
            family=str(component["family"]),
            identifier=str(component["identifier"]),
        )
        for component in declaration.get("components", ())
    )
    return ResolvedTarget(
        key=str(declaration["key"]),
        display_name=subject.display_name or str(declaration["name"]),
        ra_deg=float(declaration["ra_deg"]),
        dec_deg=float(declaration["dec_deg"]),
        components=components,
        provenance=provenance,
        matched_alias=subject.target,
    )
