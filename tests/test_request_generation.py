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
    ChartStyleOverrides,
    ChartSubjectRequest,
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
    _prepare_with_sphere,
    _RequestSkyState,
)
from wenu.charts.request_resolver import resolve_chart_request
from wenu.sky.maximal_sphere import CANONICAL_MAXIMAL_SPHERE_PROFILE


@pytest.fixture(autouse=True)
def _request_realization_context(monkeypatch):
    context = SimpleNamespace(name="request-realization-context")
    monkeypatch.setattr(
        "wenu.charts.request_generation.chart_request_realization_context",
        lambda request, observer: context,
    )
    return context


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


@pytest.mark.parametrize("family", ["regional", "binocular", "all_sky"])
def test_stellar_report_uses_final_clip_boundary_and_retains_sources(tmp_path, family):
    import json
    import numpy as np
    from wenu import RegionalChart, BinocularChart, AllSkyChart
    from wenu.geometry.projected import ProjectedPoints
    from wenu.star_designations import load_star_designations
    from wenu.charts.stellar_report import write_stellar_report
    from wenu.charts.chart_legend_workflow import RenderedChartWithLegends

    chart = {
        "regional": RegionalChart(35, 210, 20, 15),
        "binocular": BinocularChart(35, 210, 6.5),
        "all_sky": AllSkyChart(),
    }[family]
    context = chart.chart_context
    layer = type("StarLayer", (), {"layer_name": "stars"})()
    # Alpheratz is at the centre; Elnath is outside the viewport; an unknown
    # HIP and a nonfinite point must not acquire research notes.
    points = ProjectedPoints(
        x=[0, context.viewport.width * 2, 0, float("nan"), context.viewport.width * (2 if family == "regional" else .49)],
        y=[0, 0, 0, 0, context.viewport.height * .49], ids=[677, 25428, 1, 95947, 12832],
        metadata={"star_designations": np.array([
            load_star_designations().get(hip) for hip in (677, 25428, 1, 95947, 12832)
        ], dtype=object)},
    )
    export = ChartExportResult(
        rendering=RenderedChartWithLegends(
            rendering=SimpleNamespace(layers=(SimpleNamespace(layer=layer, projected=points, spherical=points),)),
            legends=SimpleNamespace(artists=()),
        ),
        output=tmp_path / (family + ".png"), composition=SimpleNamespace(context=context),
        layer_options={layer: {"render": {"draw_labels": False}}}, export_options=None,
    )
    md, structured = write_stellar_report(export, title="Synthetic retained-point fixture", constellations=("Peg",))
    report = json.loads(structured.read_text())
    assert [entry["hip"] for entry in report["objects"]] == [677]
    entry = report["objects"][0]
    assert entry["assignment"] == "δ Peg" and entry["displayed_label"] is None
    assert entry["research"]["source_values"]["Wikidata"] == ["α And", "δ Peg"]
    assert "Open question:" in md.read_text() and "e-rara" in md.read_text()
    before = structured.read_bytes()
    write_stellar_report(export, title="Synthetic retained-point fixture", constellations=("Peg",))
    assert structured.read_bytes() == before
    assert entry["assignment_basis"].startswith("Requested constellation")
    projected_layer = export.rendering.rendering.layers[0]
    for hip in (95947, 78820, 102431, 1):
        projected_layer.projected = ProjectedPoints(
            x=[0], y=[0], ids=[hip],
            metadata={"star_designations": np.array([load_star_designations().get(hip)], dtype=object)},
        )
        write_stellar_report(export, title="Missing/zero case", constellations=())
        report = json.loads(structured.read_text())
        if hip == 95947:
            entry = report["objects"][0]
            assert entry["assignment"] == "β¹ Cyg"
            assert entry["source_assignments"]["bayer"] == []
            assert entry["effective_assignments"]["bayer"] == ["β¹ Cyg"]
            assert entry["assignment_basis"].startswith("Wenu curated HIP")
            assert entry["curation"]["associations"]
        elif hip == 78820:
            entry = report["objects"][0]
            assert entry["assignment"] == "β¹ Sco"
            assert entry["research"] is None
            assert entry["curation"]["coverage_gaps"]
            assert "authored associations, not Wikidata claims" in md.read_text()
        elif hip == 102431:
            entry = report["objects"][0]
            assert entry["assignment"] is None
            assert entry["curation"]["coverage_gaps"][0]["status"] == "pending"
            assert "bayer: pending" in md.read_text()
        else:
            assert report["objects"] == []
            assert "No stars from the 77-case" in md.read_text()


