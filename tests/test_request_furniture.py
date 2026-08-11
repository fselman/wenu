"""Late declarative furniture-context contracts."""

from types import SimpleNamespace

from wenu import (
    ChartContextOptions,
    ChartFurnitureOptions,
    LegendOptions,
)
from wenu.charts.request_furniture import resolve_request_furniture_context


def test_context_metadata_is_realized_after_chart_and_sky_exist(monkeypatch):
    chart = object()
    sky = SimpleNamespace(observer=object())
    calls = []
    monkeypatch.setattr(
        "wenu.charts.request_furniture.chart_context_lines",
        lambda actual_chart, actual_sky, **options: (
            calls.append((actual_chart, actual_sky, options))
            or ("RA", "Dec")
        ),
    )
    monkeypatch.setattr(
        "wenu.charts.request_furniture.observer_context_lines",
        lambda observer, **options: (
            calls.append((observer, options)) or ("La Ligua", "2026-08-15")
        ),
    )
    furniture = ChartFurnitureOptions(
        legends=LegendOptions(
            objects=False,
            stellar_magnitudes=True,
            context=True,
            context_lines=("Custom",),
        ),
        context=ChartContextOptions(
            center=True,
            grid=False,
            location=True,
            date=True,
            local_time=False,
            labels=False,
        ),
    )

    resolved = resolve_request_furniture_context(furniture, chart, sky)

    assert resolved is not furniture
    assert resolved.context is None
    assert resolved.legends.objects is False
    assert resolved.legends.stellar_magnitudes is True
    assert resolved.legends.context is False
    assert resolved.legends.context_lines == (
        "RA", "Dec", "La Ligua", "2026-08-15", "Custom"
    )
    assert calls == [
        (chart, sky, {"center": True, "grid": False}),
        (sky.observer, {
            "location": True,
            "date": True,
            "local_time": False,
            "labels": False,
        }),
    ]


def test_absent_context_options_preserve_furniture_identity():
    furniture = ChartFurnitureOptions(legends=LegendOptions(context=False))

    assert resolve_request_furniture_context(
        furniture, object(), object()
    ) is furniture
