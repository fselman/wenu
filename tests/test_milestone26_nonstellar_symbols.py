"""Tests for visible NonStellar symbols and label options."""

import astropy.units as u
import numpy as np
import pytest
from astropy.coordinates import SkyCoord

from wenu.charts.styles import PublicationStyle
from wenu.objects.nonstellar import NonStellar


def test_minimum_symbol_size_preserves_axis_ratio():
    center = SkyCoord(ra=10.0 * u.deg, dec=20.0 * u.deg)
    outline = NonStellar._ellipse(
        center,
        8.0,
        4.0,
        35.0,
        144,
        minimum_size_arcmin=30.0,
    )
    separation = center.separation(outline).to_value(u.arcmin)
    assert np.min(separation) == pytest.approx(15.0, rel=2.0e-3)
    assert np.max(separation) == pytest.approx(30.0, rel=2.0e-3)


def test_true_angular_size_remains_available():
    center = SkyCoord(ra=10.0 * u.deg, dec=20.0 * u.deg)
    outline = NonStellar._ellipse(
        center,
        8.0,
        4.0,
        35.0,
        144,
        minimum_size_arcmin=None,
    )
    separation = center.separation(outline).to_value(u.arcmin)
    assert np.min(separation) == pytest.approx(2.0, rel=2.0e-3)
    assert np.max(separation) == pytest.approx(4.0, rel=2.0e-3)


def test_nonstellar_labels_are_optional_and_small_by_default():
    style = PublicationStyle()
    assert style.nonstellar_draw_labels is False
    assert style.nonstellar_label_fontsize < style.label_fontsize
    assert style.nonstellar_minimum_size_arcmin > 0.0
