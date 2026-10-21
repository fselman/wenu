"""Request and registration boundaries for drawable planet tracks."""
from dataclasses import replace
from pathlib import Path
import pytest
from wenu.charts.product_options import ChartProductOptions
from wenu.charts.detail import SkyContentSelection
from wenu.charts.request import (
    ChartFrameRequest,
    ChartObserverRequest,
    ChartRequest,
    ChartSubjectRequest,
)
from wenu.charts.request_tracks import (
    _coincident_start_label,
    configure_chart_request_track,
    configure_chart_request_tracks,
)
from wenu.sky.celestial_sphere import CelestialSphere
from wenu.sky.ceres import CERES_BODY
from wenu.sky.solar_system_track_layer import (
    CometTrackSymbolLayer,
    SolarSystemTrackRealization,
    SolarSystemTrackSymbolLayer,
)
from wenu.sky.solar_system_tracks import SolarSystemTrackRequest
from wenu.sky.venus import VENUS_POINT

def track():
    return SolarSystemTrackRequest(
        descriptor=VENUS_POINT,
        start_instant="2026-08-30T00:00:00Z",
        start_time_scale="utc",
        sample_step_days=1.0 / 24.0,
        tick_step_days=7.0,
        tick_count=4,
    )

def request(family="regional", selected_track=None):
    subject = (
        ChartSubjectRequest(target="venus")
        if family in {"regional", "binocular"}
        else ChartSubjectRequest()
    )
    frame = (
        ChartFrameRequest(field_width_deg=20.0, field_height_deg=20.0)
        if family == "regional"
        else ChartFrameRequest()
    )
    return ChartRequest(
        observer=ChartObserverRequest(location="La Ligua", time="2026-08-30T00:00:00Z"),
        family=family,
        product=ChartProductOptions(
            output=Path("track.png"), style="atlas", mode="presentation"
        ),
        subject=subject,
        frame=frame,
        solar_system_track=selected_track,
        projection="mollweide" if family == "all_sky" else "stereographic",
        coordinate_frame="galactic" if family == "all_sky" else "horizontal",
    )

@pytest.mark.parametrize("family", ("regional", "binocular"))
def test_track_request_is_allowed_for_supported_chart_families(family):
    assert request(family, track()).solar_system_track == track()

def test_track_request_is_rejected_for_all_sky():
    with pytest.raises(ValueError, match="only by regional and binocular"):
        request("all_sky", track())

def test_request_registration_replaces_prior_track_and_can_remove_it():
    sky = CelestialSphere(None)
    first = configure_chart_request_track(sky, request("regional", track()))
    second = configure_chart_request_track(sky, request("regional", track()))
    assert first is not second
    assert tuple(
        layer for layer in sky.layers
        if layer.layer_name == "solar_system_track"
    ) == (second,)
    assert configure_chart_request_track(
        sky, request("regional", None)
    ) is None
    assert sky.layers == ()


def test_request_registers_multiple_tracks_as_independent_layers():
    sky = CelestialSphere(None)
    ceres = SolarSystemTrackRequest(
        descriptor=CERES_BODY,
        start_instant="2026-08-30T00:00:00Z",
        start_time_scale="utc",
        sample_step_days=1.0,
        tick_step_days=7.0,
        tick_count=4,
    )
    chart_request = ChartRequest(
        observer=ChartObserverRequest(
            location="La Ligua", time="2026-08-30T00:00:00Z"
        ),
        family="regional",
        product=ChartProductOptions(
            output=Path("tracks.png"), style="atlas", mode="presentation"
        ),
        subject=ChartSubjectRequest(constellations=("Psc",)),
        solar_system_tracks=(track(), ceres),
        minor_body_resource_directory=Path("resources"),
    )

    layers = configure_chart_request_tracks(sky, chart_request)

    assert len(layers) == 2
    assert tuple(layer.request.descriptor.selection_key for layer in layers) == (
        "venus", "ceres",
    )
    assert all(layer in sky.layers for layer in layers)


def test_comet_track_places_one_symbol_at_every_major_epoch():
    encke = replace(
        CERES_BODY,
        target="2p", entity_key="comet_2p", display_name="2P/Encke",
        selection_key="2p", body_class="comet", physical_body_id="1000025",
        canonical_designation="2P/Encke", iau_number=2,
    )
    encke_track = replace(track(), descriptor=encke)
    chart_request = replace(
        request("regional"),
        minor_body_descriptors=(encke,),
        solar_system_tracks=(encke_track,),
        minor_body_resource_directory=Path("resources"),
    )
    sky = CelestialSphere(None)

    configure_chart_request_tracks(sky, chart_request)

    symbols = tuple(
        layer for layer in sky.layers
        if isinstance(layer, CometTrackSymbolLayer)
    )
    assert tuple(layer.offset_days for layer in symbols) == pytest.approx(
        encke_track.tick_offsets_days
    )
    assert all(layer.body_descriptor is encke for layer in symbols)
    assert all(layer.request_draw_label is False for layer in symbols)
    track_layer = next(
        layer for layer in sky.layers
        if layer.layer_name == "solar_system_track"
    )
    assert all(
        layer.track_realization is track_layer.track_realization
        for layer in symbols
    )


