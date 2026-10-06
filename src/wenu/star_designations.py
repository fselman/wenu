"""Offline, immutable HIP-linked Wikidata candidates, separate from astrometry.

Labels and aliases are evidence, not approved proper names. No designation or
component preference is inferred here; editorial decisions belong to curation.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from functools import lru_cache

from wenu.resources import star_designations_manifest_path

_RANKS = frozenset(("NormalRank", "PreferredRank", "DeprecatedRank"))

_CONSTELLATIONS = {
    value.casefold(): value
    for value in (
        "And Ant Aps Aqr Aql Ara Ari Aur Boo Cae Cam Cnc CVn CMa CMi Cap Car "
        "Cas Cen Cep Cet Cha Cir Col Com CrA CrB Crt Cru Crv Cyg Del Dor Dra "
        "Equ Eri For Gem Gru Her Hor Hya Hyi Ind Lac Leo LMi Lep Lib Lup Lyn "
        "Lyr Men Mic Mon Mus Nor Oct Oph Ori Pav Peg Per Phe Pic Psc PsA Pup "
        "Pyx Ret Sge Sgr Sco Scl Sct Ser Sex Tau Tel Tri TrA Tuc UMa UMi Vel "
        "Vir Vol Vul"
    ).split()
}
_GREEK = dict(
    zip(
        "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu "
        "xi omicron pi rho sigma tau upsilon phi chi psi omega".split(),
        "αβγδεζηθικλμνξοπρστυφχψω",
    )
)
_DIGITS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
_SUPERSCRIPTS = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def constellation_code(value):
    """Normalize an explicit IAU abbreviation, never infer membership."""
    try:
        return _CONSTELLATIONS[value.strip().casefold()]
    except (KeyError, AttributeError) as error:
        raise ValueError(f"Unknown constellation: {value!r}") from error


def bayer_token(value):
    """Normalize Greek spellings/superscripts while preserving Latin case."""
    token = value.strip().translate(_DIGITS)
    match = re.fullmatch(r"([A-Za-z]+|[α-ω])([0-9]*)", token)
    if match is None:
        raise ValueError(f"Invalid Bayer token: {value!r}")
    letter, suffix = match.groups()
    if len(letter) > 1:
        try:
            letter = _GREEK[letter.casefold()]
        except KeyError as error:
            raise ValueError(f"Unknown Greek spelling: {letter!r}") from error
    return letter + suffix.translate(_SUPERSCRIPTS)


def designation_parts(code, kind="bayer"):
    """Read supported source tokens; retain component suffixes separately."""
    parts = code.split()
    if len(parts) not in (2, 3):
        raise ValueError(f"Unsupported designation: {code!r}")
    token = bayer_token(parts[0]) if kind == "bayer" else parts[0]
    if kind == "flamsteed" and not token.isdecimal():
        raise ValueError(f"Invalid Flamsteed number: {code!r}")
    if len(parts) == 3 and not re.fullmatch(r"[A-Z]+", parts[2]):
        raise ValueError(f"Unsupported component suffix: {code!r}")
    return token, constellation_code(parts[1]), tuple(parts[2:])


@dataclass(frozen=True)
class StarLabelSelection:
    """Explicit source-backed name/Bayer targets; no automatic labels."""

    names: tuple[str, ...] = ()
    bayer: tuple[str, ...] = ()
    show_full_bayer_designation: bool = False

    def __post_init__(self):
        for field in ("names", "bayer"):
            values = getattr(self, field)
            if isinstance(values, str):
                raise TypeError(f"{field} must be a sequence of selectors")
            values = tuple(values)
            for value in values:
                _, tokens = parse_star_selector(value)
                if field == "bayer":
                    for token in tokens:
                        bayer_token(token)
            object.__setattr__(self, field, values)
        if not isinstance(self.show_full_bayer_designation, bool):
            raise TypeError("show_full_bayer_designation must be boolean")


def parse_star_selector(value):
    if not isinstance(value, str) or value.count(":") != 1:
        raise ValueError("Star selector must be 'IAU:token,token'")
    scope, tokens = value.split(":")
    scope = constellation_code(scope)
    tokens = tuple(token.strip() for token in tokens.split(","))
    if not tokens or any(not token for token in tokens):
        raise ValueError("Star selector contains an empty token")
    return scope, tokens


@dataclass(frozen=True)
class ResolvedStarLabels:
    """HIP identity and requested text, independent of rendered geometry."""

    labels: tuple[tuple[int, str], ...] = ()

    @property
    def hip_ids(self):
        return frozenset(hip for hip, _ in self.labels)

    def __call__(self, hip):
        return dict(self.labels).get(int(hip))


@lru_cache(maxsize=1)
def packaged_star_designations():
    """Reuse the immutable packaged catalogue for explicit resolution."""
    return load_star_designations()


def preferred_designation(record, kind, constellations=(), *, preferred=None):
    """Choose an existing Wikidata claim using approved shared-star policy.

    Same-constellation ambiguity never silently selects the first record.
    A unique PreferredRank claim may resolve an otherwise tied source set.
    """
    claims = record.candidates(kind)
    codes = sorted({claim.code for claim in claims})
    if not codes:
        return None
    if len(codes) == 1:
        return codes[0]
    scopes = {constellation_code(value) for value in constellations}
    matched = [
        code for code in codes if designation_parts(code, kind)[1] in scopes
    ]
    if preferred is not None:
        # Only reviewed shared cases receive context-dependent selection.
        if len(matched) == 1:
            return matched[0]
        if preferred not in codes:
            raise ValueError("Shared-star preference is absent from Wikidata")
        return preferred
    ranked = {claim.code for claim in claims if claim.rank == "PreferredRank"}
    if len(ranked) == 1:
        return next(iter(ranked))
    raise ValueError(
        f"Ambiguous Wikidata {kind} assignments for HIP {record.hip}: {codes}"
    )


def resolve_star_labels(selection, *, catalogue=None, constellations=()):
    """Resolve exact identifiers before magnitude selection, deduplicating HIP.

    Names are explicitly requested exact Wikidata English labels/aliases;
    this does not promote every alias to an official proper name.
    """
    if not isinstance(selection, StarLabelSelection):
        raise TypeError("selection must be StarLabelSelection")
    if not selection.names and not selection.bayer:
        return ResolvedStarLabels()
    catalogue = (
        packaged_star_designations() if catalogue is None else catalogue
    )
    from wenu.stellar_research import load_stellar_research

    research = load_stellar_research()
    contexts = set(constellations)
    for selector in (*selection.names, *selection.bayer):
        contexts.add(parse_star_selector(selector)[0])
    bayer_index, name_index = {}, {}
    for hip, record in catalogue.by_hip.items():
        scopes = set()
        for statement in record.statements:
            if statement.rank == "DeprecatedRank":
                continue
            try:
                token, scope, component = designation_parts(
                    statement.code, statement.kind
                )
            except ValueError:
                continue
            scopes.add(scope)
            if statement.kind == "bayer":
                bayer_index.setdefault((scope, token), set()).add(hip)
        for name in record.names:
            if name.language == "en":
                for scope in scopes:
                    name_index.setdefault(
                        (scope, name.value.casefold()), set()
                    ).add((hip, name.value))
    labels = {}
    for kind, selectors in (
        ("bayer", selection.bayer),
        ("name", selection.names),
    ):
        for selector in selectors:
            scope, tokens = parse_star_selector(selector)
            for token in tokens:
                matches = (
                    bayer_index.get((scope, bayer_token(token)), set())
                    if kind == "bayer"
                    else {
                        hip
                        for hip, _ in name_index.get(
                            (scope, token.casefold()), set()
                        )
                    }
                )
                if len(matches) != 1:
                    adjective = (
                        "Unknown or unavailable"
                        if not matches
                        else "Ambiguous"
                    )
                    raise ValueError(
                        f"{adjective} stellar {kind}: {scope}:{token}; HIP matches {sorted(matches)}"
                    )
                hip = next(iter(matches))
                if kind == "name":
                    spellings = {
                        name
                        for match, name in name_index[
                            (scope, token.casefold())
                        ]
                        if match == hip
                    }
                    if len(spellings) != 1:
                        raise ValueError(
                            f"Ambiguous source spelling for {scope}:{token}"
                        )
                    text = next(iter(spellings))
                else:
                    record = catalogue.get(hip)
                    shared = research.shared_preference(hip, "bayer")
                    if shared is not None:
                        code = preferred_designation(
                            record, "bayer", contexts, preferred=shared
                        )
                    else:
                        codes = {
                            s.code
                            for s in record.candidates("bayer")
                            if designation_parts(s.code)[0:2]
                            == (bayer_token(token), scope)
                        }
                        if len(codes) != 1:
                            raise ValueError(
                                f"Ambiguous component scope for {scope}:{token}"
                            )
                        code = next(iter(codes))
                    letter, constellation, component = designation_parts(code)
                    text = " ".join(
                        (
                            letter,
                            *(
                                (constellation,)
                                if selection.show_full_bayer_designation
                                else ()
                            ),
                            *component,
                        )
                    )
                if (
                    hip in labels
                    and labels[hip][0] == kind
                    and labels[hip][1] != text
                ):
                    raise ValueError(
                        f"Conflicting explicit {kind} labels for HIP {hip}"
                    )
                labels[hip] = (kind, text)
    return ResolvedStarLabels(
        tuple(sorted((hip, text) for hip, (_, text) in labels.items()))
    )
@dataclass(frozen=True)
class HipLink:
    statement_id: str
    value: str
    rank: str


@dataclass(frozen=True)
class DesignationStatement:
    statement_id: str
    item_id: str
    kind: str
    code: str
    rank: str
    hip_links: tuple[HipLink, ...]
    references: tuple[str, ...]


@dataclass(frozen=True)
class NameCandidate:
    item_id: str
    value: str
    language: str
    role: str


@dataclass(frozen=True)
class StarDesignations:
    hip: int
    statements: tuple[DesignationStatement, ...]
    names: tuple[NameCandidate, ...]
    review_fields: tuple[str, ...]

    def candidates(self, kind: str) -> tuple[DesignationStatement, ...]:
        """Return active source claims without choosing or normalizing one."""
        if kind not in ("bayer", "flamsteed"):
            raise ValueError(f"Unknown designation kind: {kind!r}")
        return tuple(
            s
            for s in self.statements
            if s.kind == kind and s.rank != "DeprecatedRank"
        )

    @property
    def item_ids(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {s.item_id for s in self.statements}
                | {n.item_id for n in self.names}
            )
        )


@dataclass(frozen=True)
class StarDesignationCatalogue:
    edition: str
    source_sha256: str
    by_hip: Mapping[int, StarDesignations]
    unjoined_statements: tuple[DesignationStatement, ...]

    def get(self, hip: int) -> StarDesignations | None:
        return self.by_hip.get(hip)


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _keys(value, expected):
    _require(
        isinstance(value, dict) and set(value) == set(expected),
        "Invalid Wikidata record fields",
    )


def _text(value):
    _require(
        isinstance(value, str) and bool(value.strip()),
        "Expected nonempty text",
    )
    return value


def _item(value):
    _require(
        isinstance(value, str) and re.fullmatch(r"Q[1-9][0-9]*", value),
        "Invalid Wikidata item ID",
    )
    return value


def _rank(value):
    _require(
        isinstance(value, str) and value in _RANKS,
        "Invalid Wikidata statement rank",
    )
    return value


def _statement_id(value, item=None):
    _text(value)
    _require(
        re.fullmatch(
            r"http://www.wikidata.org/entity/statement/[Qq][1-9][0-9]*-[A-Za-z0-9-]+",
            value,
        ),
        "Invalid Wikidata statement ID",
    )
    if item is not None:
        _require(
            value.rsplit("/", 1)[-1].upper().startswith(item + "-"),
            "Statement belongs to a different item",
        )
    return value


def _statement(value):
    _keys(
        value,
        ("id", "item", "kind", "code", "rank", "hip_links", "references"),
    )
    item = _item(value["item"])
    _require(
        value["kind"] in ("bayer", "flamsteed"), "Invalid designation kind"
    )
    _require(isinstance(value["hip_links"], list), "Invalid HIP links")
    links = []
    for link in value["hip_links"]:
        _require(isinstance(link, list) and len(link) == 3, "Invalid HIP link")
        links.append(
            HipLink(
                _statement_id(link[0], item), _text(link[1]), _rank(link[2])
            )
        )
    _require(len(set(links)) == len(links), "Duplicate HIP link")
    refs = value["references"]
    _require(
        isinstance(refs, list)
        and all(
            isinstance(x, str)
            and re.fullmatch(r"http://www.wikidata.org/reference/[0-9a-f]+", x)
            for x in refs
        ),
        "Invalid Wikidata references",
    )
    _require(len(set(refs)) == len(refs), "Duplicate reference")
    return DesignationStatement(
        _statement_id(value["id"], item),
        item,
        value["kind"],
        _text(value["code"]),
        _rank(value["rank"]),
        tuple(links),
        tuple(refs),
    )


def _json(payload):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            _require(key not in result, f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(payload, object_pairs_hook=unique)


def load_star_designations(manifest_path=None) -> StarDesignationCatalogue:
    """Read and verify a packaged snapshot, or an explicit local manifest.

    Missing HIPs return None. Ambiguous/malformed HIP assignments stay unjoined;
    deprecated claims stay in the evidence but are absent from candidates().
    """
    path = (
        star_designations_manifest_path()
        if manifest_path is None
        else Path(manifest_path)
    )
    manifest = _json(path.read_bytes())
    _require(
        manifest.get("schema") == "wenu-star-designations-manifest/1",
        "Unsupported designation manifest",
    )
    _require(
        manifest.get("source") == "Wikidata"
        and manifest.get("license") == "CC0-1.0",
        "Unsupported designation source/license",
    )
    _require(
        manifest.get("file") == "wikidata.json", "Invalid snapshot filename"
    )
    digest = manifest.get("sha256")
    _require(
        isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest),
        "Invalid snapshot digest",
    )
    payload = path.parent.joinpath("wikidata.json").read_bytes()
    _require(
        hashlib.sha256(payload).hexdigest() == digest,
        "Designation snapshot digest mismatch",
    )
    document = _json(payload)
    _keys(document, ("schema", "records", "unjoined_statements"))
    _require(
        document["schema"] == "wenu-wikidata-designations/1",
        "Unsupported snapshot schema",
    )
    _require(
        isinstance(document["records"], list)
        and isinstance(document["unjoined_statements"], list),
        "Invalid snapshot collections",
    )
    index = {}
    ids = set()

    def checked_statement(value):
        result = _statement(value)
        _require(
            result.statement_id not in ids, "Duplicate designation statement"
        )
        ids.add(result.statement_id)
        return result

    for value in document["records"]:
        _keys(value, ("hip", "statements", "names", "review_fields"))
        hip = value["hip"]
        _require(
            type(hip) is int and hip > 0 and hip not in index,
            "Invalid/duplicate HIP",
        )
        _require(
            isinstance(value["statements"], list)
            and isinstance(value["names"], list),
            "Invalid candidate collections",
        )
        statements = tuple(checked_statement(s) for s in value["statements"])
        for statement in statements:
            active = [
                link.value
                for link in statement.hip_links
                if link.rank != "DeprecatedRank"
            ]
            _require(
                bool(active) and set(active) == {f"HIP {hip}"},
                "Unsafe HIP join",
            )
        names = []
        for name in value["names"]:
            _require(
                isinstance(name, list) and len(name) == 4,
                "Invalid name candidate",
            )
            _require(
                name[3] in ("label", "alias") and name[2] == "en",
                "Invalid name scope",
            )
            names.append(
                NameCandidate(_item(name[0]), _text(name[1]), name[2], name[3])
            )
        _require(len(set(names)) == len(names), "Duplicate name candidate")
        fields = value["review_fields"]
        _require(
            isinstance(fields, list)
            and all(x in ("bayer", "flam") for x in fields)
            and len(set(fields)) == len(fields),
            "Invalid review fields",
        )
        index[hip] = StarDesignations(
            hip, statements, tuple(names), tuple(fields)
        )
    unjoined = tuple(
        checked_statement(s) for s in document["unjoined_statements"]
    )
    for key, count in (
        ("record_count", len(index)),
        ("statement_count", len(ids)),
        ("unjoined_statement_count", len(unjoined)),
    ):
        _require(
            type(manifest.get(key)) is int and manifest[key] == count,
            "Snapshot count mismatch",
        )
    return StarDesignationCatalogue(
        _text(manifest["edition"]), digest, MappingProxyType(index), unjoined
    )