@pytest.mark.parametrize("mask", [None, ("Peg",), ("And", "Peg")])
def test_prepared_request_exports_the_shared_product_matrix_once(
    monkeypatch, tmp_path, _request_realization_context, mask
):
    request = replace(_request(tmp_path, all_products=True), constellation_mask=mask)
    resolved = resolve_chart_request(
        request, CANONICAL_MAXIMAL_SPHERE_PROFILE
    )
    exported = []
    configured_titles = []
    closed = []

    class Chart:
        chart_context = object()

        def export(
            self, sky, renderer, output, *, composition, horizon_mask,
            svg_provenance, realization_context,
        ):
            assert horizon_mask is False
            assert realization_context is _request_realization_context
            assert svg_provenance.product_name == "binocular"
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
        style_overrides, furniture, reference_policy,
    ):
        assert detail_overrides.content_selection == resolved.request.content
        assert detail_overrides.stellar_label_constellations == tuple(sorted(mask or ()))
        assert reference_policy is resolved.request.reference_policy
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
    assert len(configured_titles) == 4
    assert all(
        title.startswith("Centaurus A — center RA 13h25m28s")
        and "Dec -43°01′09″" in title
        and title.endswith("6.5° binocular field")
        for title in configured_titles
    )
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

        def export(
            self, sky, renderer, output, *, composition, horizon_mask,
            svg_provenance, realization_context,
        ):
            assert horizon_mask is False
            assert svg_provenance.product_name == "binocular"
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

        def export(
            self, sky, renderer, output, *, composition, horizon_mask,
            svg_provenance, realization_context,
        ):
            assert horizon_mask is False
            assert svg_provenance.product_name == "binocular"
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
        lambda actual, value, *, state=None: events.append("horizon"),
    )
    monkeypatch.setattr(
        "wenu.charts.request_generation.configure_chart_request_disks",
        lambda actual, value, *, state=None: events.append("disks"),
    )
    monkeypatch.setattr(
        "wenu.charts.request_tracks.configure_chart_request_track",
        lambda actual, value, *, source_resolver, state=None: events.append("track"),
    )
    monkeypatch.setattr(
        "wenu.charts.request_generation.export_prepared_chart",
        lambda actual, value: events.append("export") or generation,
    )

    assert generate_chart_request(request) is generation
    assert events == [
        "build", "resolve", "grids", "horizon", "disks", "track", "prepare", "export",
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
        lambda actual, value, *, state=None: events.append("horizon"),
    )
    monkeypatch.setattr(
        "wenu.charts.request_generation.configure_chart_request_disks",
        lambda actual, value, *, state=None: events.append("disks"),
    )
    monkeypatch.setattr(
        "wenu.charts.request_tracks.configure_chart_request_track",
        lambda actual, value, *, source_resolver, state=None: events.append("track"),
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
    assert events == [
        "build", "resolve", "grids", "horizon", "disks", "track", "prepare",
    ]
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
        lambda actual, value, *, state=None: events.append((actual, value)),
    )
    monkeypatch.setattr(
        "wenu.charts.request_generation.configure_chart_request_disks",
        lambda actual, value, *, state=None: events.append((actual, value)),
    )
    monkeypatch.setattr(
        "wenu.charts.request_tracks.configure_chart_request_track",
        lambda actual, value, *, source_resolver, state=None: events.append((actual, value)),
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
        (sky, request),
        (sky, request),
        (sky, resolved),
        (sky, prepared),
    ]


