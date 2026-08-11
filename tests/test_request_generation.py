"""End-to-end ownership contracts for declarative chart generation."""

from types import SimpleNamespace

import pytest

from wenu import (
    ChartObserverRequest,
    ChartProductOptions,
    ChartRequest,
    ChartSubjectRequest,
)
from wenu.charts.export_workflow import ChartExportResult
from wenu.charts.request_chart import PreparedChartRequest
from wenu.charts.request_generation import (
    ChartRequestGeneration,
    export_prepared_chart,
    generate_chart_request,
)
from wenu.charts.request_resolver import resolve_chart_request
from wenu.sky.maximal_sphere import CANONICAL_MAXIMAL_SPHERE_PROFILE


def _request(tmp_path, *, all_products=False):
    return ChartRequest(
        family="binocular",
        observer=ChartObserverRequest(
            lat_deg=-33.0,
            lon_deg=-71.0,
            time="2026-08-10T03:00:00",
        ),
        subject=ChartSubjectRequest(target="centaurus-a"),
        product=ChartProductOptions(
            all_products=all_products,
            output=tmp_path,
        ),
    )


def test_prepared_request_exports_the_shared_product_matrix_once(
    monkeypatch, tmp_path
):
    request = _request(tmp_path, all_products=True)
    resolved = resolve_chart_request(
        request, CANONICAL_MAXIMAL_SPHERE_PROFILE
    )
    exported = []
    configured_titles = []
    closed = []

    class Chart:
        chart_context = object()

        def export(self, sky, renderer, output, *, composition):
            exported.append((sky, output, composition))
            return ChartExportResult(
                rendering=None,
                output=output,
                composition=composition,
                layer_options={},
                export_options=None,
            )

    def composition(chart, *, style, mode, detail_overrides, furniture):
        assert detail_overrides.content_selection == resolved.request.content
        return SimpleNamespace(
            mode=SimpleNamespace(width_inches=8.0, height_inches=6.0),
            style=SimpleNamespace(
                configure_axes=lambda ax, title: configured_titles.append(
                    title
                )
            ),
            product=(style, mode),
            detail=detail_overrides,
            furniture=furniture,
        )

    monkeypatch.setattr(
        "wenu.charts.request_generation.compose_chart", composition
    )
    monkeypatch.setattr(
        "matplotlib.pyplot.subplots",
        lambda **kwargs: (object(), object()),
    )
    monkeypatch.setattr("matplotlib.pyplot.close", closed.append)

    sky = SimpleNamespace(observer=object())
    prepared = PreparedChartRequest(chart=Chart(), resolved=resolved)
    result = export_prepared_chart(sky, prepared)

    assert isinstance(result, ChartRequestGeneration)
    assert len(exported) == 4
    assert [path.name for path in result.outputs] == [
        "binocular-centaurus-a-atlas-print.png",
        "binocular-centaurus-a-atlas-presentation.png",
        "binocular-centaurus-a-cartoon-print.png",
        "binocular-centaurus-a-cartoon-presentation.png",
    ]
    assert configured_titles == ["Centaurus A"] * 4
    assert len(closed) == 4


def test_generation_owns_and_closes_its_observer(monkeypatch, tmp_path):
    request = _request(tmp_path)
    events = []
    observer = SimpleNamespace(close=lambda: events.append("close"))
    sky = SimpleNamespace(observer=observer)
    resolved = object()
    prepared = object()
    generation = ChartRequestGeneration(exports=())

    monkeypatch.setattr(
        "wenu.charts.request_generation.Observer",
        lambda **kwargs: observer,
    )
    monkeypatch.setattr(
        "wenu.charts.request_generation.build_maximal_sphere",
        lambda actual, profile: events.append("build") or sky,
    )
    monkeypatch.setattr(
        "wenu.charts.request_generation.resolve_chart_request",
        lambda actual, profile: events.append("resolve") or resolved,
    )
    monkeypatch.setattr(
        "wenu.charts.request_generation.prepare_chart_request",
        lambda actual, value: events.append("prepare") or prepared,
    )
    monkeypatch.setattr(
        "wenu.charts.request_generation.export_prepared_chart",
        lambda actual, value: events.append("export") or generation,
    )

    assert generate_chart_request(request) is generation
    assert events == ["build", "resolve", "prepare", "export", "close"]


def test_generation_closes_observer_when_build_fails(monkeypatch, tmp_path):
    request = _request(tmp_path)
    closed = []
    observer = SimpleNamespace(close=lambda: closed.append(True))
    monkeypatch.setattr(
        "wenu.charts.request_generation.Observer",
        lambda **kwargs: observer,
    )

    def fail(observer, profile):
        raise RuntimeError("catalogue failure")

    monkeypatch.setattr(
        "wenu.charts.request_generation.build_maximal_sphere", fail
    )

    with pytest.raises(RuntimeError, match="catalogue failure"):
        generate_chart_request(request)
    assert closed == [True]


def test_generation_entry_points_reject_untyped_inputs():
    with pytest.raises(TypeError, match="ChartRequest"):
        generate_chart_request(object())
    with pytest.raises(TypeError, match="PreparedChartRequest"):
        export_prepared_chart(SimpleNamespace(observer=object()), object())
