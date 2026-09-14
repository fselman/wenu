"""Networked preflight acquisition for immutable numbered-asteroid resources."""

from __future__ import annotations

import base64
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import time
from urllib.parse import urlencode
from urllib.request import urlopen

from astropy.time import Time

from wenu.minor_body_ephemeris import SpiceMinorBodyKernel
from wenu.minor_body_identity import ResolvedMinorBodyIdentity


HORIZONS_API = "https://ssd.jpl.nasa.gov/api/horizons.api"
SBDB_API = "https://ssd-api.jpl.nasa.gov/sbdb.api"
DEFAULT_COVERAGE_MARGIN_DAYS = 30
_HEADER = re.compile(
    r"JPL/HORIZONS\s+(?P<number>\d+)(?:\s+(?P<name>.*?))?"
    r"\s*\((?P<designation>[^)]+)\)"
)
_COMET_HEADER = re.compile(
    r"JPL/HORIZONS\s+(?P<fullname>.+?)\s+\d{4}-[A-Za-z]{3}-\d{2}"
)
_RECORD = re.compile(r"Rec #:\s*(?P<value>\d+)")


class MovingObjectDataPolicy(str, Enum):
    """Network and cache policy applied before chart construction."""

    ACQUIRE_IF_MISSING = "acquire-if-missing"
    OFFLINE = "offline"
    REFRESH = "refresh"


@dataclass(frozen=True)
class MinorBodyPreflightResult:
    """One local resource directory selected before ordinary rendering."""

    resource_directory: Path
    policy: MovingObjectDataPolicy
    acquired: bool


def _json(url, parameters, *, timeout=120):
    with urlopen(
        url + "?" + urlencode(parameters), timeout=timeout
    ) as response:
        return json.loads(response.read().decode("utf-8"))


def _horizons_identity(result, expected_number):
    match = _HEADER.search(result)
    if match is None or int(match.group("number")) != expected_number:
        raise ValueError(
            "Horizons result does not identify the requested number."
        )
    if "ASTEROID comments:" not in result:
        raise ValueError("Horizons result is not an asteroid solution.")
    solution = re.search(r"soln ref\.=(?P<value>[^,\n]+)", result)
    solution_date = re.search(r"Soln\.date:\s*(?P<value>\S+)", result)
    epoch = re.search(
        r"EPOCH=\s*(?P<value>\S+).*?\((?P<scale>[^)]+)\)", result
    )
    if solution is None or solution_date is None or epoch is None:
        raise ValueError(
            "Horizons result lacks required orbit-solution identity."
        )
    return {
        "name": (match.group("name") or "").strip() or None,
        "primary_designation": match.group("designation").strip(),
        "orbit_solution_id": solution.group("value").strip(),
        "solution_date": solution_date.group("value"),
        "osculating_epoch": (
            f"{epoch.group('value')} {epoch.group('scale')}"
        ),
    }