def test_generation_reuses_an_observer_independent_sphere_explicitly(
    monkeypatch,
    tmp_path,
):
    request = _request(tmp_path)
    observer = SimpleNamespace(
        lat_deg=-33.0,
        lon_deg=-71.0,
        elevation_m=0.0,
        utc_datetime=request.observer.scientific_identity()[-1],
    )
    sky = SimpleNamespace(
        observer=None,
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
        lambda actual, profile: resolved,
    )
    monkeypatch.setattr(
        "wenu.charts.request_generation.configure_chart_request_grids",
        lambda actual, value, *, frame, observer: events.append(
            ("grids", observer)
        ),
    )
    monkeypatch.setattr(
        "wenu.charts.request_generation.configure_chart_request_horizon",
        lambda actual, value, *, state=None: None,
    )
    monkeypatch.setattr(
        "wenu.charts.request_generation.configure_chart_request_disks",
        lambda actual, value, *, state=None: None,
    )
    monkeypatch.setattr(
        "wenu.charts.request_tracks.configure_chart_request_track",
        lambda actual, value, *, source_resolver, state=None: None,
    )
    monkeypatch.setattr(
        "wenu.charts.request_generation.prepare_chart_request",
        lambda actual, value, *, observer: events.append(
            ("prepare", observer)
        ) or prepared,
    )
    monkeypatch.setattr(
        "wenu.charts.request_generation.export_prepared_chart",
        lambda actual, value, *, observer: events.append(
            ("export", observer)
        ) or generation,
    )

    result = generate_chart_request(
        request,
        sky=sky,
        observer=observer,
    )

    assert result is generation
    assert events == [
        ("grids", observer),
        ("prepare", observer),
        ("export", observer),
    ]
    assert sky.observer is None


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

    with pytest.raises(ValueError, match="observer-independent sky"):
        generate_chart_request(request, sky=sky, observer=observer)

    sky.observer = None
    with pytest.raises(TypeError, match="requires an explicit observer"):
        generate_chart_request(request, sky=sky)

    with pytest.raises(ValueError, match="only with a reusable sky"):
        generate_chart_request(request, observer=observer)

    sky.observer = observer
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



def test_build_close_removes_only_request_owned_satellite_layers():
    removed = []
    retained = object()
    path = object()
    events = object()
    sky = SimpleNamespace(
        observer=SimpleNamespace(close=lambda: None),
        layers=[retained, path, events],
        remove=lambda layer: (
            removed.append(layer),
            sky.layers.remove(layer),
        )[-1],
    )
    build = ChartRequestBuild(
        sky=sky,
        prepared=SimpleNamespace(chart=object()),
        request_satellite_track_layers=(path, events),
    )

    build.close()
    build.close()

    assert removed == [path, events]
    assert sky.layers == [retained]


def test_prepare_failure_removes_installed_satellite_layers(
    monkeypatch, tmp_path
):
    request = _request(tmp_path)
    layer = object()
    removed = []
    sky = SimpleNamespace(
        observer=object(),
        layers=[layer],
        solar_system_bodies={},
        remove=lambda value: removed.append(value),
    )
    resolved = SimpleNamespace(request=request, frame=None)

    monkeypatch.setattr(
        "wenu.charts.request_generation.resolve_chart_request",
        lambda actual, profile: resolved,
    )
    monkeypatch.setattr(
        "wenu.charts.request_generation.configure_chart_request_grids",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "wenu.charts.request_generation.configure_chart_request_horizon",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "wenu.charts.request_generation.configure_chart_request_disks",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "wenu.charts.request_tracks.configure_chart_request_track",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "wenu.charts.request_satellite_tracks."
        "configure_chart_request_satellite_tracks",
        lambda actual, value: (layer,),
    )
    monkeypatch.setattr(
        "wenu.charts.request_generation.prepare_chart_request",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            RuntimeError("synthetic preparation failure")
        ),
    )

    with pytest.raises(RuntimeError, match="synthetic preparation failure"):
        _prepare_with_sphere(
            request,
            sky,
            CANONICAL_MAXIMAL_SPHERE_PROFILE,
            owns_observer=False,
        )

    assert removed == [layer]


