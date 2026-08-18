"""Contracts for the twelve-chart zodiac review tool."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import astropy.units as u
from astropy.coordinates import AltAz, EarthLocation, SkyCoord
from astropy.time import Time
import pytest


PATH = Path(__file__).parents[1] / "tools/render_zodiac_constellations.py"
SPEC = importlib.util.spec_from_file_location("render_zodiac", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_traditional_zodiac_order_and_spanish_names_are_complete():
    assert MODULE.ZODIAC_CONSTELLATIONS == (
        "Ari", "Tau", "Gem", "Cnc", "Leo", "Vir",
        "Lib", "Sco", "Sgr", "Cap", "Aqr", "Psc",
    )
    assert tuple(MODULE.ENGLISH_NAMES) == MODULE.ZODIAC_CONSTELLATIONS
    assert MODULE.ENGLISH_NAMES["Gem"] == "Gemini"
    assert MODULE.ENGLISH_NAMES["Sco"] == "Scorpius"
    assert MODULE.STAR_MAGNITUDE_LIMIT == pytest.approx(5.5)


def test_defaults_are_cartoon_presentation_with_canonical_mask_switch():
    arguments = MODULE.parser().parse_args([])

    assert arguments.output == Path("output/zodiac-constellations")
    assert arguments.file_format == "png"
    assert arguments.style == "cartoon"
    assert arguments.mode == "presentation"
    assert arguments.magnitude_limit == pytest.approx(5.5)
    assert arguments.mask is False

    selected = MODULE.parser().parse_args(["--mask", "--presentation"])
    assert selected.mask is True
    assert selected.mode == "presentation"


def test_effective_arguments_fix_requested_content_without_mask_literals():
    arguments = MODULE.parser().parse_args(["--mask"])
    effective = MODULE._effective_arguments(
        arguments, Path("output/01-ari.png")
    )

    assert effective.style == "cartoon"
    assert effective.mode == "presentation"
    assert effective.magnitude_limit == pytest.approx(5.5)
    assert effective.constellation_lines is True
    assert effective.constellation_labels is True
    assert effective.constellation_boundaries is False
    assert effective.equatorial_grid is True
    assert effective.grid_references == {"equatorial", "ecliptic"}
    assert "constellation_boundaries" not in MODULE.VISIBLE_LAYERS

    source = PATH.read_text(encoding="utf-8")
    assert "draw_chart_view_from_arguments" in source
    assert "get_chart_view" in source
    assert "compose_chart" not in source
    assert "#fffdf5" not in source


def test_zodiac_presentation_enhances_ecliptic_and_grid_labels():
    assert MODULE.ECLIPTIC_LINEWIDTH == pytest.approx(1.0)
    assert MODULE.GRID_LABEL_FONTSIZE == pytest.approx(7.5)
    source = PATH.read_text(encoding="utf-8")
    assert 'ecliptic_keypoints="labeled"' in source
    assert "coordinate_label_zorder" not in source


def test_spanish_title_formats_center_ra_and_dec_to_minutes():
    frame = AltAz(
        obstime=Time("2026-08-16T01:00:00"),
        location=EarthLocation.from_geodetic(
            lon=-71.0 * u.deg,
            lat=-32.0 * u.deg,
        ),
    )
    center = SkyCoord(
        ra=30.0 * u.deg,
        dec=-10.0 * u.deg,
        frame="fk5",
        equinox=Time("J2000"),
    ).transform_to(frame)
    view = SimpleNamespace(
        chart=SimpleNamespace(
            center_alt_deg=float(center.alt.deg),
            center_az_deg=float(center.az.deg),
        ),
        observer=SimpleNamespace(altaz_frame=frame),
    )

    assert MODULE._title(view, "Tau") == (
        "Tauro — RA 02:00, Dec -10:00"
    )
