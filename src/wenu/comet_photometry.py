"""Observer-dependent comet model magnitude from NASA/JPL Horizons."""

from __future__ import annotations

import base64
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import tempfile
from typing import Callable
from urllib.request import Request, urlopen

from astropy.time import Time

from wenu.comet_designations import parse_comet_designation
from wenu.comet_discovery import CometDiscoveryRecord, CometDiscoveryResult
from wenu.observer import Observer


HORIZONS_API = "https://ssd.jpl.nasa.gov/api/horizons_file.api"
HORIZONS_SOURCE = "NASA/JPL Horizons API"
DEFAULT_MAGNITUDE_STEP = "1d"
DEFAULT_PERIHELION_WINDOW_DAYS = 30
MAX_COMETS = 50
MAX_SAMPLES_PER_COMET = 367
DEFAULT_WORKERS = 4
MAX_WORKERS = 8
_MULTIPART_BOUNDARY = "wenu-horizons-photometry"

_STEP = re.compile(r"(?P<count>[1-9]\d*)\s*(?P<unit>[hd])", re.IGNORECASE)
_SOLUTION = re.compile(r"soln ref\.\s*=\s*(?P<value>[^,\n]+)")
_TARGET = re.compile(r"Target body name:\s*(?P<value>[^\n]+)")
_TARGET_SOURCE = re.compile(r"\{source:\s*(?P<value>[^}]+?)\s*\}")


@dataclass(frozen=True)
class CometMagnitudeSample:
    """One sampled Horizons comet total/nuclear model magnitude."""

    epoch_utc: datetime
    total_magnitude: float | None
    nuclear_magnitude: float | None


@dataclass(frozen=True)
class CometPhotometryResult:
    """One comet's sampled model photometry and exact provider provenance."""

    canonical_designation: str
    provider_spk_id: str
    orbit_solution_id: str
    provider: str
    provider_endpoint: str
    provider_transport: str
    provider_version: str
    observer_location: str
    observer_latitude_deg: float
    observer_longitude_deg: float
    observer_elevation_m: float
    start_utc: datetime
    stop_utc: datetime
    magnitude_step: str
    request_parameters: tuple[tuple[str, str], ...]
    raw_sha256: str
    retrieved_at_utc: datetime
    notices: tuple[str, ...]
    samples: tuple[CometMagnitudeSample, ...]

    @property
    def brightest_total_sample(self) -> CometMagnitudeSample | None:
        """Return the numerically smallest sampled T-mag, if any."""
        available = tuple(
            sample for sample in self.samples
            if sample.total_magnitude is not None
        )
        if not available:
            return None
        return min(
            available,
            key=lambda sample: (sample.total_magnitude, sample.epoch_utc),
        )

    @property
    def brightest_nuclear_sample(self) -> CometMagnitudeSample | None:
        """Return the numerically smallest sampled N-mag, if any."""
        available = tuple(
            sample for sample in self.samples
            if sample.nuclear_magnitude is not None
        )
        if not available:
            return None
        return min(
            available,
            key=lambda sample: (sample.nuclear_magnitude, sample.epoch_utc),
        )


@dataclass(frozen=True)
class CometDiscoveryPhotometry:
    """Observer and cadence shared by a complete discovery characterization."""

    observer_location: str
    observer_latitude_deg: float
    observer_longitude_deg: float
    observer_elevation_m: float
    perihelion_window_days: int
    magnitude_step: str
    results: tuple[CometPhotometryResult, ...]


def parse_magnitude_step(value: str) -> tuple[str, timedelta]:
    """Validate a positive whole-number duration in hours or days."""
    if not isinstance(value, str):
        raise TypeError("magnitude step must be a string.")
    match = _STEP.fullmatch(value.strip())
    if match is None:
        raise ValueError(
            "magnitude step must be a positive whole number of hours or days "
            "(for example, 12h or 1d)."
        )
    count = int(match.group("count"))
    unit = match.group("unit").lower()
    duration = timedelta(hours=count) if unit == "h" else timedelta(days=count)
    return f"{count}{unit}", duration