def _minor_body_request_fixture(monkeypatch, *, failure_stage=None, close_error=False):
    """Constructed lifecycle fixture; no catalogue, propagation or rendering."""
    error = RuntimeError("synthetic setup failure: " + str(failure_stage))
    cleanup_error = RuntimeError("synthetic session close failure")
    old_resolver = object()
    observer_closes = []
    sessions = []

    class GuardedPoint:
        def __init__(self):
            self._resolver = old_resolver

        @property
        def source_resolver(self):
            return self._resolver

        @source_resolver.setter
        def source_resolver(self, value):
            if failure_stage == "bind" and getattr(value, "__self__", None) in sessions:
                raise error
            self._resolver = value

    retained = SimpleNamespace(source_resolver=old_resolver)
    moon = GuardedPoint()
    descriptors = tuple(SimpleNamespace(selection_key=key, entity_key=alias)
                        for key, alias in (("request-a", "first_alias"), ("request-b", "second_alias")))

    class Sky:
        def __init__(self):
            self.observer = SimpleNamespace(close=lambda: observer_closes.append(True))
            self.layers = [retained, moon]
            self.solar_system_bodies = {"retained": retained}
            self.moon = moon
            self.first_alias = object()

        def add_solar_system_body(self, descriptor):
            layer = SimpleNamespace(descriptor=descriptor, source_resolver=None)
            self.solar_system_bodies[descriptor.selection_key] = layer
            setattr(self, descriptor.entity_key, layer)
            if failure_stage == "add" and descriptor is descriptors[-1]:
                # Match CelestialSphere's publication before its add() call.
                raise error
            self.layers.append(layer)
            return layer

        def remove(self, layer):
            self.layers.remove(layer)

    class Session:
        def __init__(self, directory, observer):
            if failure_stage == "session":
                raise error
            self.closes = 0
            sessions.append(self)

        def source_binding(self, *args):
            raise AssertionError("lifecycle tests must not evaluate ephemerides")

        def close(self):
            self.closes += 1
            if close_error:
                raise cleanup_error

    sky = Sky()
    before = (tuple(sky.layers), dict(sky.solar_system_bodies), sky.first_alias)
    request = SimpleNamespace(minor_body_descriptors=descriptors,
                              minor_body_resource_directory="synthetic-offline")
    prepared = SimpleNamespace(chart=object())
    resolved = SimpleNamespace(request=request, frame=None)

    def stage(name, result=None):
        def operation(*args, **kwargs):
            if failure_stage == name:
                raise error
            return result
        return operation

    monkeypatch.setattr("wenu.minor_body_resources.request_minor_body_descriptors", lambda value: descriptors)
    monkeypatch.setattr("wenu.minor_body_resources.MinorBodyResourceSession", Session)
    monkeypatch.setattr("wenu.charts.request_generation.resolve_chart_request", stage("resolve", resolved))
    for name in ("grids", "horizon", "disks"):
        monkeypatch.setattr("wenu.charts.request_generation.configure_chart_request_" + name, stage(name))
    monkeypatch.setattr("wenu.charts.request_tracks.configure_chart_request_track", stage("tracks"))

    def satellite_tracks(*args):
        stage("satellite")()
        layer = object()
        sky.layers.append(layer)
        return (layer,)

    monkeypatch.setattr("wenu.charts.request_satellite_tracks.configure_chart_request_satellite_tracks", satellite_tracks)
    monkeypatch.setattr("wenu.charts.request_generation.prepare_chart_request", stage("prepare", prepared))
    return SimpleNamespace(sky=sky, request=request, before=before, sessions=sessions,
                           observer_closes=observer_closes, old_resolver=old_resolver,
                           error=error, cleanup_error=cleanup_error)


