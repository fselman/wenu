"""Render the twelve traditional zodiac constellations as separate charts."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from astropy.coordinates import BarycentricMeanEcliptic, SkyCoord
from astropy.time import Time
import astropy.units as u

from wenu import (
    CelestialSphere,
    FixedDetailPolicy,
    MatplotlibRenderer,
    Observer,
    PresentationMode,
    PrintMode,
    RegionalChart,
    ResolvedDetail,
    compose_chart,
)

ZODIAC_CONSTELLATIONS = (
    "Ari", "Tau", "Gem", "Cnc", "Leo", "Vir",
    "Lib", "Sco", "Sgr", "Cap", "Aqr", "Psc",
)
STAR_MAGNITUDE_LIMIT = 5.5
DEFAULT_OUTPUT = Path("output/zodiac-constellations")


def _vector(altitude_deg, azimuth_deg):
    altitude = np.radians(float(altitude_deg))
    azimuth = np.radians(float(azimuth_deg))
    return np.asarray((
        np.cos(altitude) * np.cos(azimuth),
        np.cos(altitude) * np.sin(azimuth),
        np.sin(altitude),
    ))


def _target_up_position_angle(
    *, center_alt_deg, center_az_deg, target_alt_deg, target_az_deg
):
    """Return chart rotation that puts one target direction at the top."""
    center = _vector(center_alt_deg, center_az_deg)
    zenith = np.asarray((0.0, 0.0, 1.0))
    chart_up = zenith - np.dot(zenith, center) * center
    norm = np.linalg.norm(chart_up)
    chart_up = (
        np.asarray((1.0, 0.0, 0.0))
        if norm <= 1.0e-15 else chart_up / norm
    )
    chart_right = np.cross(center, chart_up)
    target = _vector(target_alt_deg, target_az_deg)
    direction = target - np.dot(target, center) * center
    norm = np.linalg.norm(direction)
    if norm <= 1.0e-15:
        return 0.0
    direction /= norm
    return float(np.degrees(np.arctan2(
        np.dot(direction, chart_right),
        np.dot(direction, chart_up),
    )))


def _north_ecliptic_pole(observer):
    pole = SkyCoord(
        lon=0.0 * u.deg,
        lat=90.0 * u.deg,
        frame=BarycentricMeanEcliptic(equinox=Time("J2000")),
    )
    return pole.transform_to(observer.altaz_frame)


def _sky(observer, constellation, *, mask):
    sky = CelestialSphere(observer)
    sky.add_stars(catalog="hipparcos", magnitude_limit=STAR_MAGNITUDE_LIMIT)
    sky.add_constellations(system="western", selected=(constellation,))
    if mask:
        sky.add_constellation_boundaries(
            boundaries="iau",
            constellations=(constellation,),
        )
    sky.add_equatorial_grid(
        ra=tuple(range(0, 360, 15)),
        dec=tuple(range(-75, 76, 15)),
        include_equator=True,
        frame="fk5",
        equinox="J2000",
    )
    sky.add_ecliptic_grid(include_ecliptic=True, equinox="J2000")
    return sky


def _chart(sky, observer, constellation, *, padding, mask):
    chart = RegionalChart.from_constellations(
        sky,
        (constellation,),
        observer=observer,
        framing_padding=padding,
        minimum_angular_radius_deg=12.0,
        aspect_ratio=1.0,
        label_selection=(constellation,),
        outside_mask_constellations=(constellation,) if mask else None,
    )
    pole = _north_ecliptic_pole(observer)
    return replace(
        chart,
        position_angle_deg=_target_up_position_angle(
            center_alt_deg=chart.center_alt_deg,
            center_az_deg=chart.center_az_deg,
            target_alt_deg=float(pole.alt.deg),
            target_az_deg=float(pole.az.deg),
        ),
    )


def render_zodiac(
    output_directory=DEFAULT_OUTPUT,
    *, file_format="pdf", width_inches=7.0, dpi=300,
    framing_padding=1.25, data_directory=None, mask=False,
    presentation=False,
):
    """Render and return twelve paths in traditional zodiac order."""
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    observer_options = {}
    if data_directory is not None:
        observer_options["data_directory"] = Path(data_directory)
    observer = Observer(
        location="La Ligua",
        time="2026-08-15 21:00",
        **observer_options,
    )
    outputs = []
    try:
        for index, constellation in enumerate(ZODIAC_CONSTELLATIONS, 1):
            sky = _sky(observer, constellation, mask=bool(mask))
            chart = _chart(
                sky,
                observer,
                constellation,
                padding=float(framing_padding),
                mask=bool(mask),
            )
            mode_type = PresentationMode if presentation else PrintMode
            composition = compose_chart(
                chart,
                style="atlas",
                mode=mode_type(
                    width_inches=float(width_inches), dpi=int(dpi)
                ),
                detail=FixedDetailPolicy(ResolvedDetail(
                    star_magnitude_limit=STAR_MAGNITUDE_LIMIT,
                )),
            )
            figure, axes = plt.subplots(figsize=(
                composition.mode.width_inches,
                composition.mode.height_inches,
            ))
            composition.style.configure_axes(
                axes, title=f"{constellation} — zodiac constellation"
            )
            destination = output_directory / (
                f"{index:02d}-{constellation.lower()}.{file_format}"
            )
            try:
                chart.export(
                    sky, MatplotlibRenderer(axes), destination,
                    composition=composition,
                )
            finally:
                plt.close(figure)
            outputs.append(destination)
    finally:
        observer.close()
    return tuple(outputs)


def parser():
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    value.add_argument(
        "--format", choices=("pdf", "png", "svg"), default="pdf",
        dest="file_format",
    )
    value.add_argument("--width-inches", type=float, default=7.0)
    value.add_argument("--dpi", type=int, default=300)
    value.add_argument("--framing-padding", type=float, default=1.25)
    value.add_argument("--data-directory", type=Path)
    value.add_argument(
        "--mask",
        action="store_true",
        help="shade the chart outside the selected IAU constellation",
    )
    value.add_argument(
        "--presentation",
        action="store_true",
        help="use Wenu's high-contrast atlas presentation mode",
    )
    return value


def main():
    arguments = parser().parse_args()
    for path in render_zodiac(
        arguments.output,
        file_format=arguments.file_format,
        width_inches=arguments.width_inches,
        dpi=arguments.dpi,
        framing_padding=arguments.framing_padding,
        data_directory=arguments.data_directory,
        mask=arguments.mask,
        presentation=arguments.presentation,
    ):
        print(path)


if __name__ == "__main__":
    main()