def test_track_components_are_independently_selectable_from_one_realization():
    chart_request = replace(
        request("regional", track()),
        solar_system_track=None,
        solar_system_track_path=False,
        solar_system_track_ticks=False,
        solar_system_track_symbols="start",
        solar_system_track_labels="start",
    )
    sky = CelestialSphere(None)

    track_layer = configure_chart_request_track(sky, chart_request)

    symbols = tuple(
        layer for layer in sky.layers
        if isinstance(layer, SolarSystemTrackSymbolLayer)
    )
    assert track_layer.draw_path is False
    assert track_layer.draw_ticks is False
    assert track_layer.label_start is True
    assert track_layer.label_ticks is False
    assert len(symbols) == 1
    assert symbols[0].major_index == 0
    assert symbols[0].track_realization is track_layer.track_realization


def test_major_symbol_cadence_is_generic_for_planets():
    chart_request = replace(
        request("regional", track()), solar_system_track=None,
        solar_system_track_symbols="major"
    )
    sky = CelestialSphere(None)

    configure_chart_request_tracks(sky, chart_request)

    symbols = tuple(
        layer for layer in sky.layers
        if isinstance(layer, SolarSystemTrackSymbolLayer)
    )
    assert tuple(layer.major_index for layer in symbols) == tuple(
        range(track().tick_count + 1)
    )
    assert not any(isinstance(layer, CometTrackSymbolLayer) for layer in symbols)


def test_legacy_tick_label_flag_is_the_major_label_compatibility_alias():
    chart_request = replace(
        request("regional", track()), solar_system_track=None,
        solar_system_track_tick_labels=True
    )
    layer = configure_chart_request_track(CelestialSphere(None), chart_request)

    assert layer.label_start is True
    assert layer.label_ticks is True


def test_legacy_tick_label_flag_rejects_conflicting_explicit_cadence():
    with pytest.raises(ValueError, match="conflicts"):
        replace(
            request("regional", track()),
            solar_system_track=None,
            solar_system_track_tick_labels=True,
            solar_system_track_labels="start",
        )


def test_shared_track_realization_evaluates_the_scientific_track_once():
    class CountingRealizer:
        def __init__(self):
            self.calls = []

        def curve(self, track_request, *, context, observer):
            self.calls.append((track_request, context, observer))
            return object()

    realizer = CountingRealizer()
    realization = SolarSystemTrackRealization(track(), realizer=realizer)
    context = object()
    observer = object()

    first = realization.realize(context, observer)
    second = realization.realize(context, observer)

    assert second is first
    assert len(realizer.calls) == 1


def test_selected_comet_point_replaces_duplicate_track_start_symbol():
    encke = replace(
        CERES_BODY,
        target="2p", entity_key="comet_2p", display_name="2P/Encke",
        selection_key="2p", body_class="comet", physical_body_id="1000025",
        canonical_designation="2P/Encke", iau_number=2,
    )
    encke_track = replace(track(), descriptor=encke)
    chart_request = replace(
        request("regional"),
        content=SkyContentSelection(solar_system_objects={"2p"}),
        minor_body_descriptors=(encke,),
        solar_system_tracks=(encke_track,),
        minor_body_resource_directory=Path("resources"),
    )
    sky = CelestialSphere(None)
    sky.add_solar_system_body(encke)

    configure_chart_request_tracks(sky, chart_request)

    offsets = tuple(
        layer.offset_days for layer in sky.layers
        if isinstance(layer, CometTrackSymbolLayer)
    )
    assert offsets == pytest.approx(encke_track.tick_offsets_days[1:])


def test_request_rejects_duplicate_and_satellite_tracks():
    with pytest.raises(ValueError, match="cannot repeat"):
        replace(request("regional", track()),
                solar_system_track=None, solar_system_tracks=(track(), track()))

    moon = replace(track(), descriptor=replace(
        VENUS_POINT, target="moon", entity_key="moon", selection_key="moon",
        display_name="Moon", body_class="natural_satellite",
    ))
    with pytest.raises(ValueError, match="satellite tracks"):
        replace(request("regional"), solar_system_tracks=(moon,))


def test_coincident_selected_point_replaces_only_the_track_start_label():
    sky = CelestialSphere(None)
    sky.add_solar_system_body(CERES_BODY)
    ceres_track = SolarSystemTrackRequest(
        descriptor=CERES_BODY,
        start_instant="2026-08-30T00:00:00Z",
        start_time_scale="utc",
        sample_step_days=1.0,
        tick_step_days=7.0,
        tick_count=4,
    )
    chart_request = ChartRequest(
        observer=ChartObserverRequest(
            location="La Ligua", time="2026-08-30T00:00:00Z"
        ),
        family="regional",
        product=ChartProductOptions(
            output=Path("ceres.png"), style="atlas", mode="presentation"
        ),
        subject=ChartSubjectRequest(constellations=("Psc",)),
        content=SkyContentSelection(solar_system_objects={"ceres"}),
        solar_system_track=ceres_track,
        solar_system_track_tick_labels=True,
        minor_body_resource_directory=Path("resources"),
    )

    layer = configure_chart_request_track(sky, chart_request)

    assert layer.label_start is True
    assert layer.start_label_text == "Ceres (1)"
    assert layer.label_ticks is True
    assert sky.solar_system_bodies["ceres"].request_draw_label is False