def _assert_minor_body_request_restored(fixture):
    sky = fixture.sky
    layers, bodies, alias = fixture.before
    assert len(sky.layers) == len(layers)
    assert all(actual is old for actual, old in zip(sky.layers, layers))
    assert sky.solar_system_bodies == bodies
    assert sky.first_alias is alias
    assert not hasattr(sky, "second_alias")
    assert all(layer.source_resolver is fixture.old_resolver for layer in layers)
    assert fixture.observer_closes == []


@pytest.mark.parametrize("failure_stage", [
    "add", "session", "bind", "resolve", "grids", "horizon", "disks",
    "tracks", "satellite", "prepare",
])
def test_minor_body_request_setup_failure_restores_owned_registrations(monkeypatch, failure_stage):
    fixture = _minor_body_request_fixture(monkeypatch, failure_stage=failure_stage)
    with pytest.raises(RuntimeError) as caught:
        _prepare_with_sphere(fixture.request, fixture.sky, object(), owns_observer=False)
    assert caught.value is fixture.error
    _assert_minor_body_request_restored(fixture)
    assert all(session.closes == 1 for session in fixture.sessions)


def test_minor_body_request_success_close_restores_aliases_once(monkeypatch):
    fixture = _minor_body_request_fixture(monkeypatch)
    build = _prepare_with_sphere(fixture.request, fixture.sky, object(), owns_observer=False)
    assert fixture.sky.first_alias is not fixture.before[-1]
    assert hasattr(fixture.sky, "second_alias")
    build.close()
    build.close()
    _assert_minor_body_request_restored(fixture)
    assert fixture.sessions[0].closes == 1


def test_minor_body_export_failure_closes_and_restores_supplied_sky(monkeypatch):
    fixture = _minor_body_request_fixture(monkeypatch)
    build = _prepare_with_sphere(fixture.request, fixture.sky, object(), owns_observer=False)
    monkeypatch.setattr("wenu.charts.request_generation.build_chart_request", lambda *args, **kwargs: build)
    def fail(*args, **kwargs):
        raise fixture.error
    monkeypatch.setattr("wenu.charts.request_generation.export_prepared_chart", fail)
    with pytest.raises(RuntimeError) as caught:
        generate_chart_request(fixture.request, sky=fixture.sky)
    assert caught.value is fixture.error
    _assert_minor_body_request_restored(fixture)
    assert fixture.sessions[0].closes == 1


def test_minor_body_cleanup_error_still_restores_registrations(monkeypatch):
    fixture = _minor_body_request_fixture(monkeypatch, failure_stage="prepare", close_error=True)
    with pytest.raises(RuntimeError) as caught:
        _prepare_with_sphere(fixture.request, fixture.sky, object(), owns_observer=False)
    assert caught.value is fixture.cleanup_error
    assert caught.value.__context__ is fixture.error
    _assert_minor_body_request_restored(fixture)


def test_minor_body_build_close_error_still_restores_supplied_sky(monkeypatch):
    fixture = _minor_body_request_fixture(monkeypatch, close_error=True)
    build = _prepare_with_sphere(fixture.request, fixture.sky, object(), owns_observer=False)
    with pytest.raises(RuntimeError) as caught:
        build.close()
    assert caught.value is fixture.cleanup_error
    _assert_minor_body_request_restored(fixture)


