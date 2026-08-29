"""Regression tests for the physical polar-planisphere preview tool."""

from __future__ import annotations

import numpy as np

from tools import render_48e2_polar_preview as tool
from wenu import Observer, PolarPlanispherePairRequest


def test_polar_preview_resolves_equatorial_and_ecliptic_anchors():
    observer = Observer(location="La Ligua", time="2026-08-15 21:00")
    chart = PolarPlanispherePairRequest(
        projection_name="stereographic",
        calendar_radius_mm=78.0,
    ).resolve().south
    try:
        equatorial = tool._projected_anchor(
            chart,
            observer,
            frame="equatorial",
            angle_deg=0.0,
        )
        ecliptic = tool._projected_anchor(
            chart,
            observer,
            frame="ecliptic",
            angle_deg=0.0,
        )
    finally:
        observer.close()

    assert np.isfinite(equatorial).all()
    assert np.isfinite(ecliptic).all()