@pytest.mark.parametrize(
    ("name", "expected"),
    (("Future Name", "Future Name (79989)"), ("(79989)", "(79989)")),
)
def test_numbered_asteroid_start_label_places_number_after_official_name(
    name, expected
):
    descriptor = replace(
        CERES_BODY,
        target="79989",
        entity_key="asteroid_79989",
        display_name=name,
        selection_key="79989",
        physical_body_id="20079989",
        canonical_designation=expected,
        iau_number=79989,
        localized_display_names=(),
    )

    assert _coincident_start_label(descriptor) == expected


@pytest.mark.parametrize('components', ('all', 'start-only'))
def test_request_track_components_preserve_raw_kernel_png_and_fixed_samples(monkeypatch, tmp_path, components):
    """Public registration/style/draw path with a labelled synthetic ephemeris."""
    from types import SimpleNamespace
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.image import imread
    from test_solar_system_tracks import (
        _kernel_track_backend, ApparentRealizer, observer_state, sample_observer,
        request as sampled_request, CONTEXT,
    )
    from wenu.sky.solar_system_tracks import SolarSystemTrackRealizer
    from wenu.projections import StereographicProjection
    from wenu.rendering import MatplotlibRenderer
    from wenu.charts.styles import PublicationStyle
    from wenu.charts.detail import ResolvedDetail
    from wenu.charts.detail_application import composition_layer_options
    from wenu.charts.context import Viewport, BoundaryKind

    raw, backend = _kernel_track_backend(monkeypatch)
    value = sampled_request(descriptor=VENUS_POINT)
    dependencies = dict(sample_observer_factory=sample_observer,
                        observer_state_factory=observer_state, apparent_realizer=ApparentRealizer())
    observer = object()
    projection = StereographicProjection()
    reference = SolarSystemTrackRealizer(source_factory=lambda observer: raw, **dependencies).curve(
        value, context=CONTEXT, observer=observer)
    projected = projection.project_geometry(reference.geometry)[0]
    cx, cy = float(np.mean(projected.x)), float(np.mean(projected.y))
    viewport = Viewport(cx-.08, cx+.08, cy-.08, cy+.08)
    composition = SimpleNamespace(style=PublicationStyle(), detail=ResolvedDetail(),
        context=SimpleNamespace(boundary_kind=BoundaryKind.RECTANGULAR, viewport=viewport))
    images, receipts = [], []
    for routed in (False, True):
        chart = replace(request('regional', value), solar_system_track=None,
            solar_system_track_symbols='major' if components == 'all' else 'start',
            solar_system_track_labels='major' if components == 'all' else 'start',
            solar_system_track_path=components == 'all', solar_system_track_ticks=components == 'all')
        sky = CelestialSphere(None)
        layer = configure_chart_request_track(sky, chart)
        realizer = layer.track_realization.realizer
        realizer.sample_observer_factory = sample_observer
        realizer.observer_state_factory = observer_state
        realizer.apparent_realizer = ApparentRealizer()
        if not routed:
            realizer.source_factory = lambda observer: raw
        configured = composition_layer_options(composition, sky, reload_catalogues=False)
        symbols = tuple(x for x in sky.layers if isinstance(x, SolarSystemTrackSymbolLayer))
        assert len(symbols) == (3 if components == 'all' else 1)
        start_count = len(raw.requests)
        figure, axes = plt.subplots(figsize=(4, 3), dpi=90)
        try:
            result = sky.draw_chart(observer=observer, realization_context=CONTEXT,
                projection=projection, renderer=MatplotlibRenderer(axes),
                layer_options=configured.layer_options, viewport=viewport)
            axes.set_axis_off()
            path = tmp_path / f'track-{components}-{routed}.png'
            figure.savefig(path)
            images.append(imread(path))
            receipts.append(layer.last_result)
            assert len(raw.requests) - start_count == 2 * len(value.sample_offsets_days)
            for symbol in symbols:
                points = symbol.realize(CONTEXT, observer)
                i = layer.last_result.tick_sample_indices[symbol.major_index]
                assert points.lon_deg[0] == layer.last_result.geometry.lon_deg[0][i]
            assert len(raw.requests) - start_count == 2 * len(value.sample_offsets_days)
            assert result.layers
        finally:
            plt.close(figure)
    np.testing.assert_array_equal(images[0], images[1])
    assert np.any(images[0][:, :, :3] < .5)
    assert receipts[0].sample_instants == receipts[1].sample_instants
    np.testing.assert_allclose(receipts[0].geometry.lon_deg[0], receipts[1].geometry.lon_deg[0], rtol=0, atol=1e-11)