def _configured_request_fixture(monkeypatch, *, failure_stage=None):
    """Run real configuration owners with constructed, non-numerical layers."""
    from wenu.sky.celestial_sphere import CelestialSphere
    from wenu.sky.sky_layer import SkyLayer

    error = RuntimeError("synthetic configured-request failure: " + str(failure_stage))
    closes = []

    class Layer(SkyLayer):
        def __init__(self, name, display_kind=None):
            self.layer_name = name
            self.display_kind = display_kind

        def spherical_geometry(self, observer):
            raise AssertionError("configuration must not evaluate scientific geometry")

    class Grid(Layer):
        pass

    class Horizon(Layer):
        pass

    failed_names = {"grid": "new-grid", "horizon": "new-horizon",
                    "disk": "test_disk_limb", "sequence": "test_sequence_limb",
                    "track": "solar_system_track", "symbol": "solar_system_track_symbol"}

    class Sky(CelestialSphere):
        def add(self, layer):
            if (layer.layer_name == failed_names.get(failure_stage)
                    and not any(layer is old for old in before[0])):
                raise error
            return super().add(layer)

        def add_equatorial_grid(self, **kwargs):
            return self.add(Grid("new-grid"))

        def add_horizon_reference(self):
            self.horizon_reference = Horizon("new-horizon")
            return self.add(self.horizon_reference)

    sky = Sky(SimpleNamespace(close=lambda: closes.append(True)))
    retained = Layer("catalogue")
    selected, other = Layer("selected-point"), Layer("other-point")
    selected.request_draw_label = True
    sky.solar_system_bodies.update(selected=selected, other=other)
    original_grid, original_horizon = Grid("original-grid"), Horizon("original-horizon")
    disk = Layer("original_disk", "resolved_disk")
    sequence = Layer("original_sequence", "observed_disk_sequence")
    track = Layer("solar_system_track")
    symbol = Layer("solar_system_track_symbol")
    # Bypass the fault injector while installing the original registry.
    for layer in (retained, original_grid, selected, disk, original_horizon, sequence, track, symbol, other):
        CelestialSphere.add(sky, layer)
    sky.horizon_reference, sky.original_disk, sky.original_sequence = original_horizon, disk, sequence
    sky.venus_disk_illuminated = None  # distinguish existing None from absence
    sky.catalogue_cache = object()
    before = (tuple(sky.layers), dict(vars(sky)), dict(vars(selected)), dict(vars(other)))
    descriptor = SimpleNamespace(selection_key="selected", body_class="asteroid", display_name="Fixture", iau_number=42)
    request = SimpleNamespace(
        family="regional", coordinate_frame="equatorial", horizon=True,
        detail=SimpleNamespace(grids=True),
        reference_policy=SimpleNamespace(resolved_equinox=lambda observer: "J2000"),
        minor_body_descriptors=(), solar_system_disks=(SimpleNamespace(descriptor=descriptor, magnification=1),),
        solar_system_disk_sequence=SimpleNamespace(sequence=object(), magnification=1,
                                                  label_dates=False, temporal_components=None),
        solar_system_tracks=(SimpleNamespace(descriptor=descriptor, tick_offsets_days=(0, 1, 2)),),
        solar_system_track_labels="none", solar_system_track_symbols="major",
        solar_system_track_tick_labels=False, solar_system_track_path=True, solar_system_track_ticks=True,
    )
    monkeypatch.setattr("wenu.minor_body_resources.request_minor_body_descriptors", lambda value: ())
    monkeypatch.setattr("wenu.charts.request_generation.resolve_chart_request",
                        lambda value, profile: SimpleNamespace(request=value, frame=None))
    monkeypatch.setattr("wenu.charts.request_grids.ChartRequest", SimpleNamespace)
    monkeypatch.setattr("wenu.charts.request_grids.CoordinatesGrid", Grid)
    monkeypatch.setattr("wenu.charts.request_grids.validate_equatorial_grid_marks", lambda value: None)
    monkeypatch.setattr("wenu.charts.request_grids.requested_coordinate_grids",
                        lambda detail: {"equatorial_grid"} if detail.grids else set())
    monkeypatch.setattr("wenu.charts.request_grids._grid_specifications", lambda *args, **kwargs: {"equatorial_grid": {}})
    monkeypatch.setattr("wenu.charts.request_horizon.ChartRequest", SimpleNamespace)
    monkeypatch.setattr("wenu.charts.request_horizon.HorizonReference", Horizon)
    monkeypatch.setattr("wenu.charts.request_disks.solar_system_disk_layers", lambda *args, **kwargs: (
        Layer("test_disk_face", "resolved_disk"), Layer("test_disk_limb", "resolved_disk")))
    monkeypatch.setattr("wenu.charts.request_disks.observed_solar_system_disk_sequence_layers", lambda *args, **kwargs: (
        Layer("test_sequence_face", "observed_disk_sequence"), Layer("test_sequence_limb", "observed_disk_sequence")))
    monkeypatch.setattr("wenu.charts.request_tracks._selected_point_replaces_start_label", lambda *args: True)
    monkeypatch.setattr("wenu.charts.request_tracks.SolarSystemTrackRealizer", lambda **kwargs: object())
    monkeypatch.setattr("wenu.charts.request_tracks.SolarSystemTrackRealization", lambda *args, **kwargs: object())
    monkeypatch.setattr("wenu.charts.request_tracks.SolarSystemTrackLayer", lambda *args, **kwargs: Layer("solar_system_track"))
    monkeypatch.setattr("wenu.charts.request_tracks.SolarSystemTrackSymbolLayer", lambda *args: Layer("solar_system_track_symbol"))
    monkeypatch.setattr("wenu.charts.request_satellite_tracks.configure_chart_request_satellite_tracks", lambda *args: ())
    def prepare(*args, **kwargs):
        if failure_stage == "prepare":
            raise error
        return SimpleNamespace(chart=object())
    monkeypatch.setattr("wenu.charts.request_generation.prepare_chart_request", prepare)
    return SimpleNamespace(sky=sky, request=request, before=before, error=error, closes=closes)


