"""Provider-neutral comet discovery through the NASA/JPL SBDB Query API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from hashlib import sha256
import json
from typing import Callable
from urllib.parse import urlencode
from urllib.request import urlopen

from astropy.time import Time


SBDB_QUERY_API = "https://ssd-api.jpl.nasa.gov/sbdb_query.api"
SBDB_QUERY_SOURCE = "NASA/JPL SBDB Query API"
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
    if maximum <= 0.0:
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
    return float(value)


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
                spk_id=str(row["spkid"]),
                full_name=str(row["full_name"]).strip(),
                kind=str(row["kind"]),
                primary_designation=str(row["pdes"]).strip(),
                name=str(row["name"]).strip() if row["name"] else None,
                prefix=str(row["prefix"]).strip() if row["prefix"] else None,
                orbit_class=(
                    str(row["class"]).strip() if row["class"] else None
                ),
                perihelion_distance_au=float(row["q"]),
                perihelion_jd_tdb=float(row["tp"]),
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
        value.primary_designation.casefold(),
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
    parameters = discovery_query_parameters(
        start_utc, stop_utc, max_perihelion_distance_au
    )
    raw = fetch(SBDB_QUERY_API, parameters)
    version, count, records = parse_discovery_response(raw)
    if int(count) != len(records):
        raise ValueError("SBDB discovery count does not match returned rows.")
    clock = now or (lambda: datetime.now(timezone.utc))
    retrieved = clock()
    if retrieved.tzinfo is None:
        retrieved = retrieved.replace(tzinfo=timezone.utc)
    return CometDiscoveryResult(
        start_utc=start_utc,
        stop_utc=stop_utc,
        max_perihelion_distance_au=float(max_perihelion_distance_au),
        retrieved_at_utc=retrieved.astimezone(timezone.utc),
        provider=SBDB_QUERY_SOURCE,
        provider_version=version,
        request_parameters=tuple(sorted(parameters.items())),
        raw_sha256=sha256(raw).hexdigest(),
        records=records,
    )
