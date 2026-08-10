"""Offline resolution of IAU constellation sets and packaged groups."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
import json

from .request import ChartSubjectRequest


IAU_CONSTELLATIONS = frozenset(
    "And Ant Aps Aqr Aql Ara Ari Aur Boo Cae Cam Cnc CVn CMa CMi Cap Car "
    "Cas Cen Cep Cet Cha Cir Col Com CrA CrB Crt Cru Crv Cyg Del Dor Dra "
    "Equ Eri For Gem Gru Her Hor Hya Hyi Ind Lac Leo LMi Lep Lib Lup Lyn "
    "Lyr Men Mic Mon Mus Nor Oct Oph Ori Pav Peg Per Phe Pic Psc PsA Pup "
    "Pyx Ret Sge Sgr Sco Scl Sct Ser Sex Tau Tel Tri TrA Tuc UMa UMi Vel "
    "Vir Vol Vul".split()
)
_IAU_BY_KEY = {name.casefold(): name for name in IAU_CONSTELLATIONS}


class ConstellationResolutionError(ValueError):
    """Base error for constellation and group resolution failures."""


class UnknownConstellationError(ConstellationResolutionError):
    """Raised when an IAU abbreviation is not recognized."""


class UnknownConstellationGroupError(ConstellationResolutionError):
    """Raised when a packaged group name is not recognized."""


@dataclass(frozen=True)
class ResolvedConstellationSubject:
    """Normalized region, figure, label, content, and preset identities."""

    key: str
    display_name: str
    constellations: tuple[str, ...]
    line_constellations: tuple[str, ...]
    boundary_constellations: tuple[str, ...]
    label_constellations: tuple[str, ...]
    open_clusters: tuple[str, ...] = ()
    planetary_nebulae: tuple[str, ...] = ()
    supernova_remnants: tuple[str, ...] = ()
    field_width_deg: float | None = None
    field_height_deg: float | None = None
    provenance: str = "IAU constellation abbreviation"


def _alias_key(value):
    return "".join(
        character for character in str(value).casefold()
        if character.isalnum()
    )


def normalize_constellations(values):
    """Return unique canonical IAU abbreviations in requested order."""
    normalized = []
    unknown = []
    for value in values:
        name = _IAU_BY_KEY.get(str(value).strip().casefold())
        if name is None:
            unknown.append(str(value))
        elif name not in normalized:
            normalized.append(name)
    if unknown:
        names = ", ".join(sorted(unknown))
        raise UnknownConstellationError(
            f"Unknown IAU constellation abbreviation(s): {names}."
        )
    if not normalized:
        raise ConstellationResolutionError(
            "At least one constellation is required."
        )
    return tuple(normalized)


def _internal_identities(constellations):
    lines = []
    labels = []
    for name in constellations:
        if name == "Ser":
            lines.extend(("Ser1", "Ser2"))
            labels.extend(("SerCap", "SerCau"))
        else:
            lines.append(name)
            labels.append(name)
    return tuple(lines), tuple(labels)


def constellation_group_catalogue_path():
    """Return the packaged regional-group resource."""
    resource = files("wenu.data") / "constellation_groups.json"
    if not resource.is_file():
        raise FileNotFoundError("Packaged constellation groups are missing.")
    return resource


def load_constellation_groups():
    """Load packaged group declarations and their provenance."""
    resource = constellation_group_catalogue_path()
    with resource.open("r", encoding="utf-8") as stream:
        document = json.load(stream)
    provenance = str(document.get("provenance", "")).strip()
    groups = tuple(document.get("groups", ()))
    if not provenance:
        raise ValueError("Constellation-group provenance is required.")
    if not groups:
        raise ValueError("Constellation-group catalogue must not be empty.")
    return provenance, groups


def resolve_constellation_subject(
    subject: ChartSubjectRequest,
) -> ResolvedConstellationSubject:
    """Resolve an explicit IAU set or one named packaged teaching group."""
    if not isinstance(subject, ChartSubjectRequest):
        raise TypeError("subject must be a ChartSubjectRequest.")
    if subject.constellations is not None:
        constellations = normalize_constellations(subject.constellations)
        lines, labels = _internal_identities(constellations)
        return ResolvedConstellationSubject(
            key="+".join(name.casefold() for name in constellations),
            display_name=subject.display_name or ", ".join(constellations),
            constellations=constellations,
            line_constellations=lines,
            boundary_constellations=constellations,
            label_constellations=labels,
        )
    if subject.group is None:
        raise ConstellationResolutionError(
            "Constellation resolution requires an IAU set or group."
        )
    provenance, declarations = load_constellation_groups()
    requested = _alias_key(subject.group)
    matches = [
        item for item in declarations
        if requested in {
            _alias_key(value) for value in (
                item["key"], item["name"], *item.get("aliases", ())
            )
        }
    ]
    if not matches:
        raise UnknownConstellationGroupError(
            f"Unknown packaged constellation group {subject.group!r}."
        )
    declaration = matches[0]
    constellations = normalize_constellations(
        declaration["constellations"]
    )
    lines, labels = _internal_identities(constellations)
    return ResolvedConstellationSubject(
        key=str(declaration["key"]),
        display_name=subject.display_name or str(declaration["name"]),
        constellations=constellations,
        line_constellations=lines,
        boundary_constellations=constellations,
        label_constellations=labels,
        open_clusters=tuple(declaration.get("open_clusters", ())),
        planetary_nebulae=tuple(
            declaration.get("planetary_nebulae", ())
        ),
        supernova_remnants=tuple(
            declaration.get("supernova_remnants", ())
        ),
        field_width_deg=float(declaration["field_width_deg"]),
        field_height_deg=float(declaration["field_height_deg"]),
        provenance=provenance,
    )