def _assert_configured_sky_restored(fixture):
    sky = fixture.sky
    layers, attributes, selected, other = fixture.before
    assert len(layers) == len(sky.layers)
    assert all(a is b for a, b in zip(layers, sky.layers))
    assert vars(sky).keys() == attributes.keys()
    assert all(getattr(sky, name) is value for name, value in attributes.items())
    assert vars(sky.solar_system_bodies["selected"]) == selected
    assert vars(sky.solar_system_bodies["other"]) == other
    assert fixture.closes == []


@pytest.mark.parametrize("failure_stage", ["grid", "horizon", "disk", "sequence", "track", "symbol", "prepare"])
def test_configured_request_failure_restores_all_request_mutations(monkeypatch, failure_stage):
    fixture = _configured_request_fixture(monkeypatch, failure_stage=failure_stage)
    with pytest.raises(RuntimeError) as caught:
        _prepare_with_sphere(fixture.request, fixture.sky, object(), owns_observer=False)
    assert caught.value is fixture.error
    _assert_configured_sky_restored(fixture)


def test_configured_build_restores_order_aliases_flags_and_rejects_overlap(monkeypatch):
    fixture = _configured_request_fixture(monkeypatch)
    build = _prepare_with_sphere(fixture.request, fixture.sky, object(), owns_observer=False)
    assert build.sky is fixture.sky
    assert fixture.sky.solar_system_bodies["selected"].request_draw_label is False
    assert fixture.sky.solar_system_bodies["other"].request_draw_label is True
    configured = fixture.sky.layers
    with pytest.raises(RuntimeError, match="already active"):
        _prepare_with_sphere(fixture.request, fixture.sky, object(), owns_observer=False)
    assert fixture.sky.layers == configured
    build.close()
    build.close()
    _assert_configured_sky_restored(fixture)
    next_build = _prepare_with_sphere(fixture.request, fixture.sky, object(), owns_observer=False)
    next_build.close()
    _assert_configured_sky_restored(fixture)


def test_configured_export_failure_restores_supplied_sky(monkeypatch):
    fixture = _configured_request_fixture(monkeypatch)
    build = _prepare_with_sphere(fixture.request, fixture.sky, object(), owns_observer=False)
    monkeypatch.setattr("wenu.charts.request_generation.build_chart_request", lambda *args, **kwargs: build)
    def fail(*args, **kwargs):
        raise fixture.error
    monkeypatch.setattr("wenu.charts.request_generation.export_prepared_chart", fail)
    with pytest.raises(RuntimeError) as caught:
        generate_chart_request(fixture.request, sky=fixture.sky)
    assert caught.value is fixture.error
    _assert_configured_sky_restored(fixture)


