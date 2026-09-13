"""Installed command for explicit networked comet discovery."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from wenu.comet_discovery import (
    DEFAULT_MAX_PERIHELION_DISTANCE_AU,
    CometDiscoveryResult,
    discover_comets,
)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        description=(
            "List SBDB comet solutions by perihelion date and distance. "
            "This is not a visibility forecast."
        )
    )
    value.add_argument("start", help="first inclusive UTC civil date")
    value.add_argument("stop", help="last inclusive UTC civil date")
    value.add_argument(
        "--max-perihelion-distance",
        type=float,
        default=DEFAULT_MAX_PERIHELION_DISTANCE_AU,
        metavar="AU",
    )
    value.add_argument("--format", choices=("table", "json"), default="table")
    value.add_argument("--output", type=Path)
    return value


def _unknown(value: object, formatter=str) -> str:
    return "unknown" if value is None else formatter(value)


def table_text(result: CometDiscoveryResult) -> str:
    headers = (
        "designation", "name", "class", "perihelion UTC", "q (au)",
        "e", "period (d)", "i (deg)", "Earth MOID (au)", "orbit",
        "M1 model", "M2 model", "K1 model", "K2 model",
    )
    rows = []
    for row in result.records:
        rows.append((
            row.primary_designation,
            _unknown(row.name),
            _unknown(row.orbit_class),
            row.perihelion_date_utc,
            f"{row.perihelion_distance_au:.6g}",
            _unknown(row.eccentricity, lambda x: f"{x:.6g}"),
            _unknown(row.period_days, lambda x: f"{x:.6g}"),
            _unknown(row.inclination_deg, lambda x: f"{x:.6g}"),
            _unknown(row.earth_moid_au, lambda x: f"{x:.6g}"),
            _unknown(row.orbit_solution_id),
            _unknown(row.magnitude_model_m1, lambda x: f"{x:.6g}"),
            _unknown(row.magnitude_model_m2, lambda x: f"{x:.6g}"),
            _unknown(row.magnitude_model_k1, lambda x: f"{x:.6g}"),
            _unknown(row.magnitude_model_k2, lambda x: f"{x:.6g}"),
        ))
    widths = [len(value) for value in headers]
    for row in rows:
        widths = [max(old, len(value)) for old, value in zip(widths, row)]
    lines = [
        (
            "Comets selected by perihelion time and distance; "
            "not a visibility forecast."
        ),
        f"Retrieved: {result.retrieved_at_utc.isoformat()}",
        "  ".join(value.ljust(width) for value, width in zip(headers, widths)),
        "  ".join("-" * width for width in widths),
    ]
    lines.extend(
        "  ".join(value.ljust(width) for value, width in zip(row, widths))
        for row in rows
    )
    return "\n".join(lines) + "\n"


def json_text(result: CometDiscoveryResult) -> str:
    document = {
        "selection": {
            "start_utc": result.start_utc.isoformat(),
            "stop_utc": result.stop_utc.isoformat(),
            "max_perihelion_distance": {
                "value": result.max_perihelion_distance_au,
                "unit": "au",
            },
            "meaning": "perihelion filter; not a visibility forecast",
        },
        "provider": {
            "identity": result.provider,
            "version": result.provider_version,
            "retrieved_at_utc": result.retrieved_at_utc.isoformat(),
            "request_parameters": dict(result.request_parameters),
            "raw_sha256": result.raw_sha256,
        },
        "records": [],
    }
    for record in result.records:
        values = asdict(record)
        values["perihelion"] = {
            "jd": values.pop("perihelion_jd_tdb"),
            "calendar": values.pop("perihelion_calendar_tdb"),
            "time_scale": "TDB",
            "utc_date": record.perihelion_date_utc,
        }
        for key, unit in (
            ("perihelion_distance_au", "au"),
            ("inclination_deg", "deg"),
            ("period_days", "d"),
            ("earth_moid_au", "au"),
        ):
            values[key] = {"value": values[key], "unit": unit}
        values["photometric_model_parameters"] = {
            key: values.pop(key) for key in (
                "magnitude_model_m1", "magnitude_model_m2",
                "magnitude_model_k1", "magnitude_model_k2",
            )
        }
        document["records"].append(values)
    return json.dumps(document, indent=2, sort_keys=True) + "\n"


def main(argv=None) -> int:
    arguments = parser().parse_args(argv)
    result = discover_comets(
        arguments.start,
        arguments.stop,
        max_perihelion_distance_au=arguments.max_perihelion_distance,
    )
    text = (
        table_text(result)
        if arguments.format == "table"
        else json_text(result)
    )
    if arguments.output is None:
        print(text, end="")
    else:
        arguments.output.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
