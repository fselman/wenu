#!/usr/bin/env python3
"""Build LMC and SMC isophotes from an aggregated Gaia DR3 query.

The downloaded tables are not catalogues of confirmed members. Broad
astrometric windows suppress most Milky Way foreground stars so that the
large-scale morphology of each Magellanic Cloud can be measured. Exact ADQL
and processing parameters are saved in the provenance JSON.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Iterable

import astropy.units as u
from astropy.coordinates import SkyCoord, SkyOffsetFrame
from astropy.table import Table
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


GAIA_RELEASE = "Gaia DR3"
GAIA_TABLE = "gaiadr3.gaia_source_lite"
TAP_SERVICES = {
    "ari": "https://gaia.ari.uni-heidelberg.de/tap",
    "esa": "https://gea.esac.esa.int/tap-server/tap",
}
HEALPIX_ORDER = 9
HEALPIX_SOURCE_ORDER = 12
HEALPIX_DIVISOR = 2 ** (
    35 + 2 * (HEALPIX_SOURCE_ORDER - HEALPIX_ORDER)
)


@dataclass(frozen=True)
class Cloud:
    key: str
    name: str
    center_ra_deg: float
    center_dec_deg: float
    query_radius_deg: float
    pmra_min: float
    pmra_max: float
    pmdec_min: float
    pmdec_max: float


CLOUDS = {
    "lmc": Cloud(
        key="lmc",
        name="Large Magellanic Cloud",
        center_ra_deg=80.8942,
        center_dec_deg=-69.7561,
        query_radius_deg=12.0,
        pmra_min=0.5,
        pmra_max=3.2,
        pmdec_min=-1.0,
        pmdec_max=1.5,
    ),
    "smc": Cloud(
        key="smc",
        name="Small Magellanic Cloud",
        center_ra_deg=13.1867,
        center_dec_deg=-72.8286,
        query_radius_deg=7.0,
        pmra_min=-0.2,
        pmra_max=1.8,
        pmdec_min=-2.2,
        pmdec_max=-0.2,
    ),
}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--cloud",
        choices=("both", "lmc", "smc"),
        default="both",
        help="Cloud data to process.",
    )
    parser.add_argument(
        "--service",
        choices=("auto", "ari", "esa"),
        default="auto",
        help=(
            "Gaia TAP service. Auto tries the ARI mirror first and ESA "
            "second."
        ),
    )
    parser.add_argument(
        "--field",
        choices=("g_flux", "source_count"),
        default="g_flux",
        help="Quantity from which contours are extracted.",
    )
    parser.add_argument(
        "--g-min",
        type=float,
        default=12.0,
        help="Bright G-magnitude bound used by the Gaia query.",
    )
    parser.add_argument(
        "--g-max",
        type=float,
        default=20.0,
        help="Faint G-magnitude bound used by the Gaia query.",
    )
    parser.add_argument(
        "--parallax-limit",
        type=float,
        default=0.5,
        help="Absolute parallax limit in milliarcseconds.",
    )
    parser.add_argument(
        "--grid-step-deg",
        type=float,
        default=0.10,
        help="Tangent-plane raster pixel size.",
    )
    parser.add_argument(
        "--smooth-sigma-deg",
        type=float,
        default=0.25,
        help="Gaussian smoothing sigma.",
    )
    parser.add_argument(
        "--contour-fractions",
        type=float,
        nargs="+",
        default=(0.08, 0.16, 0.32, 0.55),
        help="Fractions of the background-subtracted smoothed peak.",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Repeat Gaia queries instead of reusing cached ECSV tables.",
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path("magellanic-clouds-output"),
        help="Directory for diagnostic PNG images.",
    )
    return parser.parse_args()


def repository_root() -> Path:
    root = Path(__file__).resolve().parents[1]
    if not (root / "pyproject.toml").is_file():
        raise SystemExit(
            "Could not locate the Wenu repository root. "
            "Keep this script in the repository tools directory."
        )
    return root


def data_directory(root: Path) -> Path:
    return (
        root
        / "src"
        / "wenu"
        / "data"
        / "isophotes"
        / "magellanic_clouds"
    )


def selected_clouds(name: str) -> list[Cloud]:
    if name == "both":
        return [CLOUDS["lmc"], CLOUDS["smc"]]
    return [CLOUDS[name]]


def adql(
    cloud: Cloud,
    *,
    g_min: float,
    g_max: float,
    parallax_limit: float,
) -> str:
    return f"""