def test_configured_requests_are_independent_of_prior_request_order(monkeypatch):
    fixture = _configured_request_fixture(monkeypatch)
    full = fixture.request
    empty = SimpleNamespace(**{**vars(full), "horizon": False, "detail": SimpleNamespace(grids=False),
                              "solar_system_disks": (), "solar_system_disk_sequence": None, "solar_system_tracks": ()})
    signatures = {}
    for name, request in (("empty", empty), ("full", full), ("full", full), ("empty", empty)):
        with _prepare_with_sphere(request, fixture.sky, object(), owns_observer=False):
            current = tuple(layer.layer_name for layer in fixture.sky.layers)
            assert signatures.setdefault(name, current) == current
        _assert_configured_sky_restored(fixture)


@pytest.mark.parametrize("failure", ["attribute", "registry"])
def test_request_state_restoration_failure_attempts_all_and_retains_lease(failure):
    values = [object(), object()]
    class Sky:
        def __init__(self):
            self.layers = list(values)
            self.fail = False

        def clear(self):
            self.layers.clear()

        def extend(self, layers):
            if self.fail and failure == "registry":
                raise RuntimeError("synthetic registry restoration failure")
            self.layers.extend(layers)
    class Owner:
        def __init__(self):
            self._value, self.fail = "old", False

        @property
        def value(self):
            return self._value

        @value.setter
        def value(self, value):
            if self.fail and failure == "attribute":
                raise RuntimeError("synthetic attribute restoration failure")
            self._value = value
    sky, owner = Sky(), Owner()
    state = _RequestSkyState(sky)
    state.remember_attribute(owner, "value")
    state.remember_attribute(sky, "temporary_alias")
    owner.value, sky.temporary_alias, sky.layers[:] = "new", object(), [object()]
    state.remember_attribute(owner, "value")  # must retain the first value
    sky.fail = owner.fail = True
    with pytest.raises(RuntimeError, match="synthetic .* restoration failure"):
        state.restore()
    assert not hasattr(sky, "temporary_alias")
    if failure == "attribute":
        assert sky.layers == values
    else:
        assert owner.value == "old"
    with pytest.raises(RuntimeError, match="already active"):
        _RequestSkyState(sky)
    sky.fail = owner.fail = False
    state.restore()
    state.restore()
    assert sky.layers == values and owner.value == "old"
    assert not hasattr(sky, "_active_chart_request_state")
    with pytest.raises(RuntimeError, match="already restored"):
        state.remember_attribute(owner, "value")


@pytest.mark.parametrize("existing_lease_slot", [False, True])
def test_request_state_preserves_original_none_and_missing_attributes(existing_lease_slot):
    sky = SimpleNamespace(layers=(), present=None)
    if existing_lease_slot:
        sky._active_chart_request_state = None
    state = _RequestSkyState(sky)
    state.remember_attribute(sky, "present")
    state.remember_attribute(sky, "absent")
    sky.present, sky.absent = object(), object()
    state.remember_attribute(sky, "present")
    state.restore()
    assert sky.present is None and not hasattr(sky, "absent")
    assert hasattr(sky, "_active_chart_request_state") is existing_lease_slot
    if existing_lease_slot:
        assert sky._active_chart_request_state is None


def test_failed_resource_close_keeps_request_lease_until_build_close_retry(monkeypatch):
    fixture = _configured_request_fixture(monkeypatch)
    build = _prepare_with_sphere(fixture.request, fixture.sky, object(), owns_observer=False)
    class Resource:
        fail = True
        def close(self):
            if self.fail:
                raise RuntimeError("synthetic resource close failure")
    resource = Resource()
    build.minor_body_session = resource
    with pytest.raises(RuntimeError, match="resource close failure"):
        build.close()
    with pytest.raises(RuntimeError, match="already active"):
        _prepare_with_sphere(fixture.request, fixture.sky, object(), owns_observer=False)
    resource.fail = False
    build.close()
    _assert_configured_sky_restored(fixture)
