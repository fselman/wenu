"""Closure contracts for authoritative packaged runtime defaults."""

from dataclasses import replace
from datetime import datetime, timezone
from types import SimpleNamespace

from wenu import (
    CANONICAL_MAXIMAL_SPHERE_PROFILE,
    CelestialSphere,
    draw_chart_view,
    get_chart_view,
)
from wenu.charts.product_options import ChartProduct
from wenu.charts.product_options import ChartProductOptions
from wenu.charts.request import ChartObserverRequest, ChartRequest
from wenu.configuration import packaged_furniture_product_export_defaults


def view():
    observer = SimpleNamespace(
        utc_datetime=datetime(
            2026, 8, 16, 1, 0, tzinfo=timezone.utc
        ),
        lat_deg=-32.4524,
        lon_deg=-71.2317,
        elevation_m=48.0,
        timezone_name="America/Santiago",
    )
    sky = CelestialSphere(None)
    sky.load_profile = CANONICAL_MAXIMAL_SPHERE_PROFILE
    return get_chart_view(sky, observer, family="planisphere")


def export_result(path):
    return SimpleNamespace(output=path)


def _configured_product(**changes):
    defaults = packaged_furniture_product_export_defaults().product
    return replace(defaults, **changes)


def test_ordinary_drawing_uses_packaged_product_metadata(monkeypatch, tmp_path):
    chart_view = view()
    requests = []
    configured = _configured_product(
        product=ChartProduct("cartoon", "presentation"),
        language="es",
        title="Carta configurada",
    )
    monkeypatch.setattr(
        "wenu.charts.drawing._product_defaults",
        lambda: configured,
    )
    monkeypatch.setattr(
        "wenu.charts.drawing.configure_chart_request_grids",
        lambda sky, request, *, frame: requests.append(request),
    )
    monkeypatch.setattr(
        "wenu.charts.drawing.configure_chart_request_horizon",
        lambda *args: None,
    )
    monkeypatch.setattr(
        "wenu.charts.drawing.export_prepared_chart",
        lambda *args, **kwargs: SimpleNamespace(
            exports=(export_result(tmp_path / "chart.png"),)
        ),
    )

    draw_chart_view(chart_view, tmp_path / "chart.png")

    request = requests[0]
    assert request.product.style == "cartoon"
    assert request.product.mode == "presentation"
    assert request.language == "es"
    assert request.title == "Carta configurada"


def test_explicit_drawing_product_metadata_retains_precedence(
    monkeypatch, tmp_path
):
    chart_view = view()
    requests = []
    configured = _configured_product(
        product=ChartProduct("cartoon", "presentation"),
        language="es",
        title="Carta configurada",
    )
    monkeypatch.setattr(
        "wenu.charts.drawing._product_defaults",
        lambda: configured,
    )
    monkeypatch.setattr(
        "wenu.charts.drawing.configure_chart_request_grids",
        lambda sky, request, *, frame: requests.append(request),
    )
    monkeypatch.setattr(
        "wenu.charts.drawing.configure_chart_request_horizon",
        lambda *args: None,
    )
    monkeypatch.setattr(
        "wenu.charts.drawing.export_prepared_chart",
        lambda *args, **kwargs: SimpleNamespace(
            exports=(export_result(tmp_path / "chart.png"),)
        ),
    )

    draw_chart_view(
        chart_view,
        tmp_path / "chart.png",
        style="atlas",
        mode="print",
        language="en",
        title="Explicit",
    )

    request = requests[0]
    assert request.product.style == "atlas"
    assert request.product.mode == "print"
    assert request.language == "en"
    assert request.title == "Explicit"


def test_request_omission_uses_packaged_language_and_title(monkeypatch):
    configured = _configured_product(
        language="es",
        title="Carta configurada",
    )
    monkeypatch.setattr(
        "wenu.charts.request._product_defaults",
        lambda: configured,
    )

    request = ChartRequest(
        observer=ChartObserverRequest(
            time="2026-08-16T01:00:00+00:00",
            lat_deg=-32.4524,
            lon_deg=-71.2317,
        ),
        family="planisphere",
        product=ChartProductOptions("output/chart.png"),
    )

    assert request.language == "es"
    assert request.title == "Carta configurada"


def test_explicit_request_language_and_title_retain_precedence(monkeypatch):
    configured = _configured_product(
        language="es",
        title="Carta configurada",
    )
    monkeypatch.setattr(
        "wenu.charts.request._product_defaults",
        lambda: configured,
    )

    request = ChartRequest(
        observer=ChartObserverRequest(
            time="2026-08-16T01:00:00+00:00",
            lat_deg=-32.4524,
            lon_deg=-71.2317,
        ),
        family="planisphere",
        product=ChartProductOptions("output/chart.png"),
        language="en",
        title="Explicit",
    )

    assert request.language == "en"
    assert request.title == "Explicit"