def _download(number, start, stop, *, fetch_json=_json):
    parameters = {
        "format": "json",
        "COMMAND": f"'{number};'",
        "OBJ_DATA": "'YES'",
        "MAKE_EPHEM": "'YES'",
        "EPHEM_TYPE": "'SPK'",
        "START_TIME": f"'{start}'",
        "STOP_TIME": f"'{stop}'",
    }
    document = fetch_json(HORIZONS_API, parameters)
    signature = document.get("signature")
    if (
        not isinstance(signature, dict)
        or signature.get("source") != "NASA/JPL Horizons API"
    ):
        raise ValueError("Horizons response has no accepted API signature.")
    identity = _horizons_identity(document.get("result", ""), number)
    try:
        payload = base64.b64decode(
            "".join(document["spk"].split()).encode("ascii"),
            validate=True,
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Horizons response has no valid SPK payload.") from error
    if not payload.startswith(b"DAF/"):
        raise ValueError("Horizons payload is not a binary DAF/SPK file.")
    target = str(document.get("spk_file_id"))
    sbdb = fetch_json(
        SBDB_API, {"sstr": str(number), "full-prec": "true"}
    )
    obj = sbdb.get("object", {})
    if str(obj.get("spkid")) != target or str(obj.get("des")) != str(number):
        raise ValueError("SBDB and Horizons asteroid identities differ.")
    orbit_class = obj.get("orbit_class", {})
    identity["classifications"] = tuple(
        value
        for value in (orbit_class.get("code"), orbit_class.get("name"))
        if isinstance(value, str) and value.strip()
    )
    return document, payload, identity, target, parameters, sbdb


def _actual_coverage(path, target, *, require_single=False):
    """Return verified type-21 TDB coverage for one acquired target."""
    kernel = SpiceMinorBodyKernel(path)
    try:
        segments = tuple(
            value for value in kernel.segments
            if value.target == int(target)
            and value.center == 10
            and value.frame_id == 1
            and value.data_type == 21
        )
        if not segments or (require_single and len(segments) != 1):
            raise ValueError(
                "Horizons SPK has no unique accepted target segment."
            )
        return {
            "start_jd_tdb": min(
                value.spk_segment.start_jd for value in segments
            ),
            "stop_jd_tdb": max(
                value.spk_segment.end_jd for value in segments
            ),
        }
    finally:
        kernel.close()


def _horizons_command(identity):
    """Return an explicit Horizons selector for one resolved identity."""
    if not isinstance(identity, ResolvedMinorBodyIdentity):
        raise TypeError("acquisition identities must be resolved minor bodies.")
    if identity.object_class == "asteroid":
        return f"{identity.primary_designation};"
    if identity.object_class != "comet":
        raise ValueError("minor-body acquisition supports asteroid or comet.")
    flags = [f"DES={identity.primary_designation}", "CAP"]
    if identity.fragment is None:
        flags.append("NOFRAG")
    return ";".join(flags)


def _horizons_solution(result, identity):
    """Validate one unique Horizons object summary against resolved identity."""
    record = _RECORD.search(result)
    solution = re.search(r"soln ref\.=(?P<value>[^,\n]+)", result)
    solution_date = re.search(r"Soln\.date:\s*(?P<value>\S+)", result)
    epoch = re.search(
        r"EPOCH=\s*(?P<value>\S+).*?\((?P<scale>[^)]+)\)", result
    )
    if None in (record, solution, solution_date, epoch):
        raise ValueError(
            "Horizons result lacks unique record or orbit-solution identity."
        )
    if identity.object_class == "comet":
        header = _COMET_HEADER.search(result)
        if header is None or "COMET comments" not in result:
            raise ValueError("Horizons result is not a comet solution.")
        fullname = header.group("fullname").strip()
        aliases = {
            " ".join(value.strip().split()).casefold()
            for value in identity.aliases
        }
        normalized_fullname = " ".join(fullname.split()).casefold()
        parenthesized = re.fullmatch(
            r"(?P<name>.+?)\s*\((?P<designation>[^()]+)\)",
            normalized_fullname,
        )
        horizons_designation = (
            parenthesized.group("designation").strip()
            if parenthesized is not None
            else None
        )
        if (
            normalized_fullname not in aliases
            and horizons_designation not in aliases
        ):
            raise ValueError(
                "Horizons comet identity "
                f"{normalized_fullname!r} does not match resolved aliases "
                f"{tuple(sorted(aliases))!r}."
            )
    else:
        header = _HEADER.search(result)
        if header is None or "ASTEROID comments:" not in result:
            raise ValueError("Horizons result is not an asteroid solution.")
        if header.group("designation").strip() != identity.primary_designation:
            raise ValueError("Horizons and resolved asteroid identities differ.")
    non_gravitational = {}
    for name in ("AMRAT", "DT", "A1", "A2", "A3", "ALN", "NK", "NM", "NN", "R0"):
        match = re.search(
            rf"(?:^|\s){name}=\s*(?P<value>[^\s]+)", result, re.MULTILINE
        )
        non_gravitational[name] = (
            match.group("value") if match is not None else None
        )
    orbit_solution_id = solution.group("value").strip()
    if identity.object_class == "comet" and orbit_solution_id.startswith(
        "JPL#"
    ):
        orbit_solution_id = orbit_solution_id.removeprefix("JPL#")
    return {
        "record_number": record.group("value"),
        "orbit_solution_id": orbit_solution_id,
        "solution_date": solution_date.group("value"),
        "osculating_epoch": f"{epoch.group('value')} {epoch.group('scale')}",
        "non_gravitational_parameters": non_gravitational,
    }


def _download_resolved_identity(identity, start, stop, *, fetch_json=_json):
    selector = _horizons_command(identity)
    lookup_parameters = {
        "format": "json",
        "COMMAND": f"'{selector}'",
        "OBJ_DATA": "'YES'",
        "MAKE_EPHEM": "'NO'",
    }
    lookup = fetch_json(HORIZONS_API, lookup_parameters)
    signature = lookup.get("signature")
    if (
        not isinstance(signature, dict)
        or signature.get("source") != "NASA/JPL Horizons API"
        or signature.get("version") != "1.2"
    ):
        raise ValueError("Horizons lookup has no accepted API signature.")
    solution = _horizons_solution(lookup.get("result", ""), identity)
    command = f"{solution['record_number']};"
    parameters = {
        "format": "json",
        "COMMAND": f"'{command}'",
        "OBJ_DATA": "'YES'",
        "MAKE_EPHEM": "'YES'",
        "EPHEM_TYPE": "'SPK'",
        "START_TIME": f"'{start}'",
        "STOP_TIME": f"'{stop}'",
    }
    document = fetch_json(HORIZONS_API, parameters)
    if document.get("signature") != signature:
        raise ValueError("Horizons lookup and SPK signatures differ.")
    repeated = _horizons_solution(document.get("result", ""), identity)
    if repeated != solution:
        raise ValueError("Horizons lookup and SPK solution identities differ.")
    try:
        payload = base64.b64decode(
            "".join(document["spk"].split()).encode("ascii"), validate=True
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Horizons response has no valid SPK payload.") from error
    if not payload.startswith(b"DAF/"):
        raise ValueError("Horizons payload is not a binary DAF/SPK file.")
    target = str(document.get("spk_file_id"))
    if target != identity.provider_spk_id:
        raise ValueError("Horizons SPK and resolved provider targets differ.")
    return lookup, document, payload, solution, target, lookup_parameters, parameters


def acquire_minor_body_resources(
    identities,
    output_directory,
    *,
    start,
    stop,
    fetch_json=_json,
):
    """Acquire resolved identities into one verified manifest-backed set."""
    identities = tuple(identities)
    if not identities:
        raise ValueError("minor-body acquisition requires an identity.")
    keys = [
        (value.object_class, value.canonical_designation)
        for value in identities
        if isinstance(value, ResolvedMinorBodyIdentity)
    ]
    if len(keys) != len(identities) or len(set(keys)) != len(keys):
        raise ValueError("minor-body acquisition identities must be unique and resolved.")
    output_directory = Path(output_directory).expanduser().resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    manifest = output_directory / "acquisition-report.json"
    if manifest.exists() or any(output_directory.iterdir()):
        raise FileExistsError(
            f"refusing to overwrite minor-body resources in {output_directory}"
        )
    records = []
    retrieved_at = datetime.now(timezone.utc).isoformat()
    for identity in identities:
        (
            lookup,
            document,
            payload,
            solution,
            target,
            lookup_parameters,
            horizons_parameters,
        ) = _download_resolved_identity(
            identity, start, stop, fetch_json=fetch_json
        )
        solution_key = re.sub(
            r"[^a-z0-9]+", "-", solution["orbit_solution_id"].casefold()
        ).strip("-")
        object_key = re.sub(
            r"[^a-z0-9]+", "-", identity.canonical_designation.casefold()
        ).strip("-")
        filename = f"{object_key}-{solution_key}-{start[:4]}-{stop[:4]}.bsp"
        resource = output_directory / filename
        resource.write_bytes(payload)
        aliases = list(identity.aliases)
        records.append({
            "key": identity.canonical_designation,
            "filename": filename,
            "sha256": sha256(payload).hexdigest(),
            "bytes": len(payload),
            "spk_file_id": target,
            "horizons_result": document["result"],
            "coverage_request": {
                "start": start,
                "stop": stop,
                "time_scale": "tdb",
            },
            "actual_coverage": _actual_coverage(
                resource, target, require_single=True
            ),
            "identity": {
                "permanent_number": identity.permanent_number,
                "primary_designation": identity.primary_designation,
                "designation_class": identity.prefix,
                "fragment": identity.fragment,
                "name": identity.name,
                "aliases": aliases,
                "object_class": identity.object_class,
                "provider_spk_id": target,
                "classifications": [
                    value for value in (
                        identity.object_class,
                        identity.orbit_class_code,
                        identity.orbit_class_name,
                    ) if value
                ],
            },
            "solution": {
                "provider": "NASA/JPL Horizons API",
                "service_version": str(document["signature"].get("version")),
                "object_class": identity.object_class,
                "primary_designation": identity.primary_designation,
                "horizons_command": f"{solution['record_number']};",
                "provider_spk_id": target,
                "orbit_solution_id": solution["orbit_solution_id"],
                "solution_date": solution["solution_date"],
                "osculating_epoch": solution["osculating_epoch"],
                "reference_system": "ICRF/J2000",
                "non_gravitational_parameters": solution[
                    "non_gravitational_parameters"
                ],
                "provenance": [
                    "Exact identity and bounded Horizons SPK acquired by Wenu"
                ],
            },
            "receipt": {
                "retrieved_at_utc": retrieved_at,
                "identity_provider": identity.provider,
                "identity_provider_version": identity.provider_version,
                "identity_request_parameters": dict(identity.request_parameters),
                "identity_retrieved_at_utc": (
                    identity.retrieved_at_utc.isoformat()
                    if identity.retrieved_at_utc is not None else None
                ),
                "identity_raw_sha256": identity.raw_sha256,
                "horizons_lookup_parameters": lookup_parameters,
                "horizons_parameters": horizons_parameters,
                "horizons_lookup_signature": lookup["signature"],
                "horizons_signature": document["signature"],
            },
        })
    manifest.write_text(
        json.dumps({
            "purpose": "Wenu installed minor bodies",
            "resources": records,
        }, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def _identity_keys(identities):
    values = tuple(sorted(
        f"{value.object_class}:{value.canonical_designation.casefold()}"
        for value in identities
    ))
    return (sha256(json.dumps(values).encode("utf-8")).hexdigest(),)


def resource_covers_identities(directory, identities, start, stop):
    """Return whether one verified collection covers resolved identities."""
    directory = Path(directory).expanduser().resolve()
    records = _manifest_records(directory)
    if records is None:
        return False
    start_jd = float(Time(start, scale="tdb").jd)
    stop_jd = float(Time(stop, scale="tdb").jd)
    for identity in identities:
        matching = [
            record for record in records
            if isinstance(record, dict)
            and isinstance(record.get("identity"), dict)
            and record["identity"].get("object_class") == identity.object_class
            and str(record["identity"].get("provider_spk_id")) == (
                identity.provider_spk_id
            )
            and identity.primary_designation in (
                record["identity"].get("primary_designation"),
                *(record["identity"].get("aliases") or ()),
            )
        ]
        if len(matching) != 1:
            return False
        record = matching[0]
        try:
            path = (directory / record["filename"]).resolve(strict=True)
            if path.parent != directory or _digest(path) != record["sha256"]:
                return False
            kernel = SpiceMinorBodyKernel(path)
        except Exception:
            return False
        try:
            covered = any(
                value.target == int(record["spk_file_id"])
                and value.center == 10
                and value.frame_id == 1
                and value.data_type == 21
                and value.spk_segment.start_jd <= start_jd
                and stop_jd <= value.spk_segment.end_jd
                for value in kernel.segments
            )
        finally:
            kernel.close()
        if not covered:
            return False
    return True


def find_cached_minor_body_resources(cache_root, identities, start, stop):
    """Find an immutable collection covering resolved identities."""
    cache_root = Path(cache_root).expanduser()
    if not cache_root.exists():
        return None
    for directory in _candidate_directories(cache_root.resolve()):
        if resource_covers_identities(directory, identities, start, stop):
            return directory
    return None


def _publish_identity_acquisition(
    cache_root, identities, start, stop, acquire
):
    staging = Path(tempfile.mkdtemp(prefix=".acquire-", dir=cache_root))
    try:
        manifest = acquire(
            identities, staging, start=start, stop=stop
        )
        if not resource_covers_identities(staging, identities, start, stop):
            raise ValueError(
                "acquired minor-body resource failed identity, digest, or "
                "coverage validation."
            )
        key = sha256(manifest.read_bytes()).hexdigest()
        destination = cache_root / key
        if destination.exists():
            shutil.rmtree(staging)
        else:
            staging.rename(destination)
        if not resource_covers_identities(
            destination, identities, start, stop
        ):
            raise ValueError(
                "acquired minor-body resource failed identity, digest, or "
                "coverage validation."
            )
        return destination
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        raise


def ensure_minor_body_resources(
    identities,
    cache_root,
    start,
    stop,
    *,
    policy=MovingObjectDataPolicy.ACQUIRE_IF_MISSING,
    finder=find_cached_minor_body_resources,
    acquire=acquire_minor_body_resources,
):
    """Resolve or acquire typed minor-body identities before rendering."""
    policy = MovingObjectDataPolicy(policy)
    identities = tuple(identities)
    if not identities or any(
        not isinstance(value, ResolvedMinorBodyIdentity)
        for value in identities
    ):
        raise ValueError("minor-body preflight requires resolved identities.")
    cache_root = Path(cache_root).expanduser().resolve()
    cached = finder(cache_root, identities, start, stop)
    if policy is not MovingObjectDataPolicy.REFRESH and cached is not None:
        return MinorBodyPreflightResult(Path(cached), policy, False)
    if policy is MovingObjectDataPolicy.OFFLINE:
        selections = ", ".join(
            value.canonical_designation for value in identities
        )
        raise FileNotFoundError(
            "offline data policy found no verified minor-body resource for "
            f"{selections} covering {start} through {stop}."
        )
    cache_root.mkdir(parents=True, exist_ok=True)
    keys = _identity_keys(identities)
    with _acquisition_lock(cache_root, keys):
        if policy is MovingObjectDataPolicy.ACQUIRE_IF_MISSING:
            cached = finder(cache_root, identities, start, stop)
            if cached is not None:
                return MinorBodyPreflightResult(Path(cached), policy, False)
        directory = _publish_identity_acquisition(
            cache_root, identities, start, stop, acquire
        )
    return MinorBodyPreflightResult(directory, policy, True)


def acquire_numbered_asteroids(
    numbers,
    output_directory,
    *,
    start,
    stop,
    fetch_json=_json,
):
    """Acquire one immutable manifest-backed asteroid resource set."""
    numbers = tuple(sorted(set(int(value) for value in numbers)))
    if not numbers or any(value <= 0 for value in numbers):
        raise ValueError("asteroid numbers must be positive integers.")
    output_directory = Path(output_directory).expanduser().resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    manifest = output_directory / "acquisition-report.json"
    if manifest.exists() or any(output_directory.iterdir()):
        raise FileExistsError(
            f"refusing to overwrite minor-body resources in {output_directory}"
        )
    records = []
    retrieved_at = datetime.now(timezone.utc).isoformat()
    for number in numbers:
        (
            document,
            payload,
            identity,
            target,
            horizons_parameters,
            sbdb,
        ) = _download(number, start, stop, fetch_json=fetch_json)
        solution_key = identity["orbit_solution_id"].lower().replace("#", "")
        filename = f"{number}-{solution_key}-{start[:4]}-{stop[:4]}.bsp"
        resource = output_directory / filename
        resource.write_bytes(payload)
        records.append({
            "key": str(number),
            "filename": filename,
            "sha256": sha256(payload).hexdigest(),
            "bytes": len(payload),
            "spk_file_id": target,
            "horizons_result": document["result"],
            "coverage_request": {
                "start": start,
                "stop": stop,
                "time_scale": "tdb",
            },
            "actual_coverage": _actual_coverage(resource, target),
            "identity": {
                "permanent_number": number,
                "primary_designation": identity["primary_designation"],
                "name": identity["name"],
                "object_class": "asteroid",
                "provider_spk_id": target,
                "classifications": list(identity["classifications"]),
            },
            "solution": {
                "provider": "NASA/JPL Horizons API",
                "service_version": str(
                    document["signature"].get("version", "unknown")
                ),
                "object_class": "asteroid",
                "primary_designation": identity["primary_designation"],
                "horizons_command": f"{number};",
                "provider_spk_id": target,
                "orbit_solution_id": identity["orbit_solution_id"],
                "solution_date": identity["solution_date"],
                "osculating_epoch": identity["osculating_epoch"],
                "reference_system": "ICRF/J2000",
                "provenance": [
                    "Horizons SPK and SBDB identity acquired by Wenu preflight"
                ],
            },
            "receipt": {
                "retrieved_at_utc": retrieved_at,
                "horizons_parameters": horizons_parameters,
                "horizons_signature": document["signature"],
                "sbdb_signature": sbdb.get("signature"),
            },
        })
    manifest.write_text(
        json.dumps(
            {
                "purpose": "Wenu installed numbered asteroids",
                "resources": records,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest


def _digest(path):
    value = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def _manifest_records(directory):
    path = directory / "acquisition-report.json"
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
        records = document["resources"]
    except (FileNotFoundError, KeyError, TypeError, json.JSONDecodeError):
        return None
    if not isinstance(records, list):
        return None
    return records


def resource_covers(directory, numbers, start, stop):
    """Return whether verified SPKs cover every requested TDB instant."""
    directory = Path(directory).expanduser().resolve()
    records = _manifest_records(directory)
    if records is None:
        return False
    by_number = {
        record.get("identity", {}).get("permanent_number"): record
        for record in records
        if isinstance(record, dict) and isinstance(record.get("identity"), dict)
    }
    start_jd = float(Time(start, scale="tdb").jd)
    stop_jd = float(Time(stop, scale="tdb").jd)
    for number in numbers:
        record = by_number.get(number)
        if record is None:
            return False
        try:
            path = (directory / record["filename"]).resolve(strict=True)
            if path.parent != directory or _digest(path) != record["sha256"]:
                return False
            kernel = SpiceMinorBodyKernel(path)
        except Exception:
            return False
        try:
            segments = tuple(
                value
                for value in kernel.segments
                if value.target == int(record["spk_file_id"])
                and value.center == 10
                and value.frame_id == 1
                and value.data_type == 21
            )
            covered = any(
                value.spk_segment.start_jd <= start_jd
                and stop_jd <= value.spk_segment.end_jd
                for value in segments
            )
        finally:
            kernel.close()
        if not covered:
            return False
    return True


def _candidate_directories(cache_root):
    manifest = cache_root / "acquisition-report.json"
    if manifest.is_file():
        yield cache_root
    if cache_root.is_dir():
        yield from sorted(
            value
            for value in cache_root.iterdir()
            if value.is_dir()
            and not value.name.startswith(".")
            and (value / "acquisition-report.json").is_file()
        )


def find_cached_resources(cache_root, numbers, start, stop):
    """Find one verified immutable collection covering all selections."""
    cache_root = Path(cache_root).expanduser()
    if not cache_root.exists():
        return None
    for directory in _candidate_directories(cache_root.resolve()):
        if resource_covers(directory, numbers, start, stop):
            return directory
    return None


@contextmanager
def _acquisition_lock(cache_root, numbers, *, timeout=120):
    key = "-".join(str(value) for value in numbers)
    lock = cache_root / f".acquire-{key}.lock"
    deadline = time.monotonic() + timeout
    while True:
        try:
            lock.mkdir()
            (lock / "owner.json").write_text(
                json.dumps({"pid": os.getpid()}) + "\n", encoding="utf-8"
            )
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"timed out waiting for minor-body acquisition lock {lock}"
                ) from None
            time.sleep(0.1)
    try:
        yield
    finally:
        shutil.rmtree(lock)


def _publish_acquisition(cache_root, numbers, start, stop, acquire):
    staging = Path(tempfile.mkdtemp(prefix=".acquire-", dir=cache_root))
    try:
        manifest = acquire(
            numbers, staging, start=start, stop=stop
        )
        if not resource_covers(staging, numbers, start, stop):
            raise ValueError(
                "acquired minor-body resource failed identity, digest, or "
                "coverage validation."
            )
        document = manifest.read_bytes()
        key = sha256(document).hexdigest()
        destination = cache_root / key
        if destination.exists():
            shutil.rmtree(staging)
        else:
            staging.rename(destination)
        if not resource_covers(destination, numbers, start, stop):
            raise ValueError(
                "acquired minor-body resource failed identity, digest, or "
                "coverage validation."
            )
        return destination
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        raise


def ensure_numbered_asteroid_resources(
    numbers,
    cache_root,
    start,
    stop,
    *,
    policy=MovingObjectDataPolicy.ACQUIRE_IF_MISSING,
    finder=find_cached_resources,
    acquire=acquire_numbered_asteroids,
):
    """Resolve or acquire one complete collection before rendering."""
    policy = MovingObjectDataPolicy(policy)
    numbers = tuple(sorted(set(int(value) for value in numbers)))
    if not numbers or any(value <= 0 for value in numbers):
        raise ValueError("asteroid numbers must be positive integers.")
    cache_root = Path(cache_root).expanduser().resolve()
    cached = finder(cache_root, numbers, start, stop)
    if policy is not MovingObjectDataPolicy.REFRESH and cached is not None:
        return MinorBodyPreflightResult(Path(cached), policy, False)
    if policy is MovingObjectDataPolicy.OFFLINE:
        raise FileNotFoundError(
            "offline data policy found no verified numbered-asteroid "
            "resource with adequate time coverage."
        )
    cache_root.mkdir(parents=True, exist_ok=True)
    with _acquisition_lock(cache_root, numbers):
        if policy is MovingObjectDataPolicy.ACQUIRE_IF_MISSING:
            cached = finder(cache_root, numbers, start, stop)
            if cached is not None:
                return MinorBodyPreflightResult(Path(cached), policy, False)
        directory = _publish_acquisition(
            cache_root, numbers, start, stop, acquire
        )
    return MinorBodyPreflightResult(directory, policy, True)


def coverage_interval(instants, *, margin_days=DEFAULT_COVERAGE_MARGIN_DAYS):
    """Return deterministic date bounds surrounding all UTC instants."""
    values = tuple(
        value.astimezone(timezone.utc)
        if value.tzinfo is not None
        else value.replace(tzinfo=timezone.utc)
        for value in instants
    )
    if not values:
        raise ValueError("minor-body coverage requires at least one instant.")
    margin = timedelta(days=margin_days)
    return (
        (min(values) - margin).date().isoformat(),
        (max(values) + margin).date().isoformat(),
    )
