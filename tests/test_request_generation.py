"""End-to-end ownership contracts for declarative chart generation."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from wenu import (
    ChartContextOptions,
    ChartFurnitureOptions,
    ChartObserverRequest,
    ChartProduct,
    ChartProductCompositionOptions,
    ChartProductOptions,
    ChartRequest,
    ChartSubjectRequest,
    ChartStyleOverrides,
    FixedDetailPolicy,
    ResolvedDetail,
)
from wenu.charts.export_workflow import ChartExportResult
from wenu.charts.request_chart import PreparedChartRequest
from wenu.charts.request_generation import (
    ChartRequestBuild,
    ChartRequestGeneration,
    build_chart_request,
    export_prepared_chart,
    generate_chart_request,
)
from wenu.charts.request_resolver import resolve_chart_request
from wenu.sky.maximal_sphere import CANONICAL_MAXIMAL_SPHERE_PROFILE


def _request(tmp_path, *, all_products=False, product_compositions=()):
    return ChartRequest(
        family="binocular",
        observer=ChartObserverRequest(
            lat_deg=-33.0,
            lon_deg=-71.0,
            time="2026-08-10T03:00:00Z",
        ),
        subject=ChartSubjectRequest(target="centaurus-a"),
        product=ChartProductOptions(
            all_products=all_products,
            output=tmp_path,
        ),
        product_compositions=product_compositions,
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

    def composition(
        chart, *, style, mode, detail, detail_overrides,
        style_overrides, furniture,
    ):
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
            detail_policy=detail,
            style_overrides=style_overrides,
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


def test_prepared_request_applies_exact_product_composition_options(
    monkeypatch, tmp_path
):
    atlas_detail = FixedDetailPolicy(
        ResolvedDetail(star_magnitude_limit=11.0)
    )
    cartoon_detail = FixedDetailPolicy(ResolvedDetail(
        star_magnitude_limit=11.0,
        enabled_layers={"stars", "constellation_lines", "galaxies"},
        constellation_star_mode="selected",
    ))
    atlas_style = ChartStyleOverrides(boundary_linewidth=0.5)
    cartoon_style = ChartStyleOverrides(boundary_linewidth=1.0)
    request = _request(
        tmp_path,
        all_products=True,
        product_compositions=(
            ChartProductCompositionOptions(
                product=ChartProduct("atlas", "print"),
                detail=atlas_detail,
                style_overrides=atlas_style,
            ),
            ChartProductCompositionOptions(
                product=ChartProduct("cartoon", "presentation"),
                detail=cartoon_detail,
                style_overrides=cartoon_style,
            ),
        ),
    )
    resolved = resolve_chart_request(
        request, CANONICAL_MAXIMAL_SPHERE_PROFILE
    )
    calls = []

    class Chart:
        chart_context = object()

        def export(self, sky, renderer, output, *, composition):
            return ChartExportResult(
                rendering=None,
                output=output,
                composition=composition,
                layer_options={},
                export_options=None,
            )

    def composition(chart, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(
            mode=SimpleNamespace(width_inches=8.0, height_inches=6.0),
            style=SimpleNamespace(configure_axes=lambda ax, title: None),
        )

    monkeypatch.setattr(
        "wenu.charts.request_generation.compose_chart", composition
    )
    monkeypatch.setattr(
        "matplotlib.pyplot.subplots",
        lambda **kwargs: (object(), object()),
    )
    monkeypatch.setattr("matplotlib.pyplot.close", lambda figure: None)

    export_prepared_chart(
        SimpleNamespace(observer=object()),
        PreparedChartRequest(chart=Chart(), resolved=resolved),
    )

    assert [call["detail"] for call in calls] == [
        atlas_detail, None, None, cartoon_detail
    ]
    assert [call["style_overrides"] for call in calls] == [
        atlas_style, None, None, cartoon_style
    ]


def test_prepared_request_resolves_generic_context_after_chart_construction(
    monkeypatch, tmp_path
):
    request = _request(tmp_path)
    request = replace(
        request,
        furniture=ChartFurnitureOptions(
            context=ChartContextOptions(
                center=True,
                grid=False,
                location=False,
                date=False,
                local_time=False,
            )
        ),
    )
    resolved = resolve_chart_request(
        request, CANONICAL_MAXIMAL_SPHERE_PROFILE
    )
    resolved_furniture = ChartFurnitureOptions()
    captured = []

    class Chart:
        chart_context = object()

        def export(self, sky, renderer, output, *, composition):
            return ChartExportResult(
                rendering=None, output=output, composition=composition,
                layer_options={}, export_options=None,
            )

    monkeypatch.setattr(
        "wenu.charts.request_generation.resolve_request_furniture_context",
        lambda furniture, chart, sky: resolved_furniture,
    )
    monkeypatch.setattr(
        "wenu.charts.request_generation.compose_chart",
        lambda chart, **kwargs: captured.append(kwargs) or SimpleNamespace(
            mode=SimpleNamespace(width_inches=8.0, height_inches=6.0),
            style=SimpleNamespace(configure_axes=lambda ax, title: None),
        ),
    )
    monkeypatch.setattr(
        "matplotlib.pyplot.subplots",
        lambda **kwargs: (object(), object()),
    )
    monkeypatch.setattr("matplotlib.pyplot.close", lambda figure: None)

    export_prepared_chart(
        SimpleNamespace(observer=object()),
        PreparedChartRequest(chart=Chart(), resolved=resolved),
    )

    assert captured[0]["furniture"] is resolved_furniture


def test_generation_owns_and_closes_its_observer(monkeypatch, tmp_path):
    request = _request(tmp_path)
    events = []
    observer = SimpleNamespace(close=lambda: events.append("close"))
    sky = SimpleNamespace(observer=observer)
    resolved = SimpleNamespace(request=request)
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
        "wenu.charts.request_generation.configure_chart_request_grids",
        lambda actual, value, *, frame: events.append("grids"),
    )
    monkeypatch.setattr(
        "wenu.charts.request_generation.configure_chart_request_horizon",
        lambda actual, value: events.append("horizon"),
    )
    monkeypatch.setattr(
        "wenu.charts.request_generation.export_prepared_chart",
        lambda actual, value: events.append("export") or generation,
    )

    assert generate_chart_request(request) is generation
    assert events == [
        "build", "resolve", "grids", "horizon", "prepare", "export",
        "close",
    ]


def test_build_result_exposes_prepared_chart_and_closes_owned_observer_once():
    closed = []
    chart = object()
    sky = SimpleNamespace(
        observer=SimpleNamespace(close=lambda: closed.append(True))
    )
    build = ChartRequestBuild(
        sky=sky,
        prepared=SimpleNamespace(chart=chart),
        owns_observer=True,
    )

    assert build.chart is chart
    build.close()
    build.close()
    assert closed == [True]


def test_build_result_never_closes_a_supplied_sphere():
    closed = []
    build = ChartRequestBuild(
        sky=SimpleNamespace(
            observer=SimpleNamespace(close=lambda: closed.append(True))
        ),
        prepared=SimpleNamespace(chart=object()),
        owns_observer=False,
    )

    with build:
        pass
    assert closed == []


def test_public_build_boundary_prepares_without_exporting(
    monkeypatch, tmp_path
):
    request = _request(tmp_path)
    observer = SimpleNamespace(close=lambda: None)
    sky = SimpleNamespace(observer=observer)
    resolved = SimpleNamespace(request=request)
    prepared = SimpleNamespace(chart=object())
    events = []
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
        "wenu.charts.request_generation.configure_chart_request_grids",
        lambda actual, value, *, frame: events.append("grids"),
    )
    monkeypatch.setattr(
        "wenu.charts.request_generation.configure_chart_request_horizon",
        lambda actual, value: events.append("horizon"),
    )
    monkeypatch.setattr(
        "wenu.charts.request_generation.prepare_chart_request",
        lambda actual, value: events.append("prepare") or prepared,
    )
    monkeypatch.setattr(
        "wenu.charts.request_generation.export_prepared_chart",
        lambda *args: pytest.fail("build must not export"),
    )

    build = build_chart_request(request)

    assert build.sky is sky
    assert build.prepared is prepared
    assert build.owns_observer is True
    assert events == ["build", "resolve", "grids", "horizon", "prepare"]
    build.close()


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


def test_generation_reuses_a_compatible_supplied_sphere(
    monkeypatch, tmp_path
):
    request = _request(tmp_path)
    observer = SimpleNamespace(
        lat_deg=-33.0,
        lon_deg=-71.0,
        elevation_m=0.0,
        utc_datetime=request.observer.scientific_identity()[-1],
    )
    sky = SimpleNamespace(
        observer=observer,
        load_profile=CANONICAL_MAXIMAL_SPHERE_PROFILE,
    )
    resolved = SimpleNamespace(request=request)
    prepared = object()
    generation = ChartRequestGeneration(exports=())
    events = []

    monkeypatch.setattr(
        "wenu.charts.request_generation.build_maximal_sphere",
        lambda *args, **kwargs: pytest.fail("must reuse supplied sphere"),
    )
    monkeypatch.setattr(
        "wenu.charts.request_generation.resolve_chart_request",
        lambda actual, profile: events.append((actual, profile)) or resolved,
    )
    monkeypatch.setattr(
        "wenu.charts.request_generation.prepare_chart_request",
        lambda actual, value: events.append((actual, value)) or prepared,
    )
    monkeypatch.setattr(
        "wenu.charts.request_generation.configure_chart_request_grids",
        lambda actual, value, *, frame: events.append((actual, value)),
    )
    monkeypatch.setattr(
        "wenu.charts.request_generation.configure_chart_request_horizon",
        lambda actual, value: events.append((actual, value)),
    )
    monkeypatch.setattr(
        "wenu.charts.request_generation.export_prepared_chart",
        lambda actual, value: events.append((actual, value)) or generation,
    )

    assert generate_chart_request(request, sky=sky) is generation
    assert events == [
        (request, CANONICAL_MAXIMAL_SPHERE_PROFILE),
        (sky, request),
        (sky, request),
        (sky, resolved),
        (sky, prepared),
    ]


def test_supplied_sphere_must_match_observer_and_profile(tmp_path):
    request = _request(tmp_path)
    observer = SimpleNamespace(
        lat_deg=-34.0,
        lon_deg=-71.0,
        elevation_m=0.0,
        utc_datetime=request.observer.scientific_identity()[-1],
    )
    sky = SimpleNamespace(
        observer=observer,
        load_profile=CANONICAL_MAXIMAL_SPHERE_PROFILE,
    )

    with pytest.raises(ValueError, match="observer does not match"):
        generate_chart_request(request, sky=sky)

    observer.lat_deg = -33.0
    sky.load_profile = None
    with pytest.raises(ValueError, match="does not declare a load profile"):
        generate_chart_request(request, sky=sky)


def test_explicit_profile_must_match_supplied_sphere(tmp_path):
    request = _request(tmp_path)
    observer = SimpleNamespace(
        lat_deg=-33.0,
        lon_deg=-71.0,
        elevation_m=0.0,
        utc_datetime=request.observer.scientific_identity()[-1],
    )
    sky = SimpleNamespace(
        observer=observer,
        load_profile=CANONICAL_MAXIMAL_SPHERE_PROFILE,
    )

    with pytest.raises(ValueError, match="load profile does not match"):
        generate_chart_request(request, sky=sky, profile=object())


def test_generation_entry_points_reject_untyped_inputs():
    with pytest.raises(TypeError, match="ChartRequest"):
        generate_chart_request(object())
    with pytest.raises(TypeError, match="PreparedChartRequest"):
        export_prepared_chart(SimpleNamespace(observer=object()), object())
