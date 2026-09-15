"""Policy-compliant SatChecker crossing adapter and exact local cache."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import warnings

from astropy.time import Time
from astropy.utils import iers

from wenu.coordinates import PositionStatus
from wenu.satellite_crossings import (
    InclusiveTimeInterval,
    SatelliteCrossingCandidate,
    SatelliteFieldOfView,
    SatelliteIdentity,
    SatelliteObserver,
)


SATCHECKER_BASE_URL = "https://satchecker.cps.iau.org"
SATCHECKER_PROVIDER = "IAU CPS SatChecker"
SATCHECKER_SCHEMA_VERSION = 1
_SAMPLE_WARNING = (
    "SatChecker uses a one-second stop-exclusive sampling grid; absence "
    "between samples is not a no-crossing proof."
)
_ENVELOPE_WARNING = (
    "SatChecker returns a 1.2-radius candidate envelope; samples are not "
    "exact Wenu boundary events."
)


def _utc_text(value, *, name):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string.")
    candidate = value.strip()
    if candidate.endswith(" UTC"):
        candidate = candidate[:-4] + "+00:00"
    elif candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        instant = datetime.fromisoformat(candidate)
    except ValueError as error:
        raise ValueError(f"{name} must be an ISO-8601 UTC instant.") from error
    if instant.tzinfo is None or instant.utcoffset() != timezone.utc.utcoffset(
        instant
    ):
        raise ValueError(f"{name} must be an ISO-8601 UTC instant.")
    return instant.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _retrieved_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _utc_to_ut1_jd(value):
    with iers.conf.set_temp("auto_download", False):
        with warnings.catch_warnings():
            warnings.simplefilter("error", iers.IERSWarning)
            try:
                return float(Time(value, scale="utc").ut1.jd)
            except (ValueError, iers.IERSRangeError, iers.IERSWarning) as error:
                raise ValueError(
                    "UTC-to-UT1 conversion requires valid local "
                    "Earth-orientation data."
                ) from error


def _ut1_jd_to_utc(value):
    with iers.conf.set_temp("auto_download", False):
        with warnings.catch_warnings():
            warnings.simplefilter("error", iers.IERSWarning)
            try:
                isot = Time(value, format="jd", scale="ut1").utc.isot
            except (ValueError, iers.IERSRangeError, iers.IERSWarning) as error:
                raise ValueError(
                    "UT1-to-UTC conversion requires valid local "
                    "Earth-orientation data."
                ) from error
    return _utc_text(isot + "Z", name="sample instant")


def _finite(value, *, name):
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a finite number.")
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise TypeError(f"{name} must be a finite number.") from error
    if not (-float("inf") < result < float("inf")):
        raise ValueError(f"{name} must be finite.")
    return result


def _canonical_json(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


@dataclass(frozen=True)
class SatCheckerQuery:
    """One exact versioned SatChecker request mapped from the 50S.1 domain."""

    observer: SatelliteObserver
    field_of_view: SatelliteFieldOfView
    interval: InclusiveTimeInterval
    start_time_ut1_jd: float
    duration_seconds: float
    earth_orientation_identity: str
    base_url: str = SATCHECKER_BASE_URL
    data_source: str = "any"

    def __post_init__(self):
        if not isinstance(self.observer, SatelliteObserver):
            raise TypeError("observer must be a SatelliteObserver.")
        if not isinstance(self.field_of_view, SatelliteFieldOfView):
            raise TypeError("field_of_view must be a SatelliteFieldOfView.")
        if not isinstance(self.interval, InclusiveTimeInterval):
            raise TypeError("interval must be an InclusiveTimeInterval.")
        spec = self.field_of_view.coordinate_spec
        if (
            spec.frame != "icrs"
            or spec.origin != "topocentric-direction"
            or spec.position_status is not PositionStatus.GEOMETRIC
        ):
            raise ValueError(
                "SatChecker requires geometric topocentric-direction ICRS "
                "field coordinates."
            )
        start = _finite(self.start_time_ut1_jd, name="start_time_ut1_jd")
        duration = _finite(self.duration_seconds, name="duration_seconds")
        if duration <= 0.0:
            raise ValueError("duration_seconds must be positive.")
        identity = str(self.earth_orientation_identity).strip()
        if not identity:
            raise ValueError("earth_orientation_identity must be non-empty.")
        base = str(self.base_url).strip().rstrip("/")
        if not base.startswith("https://"):
            raise ValueError("base_url must use HTTPS.")
        source = str(self.data_source).strip().lower()
        if source not in {"any", "celestrak", "spacetrack"}:
            raise ValueError("data_source is not supported by SatChecker.")
        object.__setattr__(self, "start_time_ut1_jd", start)
        object.__setattr__(self, "duration_seconds", duration)
        object.__setattr__(self, "earth_orientation_identity", identity)
        object.__setattr__(self, "base_url", base)
        object.__setattr__(self, "data_source", source)

    @classmethod
    def from_domain(
        cls,
        observer,
        field_of_view,
        interval,
        *,
        earth_orientation_identity,
        base_url=SATCHECKER_BASE_URL,
        data_source="any",
        utc_to_ut1_jd=_utc_to_ut1_jd,
    ):
        """Map one explicit domain query without network access."""
        start = datetime.fromisoformat(interval.start.replace("Z", "+00:00"))
        stop = datetime.fromisoformat(interval.stop.replace("Z", "+00:00"))
        duration = (stop - start).total_seconds()
        return cls(
            observer=observer,
            field_of_view=field_of_view,
            interval=interval,
            start_time_ut1_jd=utc_to_ut1_jd(interval.start),
            duration_seconds=duration,
            earth_orientation_identity=earth_orientation_identity,
            base_url=base_url,
            data_source=data_source,
        )

    @property
    def endpoint(self):
        return self.base_url + "/v1/fov/satellite-passes/"

    @property
    def parameters(self):
        return (
            ("latitude", self.observer.latitude_deg),
            ("longitude", self.observer.longitude_deg),
            ("elevation", self.observer.elevation_m),
            ("start_time_jd", self.start_time_ut1_jd),
            ("duration", self.duration_seconds),
            ("ra", self.field_of_view.center_longitude_deg),
            ("dec", self.field_of_view.center_latitude_deg),
            ("fov_radius", self.field_of_view.angular_radius_deg),
            ("group_by", "satellite"),
            ("include_orbital_data", "true"),
            ("data_source", self.data_source),
            ("illuminated_only", "false"),
            ("async", "true"),
            ("convert_omm_to_tle", "false"),
        )

    @property
    def canonical_document(self):
        return {
            "schema_version": SATCHECKER_SCHEMA_VERSION,
            "endpoint": self.endpoint,
            "parameters": dict(self.parameters),
            "wenu_request": {
                "observer": {
                    "observer_id": self.observer.observer_id,
                    "longitude_deg": self.observer.longitude_deg,
                    "latitude_deg": self.observer.latitude_deg,
                    "elevation_m": self.observer.elevation_m,
                    "refraction_policy": self.observer.refraction_policy,
                    "earth_orientation_policy": (
                        self.observer.earth_orientation_policy
                    ),
                },
                "field_of_view": {
                    "field_id": self.field_of_view.field_id,
                    "center_longitude_deg": (
                        self.field_of_view.center_longitude_deg
                    ),
                    "center_latitude_deg": (
                        self.field_of_view.center_latitude_deg
                    ),
                    "angular_radius_deg": (
                        self.field_of_view.angular_radius_deg
                    ),
                    "boundary": self.field_of_view.boundary,
                    "coordinate_spec": {
                        "frame": self.field_of_view.coordinate_spec.frame,
                        "origin": self.field_of_view.coordinate_spec.origin,
                        "position_status": (
                            self.field_of_view.coordinate_spec.position_status.value
                        ),
                        "instant": self.field_of_view.coordinate_spec.instant,
                        "time_scale": (
                            self.field_of_view.coordinate_spec.time_scale
                        ),
                    },
                },
                "interval": {
                    "start_utc": self.interval.start,
                    "stop_utc": self.interval.stop,
                    "time_scale": self.interval.time_scale,
                    "boundary": self.interval.boundary,
                },
            },
            "earth_orientation_identity": self.earth_orientation_identity,
        }

    @property
    def cache_key(self):
        return sha256(_canonical_json(self.canonical_document)).hexdigest()


@dataclass(frozen=True)
class SatCheckerReceipt:
    """Exact bytes and retrieval metadata for one provider interaction."""

    endpoint: str
    retrieved_at_utc: str
    http_status: int
    media_type: str
    headers: tuple[tuple[str, str], ...]
    body: bytes

    def __post_init__(self):
        endpoint = str(self.endpoint).strip()
        if not endpoint.startswith("https://"):
            raise ValueError("receipt endpoint must use HTTPS.")
        instant = _utc_text(self.retrieved_at_utc, name="retrieved_at_utc")
        if isinstance(self.http_status, bool) or not isinstance(
            self.http_status, int
        ):
            raise TypeError("http_status must be an integer.")
        media = str(self.media_type).split(";", 1)[0].strip().lower()
        normalized_headers = tuple(
            sorted(
                (
                    str(name).strip().lower(),
                    str(value).strip(),
                )
                for name, value in self.headers
            )
        )
        if not isinstance(self.body, bytes) or not self.body:
            raise ValueError("receipt body must contain exact response bytes.")
        object.__setattr__(self, "endpoint", endpoint)
        object.__setattr__(self, "retrieved_at_utc", instant)
        object.__setattr__(self, "media_type", media)
        object.__setattr__(self, "headers", normalized_headers)

    @property
    def body_sha256(self):
        return sha256(self.body).hexdigest()


class SatCheckerTaskState(str, Enum):
    PENDING = "PENDING"
    PROGRESS = "PROGRESS"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class SatCheckerSample:
    """One provider-sampled geometric topocentric direction."""

    instant_utc: str
    julian_date_ut1: float
    right_ascension_deg: float
    declination_deg: float
    angular_distance_deg: float
    altitude_deg: float | None = None
    azimuth_deg: float | None = None
    range_km: float | None = None
    illuminated: bool | None = None

    def __post_init__(self):
        object.__setattr__(
            self, "instant_utc", _utc_text(self.instant_utc, name="instant_utc")
        )
        for name in (
            "julian_date_ut1",
            "right_ascension_deg",
            "declination_deg",
            "angular_distance_deg",
        ):
            object.__setattr__(
                self, name, _finite(getattr(self, name), name=name)
            )
        if not -90.0 <= self.declination_deg <= 90.0:
            raise ValueError("declination_deg must be between -90 and 90.")
        if self.angular_distance_deg < 0.0:
            raise ValueError("angular_distance_deg must be non-negative.")
        object.__setattr__(
            self, "right_ascension_deg", self.right_ascension_deg % 360.0
        )
        for name in ("altitude_deg", "azimuth_deg", "range_km"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _finite(value, name=name))
        if self.range_km is not None and self.range_km < 0.0:
            raise ValueError("range_km must be non-negative.")
        if self.illuminated is not None and not isinstance(
            self.illuminated, bool
        ):
            raise TypeError("illuminated must be a boolean or None.")


@dataclass(frozen=True)
class SatCheckerCandidateEvidence:
    """One normalized candidate with ordered provider samples."""

    candidate: SatelliteCrossingCandidate
    samples: tuple[SatCheckerSample, ...]
    response_sha256: str
    provider_version: str

    def __post_init__(self):
        if not isinstance(self.candidate, SatelliteCrossingCandidate):
            raise TypeError("candidate must be a SatelliteCrossingCandidate.")
        samples = tuple(self.samples)
        if not samples or any(
            not isinstance(value, SatCheckerSample) for value in samples
        ):
            raise ValueError("samples must contain SatCheckerSample values.")
        instants = [
            datetime.fromisoformat(value.instant_utc.replace("Z", "+00:00"))
            for value in samples
        ]
        if instants != sorted(instants):
            raise ValueError("provider samples must be ordered.")
        if any(
            not self.candidate.interval.contains(value.instant_utc)
            for value in samples
        ):
            raise ValueError("provider sample lies outside the query interval.")
        digest = str(self.response_sha256).strip().lower()
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("response_sha256 must be a SHA-256 digest.")
        version = str(self.provider_version).strip()
        if not version:
            raise ValueError("provider_version must be non-empty.")
        object.__setattr__(self, "samples", samples)
        object.__setattr__(self, "response_sha256", digest)
        object.__setattr__(self, "provider_version", version)


@dataclass(frozen=True)
class SatCheckerResponse:
    """One parsed task response and any normalized terminal evidence."""

    state: SatCheckerTaskState
    task_id: str | None
    progress: float | None
    message: str | None
    receipt: SatCheckerReceipt
    evidence: tuple[SatCheckerCandidateEvidence, ...] = ()

    @property
    def terminal(self):
        return self.state in {
            SatCheckerTaskState.SUCCESS,
            SatCheckerTaskState.FAILURE,
            SatCheckerTaskState.ERROR,
        }


def _fetch(endpoint, parameters, *, timeout):
    url = endpoint
    if parameters:
        url += "?" + urlencode(parameters)
    request = Request(url, headers={"Accept": "application/json"})
    with urlopen(request, timeout=timeout) as response:
        body = response.read()
        headers = tuple(response.headers.items())
        status = int(response.status)
        media_type = response.headers.get("Content-Type", "")
    return SatCheckerReceipt(
        endpoint=url,
        retrieved_at_utc=_retrieved_now(),
        http_status=status,
        media_type=media_type,
        headers=headers,
        body=body,
    )


def _payload(receipt):
    if not 200 <= receipt.http_status < 300:
        raise ValueError(
            f"SatChecker returned HTTP status {receipt.http_status}."
        )
    if receipt.media_type != "application/json":
        raise ValueError("SatChecker response media type is not application/json.")
    try:
        value = json.loads(receipt.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("SatChecker response is not valid UTF-8 JSON.") from error
    if isinstance(value, list):
        if len(value) != 1 or not isinstance(value[0], dict):
            raise ValueError("SatChecker response wrapper is not accepted.")
        value = value[0]
    if not isinstance(value, dict):
        raise ValueError("SatChecker response must be an object.")
    return value


def _state(payload):
    try:
        return SatCheckerTaskState(payload["status"])
    except KeyError:
        if "data" in payload:
            return SatCheckerTaskState.SUCCESS
        raise ValueError("SatChecker response has no task status.") from None
    except ValueError as error:
        raise ValueError("SatChecker returned an unknown task status.") from error


def _optional_number(value, *, name):
    if value is None:
        return None
    return _finite(value, name=name)


def _element_epoch(value):
    if value is None:
        return None
    return _utc_text(str(value), name="orbital_data_epoch")


def _identity_designator(satellite):
    orbital = satellite.get("orbital_data")
    if not isinstance(orbital, dict):
        return None
    values = {
        orbital.get("OBJECT_ID"),
        orbital.get("object_id"),
        orbital.get("international_designator"),
    }
    values.discard(None)
    normalized = {str(value).strip() for value in values if str(value).strip()}
    if len(normalized) > 1:
        raise ValueError("SatChecker orbital identity fields conflict.")
    return next(iter(normalized), None)


def _normalize_success(query, payload, receipt, *, ut1_jd_to_utc):
    result = payload.get("result", payload)
    if not isinstance(result, dict):
        raise ValueError("SatChecker SUCCESS result is not an object.")
    provider_source = result.get("source", payload.get("source"))
    provider_version = result.get("version", payload.get("version"))
    if provider_source != SATCHECKER_PROVIDER:
        raise ValueError("SatChecker provider identity is missing or changed.")
    if not isinstance(provider_version, str) or not provider_version.strip():
        raise ValueError("SatChecker provider version is missing.")
    data = result.get("data")
    if not isinstance(data, dict):
        raise ValueError("SatChecker SUCCESS response has no data object.")
    satellites = data.get("satellites")
    if not isinstance(satellites, dict):
        raise ValueError("SatChecker grouped satellite data is missing.")
    evidence = []
    for provider_key in sorted(satellites):
        satellite = satellites[provider_key]
        if not isinstance(satellite, dict):
            raise ValueError("SatChecker satellite record is not an object.")
        name = satellite.get("name")
        norad_id = satellite.get("norad_id")
        identity = SatelliteIdentity(
            norad_catalog_id=norad_id,
            object_name=name,
            international_designator=_identity_designator(satellite),
        )
        positions = satellite.get("positions")
        if not isinstance(positions, list) or not positions:
            raise ValueError("SatChecker candidate has no sampled positions.")
        samples = []
        epochs = set()
        sources = set()
        for position in positions:
            if not isinstance(position, dict):
                raise ValueError("SatChecker sampled position is not an object.")
            jd = _finite(position.get("julian_date"), name="julian_date")
            instant = ut1_jd_to_utc(jd)
            sample = SatCheckerSample(
                instant_utc=instant,
                julian_date_ut1=jd,
                right_ascension_deg=position.get("ra"),
                declination_deg=position.get("dec"),
                angular_distance_deg=position.get("angle"),
                altitude_deg=_optional_number(
                    position.get("altitude"), name="altitude"
                ),
                azimuth_deg=_optional_number(
                    position.get("azimuth"), name="azimuth"
                ),
                range_km=_optional_number(
                    position.get("range_km"), name="range_km"
                ),
                illuminated=position.get("illuminated"),
            )
            samples.append(sample)
            epoch = _element_epoch(
                position.get("orbital_data_epoch", position.get("tle_epoch"))
            )
            if epoch is not None:
                epochs.add(epoch)
            source = position.get("orbital_data_source")
            if source is not None:
                sources.add(str(source).strip().lower())
        if len(epochs) > 1 or len(sources) > 1:
            raise ValueError("SatChecker candidate orbit evidence conflicts.")
        candidate = SatelliteCrossingCandidate(
            satellite=identity,
            observer=query.observer,
            field_of_view=query.field_of_view,
            interval=query.interval,
            source_provider=SATCHECKER_PROVIDER,
            element_epoch=next(iter(epochs), None),
            provenance=(
                f"SatChecker endpoint {receipt.endpoint}",
                f"SatChecker response SHA-256 {receipt.body_sha256}",
                f"SatChecker API version {provider_version.strip()}",
                (
                    "UTC-to-UT1 Earth-orientation identity "
                    f"{query.earth_orientation_identity}"
                ),
                (
                    "provider-source-inferred geometric topocentric "
                    "ICRF/ICRS-oriented directions"
                ),
                (
                    "SatChecker orbit source "
                    + (next(iter(sources)) if sources else "unknown")
                ),
            ),
            warnings=(_SAMPLE_WARNING, _ENVELOPE_WARNING),
        )
        evidence.append(
            SatCheckerCandidateEvidence(
                candidate=candidate,
                samples=tuple(samples),
                response_sha256=receipt.body_sha256,
                provider_version=provider_version,
            )
        )
    expected_satellites = data.get("total_satellites")
    expected_positions = data.get("total_position_results")
    if expected_satellites is not None and expected_satellites != len(evidence):
        raise ValueError("SatChecker satellite total is inconsistent.")
    count = sum(len(value.samples) for value in evidence)
    if expected_positions is not None and expected_positions != count:
        raise ValueError("SatChecker position total is inconsistent.")
    return tuple(evidence)


def parse_response(
    query,
    receipt,
    *,
    expected_task_id=None,
    ut1_jd_to_utc=_ut1_jd_to_utc,
):
    """Parse one receipt and normalize terminal success without I/O."""
    if not isinstance(query, SatCheckerQuery):
        raise TypeError("query must be a SatCheckerQuery.")
    if not isinstance(receipt, SatCheckerReceipt):
        raise TypeError("receipt must be a SatCheckerReceipt.")
    payload = _payload(receipt)
    state = _state(payload)
    task_id = payload.get("task_id")
    if task_id is not None:
        task_id = str(task_id).strip()
        if not task_id:
            raise ValueError("SatChecker task_id must be non-empty.")
    if expected_task_id is not None and task_id != expected_task_id:
        raise ValueError("SatChecker task identifier changed.")
    if state in {SatCheckerTaskState.PENDING, SatCheckerTaskState.PROGRESS}:
        if task_id is None:
            raise ValueError("Nonterminal SatChecker response has no task_id.")
    progress = None
    if state is SatCheckerTaskState.PROGRESS:
        progress = _finite(payload.get("progress"), name="progress")
        if not 0.0 <= progress <= 100.0:
            raise ValueError("SatChecker progress must be between 0 and 100.")
    evidence = ()
    if state is SatCheckerTaskState.SUCCESS:
        if expected_task_id is not None and task_id is None:
            raise ValueError("Terminal SatChecker response has no task_id.")
        evidence = _normalize_success(
            query, payload, receipt, ut1_jd_to_utc=ut1_jd_to_utc
        )
    message = payload.get("message", payload.get("error"))
    if message is not None:
        message = str(message).strip() or None
    return SatCheckerResponse(
        state=state,
        task_id=task_id,
        progress=progress,
        message=message,
        receipt=receipt,
        evidence=evidence,
    )


def submit(query, *, timeout=120, fetch=_fetch):
    """Submit one async request exactly once; never poll or retry."""
    if not isinstance(query, SatCheckerQuery):
        raise TypeError("query must be a SatCheckerQuery.")
    receipt = fetch(query.endpoint, query.parameters, timeout=timeout)
    return parse_response(query, receipt)


def poll(query, task_id, *, timeout=120, fetch=_fetch):
    """Poll one task exactly once; never loop or retry."""
    if not isinstance(query, SatCheckerQuery):
        raise TypeError("query must be a SatCheckerQuery.")
    task_id = str(task_id).strip()
    if not task_id or "/" in task_id:
        raise ValueError("task_id is not a safe SatChecker task identifier.")
    endpoint = query.base_url + "/v1/fov/task-status/" + task_id
    receipt = fetch(endpoint, (), timeout=timeout)
    return parse_response(query, receipt, expected_task_id=task_id)


@dataclass(frozen=True)
class SatCheckerCacheEntry:
    """Validated exact receipt chain and stored normalized interpretation."""

    receipts: tuple[SatCheckerReceipt, ...]
    normalized_json: bytes


def _evidence_document(evidence):
    return [
        {
            "norad_catalog_id": item.candidate.satellite.norad_catalog_id,
            "object_name": item.candidate.satellite.object_name,
            "international_designator": (
                item.candidate.satellite.international_designator
            ),
            "provider_version": item.provider_version,
            "response_sha256": item.response_sha256,
            "samples": [
                {
                    "instant_utc": sample.instant_utc,
                    "julian_date_ut1": sample.julian_date_ut1,
                    "ra_deg": sample.right_ascension_deg,
                    "dec_deg": sample.declination_deg,
                    "angle_deg": sample.angular_distance_deg,
                    "altitude_deg": sample.altitude_deg,
                    "azimuth_deg": sample.azimuth_deg,
                    "range_km": sample.range_km,
                    "illuminated": sample.illuminated,
                }
                for sample in item.samples
            ],
        }
        for item in evidence
    ]


class SatCheckerCache:
    """Content-addressed local SatChecker receipt cache."""

    def __init__(self, root):
        self.root = Path(root).expanduser().resolve()

    def store(self, query, responses):
        """Atomically publish one terminal-success receipt chain."""
        if not isinstance(query, SatCheckerQuery):
            raise TypeError("query must be a SatCheckerQuery.")
        responses = tuple(responses)
        if not responses or any(
            not isinstance(value, SatCheckerResponse) for value in responses
        ):
            raise ValueError("responses must contain SatCheckerResponse values.")
        terminal = responses[-1]
        if terminal.state is not SatCheckerTaskState.SUCCESS:
            raise ValueError("only terminal-success response chains are cached.")
        task_ids = {value.task_id for value in responses if value.task_id}
        if len(task_ids) > 1:
            raise ValueError("response chain contains multiple task identifiers.")
        normalized = _canonical_json(_evidence_document(terminal.evidence))
        manifest = {
            "schema_version": SATCHECKER_SCHEMA_VERSION,
            "cache_key": query.cache_key,
            "request": query.canonical_document,
            "receipts": [
                {
                    "endpoint": value.receipt.endpoint,
                    "retrieved_at_utc": value.receipt.retrieved_at_utc,
                    "http_status": value.receipt.http_status,
                    "media_type": value.receipt.media_type,
                    "headers": list(value.receipt.headers),
                    "body_sha256": value.receipt.body_sha256,
                }
                for value in responses
            ],
            "normalized_sha256": sha256(normalized).hexdigest(),
            "normalized": json.loads(normalized),
        }
        document = _canonical_json(manifest)
        destination = self.root / query.cache_key
        self.root.mkdir(parents=True, exist_ok=True)
        blobs = self.root / "blobs"
        blobs.mkdir(exist_ok=True)
        for value in responses:
            path = blobs / value.receipt.body_sha256
            if path.exists():
                if path.read_bytes() != value.receipt.body:
                    raise ValueError("cached SatChecker response digest conflicts.")
            else:
                _atomic_write(path, value.receipt.body)
        manifest_path = destination / "manifest.json"
        if manifest_path.exists():
            if manifest_path.read_bytes() != document:
                raise FileExistsError(
                    "SatChecker cache already contains different exact receipts."
                )
            return destination
        destination.mkdir()
        _atomic_write(manifest_path, document)
        return destination

    def load(self, query):
        """Load and validate one exact cached response chain."""
        if not isinstance(query, SatCheckerQuery):
            raise TypeError("query must be a SatCheckerQuery.")
        path = self.root / query.cache_key / "manifest.json"
        try:
            document = path.read_bytes()
            manifest = json.loads(document)
        except (FileNotFoundError, UnicodeDecodeError, json.JSONDecodeError):
            return None
        if (
            manifest.get("schema_version") != SATCHECKER_SCHEMA_VERSION
            or manifest.get("cache_key") != query.cache_key
            or manifest.get("request") != query.canonical_document
        ):
            raise ValueError("SatChecker cache manifest identity is invalid.")
        normalized = _canonical_json(manifest.get("normalized"))
        if sha256(normalized).hexdigest() != manifest.get("normalized_sha256"):
            raise ValueError("SatChecker cached normalization is corrupt.")
        receipts = []
        records = manifest.get("receipts")
        if not isinstance(records, list) or not records:
            raise ValueError("SatChecker cache receipt chain is missing.")
        for record in records:
            try:
                digest = record["body_sha256"]
                body = (self.root / "blobs" / digest).read_bytes()
                if sha256(body).hexdigest() != digest:
                    raise ValueError("SatChecker cached response is corrupt.")
                receipt = SatCheckerReceipt(
                    endpoint=record["endpoint"],
                    retrieved_at_utc=record["retrieved_at_utc"],
                    http_status=record["http_status"],
                    media_type=record["media_type"],
                    headers=tuple(tuple(value) for value in record["headers"]),
                    body=body,
                )
            except (KeyError, TypeError, FileNotFoundError) as error:
                raise ValueError(
                    "SatChecker cache receipt metadata is invalid."
                ) from error
            receipts.append(receipt)
        return SatCheckerCacheEntry(tuple(receipts), normalized)


def _atomic_write(path, content):
    handle, temporary = tempfile.mkstemp(prefix=".satchecker-", dir=path.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise
