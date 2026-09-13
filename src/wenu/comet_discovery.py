"""Provider-neutral comet discovery through the NASA/JPL SBDB Query API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from hashlib import sha256
import json
import math
import re
from typing import Callable
from urllib.parse import urlencode
from urllib.request import urlopen

from astropy.time import Time


SBDB_QUERY_API = "https://ssd-api.jpl.nasa.gov/sbdb_query.api"
SBDB_QUERY_SOURCE = "NASA/JPL SBDB (Small-Body DataBase) Query API"
DEFAULT_MAX_PERIHELION_DISTANCE_AU = 5.0

DISCOVERY_FIELDS = (
    "spkid", "full_name", "kind", "pdes", "name", "prefix", "class",
    "q", "tp", "tp_cal", "e", "i", "per", "moid", "t_jup",
    "orbit_id", "M1", "M2", "K1", "K2",
)


@dataclass(frozen=True)
class CometDiscoveryRecord:
    """One current comet solution returned by SBDB."""

    spk_id: str
    full_name: str
    kind: str
    primary_designation: str
    name: str | None
    prefix: str | None
    orbit_class: str | None
    perihelion_distance_au: float
    perihelion_jd_tdb: float
    perihelion_calendar_tdb: str | None
    eccentricity: float | None
    inclination_deg: float | None
    period_days: float | None
    earth_moid_au: float | None
    tisserand_jupiter: float | None
    orbit_solution_id: str | None
    magnitude_model_m1: float | None
    magnitude_model_m2: float | None
    magnitude_model_k1: float | None
    magnitude_model_k2: float | None

    @property
    def canonical_designation(self) -> str:
        numbered = re.fullmatch(
            r"\d+[PDI](?:-[A-Z0-9]+)?",
            self.primary_designation,
            flags=re.IGNORECASE,
        )
        if numbered is not None or self.prefix is None:
            return self.primary_designation
        return f"{self.prefix}/{self.primary_designation}"

    @property
    def perihelion_date_utc(self) -> str:
        return Time(
            self.perihelion_jd_tdb, format="jd", scale="tdb"
        ).utc.datetime.date().isoformat()


@dataclass(frozen=True)
class CometDiscoveryResult:
    """Immutable discovery rows plus exact provider provenance."""

    start_utc: datetime
    stop_utc: datetime
    max_perihelion_distance_au: float
    retrieved_at_utc: datetime
    provider: str
    provider_version: str
    request_parameters: tuple[tuple[str, str], ...]
    raw_sha256: str
    records: tuple[CometDiscoveryRecord, ...]


def civil_utc_interval(start: str, stop: str) -> tuple[datetime, datetime]:
    """Parse an inclusive pair of ISO civil dates as complete UTC days."""
    try:
        start_date = date.fromisoformat(start)
        stop_date = date.fromisoformat(stop)
    except ValueError as error:
        raise ValueError(
            "START and STOP must be ISO dates (YYYY-MM-DD)."
        ) from error
    if stop_date < start_date:
        raise ValueError("STOP must not precede START.")
    return (
        datetime.combine(start_date, time.min, tzinfo=timezone.utc),
        datetime.combine(stop_date, time.max, tzinfo=timezone.utc),
    )


def discovery_query_parameters(
    start_utc: datetime,
    stop_utc: datetime,
    max_perihelion_distance_au: float,
) -> dict[str, str]:
    """Build the complete deterministic SBDB query parameter mapping."""
    maximum = float(max_perihelion_distance_au)
    if not math.isfinite(maximum) or maximum <= 0.0:
        raise ValueError("maximum perihelion distance must be positive.")
    start_jd = Time(start_utc, scale="utc").tdb.jd
    stop_jd = Time(stop_utc, scale="utc").tdb.jd
    constraints = json.dumps(
        {"AND": [
            f"tp|RG|{start_jd:.12f}|{stop_jd:.12f}",
            f"q|LE|{maximum:.15g}",
        ]},
        separators=(",", ":"),
    )
    return {
        "fields": ",".join(DISCOVERY_FIELDS),
        "sb-kind": "c",
        "sb-cdata": constraints,
        "sort": "tp,pdes",
        "full-prec": "true",
    }


def _fetch(
    url: str, parameters: dict[str, str], *, timeout: int = 120
) -> bytes:
    request_url = url + "?" + urlencode(parameters)
    with urlopen(request_url, timeout=timeout) as response:
        return response.read()


def _optional_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("SBDB numeric value must be finite.")
    return result


def _required_text(value: object) -> str:
    result = str(value).strip() if value is not None else ""
    if not result:
        raise ValueError("SBDB required text value is missing.")
    return result


def _required_float(value: object) -> float:
    result = _optional_float(value)
    if result is None:
        raise ValueError("SBDB required numeric value is missing.")
    return result


def parse_discovery_response(
    raw: bytes,
) -> tuple[str, str, tuple[CometDiscoveryRecord, ...]]:
    """Validate and parse one frozen SBDB Query API response."""
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(
            "SBDB discovery response is not valid UTF-8 JSON."
        ) from error
    signature = document.get("signature")
    if (
        not isinstance(signature, dict)
        or signature.get("source") != SBDB_QUERY_SOURCE
    ):
        raise ValueError(
            "SBDB discovery response has no accepted API signature."
        )
    if document.get("fields") != list(DISCOVERY_FIELDS):
        raise ValueError(
            "SBDB discovery response fields differ from the requested schema."
        )
    data = document.get("data")
    if not isinstance(data, list):
        raise ValueError("SBDB discovery response has no data rows.")
    records = []
    for values in data:
        if (
            not isinstance(values, list)
            or len(values) != len(DISCOVERY_FIELDS)
        ):
            raise ValueError(
                "SBDB discovery response contains a malformed row."
            )
        row = dict(zip(DISCOVERY_FIELDS, values))
        if row["kind"] not in {"cn", "cu"}:
            raise ValueError(
                "SBDB discovery response contains a non-comet row."
            )
        try:
            record = CometDiscoveryRecord(
                spk_id=_required_text(row["spkid"]),
                full_name=_required_text(row["full_name"]),
                kind=str(row["kind"]),
                primary_designation=_required_text(row["pdes"]),
                name=str(row["name"]).strip() if row["name"] else None,
                prefix=str(row["prefix"]).strip() if row["prefix"] else None,
                orbit_class=(
                    str(row["class"]).strip() if row["class"] else None
                ),
                perihelion_distance_au=_required_float(row["q"]),
                perihelion_jd_tdb=_required_float(row["tp"]),
                perihelion_calendar_tdb=(
                    str(row["tp_cal"]).strip() if row["tp_cal"] else None
                ),
                eccentricity=_optional_float(row["e"]),
                inclination_deg=_optional_float(row["i"]),
                period_days=_optional_float(row["per"]),
                earth_moid_au=_optional_float(row["moid"]),
                tisserand_jupiter=_optional_float(row["t_jup"]),
                orbit_solution_id=(
                    str(row["orbit_id"]).strip() if row["orbit_id"] else None
                ),
                magnitude_model_m1=_optional_float(row["M1"]),
                magnitude_model_m2=_optional_float(row["M2"]),
                magnitude_model_k1=_optional_float(row["K1"]),
                magnitude_model_k2=_optional_float(row["K2"]),
            )
        except (TypeError, ValueError) as error:
            raise ValueError(
                "SBDB discovery response contains invalid values."
            ) from error
        records.append(record)
    records.sort(key=lambda value: (
        value.perihelion_jd_tdb,
        value.canonical_designation.casefold(),
    ))
    return (
        str(signature.get("version", "unknown")),
        str(document.get("count", len(records))),
        tuple(records),
    )


def discover_comets(
    start: str,
    stop: str,
    *,
    max_perihelion_distance_au: float = DEFAULT_MAX_PERIHELION_DISTANCE_AU,
    fetch: Callable[[str, dict[str, str]], bytes] = _fetch,
    now: Callable[[], datetime] | None = None,
) -> CometDiscoveryResult:
    """Retrieve comets meeting the declared perihelion-time/distance filter."""
    start_utc, stop_utc = civil_utc_interval(start, stop)
    maximum = float(max_perihelion_distance_au)
    parameters = discovery_query_parameters(
        start_utc, stop_utc, maximum
    )
    raw = fetch(SBDB_QUERY_API, parameters)
    version, count, records = parse_discovery_response(raw)
    if int(count) != len(records):
        raise ValueError("SBDB discovery count does not match returned rows.")
    start_jd = float(Time(start_utc, scale="utc").tdb.jd)
    stop_jd = float(Time(stop_utc, scale="utc").tdb.jd)
    if any(
        not start_jd <= record.perihelion_jd_tdb <= stop_jd
        or record.perihelion_distance_au > maximum
        for record in records
    ):
        raise ValueError("SBDB discovery row falls outside the requested filter.")
    clock = now or (lambda: datetime.now(timezone.utc))
    retrieved = clock()
    if retrieved.tzinfo is None:
        retrieved = retrieved.replace(tzinfo=timezone.utc)
    return CometDiscoveryResult(
        start_utc=start_utc,
        stop_utc=stop_utc,
        max_perihelion_distance_au=maximum,
        retrieved_at_utc=retrieved.astimezone(timezone.utc),
        provider=SBDB_QUERY_SOURCE,
        provider_version=version,
        request_parameters=tuple(sorted(parameters.items())),
        raw_sha256=sha256(raw).hexdigest(),
        records=records,
    )
