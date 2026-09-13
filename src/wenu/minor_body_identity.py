"""Exact installed/provider identity resolution for minor bodies."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from typing import Callable
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen

from wenu.comet_designations import (
    normalize_comet_selection,
    parse_comet_designation,
)


SBDB_API = "https://ssd-api.jpl.nasa.gov/sbdb.api"
SBDB_SOURCE = "NASA/JPL Small-Body Database (SBDB) API"
EXPECTED_SBDB_VERSION = "1.3"
_OBJECT_CLASSES = frozenset({"asteroid", "comet"})
_KINDS = {
    "asteroid": frozenset({"an", "au"}),
    "comet": frozenset({"cn", "cu"}),
}


class MinorBodyIdentityError(ValueError):
    """Base failure for exact minor-body identity resolution."""


class MinorBodyIdentityNotFoundError(MinorBodyIdentityError):
    """No exact identity matched the requested selection."""


class AmbiguousMinorBodyIdentityError(MinorBodyIdentityError):
    """The provider reported multiple possible identities."""


@dataclass(frozen=True)
class ProviderResponse:
    """One HTTP status and its exact response bytes."""

    status: int
    raw: bytes


@dataclass(frozen=True)
class ResolvedMinorBodyIdentity:
    """Immutable exact identity plus installed or provider provenance."""

    original_selection: str
    normalized_selection: str
    object_class: str
    kind: str
    canonical_designation: str
    primary_designation: str
    prefix: str | None
    permanent_number: int | None
    fragment: str | None
    name: str | None
    aliases: tuple[str, ...]
    provider_spk_id: str
    orbit_class_code: str | None
    orbit_class_name: str | None
    orbit_solution_id: str
    provider: str
    provider_version: str
    source: str
    request_parameters: tuple[tuple[str, str], ...] = ()
    retrieved_at_utc: datetime | None = None
    raw_sha256: str | None = None


def normalize_minor_body_selection(selection: str) -> str:
    """Case-fold one non-empty selection after whitespace normalization."""
    if not isinstance(selection, str):
        raise TypeError("minor-body selection must be a string.")
    normalized = " ".join(selection.strip().split())
    if not normalized:
        raise ValueError("minor-body selection must be non-empty.")
    return normalized.casefold()


def _expected_class(value: str) -> str:
    if value not in _OBJECT_CLASSES:
        raise ValueError("expected_class must be 'asteroid' or 'comet'.")
    return value


def identity_query_parameters(
    selection: str, *, expected_class: str
) -> dict[str, str]:
    """Build one exact designation or name-oriented SBDB request."""
    expected = _expected_class(expected_class)
    normalized = " ".join(selection.strip().split())
    if expected == "comet":
        if normalized.isdecimal():
            raise MinorBodyIdentityNotFoundError(
                f"bare number {normalized!r} is not a comet designation."
            )
        try:
            parsed = parse_comet_designation(normalized)
        except ValueError:
            try:
                named = normalize_comet_selection(normalized)
            except (TypeError, ValueError):
                named = normalize_minor_body_selection(normalized)
            match = re.fullmatch(
                r"(?P<designation>[1-9]\d*[PDI](?:-[A-Z]+)?)/.+",
                named,
                flags=re.IGNORECASE,
            )
            key = "des" if match is not None else "sstr"
            value = (
                match.group("designation").upper()
                if match is not None else normalized
            )
        else:
            key, value = "des", parsed.canonical
    else:
        key = "des" if normalized.isdecimal() else "sstr"
        value = normalized
    return {
        key: value,
        "alt-des": "true",
        "full-prec": "true",
        "no-orbit": "true",
    }


def _fetch(
    url: str, parameters: dict[str, str], *, timeout: int = 120
) -> ProviderResponse:
    request_url = url + "?" + urlencode(parameters)
    try:
        with urlopen(request_url, timeout=timeout) as response:
            return ProviderResponse(response.status, response.read())
    except HTTPError as error:
        return ProviderResponse(error.code, error.read())


def _text(value: object, field: str) -> str:
    result = str(value).strip() if value is not None else ""
    if not result:
        raise MinorBodyIdentityError(
            f"SBDB identity response requires non-empty {field}."
        )
    return result


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    result = str(value).strip()
    return result or None


def _signature(document: object) -> tuple[str, str]:
    if not isinstance(document, dict):
        raise MinorBodyIdentityError("SBDB identity response must be an object.")
    signature = document.get("signature")
    if (
        not isinstance(signature, dict)
        or signature.get("source") != SBDB_SOURCE
        or signature.get("version") != EXPECTED_SBDB_VERSION
    ):
        raise MinorBodyIdentityError(
            "SBDB identity response has no accepted API signature."
        )
    return str(signature["source"]), str(signature["version"])


def _decode(raw: bytes) -> dict:
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise MinorBodyIdentityError(
            "SBDB identity response is not valid UTF-8 JSON."
        ) from error
    _signature(document)
    return document


def _canonical_designation(
    primary: str, prefix: str | None, object_class: str
) -> tuple[str, int | None, str | None]:
    if object_class == "asteroid":
        number = int(primary) if primary.isdecimal() else None
        return primary, number, None
    candidate = primary
    if prefix and not re.match(r"^[PCDXAI]/", candidate, re.IGNORECASE):
        if not re.match(r"^[1-9]\d*[PDI]", candidate, re.IGNORECASE):
            candidate = f"{prefix}/{candidate}"
    try:
        parsed = parse_comet_designation(candidate)
    except ValueError as error:
        raise MinorBodyIdentityError(
            f"invalid provider comet designation: {candidate!r}."
        ) from error
    return parsed.canonical, parsed.permanent_number, parsed.fragment


def _name_from_object(
    fullname: str, shortname: str | None, canonical: str
) -> str | None:
    candidate = shortname or fullname
    candidate = re.sub(r"\s*\([^()]*\)\s*$", "", candidate).strip()
    if candidate.casefold().startswith(canonical.casefold() + "/"):
        return candidate[len(canonical) + 1:].strip() or None
    if candidate.casefold().startswith(canonical.casefold() + " "):
        return candidate[len(canonical):].strip() or None
    return None


def _provider_aliases(
    values: dict, canonical: str, name: str | None
) -> tuple[str, ...]:
    candidates = [
        canonical,
        _optional_text(values.get("des")),
        _optional_text(values.get("fullname")),
        _optional_text(values.get("shortname")),
        name,
    ]
    alternates = values.get("des_alt", ())
    if not isinstance(alternates, list):
        raise MinorBodyIdentityError(
            "SBDB alternate designations must be a list."
        )
    for item in alternates:
        if not isinstance(item, dict):
            raise MinorBodyIdentityError(
                "SBDB alternate designation must be an object."
            )
        candidates.extend(_optional_text(value) for value in item.values())
    aliases = {}
    for candidate in candidates:
        if candidate is None:
            continue
        aliases.setdefault(normalize_minor_body_selection(candidate), candidate)
    return tuple(aliases[key] for key in sorted(aliases))


def parse_unique_identity_response(
    raw: bytes,
    *,
    selection: str,
    expected_class: str,
    parameters: dict[str, str],
    retrieved_at_utc: datetime,
) -> ResolvedMinorBodyIdentity:
    """Validate one unique SBDB identity response."""
    expected = _expected_class(expected_class)
    document = _decode(raw)
    if set(document) != {"signature", "object"}:
        raise MinorBodyIdentityError(
            "SBDB unique identity response schema changed."
        )
    values = document["object"]
    if not isinstance(values, dict):
        raise MinorBodyIdentityError(
            "SBDB unique identity response has no object data."
        )
    kind = _text(values.get("kind"), "object.kind")
    if kind not in _KINDS[expected]:
        raise MinorBodyIdentityNotFoundError(
            f"SBDB identity is {kind!r}, not expected class {expected!r}."
        )
    primary = _text(values.get("des"), "object.des")
    prefix = _optional_text(values.get("prefix"))
    canonical, number, fragment = _canonical_designation(
        primary, prefix, expected
    )
    fullname = _text(values.get("fullname"), "object.fullname")
    shortname = _optional_text(values.get("shortname"))
    name = _name_from_object(fullname, shortname, canonical)
    aliases = _provider_aliases(values, canonical, name)
    normalized = normalize_minor_body_selection(selection)
    if normalized not in {
        normalize_minor_body_selection(value) for value in aliases
    }:
        raise MinorBodyIdentityNotFoundError(
            f"SBDB returned no exact identity for {normalized!r}."
        )
    orbit_class = values.get("orbit_class")
    if not isinstance(orbit_class, dict):
        raise MinorBodyIdentityError(
            "SBDB identity response requires object.orbit_class."
        )
    provider, version = _signature(document)
    return ResolvedMinorBodyIdentity(
        original_selection=selection,
        normalized_selection=normalized,
        object_class=expected,
        kind=kind,
        canonical_designation=canonical,
        primary_designation=primary,
        prefix=prefix,
        permanent_number=number,
        fragment=fragment,
        name=name,
        aliases=aliases,
        provider_spk_id=_text(values.get("spkid"), "object.spkid"),
        orbit_class_code=_optional_text(orbit_class.get("code")),
        orbit_class_name=_optional_text(orbit_class.get("name")),
        orbit_solution_id=_text(
            values.get("orbit_id"), "object.orbit_id"
        ),
        provider=provider,
        provider_version=version,
        source="provider",
        request_parameters=tuple(sorted(parameters.items())),
        retrieved_at_utc=retrieved_at_utc,
        raw_sha256=sha256(raw).hexdigest(),
    )


def _raise_ambiguous(raw: bytes, selection: str) -> None:
    document = _decode(raw)
    if set(document) != {
        "signature", "code", "count", "list", "message"
    }:
        raise MinorBodyIdentityError(
            "SBDB ambiguous identity response schema changed."
        )
    candidates = document["list"]
    if (
        document.get("code") != 300
        or not isinstance(candidates, list)
        or document.get("count") != len(candidates)
    ):
        raise MinorBodyIdentityError(
            "SBDB ambiguous identity response is malformed."
        )
    names = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise MinorBodyIdentityError(
                "SBDB ambiguous candidate must be an object."
            )
        names.append(_text(candidate.get("name"), "candidate.name"))
        _text(candidate.get("pdes"), "candidate.pdes")
    normalized = normalize_minor_body_selection(selection)
    raise AmbiguousMinorBodyIdentityError(
        f"SBDB identity {normalized!r} is ambiguous among "
        f"{len(names)} candidates: {', '.join(names)}."
    )


def _installed_identity(
    selection: str, expected_class: str, collection
) -> ResolvedMinorBodyIdentity | None:
    if collection is None:
        return None
    try:
        descriptor = collection.resolve(selection)
    except KeyError:
        return None
    if descriptor.body_class != expected_class:
        raise MinorBodyIdentityNotFoundError(
            f"installed identity is {descriptor.body_class!r}, "
            f"not expected class {expected_class!r}."
        )
    solution = collection.solution_for(descriptor)
    canonical = descriptor.canonical_designation
    designation = solution.primary_designation
    prefix = None
    number = descriptor.iau_number
    fragment = None
    if expected_class == "comet":
        parsed = parse_comet_designation(designation)
        prefix = parsed.designation_class
        number = parsed.permanent_number
        fragment = parsed.fragment
    aliases = tuple(dict.fromkeys(
        (designation, canonical, *(solution.aliases or ()))
    ))
    return ResolvedMinorBodyIdentity(
        original_selection=selection,
        normalized_selection=normalize_minor_body_selection(selection),
        object_class=expected_class,
        kind="cn" if expected_class == "comet" and number else (
            "cu" if expected_class == "comet" else (
                "an" if number else "au"
            )
        ),
        canonical_designation=canonical,
        primary_designation=designation,
        prefix=prefix,
        permanent_number=number,
        fragment=fragment,
        name=solution.name,
        aliases=aliases,
        provider_spk_id=solution.provider_spk_id,
        orbit_class_code=None,
        orbit_class_name=None,
        orbit_solution_id=solution.orbit_solution_id,
        provider=solution.provider,
        provider_version=solution.service_version,
        source="installed",
    )


def resolve_minor_body_identity(
    selection: str,
    *,
    expected_class: str,
    installed_collection=None,
    fetch: Callable[[str, dict[str, str]], ProviderResponse] = _fetch,
    now: Callable[[], datetime] | None = None,
) -> ResolvedMinorBodyIdentity:
    """Resolve one exact installed or provider minor-body identity."""
    expected = _expected_class(expected_class)
    normalize_minor_body_selection(selection)
    installed = _installed_identity(
        selection, expected, installed_collection
    )
    if installed is not None:
        return installed
    parameters = identity_query_parameters(
        selection, expected_class=expected
    )
    response = fetch(SBDB_API, parameters)
    if response.status == 300:
        _raise_ambiguous(response.raw, selection)
    if response.status != 200:
        raise MinorBodyIdentityNotFoundError(
            f"SBDB identity request failed with HTTP {response.status}."
        )
    clock = now or (lambda: datetime.now(timezone.utc))
    retrieved = clock()
    if retrieved.tzinfo is None:
        retrieved = retrieved.replace(tzinfo=timezone.utc)
    return parse_unique_identity_response(
        response.raw,
        selection=selection,
        expected_class=expected,
        parameters=parameters,
        retrieved_at_utc=retrieved.astimezone(timezone.utc),
    )


def resolve_comet_identity(selection: str, **kwargs):
    """Resolve one exact comet identity through the generic boundary."""
    return resolve_minor_body_identity(
        selection, expected_class="comet", **kwargs
    )
