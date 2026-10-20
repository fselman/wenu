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


def test_target_title_consumes_kernel_lookup_and_refuses_after_success(monkeypatch):
    from dataclasses import replace
    import pytest
    from wenu import ChartSubjectRequest, resolve_target
    from wenu.catalogue_state import _unit_direction
    from wenu.charts.request_furniture import binocular_product_title
    from wenu_kernel import KernelSession
    target = resolve_target(ChartSubjectRequest(target="M57"))
    evaluate = KernelSession.evaluate
    def shifted(session, query):
        batch = evaluate(session, query)
        return replace(batch, states=tuple(replace(state, vector=_unit_direction(30., -10.)) for state in batch.states))
    monkeypatch.setattr(KernelSession, "evaluate", shifted)
    title = binocular_product_title(target, 6.5)
    assert "RA 2h00m00s" in title
    assert "Dec -10°00′00″" in title
    def refuse(*args, **kwargs):
        raise RuntimeError("synthetic title refusal")
    monkeypatch.setattr(KernelSession, "evaluate", refuse)
    with pytest.raises(RuntimeError, match="title refusal"):
        binocular_product_title(target, 6.5)


def test_context_furniture_consumes_coordinate_service_and_propagates_refusal(monkeypatch):
    import pytest
    from wenu.geometry.spherical import SphericalPoints
    from wenu.coordinates import GENERIC_SPHERICAL_SPEC
    from wenu.charts import legend_metadata
    observing = object()
    source = SimpleNamespace(observer=observing, layers=())
    chart = SimpleNamespace(center_alt_deg=45., center_az_deg=120.)
    calls = []
    def transform(self, geometry, spec, observation):
        calls.append(geometry)
        return SphericalPoints([30.], [-10.], coordinate_spec=GENERIC_SPHERICAL_SPEC)
    monkeypatch.setattr(legend_metadata.CoordinateService, "transform", transform)
    monkeypatch.setattr(legend_metadata, "observer_altaz_spec", lambda *a, **k: GENERIC_SPHERICAL_SPEC)
    monkeypatch.setattr(legend_metadata, "observation_context", lambda observer: observer)
    # Observer/date text has no astronomical state lookup and is independent.
    monkeypatch.setattr("wenu.charts.request_furniture.observer_context_lines", lambda *a, **k: ())
    furniture = ChartFurnitureOptions(context=ChartContextOptions(center=True, grid=False))
    result = resolve_request_furniture_context(furniture, chart, source)
    assert result.legends.context_lines == ("RA 2h00m00s", "Dec -10°00′00″")
    assert calls[0].lon_deg[0] == 120.
    assert calls[0].lat_deg[0] == 45.
    def refuse(*a, **k):
        raise RuntimeError("synthetic context refusal")
    monkeypatch.setattr(legend_metadata.CoordinateService, "transform", refuse)
    with pytest.raises(RuntimeError, match="context refusal"):
        resolve_request_furniture_context(furniture, chart, source)
