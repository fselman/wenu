"""Canonical chart construction from resolved declarative requests."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from wenu import (
    CANONICAL_MAXIMAL_SPHERE_PROFILE,
    BinocularChart,
    ChartFrameRequest,
    ChartObserverRequest,
    ChartProductOptions,
    ChartRequest,
    ChartSubjectRequest,
    CircumpolarChart,
    FullSkyChart,
    PreparedChartRequest,
    RegionalChart,
    prepare_chart_request,
    resolve_chart_request,
)


def request(family, *, subject=None, frame=None, mask=False):
    return ChartRequest(
        observer=ChartObserverRequest(
            location="La Ligua", time="2026-08-15 22:00"
        ),
        family=family,
        subject=subject or ChartSubjectRequest(),
        frame=frame or ChartFrameRequest(),
        mask=mask,
        product=ChartProductOptions(output=Path("output/chart.png")),
    )


def sky():
    return SimpleNamespace(
        observer=object(),
        nonstellar=None,
        galaxies=None,
        open_clusters=None,
        globular_clusters=None,
        planetary_nebulae=None,
        supernova_remnants=None,
    )


def resolve(value):
    return resolve_chart_request(
        value, CANONICAL_MAXIMAL_SPHERE_PROFILE
    )


def test_planisphere_construction_owns_requested_mask():
    prepared = prepare_chart_request(
        sky(),
        resolve(request(
            "planisphere",
            subject=ChartSubjectRequest(constellations=("Cru", "Cen")),
            mask=True,
        )),
    )

    assert isinstance(prepared, PreparedChartRequest)
    assert isinstance(prepared.chart, FullSkyChart)
    assert prepared.chart.outside_mask_constellations == ("Cru", "Cen")


def test_regional_construction_uses_resolved_group_field(monkeypatch):
    calls = {}

    def build(cls, source, constellations, **kwargs):
        calls.update(kwargs)
        calls["constellations"] = constellations
        return SimpleNamespace(projection=object(), viewport=object())

    monkeypatch.setattr(RegionalChart, "from_constellations", classmethod(build))
    prepared = prepare_chart_request(
        sky(),
        resolve(request(
            "regional",
            subject=ChartSubjectRequest(group="galactic-center"),
            mask=True,
        )),
    )

    assert prepared.chart is not None
    assert calls["constellations"][-2:] == ("Ser1", "Ser2")
    assert calls["angular_radius_deg"] == pytest.approx(45.0)
    assert calls["aspect_ratio"] == pytest.approx(1.0)
    assert calls["north_up"] is True
    assert calls["outside_mask_constellations"] == (
        "Sgr", "Sco", "Oph", "Ser"
    )


def test_binocular_construction_uses_resolved_target_and_field(monkeypatch):
    calls = {}

    def build(cls, observer, coordinate, **kwargs):
        calls.update(kwargs)
        calls["coordinate"] = coordinate
        return SimpleNamespace(projection=object(), viewport=object())

    monkeypatch.setattr(BinocularChart, "from_coordinate", classmethod(build))
    prepare_chart_request(
        sky(),
        resolve(request(
            "binocular", subject=ChartSubjectRequest(target="M57")
        )),
    )

    assert calls["field_diameter_deg"] == pytest.approx(6.5)
    assert calls["north_up"] is True
    assert calls["coordinate"].icrs.ra.deg == pytest.approx(283.39892816)
    assert calls["coordinate"].icrs.dec.deg == pytest.approx(33.02786646)


def test_circumpolar_construction_uses_declination_boundary():
    prepared = prepare_chart_request(
        sky(),
        resolve(request(
            "circumpolar",
            frame=ChartFrameRequest(
                pole="south", limiting_declination_deg=-69.75
            ),
        )),
    )

    assert isinstance(prepared.chart, CircumpolarChart)
    assert prepared.chart.limiting_declination_deg == pytest.approx(-69.75)


def test_preparation_rejects_unresolved_or_observerless_inputs():
    resolved = resolve(request(
        "binocular", subject=ChartSubjectRequest(target="M57")
    ))
    with pytest.raises(TypeError, match="ResolvedChartRequest"):
        prepare_chart_request(sky(), object())
    with pytest.raises(TypeError, match="scientific observer"):
        prepare_chart_request(SimpleNamespace(), resolved)
