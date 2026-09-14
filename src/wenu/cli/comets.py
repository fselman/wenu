"""Installed command for explicit networked comet discovery."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

from wenu.comet_discovery import (
    DEFAULT_MAX_PERIHELION_DISTANCE_AU,
    CometDiscoveryResult,
    discover_comets,
)
from wenu.comet_photometry import (
    DEFAULT_PERIHELION_WINDOW_DAYS,
    MAX_COMETS,
    CometDiscoveryPhotometry,
    characterize_discovery_photometry,
)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        description=(
            "List SBDB comet solutions by perihelion date and distance. "
            "Optional Horizons magnitude is a sampled provider model, "
            "not a visibility forecast."
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
    value.add_argument(
        "--observer-location",
        help=(
            "governed Wenu location for sampled Horizons T-mag/N-mag "
            "characterization"
        ),
    )
    value.add_argument(
        "--magnitude-step",
        metavar="DURATION",
        help=(
            "positive whole hours or days (for example 12h or 1d); "
            "default with an observer: automatic (normally 1d)"
        ),
    )
    value.add_argument(
        "--max-photometry-comets",
        type=int,
        default=MAX_COMETS,
        metavar="COUNT",
        help=(
            "maximum sequential Horizons requests authorized for this run; "
            f"default: {MAX_COMETS}"
        ),
    )
    value.add_argument(
        "--debug",
        action="store_true",
        help="show a traceback instead of formatting an expected failure",
    )
    value.add_argument("--format", choices=("table", "json"), default="table")
    value.add_argument("--output", type=Path)
    return value


def _unknown(value: object, formatter=str) -> str:
    return "unknown" if value is None else formatter(value)


def _photometry_by_designation(
    result: CometDiscoveryResult,
    photometry: CometDiscoveryPhotometry | None,
):
    if photometry is None:
        return None
    values = {
        value.canonical_designation: value
        for value in photometry.results
    }
    expected = {value.canonical_designation for value in result.records}
    if len(values) != len(photometry.results) or set(values) != expected:
        raise ValueError(
            "photometry results do not match the discovery records."
        )
    return values


def _ordered_records(
    result: CometDiscoveryResult,
    by_designation,
):
    if by_designation is None:
        return result.records

    def key(record):
        sample = by_designation[
            record.canonical_designation
        ].brightest_total_sample
        return (
            sample is None,
            float("inf") if sample is None else sample.total_magnitude,
            record.canonical_designation.casefold(),
        )

    return tuple(sorted(result.records, key=key))


def table_text(
    result: CometDiscoveryResult,
    photometry: CometDiscoveryPhotometry | None = None,
) -> str:
    headers = (
        "designation", "name", "1st obs.", "class", "perihelion UTC",
        "q (au)",
        "e", "period (d)", "i (deg)", "Earth MOID (au)", "orbit",
        "M1 model", "M2 model", "K1 model", "K2 model",
    )
    by_designation = _photometry_by_designation(result, photometry)
    if by_designation is not None:
        headers += (
            "brightest sampled T-mag model", "T-mag epoch UTC",
            "brightest sampled N-mag model", "N-mag epoch UTC",
        )
    rows = []
    for row in _ordered_records(result, by_designation):
        values = (
            row.canonical_designation,
            _unknown(row.name),
            _unknown(row.first_observation),
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
        )
        if by_designation is not None:
            model = by_designation[row.canonical_designation]
            total = model.brightest_total_sample
            nuclear = model.brightest_nuclear_sample
            values += (
                _unknown(
                    None if total is None else total.total_magnitude,
                    lambda x: f"{x:.3f}",
                ),
                _unknown(
                    None if total is None else total.epoch_utc,
                    lambda x: x.isoformat(),
                ),
                _unknown(
                    None if nuclear is None else nuclear.nuclear_magnitude,
                    lambda x: f"{x:.3f}",
                ),
                _unknown(
                    None if nuclear is None else nuclear.epoch_utc,
                    lambda x: x.isoformat(),
                ),
            )
        rows.append(values)
    widths = [len(value) for value in headers]
    for row in rows:
        widths = [max(old, len(value)) for old, value in zip(widths, row)]
    lines = [
        (
            "Comets selected by perihelion time and distance; "
            "not a visibility forecast."
        ),
        f"Retrieved: {result.retrieved_at_utc.isoformat()}",
        f"Matched comets: {len(result.records)}",
    ]
    if photometry is not None:
        lines.extend((
            (
                "Horizons observer model: "
                f"{photometry.observer_location} "
                f"({photometry.observer_latitude_deg:.6f}, "
                f"{photometry.observer_longitude_deg:.6f}, "
                f"{photometry.observer_elevation_m:.1f} m); "
                f"±{photometry.perihelion_window_days}d around each "
                f"perihelion; step {photometry.magnitude_step}."
            ),
            (
                "Brightest sampled T-mag/N-mag values are provider models, "
                "not continuous minima, visibility, or detectability."
            ),
        ))
    lines.extend((
        "  ".join(value.ljust(width) for value, width in zip(headers, widths)),
        "  ".join("-" * width for width in widths),
    ))
    lines.extend(
        "  ".join(value.ljust(width) for value, width in zip(row, widths))
        for row in rows
    )
    lines.extend((
        "",
        "Header key:",
        (
            "  designation: canonical comet designation; "
            "name: comet name, if any."
        ),
        (
            "  1st obs.: earliest observation used by the current orbit "
            "solution; not necessarily the discovery date."
        ),
        (
            "  P: periodic; C: non-periodic; D: disappeared; "
            "X: orbit not meaningfully computable."
        ),
        (
            "  A: object found to be a minor planet; "
            "I: interstellar object."
        ),
        (
            "  A leading number is the permanent number of a "
            "periodic comet (for example, 2P)."
        ),
        "  class: SBDB orbit-class code; orbit: provider orbit-solution ID.",
        (
            "  perihelion UTC: UTC calendar date derived from the "
            "TDB perihelion time."
        ),
        "  q: perihelion distance (au); e: orbital eccentricity.",
        "  period: orbital period (d); i: orbital inclination (deg).",
        "  Earth MOID: minimum orbit intersection distance from Earth (au).",
        (
            "  M1/M2: provider total/nuclear absolute-magnitude "
            "parameters."
        ),
        "  K1/K2: provider total/nuclear magnitude-slope parameters.",
    ))
    if photometry is not None:
        lines.extend((
            (
                "  T-mag/N-mag: brightest valid sampled Horizons total/"
                "nuclear model magnitude and its UTC epoch."
            ),
            (
                "  Horizons advises treating small-body magnitudes as "
                "uncertain at roughly 1 mag in practice, potentially worse "
                "at large phase angle."
            ),
        ))
    lines.append(
        "  au: astronomical unit; d: day; deg: degree; "
        "UTC: Coordinated Universal Time."
    )
    return "\n".join(lines) + "\n"


def _sample_document(sample):
    return {
        "epoch_utc": sample.epoch_utc.isoformat(),
        "time_scale": "UTC",
        "total_model_magnitude": {
            "quantity": "T-mag",
            "value": sample.total_magnitude,
            "unit": "mag",
        },
        "nuclear_model_magnitude": {
            "quantity": "N-mag",
            "value": sample.nuclear_magnitude,
            "unit": "mag",
        },
    }


def _summary_document(sample, *, quantity, attribute):
    return {
        "quantity": quantity,
        "value": None if sample is None else getattr(sample, attribute),
        "unit": "mag",
        "epoch_utc": None if sample is None else sample.epoch_utc.isoformat(),
        "time_scale": "UTC",
        "meaning": "brightest valid sampled provider model value",
    }


def json_text(
    result: CometDiscoveryResult,
    photometry: CometDiscoveryPhotometry | None = None,
) -> str:
    by_designation = _photometry_by_designation(result, photometry)
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
    if photometry is not None:
        document["observer_model_photometry"] = {
            "observer": {
                "location": photometry.observer_location,
                "latitude": {
                    "value": photometry.observer_latitude_deg,
                    "unit": "deg",
                },
                "longitude": {
                    "value": photometry.observer_longitude_deg,
                    "unit": "deg",
                },
                "elevation": {
                    "value": photometry.observer_elevation_m,
                    "unit": "m",
                },
            },
            "sampling": {
                "strategy": "per-comet window centered on perihelion",
                "perihelion_window_days_each_side": (
                    photometry.perihelion_window_days
                ),
                "step": photometry.magnitude_step,
                "endpoint_inclusive": True,
            },
            "meaning": (
                "sampled Horizons provider model; not a continuous minimum, "
                "visibility forecast, or detectability estimate"
            ),
            "practical_uncertainty_warning": (
                "Treat small-body model magnitudes as uncertain at roughly "
                "1 mag in practice and potentially worse at large phase angle."
            ),
        }
    for record in _ordered_records(result, by_designation):
        values = asdict(record)
        values["canonical_designation"] = record.canonical_designation
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
        if by_designation is not None:
            model = by_designation[record.canonical_designation]
            values["observer_model_photometry"] = {
                "provider": {
                    "identity": model.provider,
                    "endpoint": model.provider_endpoint,
                    "transport": model.provider_transport,
                    "version": model.provider_version,
                    "retrieved_at_utc": model.retrieved_at_utc.isoformat(),
                    "request_parameters": dict(model.request_parameters),
                    "raw_sha256": model.raw_sha256,
                },
                "target": {
                    "provider_spk_id": model.provider_spk_id,
                    "orbit_solution_id": model.orbit_solution_id,
                },
                "sampling": {
                    "start_utc": model.start_utc.isoformat(),
                    "stop_utc": model.stop_utc.isoformat(),
                    "step": model.magnitude_step,
                    "sample_count": len(model.samples),
                    "endpoint_inclusive": True,
                },
                "brightest_sampled_total": _summary_document(
                    model.brightest_total_sample,
                    quantity="T-mag",
                    attribute="total_magnitude",
                ),
                "brightest_sampled_nuclear": _summary_document(
                    model.brightest_nuclear_sample,
                    quantity="N-mag",
                    attribute="nuclear_magnitude",
                ),
                "notices": list(model.notices),
                "samples": [
                    _sample_document(sample) for sample in model.samples
                ],
            }
        document["records"].append(values)
    return json.dumps(document, indent=2, sort_keys=True) + "\n"


def main(argv=None) -> int:
    argument_parser = parser()
    arguments = argument_parser.parse_args(argv)
    if arguments.magnitude_step is not None and arguments.observer_location is None:
        argument_parser.error(
            "--magnitude-step requires --observer-location."
        )
    if (
        arguments.max_photometry_comets != MAX_COMETS
        and arguments.observer_location is None
    ):
        argument_parser.error(
            "--max-photometry-comets requires --observer-location."
        )
    try:
        result = discover_comets(
            arguments.start,
            arguments.stop,
            max_perihelion_distance_au=arguments.max_perihelion_distance,
        )
        photometry = None
        if arguments.observer_location is not None:
            photometry = characterize_discovery_photometry(
                result,
                observer_location=arguments.observer_location,
                magnitude_step=arguments.magnitude_step,
                perihelion_window_days=DEFAULT_PERIHELION_WINDOW_DAYS,
                max_comets=arguments.max_photometry_comets,
            )
        text = (
            table_text(result, photometry)
            if arguments.format == "table"
            else json_text(result, photometry)
        )
        if arguments.output is None:
            print(text, end="")
        else:
            arguments.output.write_text(text, encoding="utf-8")
        return 0
    except (OSError, ValueError) as error:
        if arguments.debug:
            raise
        print(f"wenu_retrieve_comets: error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
