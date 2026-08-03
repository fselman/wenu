"""Regression tests for NonStellar dot symbols and Sagittarius."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from wenu.charts.styles import PublicationStyle

class _FakeNonStellar:
    samples = 73

def _fake_sky():
    layer = _FakeNonStellar()
    return SimpleNamespace(
        stars=None,
        nonstellar=layer,
        constellation_lines=None,
        constellation_labels=None,
        constellation_boundaries=None,
        points=None,
        layers=(layer,),
    )


def test_nonstellar_uses_explicit_dots():
    style = PublicationStyle()
    sky = _fake_sky()
    rendered = style.layer_options(sky)[sky.nonstellar]["render"]
    symbol = rendered["style"]
    assert symbol["linestyle"] == "None"
    assert symbol["marker"] == "."
    count = len(range(0, sky.nonstellar.samples, symbol["markevery"]))
    assert count >= 8


def test_nonstellar_dot_count_cannot_be_less_than_eight():
    style = PublicationStyle(nonstellar_symbol_dots=7)
    with pytest.raises(ValueError, match="at least 8"):
        style.layer_options(_fake_sky())


def test_sagittarius_example_uses_iau_abbreviation():
    source = Path("tests/fixtures/example_regressions/sag_sco_oph_ser_mask.py").read_text()
    assert '"Sgr"' in source
    assert '"Sag"' not in source
