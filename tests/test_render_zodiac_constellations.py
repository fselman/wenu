"""Contracts for the twelve-chart zodiac review tool."""

import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).parents[1] / "tools/render_zodiac_constellations.py"
SPEC = importlib.util.spec_from_file_location("render_zodiac", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_traditional_zodiac_order_contains_twelve_separate_constellations():
    assert MODULE.ZODIAC_CONSTELLATIONS == (
        "Ari", "Tau", "Gem", "Cnc", "Leo", "Vir",
        "Lib", "Sco", "Sgr", "Cap", "Aqr", "Psc",
    )
    assert MODULE.STAR_MAGNITUDE_LIMIT == pytest.approx(5.5)


def test_target_up_rotation_is_zero_when_target_is_already_above_center():
    angle = MODULE._target_up_position_angle(
        center_alt_deg=30.0,
        center_az_deg=45.0,
        target_alt_deg=60.0,
        target_az_deg=45.0,
    )
    assert angle == pytest.approx(0.0, abs=1.0e-10)


def test_command_line_defaults_to_twelve_pdf_outputs():
    arguments = MODULE.parser().parse_args([])
    assert arguments.output == Path("output/zodiac-constellations")
    assert arguments.file_format == "pdf"
    assert arguments.framing_padding == pytest.approx(1.25)
    assert arguments.mask is False
    assert arguments.presentation is False


def test_mask_and_presentation_are_explicit_independent_switches():
    arguments = MODULE.parser().parse_args(["--mask", "--presentation"])

    assert arguments.mask is True
    assert arguments.presentation is True