SELECT
    source_id / {HEALPIX_DIVISOR} AS healpix{HEALPIX_ORDER},
    AVG(ra) AS ra_deg,
    MIN(ra) AS ra_min_deg,
    MAX(ra) AS ra_max_deg,
    AVG(dec) AS dec_deg,
    COUNT(*) AS source_count,
    SUM(POWER(10.0, -0.4 * phot_g_mean_mag)) AS g_flux
FROM {GAIA_TABLE}
WHERE
    1 = CONTAINS(
        POINT('ICRS', ra, dec),
        CIRCLE(
            'ICRS',
            {cloud.center_ra_deg},
            {cloud.center_dec_deg},
            {cloud.query_radius_deg}
        )
    )
    AND phot_g_mean_mag >= {g_min}
    AND phot_g_mean_mag <= {g_max}
    AND parallax >= {-parallax_limit}
    AND parallax <= {parallax_limit}
    AND pmra >= {cloud.pmra_min}
    AND pmra <= {cloud.pmra_max}
    AND pmdec >= {cloud.pmdec_min}
    AND pmdec <= {cloud.pmdec_max}
GROUP BY healpix{HEALPIX_ORDER}
""".strip()


def service_order(requested: str) -> tuple[str, ...]:
    if requested == "auto":
        return ("ari", "esa")
    return (requested,)


def query_gaia(
    query: str,
    *,
    requested_service: str,
) -> tuple[Table, str, str]:
    try:
        import pyvo
    except ImportError as error:
        raise SystemExit(
            "PyVO is required. Install or update Astroquery with:\n"
            "  conda install --solver=classic -c conda-forge "
            '"astroquery>=0.4.11"'
        ) from error

    failures = []
    for service_name in service_order(requested_service):
        service_url = TAP_SERVICES[service_name]
        print(f"Using Gaia TAP service: {service_name} ({service_url})")
        try:
            service = pyvo.dal.TAPService(service_url)
            result = service.run_async(
                query,
                timeout=7200.0,
                delete=True,
            )
            return Table(result.to_table()), service_name, service_url
        except Exception as error:
            failures.append((service_name, service_url, error))
            print(f"{service_name.upper()} TAP failed: {error}")
            if requested_service == "auto":
                print("Trying the next Gaia TAP service...")

    print("\nAll selected Gaia TAP services failed.")
    print("The submitted ADQL was:\n")
    print(query)
    summary = "\n".join(
        f"  {name} ({url}): {error}"
        for name, url, error in failures
    )
    raise SystemExit(f"\nGaia TAP errors:\n{summary}")


def repair_ra_seam(table: Table) -> None:
    """Repair arithmetic RA means for cells that straddle zero degrees."""
    ra = np.asarray(table["ra_deg"], dtype=float)
    ra_min = np.asarray(table["ra_min_deg"], dtype=float)
    ra_max = np.asarray(table["ra_max_deg"], dtype=float)
    crossing = (ra_max - ra_min) > 180.0
    ra[crossing] = np.mod(ra[crossing] + 180.0, 360.0)
    table["ra_deg"] = ra


def cached_or_query(
    cloud: Cloud,
    directory: Path,
    *,
    refresh: bool,
    requested_service: str,
    g_min: float,
    g_max: float,
    parallax_limit: float,
) -> tuple[Table, str, str | None, str | None, bool]:
    cache = directory / (
        f"{cloud.key}_gaia_dr3_healpix{HEALPIX_ORDER}.ecsv"
    )
    query = adql(
        cloud,
        g_min=g_min,
        g_max=g_max,
        parallax_limit=parallax_limit,
    )
    if cache.is_file() and not refresh:
        print(f"Reusing: {cache}")
        table = Table.read(cache, format="ascii.ecsv")
        return (
            table,
            query,
            table.meta.get("tap_service"),
            table.meta.get("tap_service_url"),
            True,
        )

    print(f"Querying Gaia DR3 for the {cloud.name}...")
    table, service_name, service_url = query_gaia(
        query,
        requested_service=requested_service,
    )
    repair_ra_seam(table)
    table.meta.update(
        {
            "gaia_release": GAIA_RELEASE,
            "gaia_table": GAIA_TABLE,
            "cloud": cloud.name,
            "healpix_order": HEALPIX_ORDER,
            "tap_service": service_name,
            "tap_service_url": service_url,
        }
    )
    table.write(cache, format="ascii.ecsv", overwrite=True)
    print(f"Cached:  {cache} ({len(table)} aggregate cells)")
    return table, query, service_name, service_url, False


def gaussian_kernel(sigma_pixels: float) -> np.ndarray:
    if sigma_pixels <= 0.0:
        return np.asarray([1.0])
    radius = max(1, int(np.ceil(4.0 * sigma_pixels)))
    coordinate = np.arange(-radius, radius + 1, dtype=float)
    kernel = np.exp(-0.5 * (coordinate / sigma_pixels) ** 2)
    return kernel / kernel.sum()


def smooth(array: np.ndarray, sigma_pixels: float) -> np.ndarray:
    kernel = gaussian_kernel(sigma_pixels)
    first = np.apply_along_axis(
        lambda values: np.convolve(values, kernel, mode="same"),
        axis=0,
        arr=array,
    )
    return np.apply_along_axis(
        lambda values: np.convolve(values, kernel, mode="same"),
        axis=1,
        arr=first,
    )


def projected_cells(
    cloud: Cloud,
    table: Table,
) -> tuple[np.ndarray, np.ndarray]:
    center = SkyCoord(
        ra=cloud.center_ra_deg * u.deg,
        dec=cloud.center_dec_deg * u.deg,
        frame="icrs",
    )
    frame = SkyOffsetFrame(origin=center)
    coordinates = SkyCoord(
        ra=np.asarray(table["ra_deg"], dtype=float) * u.deg,
        dec=np.asarray(table["dec_deg"], dtype=float) * u.deg,
        frame="icrs",
    ).transform_to(frame)
    return (
        coordinates.lon.to_value(u.deg),
        coordinates.lat.to_value(u.deg),
    )


def raster(
    cloud: Cloud,
    table: Table,
    *,
    field: str,
    grid_step_deg: float,
    smooth_sigma_deg: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    x, y = projected_cells(cloud, table)
    radius = cloud.query_radius_deg
    edges = np.arange(
        -radius,
        radius + grid_step_deg * 1.01,
        grid_step_deg,
    )
    weights = np.asarray(table[field], dtype=float)
    values, x_edges, y_edges = np.histogram2d(
        x,
        y,
        bins=(edges, edges),
        weights=weights,
    )
    sigma_pixels = smooth_sigma_deg / grid_step_deg
    values = smooth(values, sigma_pixels)

    x_centers = 0.5 * (x_edges[:-1] + x_edges[1:])
    y_centers = 0.5 * (y_edges[:-1] + y_edges[1:])
    xx, yy = np.meshgrid(x_centers, y_centers, indexing="ij")
    outer = np.hypot(xx, yy) >= 0.75 * radius
    background = float(np.nanmedian(values[outer]))
    values = np.maximum(values - background, 0.0)
    return x_centers, y_centers, values, background


def ring_area(ring: np.ndarray) -> float:
    x = ring[:, 0]
    y = ring[:, 1]
    return 0.5 * abs(
        np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1))
    )


def close_ring(segment: np.ndarray) -> np.ndarray | None:
    if len(segment) < 8:
        return None
    if not np.allclose(segment[0], segment[-1], atol=1.0e-7):
        segment = np.vstack((segment, segment[0]))
    if ring_area(segment) < 0.01:
        return None
    ring = segment.copy()
    ring[-1] = ring[0]
    return ring


def celestial_ring(cloud: Cloud, ring: np.ndarray) -> list[list[float]]:
    center = SkyCoord(
        ra=cloud.center_ra_deg * u.deg,
        dec=cloud.center_dec_deg * u.deg,
        frame="icrs",
    )
    frame = SkyOffsetFrame(origin=center)
    coordinates = SkyCoord(
        lon=ring[:, 0] * u.deg,
        lat=ring[:, 1] * u.deg,
        frame=frame,
    ).icrs
    longitude = (
        (coordinates.ra.to_value(u.deg) + 180.0) % 360.0
    ) - 180.0
    latitude = coordinates.dec.to_value(u.deg)
    return [
        [round(float(lon), 7), round(float(lat), 7)]
        for lon, lat in zip(longitude, latitude)
    ]


def contour_polygons(contour_set) -> list[list[np.ndarray]]:
    """Return closed polygon rings grouped by contour level.

    Matplotlib 3.8 represents each contour level as a compound Path.
    ``ContourSet.allsegs`` passes the vertices of that compound path through
    a deprecated compatibility layer and can expose individual coordinate
    pairs instead of polygon arrays. ``Path.to_polygons`` is the supported
    way to split each compound path into its closed component rings.
    """
    paths = contour_set.get_paths()
    if len(paths) != len(contour_set.levels):
        raise RuntimeError(
            "Matplotlib returned an unexpected number of contour paths: "
            f"{len(paths)} paths for {len(contour_set.levels)} levels."
        )
    return [
        [
            np.asarray(polygon, dtype=float)
            for polygon in path.to_polygons(closed_only=True)
        ]
        for path in paths
    ]


def contours(
    cloud: Cloud,
    x: np.ndarray,
    y: np.ndarray,
    values: np.ndarray,
    fractions: Iterable[float],
) -> tuple[list[dict], list[float]]:
    peak = float(np.nanmax(values))
    if not np.isfinite(peak) or peak <= 0.0:
        raise SystemExit(f"No usable signal remains for {cloud.name}.")

    fraction_values = sorted(set(float(value) for value in fractions))
    if (
        not fraction_values
        or fraction_values[0] <= 0.0
        or fraction_values[-1] >= 1.0
    ):
        raise SystemExit(
            "Contour fractions must be unique values strictly between 0 and 1."
        )
    levels = [fraction * peak for fraction in fraction_values]

    figure, axes = plt.subplots()
    contour_set = axes.contour(x, y, values.T, levels=levels)
    features = []
    for index, segments in enumerate(contour_polygons(contour_set)):
        polygons = []
        for segment in segments:
            ring = close_ring(np.asarray(segment, dtype=float))
            if ring is None:
                continue
            polygons.append([celestial_ring(cloud, ring)])
        if not polygons:
            continue
        features.append(
            {
                "type": "Feature",
                "id": f"{cloud.key}-level-{index + 1}",
                "properties": {
                    "cloud": cloud.key.upper(),
                    "name": cloud.name,
                    "level": index + 1,
                    "fraction_of_peak": fraction_values[index],
                    "outer_to_inner": True,
                },
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": polygons,
                },
            }
        )
    plt.close(figure)
    return features, levels


def diagnostic(
    cloud: Cloud,
    x: np.ndarray,
    y: np.ndarray,
    values: np.ndarray,
    levels: list[float],
    destination: Path,
    field: str,
) -> None:
    figure, axes = plt.subplots(figsize=(8, 8), constrained_layout=True)
    image = axes.imshow(
        values.T,
        origin="lower",
        extent=(x[0], x[-1], y[0], y[-1]),
        interpolation="nearest",
        cmap="magma",
        aspect="equal",
    )
    axes.contour(x, y, values.T, levels=levels, colors="cyan")
    axes.set(
        title=f"{cloud.name}: Gaia DR3 {field}",
        xlabel="Tangent-plane longitude (deg)",
        ylabel="Tangent-plane latitude (deg)",
    )
    figure.colorbar(image, ax=axes, label=field)
    figure.savefig(destination, dpi=180)
    plt.close(figure)
    print(f"Diagnostic: {destination}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_support_files(directory: Path) -> None:
    (directory / "__init__.py").write_text(
        '"""Gaia-derived Magellanic Cloud isophote data."""\n',
        encoding="utf-8",
    )
    (directory / "README.md").write_text(
        "# Magellanic Cloud isophotes\n\n"
        "This directory is generated by "
        "`tools/query_magellanic_clouds_gaia.py`.\n\n"
        "The ECSV files contain Gaia DR3 aggregates for broad "
        "LMC/SMC-like astrometric selections. The GeoJSON contains "
        "derived contour polygons. These selections describe morphology "
        "and must not be interpreted as membership probabilities. See "
        "the provenance JSON for the complete ADQL and processing "
        "parameters.\n\n"
        "Data source: Gaia DR3, queried through an official Gaia TAP "
        "service or partner mirror.\n",
        encoding="utf-8",
    )


def main() -> None:
    arguments = parse_arguments()
    if arguments.g_min >= arguments.g_max:
        raise SystemExit("--g-min must be smaller than --g-max.")
    if arguments.grid_step_deg <= 0.0:
        raise SystemExit("--grid-step-deg must be positive.")
    if arguments.smooth_sigma_deg < 0.0:
        raise SystemExit("--smooth-sigma-deg cannot be negative.")

    root = repository_root()
    directory = data_directory(root)
    directory.mkdir(parents=True, exist_ok=True)
    write_support_files(directory)
    diagnostics = (root / arguments.output_directory).resolve()
    diagnostics.mkdir(parents=True, exist_ok=True)

    query_records: list[dict] = []
    cloud_records: list[dict] = []
    output_records: list[dict] = []

    for cloud in selected_clouds(arguments.cloud):
        table, query, service_name, service_url, reused = cached_or_query(
            cloud,
            directory,
            refresh=arguments.refresh,
            requested_service=arguments.service,
            g_min=arguments.g_min,
            g_max=arguments.g_max,
            parallax_limit=arguments.parallax_limit,
        )
        x, y, values, background = raster(
            cloud,
            table,
            field=arguments.field,
            grid_step_deg=arguments.grid_step_deg,
            smooth_sigma_deg=arguments.smooth_sigma_deg,
        )
        features, levels = contours(
            cloud,
            x,
            y,
            values,
            arguments.contour_fractions,
        )
        geojson_path = directory / f"{cloud.key}_gaia_dr3.json"
        geojson = {
            "type": "FeatureCollection",
            "properties": {
                "title": f"Gaia DR3 {cloud.name} isophotes",
                "cloud": cloud.key.upper(),
                "frame": "ICRS",
                "longitude": (
                    "right ascension in degrees, normalized to [-180, 180]"
                ),
                "latitude": "declination in degrees",
                "field": arguments.field,
                "level_order": "outer to inner",
            },
            "features": features,
        }
        geojson_path.write_text(
            json.dumps(geojson, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Canonical contours: {geojson_path}")
        output_records.append(
            {
                "cloud": cloud.key,
                "path": str(geojson_path.relative_to(root)),
                "sha256": sha256(geojson_path),
                "feature_count": len(features),
            }
        )
        diagnostic(
            cloud,
            x,
            y,
            values,
            levels,
            diagnostics / f"{cloud.key}-diagnostic.png",
            arguments.field,
        )
        query_records.append(
            {
                "cloud": cloud.key,
                "adql": query,
                "requested_service": arguments.service,
                "tap_service": service_name,
                "tap_service_url": service_url,
                "cache_reused": reused,
            }
        )
        cloud_records.append(
            {
                **asdict(cloud),
                "aggregate_cells": len(table),
                "background": background,
                "absolute_contour_levels": levels,
                "features_written": len(features),
            }
        )

    provenance_path = (
        directory / "magellanic_clouds_gaia_dr3.provenance.json"
    )
    provenance = {
        "title": "Gaia-derived Magellanic Cloud isophotes",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "release": GAIA_RELEASE,
            "table": GAIA_TABLE,
            "available_tap_services": TAP_SERVICES,
            "requested_service": arguments.service,
            "query_interface": "pyvo.dal.TAPService.run_async",
        },
        "interpretation": (
            "Broad astrometric selections for morphology; not membership "
            "probabilities."
        ),
        "healpix": {
            "source_id_order": HEALPIX_SOURCE_ORDER,
            "aggregate_order": HEALPIX_ORDER,
            "source_id_divisor": HEALPIX_DIVISOR,
        },
        "selection": {
            "phot_g_mean_mag": [arguments.g_min, arguments.g_max],
            "absolute_parallax_max_mas": arguments.parallax_limit,
        },
        "processing": {
            "field": arguments.field,
            "grid_step_deg": arguments.grid_step_deg,
            "smooth_sigma_deg": arguments.smooth_sigma_deg,
            "background": (
                "median of smoothed pixels at radius >= 0.75 query radius"
            ),
            "contour_fractions": sorted(
                set(float(value) for value in arguments.contour_fractions)
            ),
            "minimum_closed_ring_vertices": 8,
            "minimum_tangent_plane_area_deg2": 0.01,
        },
        "clouds": cloud_records,
        "queries": query_records,
        "outputs": output_records,
    }
    provenance_path.write_text(
        json.dumps(provenance, indent=2) + "\n",
        encoding="utf-8",
    )

    print()
    print(f"Provenance:         {provenance_path}")
    print(
        "Features:           "
        f"{sum(record['feature_count'] for record in output_records)}"
    )
    print()
    print(
        "Inspect both diagnostic PNGs before integrating these contours "
        "into Wenu."
    )


if __name__ == "__main__":
    main()
