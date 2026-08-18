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
    assert MODULE.REVIEW_CONSTELLATIONS == (
        *MODULE.ZODIAC_CONSTELLATIONS, "Oph"
    )
    assert tuple(MODULE.ENGLISH_NAMES) == MODULE.REVIEW_CONSTELLATIONS
    assert MODULE.ENGLISH_NAMES["Gem"] == "Gemini"
    assert MODULE.ENGLISH_NAMES["Sco"] == "Scorpius"
    assert MODULE.ENGLISH_NAMES["Oph"] == "Ophiuchus"
    assert MODULE.REVIEW_FIGURES == {"Oph": ("Oph", "Ser")}
    assert MODULE.REVIEW_LABEL_POSITIONS == {"Oph": {"SerCau": "cl"}}
    assert MODULE.STAR_MAGNITUDE_LIMIT == pytest.approx(5.5)
    assert MODULE.REFERENCE_MAGNITUDE_RANGE == (0, 5)
    assert MODULE.ZODIAC_LEGEND_PLAN.stars.anchor == pytest.approx(
        (0.99, 0.02)
    )


def test_defaults_are_cartoon_presentation_with_canonical_mask_switch():
    arguments = MODULE.parser().parse_args([])

    assert arguments.output == Path("output/zodiac-constellations")
    assert arguments.file_format == "png"
    assert arguments.style == "cartoon"
    assert arguments.mode == "presentation"
    assert arguments.magnitude_limit == pytest.approx(5.5)
    assert arguments.mask is False
    assert arguments.dpi is None
    assert arguments.constellations == MODULE.ZODIAC_CONSTELLATIONS

    selected = MODULE.parser().parse_args(["--mask", "--presentation"])
    assert selected.mask is True
    assert selected.mode == "presentation"

    colored = MODULE.parser().parse_args(["--sky-color", "#1F699B"])
    assert colored.sky_color == "#1F699B"

    raster = MODULE.parser().parse_args(["--dpi", "300"])
    assert raster.dpi == 300

    with pytest.raises(SystemExit):
        MODULE.parser().parse_args(["--dpi", "0"])


def test_constellation_list_uses_shared_normalization_and_accepts_one():
    selected = MODULE.parser().parse_args([
        "--constellations", "sco, SGR"
    ])
    single = MODULE.parser().parse_args(["--constellations", "sco"])

    assert selected.constellations == ("Sco", "Sgr")
    assert single.constellations == ("Sco",)
    assert MODULE._selected_constellations(selected) == ("Sco", "Sgr")

    ophiuchus = MODULE.parser().parse_args(["--constellations", "Oph"])
    assert MODULE._selected_constellations(ophiuchus) == ("Oph",)

    unsupported = MODULE.parser().parse_args(["--constellations", "Cru"])
    with pytest.raises(ValueError, match="Ophiuchus.*Cru"):
        MODULE._selected_constellations(unsupported)


def test_ophiuchus_keeps_existing_zodiac_numbers_and_uses_thirteen():
    assert MODULE.REVIEW_CONSTELLATIONS.index("Sco") + 1 == 8
    assert MODULE.REVIEW_CONSTELLATIONS.index("Sgr") + 1 == 9
    assert MODULE.REVIEW_CONSTELLATIONS.index("Oph") + 1 == 13


def test_ophiuchus_reuses_constellation_set_resolution_for_serpens():
    source = PATH.read_text(encoding="utf-8")

    assert MODULE._review_figures("Oph") == ("Oph", "Ser")
    assert MODULE._review_figures("Sco") == ("Sco",)
    assert "Ser1" not in source
    assert "Ser2" not in source


def test_ophiuchus_places_serpens_cauda_label_to_the_left():
    offsets = MODULE._review_label_offsets("Oph")

    assert offsets == {"SerCau": pytest.approx((-0.48, 0.0))}
    assert MODULE._review_label_offsets("Sco") is None


def test_effective_arguments_preserve_optional_boundaries():
    arguments = MODULE.parser().parse_args([
        "--mask", "--constellation-boundaries"
    ])
    effective = MODULE._effective_arguments(
        arguments, Path("output/01-ari.png")
    )

    assert effective.style == "cartoon"
    assert effective.mode == "presentation"
    assert effective.magnitude_limit == pytest.approx(5.5)
    assert effective.constellation_lines is True
    assert effective.constellation_labels is True
    assert effective.constellation_boundaries is True
    assert effective.equatorial_grid is True
    assert effective.grid_references == {"equatorial", "ecliptic"}
    assert effective.magnitude_legend is True
    assert effective.object_legend is False
    assert "constellation_boundaries" not in MODULE.VISIBLE_LAYERS

    source = PATH.read_text(encoding="utf-8")
    assert "draw_chart_view_from_arguments" in source
    assert "get_chart_view" in source
    assert "compose_chart" not in source
    assert "#fffdf5" not in source


def test_dpi_override_updates_wenu_presentation_mode_only():
    configuration = MODULE.chart_configuration(MODULE.parser().parse_args([]))
    original_print_dpi = configuration.style_mode.print_mode.dpi
    original_presentation_dpi = configuration.style_mode.presentation_mode.dpi

    resolved = MODULE._configuration_with_dpi(configuration, 420)

    assert resolved.style_mode.presentation_mode.dpi == 420
    assert resolved.style_mode.print_mode.dpi == original_print_dpi
    assert (
        configuration.style_mode.presentation_mode.dpi
        == original_presentation_dpi
    )
    assert MODULE._configuration_with_dpi(configuration, None) is configuration


def test_zodiac_presentation_enhances_ecliptic_and_grid_labels():
    assert MODULE.ECLIPTIC_LINEWIDTH == pytest.approx(1.5)
    assert MODULE.EQUATORIAL_REFERENCE_LINEWIDTH == pytest.approx(1.0)
    assert MODULE.GRID_LABEL_FONTSIZE == pytest.approx(7.5)
    source = PATH.read_text(encoding="utf-8")
    assert 'ecliptic_keypoints="labeled"' in source
    assert "ecliptic_keypoint_legend=True" in source
    assert "stellar_reference_range=REFERENCE_MAGNITUDE_RANGE" in source
    assert 'stellar_background="sky"' in source
    assert "legend_plan=ZODIAC_LEGEND_PLAN" in source
    assert "coordinate_label_zorder" not in source
    assert "equatorial_reference_linewidth" in source


def test_keypoints_do_not_modify_constellation_framing():
    source = PATH.read_text(encoding="utf-8")

    assert "KEYPOINT_FIELD_SCALE" not in source
    assert "field_scale" not in source


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
    assert MODULE._title(view, "Oph") == (
        "Ofiuco — RA 02:00, Dec -10:00"
    )
