"""Lossless IAU/MPC comet-designation identity vocabulary."""

from __future__ import annotations

import re
from dataclasses import dataclass

_NUMBERED = re.compile(r"^(?P<number>[1-9]\d*)(?P<class>[PDI])(?:-(?P<fragment>[A-Z]+))?$")
_PROVISIONAL = re.compile(
    r"^(?P<class>[PCXAI])/(?P<year>\d{4})\s+(?P<code>[A-Z][A-Z0-9]+)"
    r"(?:-(?P<fragment>[A-Z]+))?$"
)
COMET_DESIGNATION_CLASSES = frozenset({"P", "D", "I", "C", "X", "A"})
_NUMBERED_NAMED = re.compile(
    r"^(?P<designation>[1-9]\d*[PDI](?:-[A-Z]+)?)/(?P<name>[^/,]+)$"
)
_INSTALLED_NAME = re.compile(r"^[^/,]+$")


@dataclass(frozen=True)
class CometDesignation:
    """Structured designation without destructive punctuation stripping."""

    canonical: str
    designation_class: str
    permanent_number: int | None = None
    provisional_year: int | None = None
    provisional_code: str | None = None
    fragment: str | None = None


def parse_comet_designation(value):
    """Recognize numbered and provisional comet-system designations."""
    if not isinstance(value, str):
        raise TypeError("comet designation must be a string.")
    normalized = " ".join(value.strip().upper().split())
    match = _NUMBERED.fullmatch(normalized)
    if match is not None:
        return CometDesignation(
            canonical=normalized,
            designation_class=match.group("class"),
            permanent_number=int(match.group("number")),
            fragment=match.group("fragment"),
        )
    match = _PROVISIONAL.fullmatch(normalized)
    if match is not None:
        return CometDesignation(
            canonical=normalized,
            designation_class=match.group("class"),
            provisional_year=int(match.group("year")),
            provisional_code=match.group("code"),
            fragment=match.group("fragment"),
        )
    raise ValueError(f"invalid comet designation: {value!r}.")


def normalize_comet_selection(value):
    """Normalize a designation or exact installed comet-name alias."""
    if not isinstance(value, str):
        raise TypeError("comet selection must be a string.")
    normalized = " ".join(value.strip().split())
    if not normalized:
        raise ValueError("comet selection cannot be empty.")
    try:
        parse_comet_designation(normalized)
    except ValueError:
        upper = normalized.upper()
        named = _NUMBERED_NAMED.fullmatch(upper)
        if named is not None:
            parse_comet_designation(named.group("designation"))
        elif _INSTALLED_NAME.fullmatch(normalized) is None:
            raise ValueError(f"invalid comet selection: {value!r}.") from None
    return normalized.casefold()