def magnitude_sample_epochs(
    start_utc: datetime,
    stop_utc: datetime,
    magnitude_step: str | None = None,
) -> tuple[str, tuple[datetime, ...]]:
    """Return start-inclusive regular samples plus the exact stop endpoint."""
    if start_utc.tzinfo is None or stop_utc.tzinfo is None:
        raise ValueError("magnitude sampling bounds must be timezone-aware.")
    start = start_utc.astimezone(timezone.utc)
    stop = stop_utc.astimezone(timezone.utc)
    if stop < start:
        raise ValueError("magnitude sampling stop must not precede start.")
    if magnitude_step is None:
        minimum_hours = max(
            1,
            math.ceil(
                (stop - start).total_seconds()
                / (MAX_SAMPLES_PER_COMET - 1)
                / 3600.0
            ),
        )
        default_hours = int(
            parse_magnitude_step(DEFAULT_MAGNITUDE_STEP)[1].total_seconds()
            / 3600.0
        )
        selected_hours = max(default_hours, minimum_hours)
        magnitude_step = (
            f"{selected_hours // 24}d"
            if selected_hours % 24 == 0
            else f"{selected_hours}h"
        )
    canonical, duration = parse_magnitude_step(magnitude_step)
    count = int((stop - start) // duration)
    epochs = [start + index * duration for index in range(count + 1)]
    if epochs[-1] != stop:
        epochs.append(stop)
    if len(epochs) > MAX_SAMPLES_PER_COMET:
        minimum_hours = math.ceil(
            (stop - start).total_seconds()
            / (MAX_SAMPLES_PER_COMET - 1)
            / 3600.0
        )
        minimum = (
            f"{minimum_hours // 24}d"
            if minimum_hours % 24 == 0
            else f"{minimum_hours}h"
        )
        raise ValueError(
            f"magnitude sampling requires {len(epochs)} epochs; "
            f"the limit is {MAX_SAMPLES_PER_COMET}. The minimum usable "
            f"--magnitude-step for this window is {minimum}."
        )
    return canonical, tuple(epochs)


def perihelion_sampling_window(
    record: CometDiscoveryRecord,
    *,
    window_days: int = DEFAULT_PERIHELION_WINDOW_DAYS,
) -> tuple[datetime, datetime]:
    """Return the UTC interval equally bounded around perihelion."""
    if not isinstance(record, CometDiscoveryRecord):
        raise TypeError("photometry requires a comet discovery record.")
    if isinstance(window_days, bool) or not isinstance(window_days, int):
        raise TypeError("perihelion window must be a whole number of days.")
    if window_days <= 0:
        raise ValueError("perihelion window must be positive.")
    center = Time(
        record.perihelion_jd_tdb, format="jd", scale="tdb"
    ).utc.to_datetime(timezone=timezone.utc)
    width = timedelta(days=window_days)
    return center - width, center + width


def _horizons_command(record: CometDiscoveryRecord) -> str:
    parsed = parse_comet_designation(record.canonical_designation)
    flags = [f"DES={record.primary_designation}", "CAP"]
    if parsed.fragment is None:
        flags.append("NOFRAG")
    return ";".join(flags)


def photometry_query_parameters(
    record: CometDiscoveryRecord,
    *,
    latitude_deg: float,
    longitude_deg: float,
    elevation_m: float,
    epochs_utc: tuple[datetime, ...],
) -> dict[str, str]:
    """Build one exact, airless, topocentric Horizons observer request."""
    if not isinstance(record, CometDiscoveryRecord):
        raise TypeError("photometry requires a comet discovery record.")
    if not epochs_utc:
        raise ValueError("photometry requires at least one sample epoch.")
    coordinates = (float(latitude_deg), float(longitude_deg), float(elevation_m))
    if not all(math.isfinite(value) for value in coordinates):
        raise ValueError("observer coordinates and elevation must be finite.")
    if not -90.0 <= coordinates[0] <= 90.0:
        raise ValueError("observer latitude must be between -90 and 90 degrees.")
    if not -180.0 <= coordinates[1] <= 180.0:
        raise ValueError(
            "observer longitude must be between -180 and 180 degrees."
        )
    jd_values = []
    for epoch in epochs_utc:
        if epoch.tzinfo is None:
            raise ValueError("sample epochs must be timezone-aware.")
        jd_values.append(
            f"{float(Time(epoch, scale='utc').utc.jd):.12f}"
        )
    return {
        "format": "json",
        "COMMAND": f"'{_horizons_command(record)}'",
        "OBJ_DATA": "'YES'",
        "MAKE_EPHEM": "'YES'",
        "TABLE_TYPE": "'OBSERVER'",
        "CENTER": "'coord@399'",
        "COORD_TYPE": "'GEODETIC'",
        "SITE_COORD": (
            f"'{coordinates[1]:.12g},{coordinates[0]:.12g},"
            f"{coordinates[2] / 1000.0:.12g}'"
        ),
        # Horizons batch input accepts continuation lines. Keep each epoch on
        # its own line so the file transport does not encounter the batch
        # parser's practical input-line limit.
        "TLIST": "'" + "','\n'".join(jd_values) + "'",
        "TLIST_TYPE": "'JD'",
        "TIME_TYPE": "'UT'",
        "CAL_FORMAT": "'BOTH'",
        "TIME_DIGITS": "'FRACSEC'",
        "QUANTITIES": "'9'",
        "CSV_FORMAT": "'YES'",
        "APPARENT": "'AIRLESS'",
        "SKIP_DAYLT": "'NO'",
        "ELEV_CUT": "'-90'",
    }


def photometry_batch_input(parameters: dict[str, str]) -> str:
    """Serialize API parameters as a Horizons batch input file."""
    return "!$$SOF\n" + "\n".join(
        f"{key}={value}"
        for key, value in parameters.items()
        if key != "format"
    ) + "\n"


def _multipart_body(parameters: dict[str, str]) -> bytes:
    batch = photometry_batch_input(parameters)
    parts = (
        f"--{_MULTIPART_BOUNDARY}\r\n"
        'Content-Disposition: form-data; name="format"\r\n\r\n'
        "json\r\n"
        f"--{_MULTIPART_BOUNDARY}\r\n"
        'Content-Disposition: form-data; name="input"; '
        'filename="wenu-horizons.txt"\r\n'
        "Content-Type: text/plain; charset=utf-8\r\n\r\n"
        f"{batch}\r\n"
        f"--{_MULTIPART_BOUNDARY}--\r\n"
    )
    return parts.encode("utf-8")


def _fetch(
    url: str, parameters: dict[str, str], *, timeout: int = 120
) -> bytes:
    request = Request(
        url,
        data=_multipart_body(parameters),
        headers={
            "Content-Type": (
                "multipart/form-data; boundary=" + _MULTIPART_BOUNDARY
            )
        },
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def default_photometry_cache_directory() -> Path:
    """Return Wenu's user-local raw Horizons photometry cache."""
    return Path.home() / ".cache" / "wenu" / "comet_photometry"


def _cache_key(parameters: dict[str, str]) -> str:
    identity = json.dumps(
        {"endpoint": HORIZONS_API, "parameters": parameters},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(identity).hexdigest()


def _read_cached_response(
    directory: Path, parameters: dict[str, str]
) -> tuple[bytes, datetime] | None:
    key = _cache_key(parameters)
    path = directory / f"{key}.json"
    if not path.exists():
        return None
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
        if document["schema"] != 1 or document["key"] != key:
            raise ValueError
        raw = base64.b64decode(document["response_base64"], validate=True)
        if sha256(raw).hexdigest() != document["response_sha256"]:
            raise ValueError
        retrieved = datetime.fromisoformat(document["retrieved_at_utc"])
        if retrieved.tzinfo is None:
            raise ValueError
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid photometry cache entry: {path}") from error
    return raw, retrieved.astimezone(timezone.utc)


def _write_cached_response(
    directory: Path,
    parameters: dict[str, str],
    raw: bytes,
    retrieved: datetime,
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    key = _cache_key(parameters)
    document = {
        "schema": 1,
        "key": key,
        "endpoint": HORIZONS_API,
        "parameters": parameters,
        "response_sha256": sha256(raw).hexdigest(),
        "response_base64": base64.b64encode(raw).decode("ascii"),
        "retrieved_at_utc": retrieved.astimezone(timezone.utc).isoformat(),
    }
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=directory,
        prefix=f".{key}-", suffix=".tmp", delete=False,
    ) as temporary:
        json.dump(document, temporary, indent=2, sort_keys=True)
        temporary.write("\n")
        temporary_path = Path(temporary.name)
    temporary_path.replace(directory / f"{key}.json")


def _normalized_solution(value: str) -> str:
    result = " ".join(value.strip().split())
    result = re.sub(r"^JPL(?:#|\s)+", "", result, flags=re.IGNORECASE)
    return result.casefold()


def _target_identity(
    record: CometDiscoveryRecord,
    target_value: str,
) -> tuple[bool, str | None]:
    source = _TARGET_SOURCE.search(target_value)
    name = (
        target_value[:source.start()].strip()
        if source
        else target_value.strip()
    )
    designation = record.canonical_designation
    matches = (
        name == designation
        or name.startswith(designation + " ")
        or name.startswith(designation + "/")
        or name.endswith(f"({designation})")
    )
    return matches, None if source is None else source.group("value")


def _optional_magnitude(value: str) -> float | None:
    text = value.strip()
    if not text or text.casefold() in {"n.a.", "n.a", "na"}:
        return None
    result = float(text)
    if not math.isfinite(result):
        raise ValueError("Horizons magnitude must be finite.")
    return result


def _column_index(headers: tuple[str, ...], token: str) -> int:
    for index, header in enumerate(headers):
        if token.casefold() in header.casefold():
            return index
    raise ValueError(f"Horizons photometry table lacks {token!r} column.")


def _magnitude_notices(result: str, eoe_index: int) -> tuple[str, ...]:
    notices = []
    for line in result[eoe_index:].splitlines()[1:]:
        text = " ".join(line.strip().split())
        lowered = text.casefold()
        if text and any(
            token in lowered
            for token in ("magnitude", "t-mag", "n-mag", "phase angle")
        ):
            if text not in notices:
                notices.append(text)
    return tuple(notices)


def parse_photometry_response(
    raw: bytes,
    *,
    record: CometDiscoveryRecord,
    requested_epochs_utc: tuple[datetime, ...],
) -> tuple[str, tuple[CometMagnitudeSample, ...], tuple[str, ...]]:
    """Validate one complete frozen Horizons observer-table response."""
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(
            "Horizons photometry response is not valid UTF-8 JSON."
        ) from error
    signature = document.get("signature")
    if (
        not isinstance(signature, dict)
        or signature.get("source") != HORIZONS_SOURCE
        or not str(signature.get("version", "")).strip()
    ):
        raise ValueError(
            "Horizons photometry response has no accepted API signature."
        )
    result = document.get("result")
    if not isinstance(result, str):
        raise ValueError("Horizons photometry response has no result text.")

    target = _TARGET.search(result)
    target_matches, target_solution = (
        (False, None)
        if target is None
        else _target_identity(record, target.group("value"))
    )
    if not target_matches:
        raise ValueError(
            "Horizons photometry target differs from the discovery identity."
        )
    if (
        target_solution is None
        or _normalized_solution(target_solution) != _normalized_solution(
            record.orbit_solution_id or ""
        )
    ):
        raise ValueError(
            "Horizons target source and SBDB orbit solutions differ."
        )
    solution = _SOLUTION.search(result)
    if solution is None:
        raise ValueError(
            "Horizons photometry result lacks orbit-solution identity."
        )
    if _normalized_solution(solution.group("value")) != _normalized_solution(
        record.orbit_solution_id or ""
    ):
        raise ValueError(
            "Horizons and SBDB photometry orbit solutions differ."
        )

    soe_index = result.find("$$SOE")
    eoe_index = result.find("$$EOE")
    if soe_index < 0 or eoe_index <= soe_index:
        raise ValueError("Horizons photometry result has no complete table.")
    preamble = result[:soe_index].splitlines()
    header_line = next(
        (
            line for line in reversed(preamble)
            if "T-mag" in line and "N-mag" in line
        ),
        None,
    )
    if header_line is None:
        raise ValueError(
            "Horizons photometry result lacks T-mag and N-mag headers."
        )
    headers = tuple(value.strip() for value in next(csv.reader([header_line])))
    jd_index = _column_index(headers, "JDUT")
    total_index = _column_index(headers, "T-mag")
    nuclear_index = _column_index(headers, "N-mag")
    required_index = max(jd_index, total_index, nuclear_index)

    samples = []
    table = result[soe_index + len("$$SOE"):eoe_index]
    for line in table.splitlines():
        if not line.strip():
            continue
        values = tuple(value.strip() for value in next(csv.reader([line])))
        if len(values) <= required_index:
            raise ValueError(
                "Horizons photometry table contains a malformed row."
            )
        try:
            jd_utc = float(values[jd_index])
            if not math.isfinite(jd_utc):
                raise ValueError
            epoch = Time(jd_utc, format="jd", scale="utc").to_datetime(
                timezone=timezone.utc
            )
            total = _optional_magnitude(values[total_index])
            nuclear = _optional_magnitude(values[nuclear_index])
        except (TypeError, ValueError) as error:
            raise ValueError(
                "Horizons photometry table contains invalid values."
            ) from error
        samples.append(CometMagnitudeSample(
            epoch_utc=epoch,
            total_magnitude=total,
            nuclear_magnitude=nuclear,
        ))

    if len(samples) != len(requested_epochs_utc):
        raise ValueError(
            "Horizons photometry sample count differs from the request."
        )
    for sample, requested in zip(samples, requested_epochs_utc):
        expected = requested.astimezone(timezone.utc)
        if abs((sample.epoch_utc - expected).total_seconds()) > 1.0:
            raise ValueError(
                "Horizons photometry sample epoch differs from the request."
            )
    return (
        str(signature["version"]),
        tuple(samples),
        _magnitude_notices(result, eoe_index),
    )


def characterize_discovery_photometry(
    discovery: CometDiscoveryResult,
    *,
    observer_location: str,
    magnitude_step: str | None = None,
    perihelion_window_days: int = DEFAULT_PERIHELION_WINDOW_DAYS,
    max_comets: int = MAX_COMETS,
    fetch: Callable[[str, dict[str, str]], bytes] = _fetch,
    now: Callable[[], datetime] | None = None,
    progress: Callable[[int, int, str, bool], None] | None = None,
    workers: int = 1,
    cache_directory: Path | None = None,
    refresh_cache: bool = False,
) -> CometDiscoveryPhotometry:
    """Characterize discovered solutions with cached bounded Horizons calls."""
    if not isinstance(discovery, CometDiscoveryResult):
        raise TypeError("photometry requires a comet discovery result.")
    if isinstance(max_comets, bool) or not isinstance(max_comets, int):
        raise TypeError("maximum photometry comets must be a whole number.")
    if max_comets <= 0:
        raise ValueError("maximum photometry comets must be positive.")
    if isinstance(workers, bool) or not isinstance(workers, int):
        raise TypeError("photometry workers must be a whole number.")
    if not 1 <= workers <= MAX_WORKERS:
        raise ValueError(
            f"photometry workers must be between 1 and {MAX_WORKERS}."
        )
    if len(discovery.records) > max_comets:
        raise ValueError(
            f"photometry selected {len(discovery.records)} comets; "
            f"the current limit is {max_comets}. Use "
            f"--max-photometry-comets {len(discovery.records)} to "
            "authorize that workload, or narrow the discovery."
        )
    location_name = str(observer_location).strip()
    if not location_name:
        raise ValueError("observer location must be non-empty.")
    latitude, longitude, elevation, _ = Observer.resolve_scientific_identity(
        location=location_name,
        time=discovery.start_utc,
    )

    clock = now or (lambda: datetime.now(timezone.utc))
    cache = None if cache_directory is None else Path(cache_directory).expanduser()
    prepared = []
    selected_step = None
    total = len(discovery.records)
    for index, record in enumerate(discovery.records):
        start, stop = perihelion_sampling_window(
            record, window_days=perihelion_window_days
        )
        step, epochs = magnitude_sample_epochs(start, stop, magnitude_step)
        if selected_step is None:
            selected_step = step
        elif selected_step != step:
            selected_step = "per-comet automatic"
        parameters = photometry_query_parameters(
            record,
            latitude_deg=latitude,
            longitude_deg=longitude,
            elevation_m=elevation,
            epochs_utc=epochs,
        )
        prepared.append((index, record, start, stop, step, epochs, parameters))

    def characterize(item):
        index, record, start, stop, step, epochs, parameters = item
        cached = None
        if cache is not None and not refresh_cache:
            cached = _read_cached_response(cache, parameters)
        if cached is None:
            raw = fetch(HORIZONS_API, parameters)
            retrieved = clock()
            if retrieved.tzinfo is None:
                retrieved = retrieved.replace(tzinfo=timezone.utc)
            retrieved = retrieved.astimezone(timezone.utc)
            cache_hit = False
        else:
            raw, retrieved = cached
            cache_hit = True
        try:
            version, samples, notices = parse_photometry_response(
                raw,
                record=record,
                requested_epochs_utc=epochs,
            )
        except ValueError as error:
            raise ValueError(
                "Horizons photometry failed for "
                f"{record.canonical_designation}: {error}"
            ) from error
        if cache is not None and not cache_hit:
            _write_cached_response(cache, parameters, raw, retrieved)
        result = CometPhotometryResult(
            canonical_designation=record.canonical_designation,
            provider_spk_id=record.spk_id,
            orbit_solution_id=record.orbit_solution_id or "unknown",
            provider=HORIZONS_SOURCE,
            provider_endpoint=HORIZONS_API,
            provider_transport="multipart/form-data POST",
            provider_version=version,
            observer_location=location_name,
            observer_latitude_deg=latitude,
            observer_longitude_deg=longitude,
            observer_elevation_m=elevation,
            start_utc=start,
            stop_utc=stop,
            magnitude_step=step,
            request_parameters=tuple(sorted(parameters.items())),
            raw_sha256=sha256(raw).hexdigest(),
            retrieved_at_utc=retrieved,
            notices=notices,
            samples=samples,
        )
        return index, result, cache_hit

    results = [None] * total
    if progress is not None:
        progress(0, total, "starting", False)
    if workers == 1:
        completed = (characterize(item) for item in prepared)
        for count, (index, result, cache_hit) in enumerate(completed, start=1):
            results[index] = result
            if progress is not None:
                progress(count, total, result.canonical_designation, cache_hit)
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(characterize, item) for item in prepared]
            for count, future in enumerate(as_completed(futures), start=1):
                index, result, cache_hit = future.result()
                results[index] = result
                if progress is not None:
                    progress(
                        count, total, result.canonical_designation, cache_hit
                    )
    return CometDiscoveryPhotometry(
        observer_location=location_name,
        observer_latitude_deg=latitude,
        observer_longitude_deg=longitude,
        observer_elevation_m=elevation,
        perihelion_window_days=perihelion_window_days,
        magnitude_step=selected_step or (
            magnitude_step or DEFAULT_MAGNITUDE_STEP
        ),
        results=tuple(results),
    )
