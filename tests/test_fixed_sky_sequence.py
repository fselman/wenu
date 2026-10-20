"""Fixed-sky and rotating-horizon planning-contract tests."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from wenu.charts.fixed_sky_sequence import (
    FixedSkyRotatingHorizonGeneration,
    FixedSkyRotatingHorizonSequenceRequest,
    FixedSkySequenceExecution,
    generate_fixed_sky_rotating_horizon_sequence,
    resolve_fixed_sky_rotating_horizon_frame,
)
from wenu.charts.product_options import ChartProductOptions
from wenu.charts.request import (
    ChartFrameRequest,
    ChartObserverRequest,
    ChartRequest,
)
from wenu.output_policy import OutputFormat
from wenu.sky.maximal_sphere import CANONICAL_MAXIMAL_SPHERE_PROFILE
from wenu.temporal import PlaybackSpec, TemporalTimeline


def chart_request(output):
    return ChartRequest(
        observer=ChartObserverRequest(
            time="2026-08-21T21:00:00-04:00",
            location="La Ligua",
        ),
        family="circumpolar",
        frame=ChartFrameRequest(
            pole="south",
            limiting_declination_deg=-60,
        ),
        product=ChartProductOptions(
            output=output,
            output_format=OutputFormat.PNG,
        ),
    )


def timeline():
    return TemporalTimeline.uniform(
        datetime(2026, 8, 22, 1, tzinfo=timezone.utc),
        datetime(2026, 8, 22, 7, tzinfo=timezone.utc),
        3,
        display_timezone="America/Santiago",
    )


@pytest.mark.parametrize("failure", ("local_construction", "orientation", "anchor_close", "local_close"))
def test_frame_resolution_releases_every_constructed_observer_on_failure(tmp_path, monkeypatch, failure):
    from wenu.charts import fixed_sky_sequence as module
    from wenu.charts.fixed_sky_orientation import FixedSkyCircumpolarOrientation

    frame = FixedSkyRotatingHorizonSequenceRequest(
        chart=chart_request(tmp_path / "frames"), timeline=timeline(),
        celestial_anchor_time=timeline().instants[0],
    ).frames[-1]
    constructed, closed = [], []

    def observer(**kwargs):
        index = len(constructed)
        if index == 1 and failure == "local_construction":
            raise RuntimeError("local construction refused")
        value = SimpleNamespace(time=kwargs["time"])

        def close():
            closed.append(index)
            if failure == ("anchor_close" if index == 0 else "local_close"):
                raise RuntimeError("observer close refused")

        value.close = close
        constructed.append(value)
        return value

    def orientation(anchor, local, **kwargs):
        assert anchor.time == frame.celestial_request.observer.time
        assert local.time == frame.local_observer.time
        if failure == "orientation":
            raise RuntimeError("orientation refused")
        return FixedSkyCircumpolarOrientation("south", 0, 12, 12)

    monkeypatch.setattr(module, "Observer", observer)
    monkeypatch.setattr(module, "fixed_sky_circumpolar_orientation", orientation)
    with pytest.raises(RuntimeError, match="refused"):
        resolve_fixed_sky_rotating_horizon_frame(frame)
    assert sorted(closed) == list(range(len(constructed)))


def test_frame_resolution_consumes_returned_orientation_without_changing_anchor(tmp_path, monkeypatch):
    from wenu.charts import fixed_sky_sequence as module
    from wenu.charts.fixed_sky_orientation import FixedSkyCircumpolarOrientation

    sequence = FixedSkyRotatingHorizonSequenceRequest(
        chart=chart_request(tmp_path / "frames"), timeline=timeline(),
        celestial_anchor_time=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )
    observers = []
    def observer(**kwargs):
        value = SimpleNamespace(time=kwargs["time"], closed=False)
        value.close = lambda: setattr(value, "closed", True)
        observers.append(value)
        return value
    returned = FixedSkyCircumpolarOrientation("south", 14, 33, 27)
    monkeypatch.setattr(module, "Observer", observer)
    monkeypatch.setattr(module, "fixed_sky_circumpolar_orientation", lambda *args, **kwargs: returned)
    frame = sequence.frames[-1]
    resolved = resolve_fixed_sky_rotating_horizon_frame(frame)
    assert resolved.orientation is returned
    assert resolved.chart_request.frame.position_angle_deg == 27
    assert resolved.chart_request.observer.time == frame.simulation_time
    assert resolved.frame.celestial_request.observer.time == sequence.celestial_anchor_time
    assert all(value.closed for value in observers)


def _fixed_kernel_environment(monkeypatch):
    """Constructed stars and synthetic observation backend; real shared services."""
    from test_chart_sequence import _kernel_sequence_environment
    from test_stars import FakeApparent
    from wenu.charts import fixed_sky_sequence as module, request_generation
    from wenu.sky.maximal_sphere import CANONICAL_MAXIMAL_SPHERE_PROFILE
    from astropy.coordinates import SkyCoord
    import astropy.units as u

    observers, skies, realized = _kernel_sequence_environment(monkeypatch)
    create_observer = request_generation.Observer
    create_sphere = request_generation.build_maximal_sphere

    def observer(**kwargs):
        value = create_observer(**kwargs)
        def observe(target):
            # Synthetic Skyfield-like seam using real Astropy coordinates.
            horizontal = SkyCoord(ra=target.ra.hours * 15 * u.deg,
                dec=target.dec.degrees * u.deg, frame="icrs").transform_to(value.altaz_frame)
            return FakeApparent(horizontal.alt.deg, horizontal.az.deg)
        value.skyfield = SimpleNamespace(at=lambda time: SimpleNamespace(observe=observe))
        return value

    def sphere(observer, *, profile=CANONICAL_MAXIMAL_SPHERE_PROFILE):
        sky = create_sphere(observer, profile=profile)
        sky.stars.source_catalog.loc[:, "dec_degrees"] = [-80., -75.]
        sky.stars.catalog = sky.stars.source_catalog.copy(deep=True)
        return sky

    monkeypatch.setattr(request_generation, "Observer", observer)
    monkeypatch.setattr(module, "Observer", observer)
    monkeypatch.setattr(request_generation, "build_maximal_sphere", sphere)
    monkeypatch.setattr("wenu.sky.maximal_sphere.generate_celestial_sphere", lambda: sphere(None))
    return observers, skies, realized


@pytest.mark.parametrize("output_format", (OutputFormat.PNG, OutputFormat.SVG, OutputFormat.PDF))
def test_fixed_sky_real_kernel_cold_and_loaded_outputs_agree(tmp_path, monkeypatch, output_format):
    import numpy as np
    from wenu.charts.detail import DetailOverrides
    from wenu.configuration import load_configuration_defaults
    from wenu.charts.fixed_sky_baseline import compare_png_frames, compare_normalized_svg, render_pdf_page_rgba
    from wenu.charts import request_generation

    observers, skies, realized = _fixed_kernel_environment(monkeypatch)
    instants = timeline().instants[::2]
    configuration = load_configuration_defaults()
    planned = FixedSkyRotatingHorizonSequenceRequest(
        chart=ChartRequest(family="circumpolar",
            observer=ChartObserverRequest(time="2000-01-01T00:00:00Z", lat_deg=-33, lon_deg=-71),
            frame=ChartFrameRequest(pole="south", limiting_declination_deg=-60),
            product=ChartProductOptions(output=tmp_path / "cold", output_format=output_format),
            detail=DetailOverrides(enabled_layers=frozenset({"stars"}))),
        timeline=TemporalTimeline(instants, display_timezone="America/Santiago"),
        celestial_anchor_time=instants[0] - timedelta(hours=1), configuration=configuration)
    original = request_generation.generate_chart_request
    calls = []
    def generate(request, **kwargs):
        calls.append((request, kwargs))
        return original(request, **kwargs)
    monkeypatch.setattr(request_generation, "generate_chart_request", generate)
    cold = generate_fixed_sky_rotating_horizon_sequence(planned)
    reused = generate_fixed_sky_rotating_horizon_sequence(replace(planned,
        chart=replace(planned.chart, product=replace(planned.chart.product, output=tmp_path / "reused"))),
        execution="reuse_loaded_sphere")
    assert cold.canonical_sphere_build_count == 2
    assert reused.canonical_sphere_build_count == 1
    assert len(skies) == 3
    assert skies[-1].observer is None
    assert all(value.closed for value in observers)
    assert all(not hasattr(sky, "_active_chart_request_state") for sky in skies)
    assert all(options["configuration"] is configuration for _, options in calls)
    assert tuple(request.observer.time for request, _ in calls) == instants * 2
    assert all(frame.resolved.frame.celestial_request.observer.time == planned.celestial_anchor_time
        for frame in (*cold.frames, *reused.frames))
    assert tuple(context.evaluation_instant for context, _, _ in realized[:2]) == tuple(
        context.evaluation_instant for context, _, _ in realized[2:])
    from astropy.time import Time
    assert tuple(context.evaluation_instant for context, _, _ in realized[:2]) == tuple(
        Time(instant).utc.isot for instant in instants)
    assert all(context.evaluation_instant != Time(planned.celestial_anchor_time).utc.isot
        for context, _, _ in realized)
    assert all(sky.layers == (sky.stars,) for sky in skies)
    for (_, _, left), (_, _, right) in zip(realized[:2], realized[2:], strict=True):
        np.testing.assert_array_equal(left.ids, right.ids)
        np.testing.assert_allclose(left.lon_deg, right.lon_deg, atol=0, rtol=0)
        np.testing.assert_allclose(left.lat_deg, right.lat_deg, atol=0, rtol=0)
    for left_frame, right_frame in zip(cold.frames, reused.frames, strict=True):
        def layers(frame):
            rendering = frame.generation.exports[0].rendering
            return getattr(rendering, "rendering", rendering).layers
        left_layers, right_layers = layers(left_frame), layers(right_frame)
        assert len(left_layers) == len(right_layers) == 1
        left, right = left_layers[0], right_layers[0]
        assert left.layer.layer_name == right.layer.layer_name == "stars"
        np.testing.assert_array_equal(left.projected.ids, right.projected.ids)
        np.testing.assert_array_equal(left.projected.x, right.projected.x)
        np.testing.assert_array_equal(left.projected.y, right.projected.y)
    for index, (left, right) in enumerate(zip(cold.outputs, reused.outputs, strict=True)):
        assert left.is_file() and right.is_file()
        if output_format is OutputFormat.SVG:
            assert compare_normalized_svg(left, right)
        else:
            if output_format is OutputFormat.PDF:
                left = render_pdf_page_rgba(left, tmp_path / f"cold-{index}.png", dpi=40)
                right = render_pdf_page_rgba(right, tmp_path / f"reused-{index}.png", dpi=40)
            assert compare_png_frames(left, right).changed_pixels == 0
    if output_format is OutputFormat.PNG:
        from wenu.charts.fixed_sky_baseline import generate_fixed_sky_complete_render_baseline
        baseline = generate_fixed_sky_complete_render_baseline(planned, tmp_path / "baseline")
        assert tuple(frame.frame.simulation_time for frame in baseline.frames) == instants
        assert all(path.is_file() for path in baseline.outputs)
        assert compare_png_frames(baseline.outputs[-1], cold.outputs[-1]).changed_pixels > 0

    from wenu_kernel import KernelSession
    warm_sky = skies[2]
    before = tuple(path.read_bytes() for path in reused.outputs)
    monkeypatch.setattr("wenu.sky.maximal_sphere.generate_celestial_sphere", lambda: warm_sky)
    def refuse(*args, **kwargs):
        raise RuntimeError("fixed-sky kernel refusal")
    monkeypatch.setattr(KernelSession, "evaluate", refuse)
    with pytest.raises(RuntimeError, match="fixed-sky kernel refusal"):
        generate_fixed_sky_rotating_horizon_sequence(replace(planned,
            chart=replace(planned.chart, product=replace(planned.chart.product, output=tmp_path / "reused"))),
            execution="reuse_loaded_sphere")
    assert tuple(path.read_bytes() for path in reused.outputs) == before
    assert all(value.closed for value in observers)
    assert not hasattr(warm_sky, "_active_chart_request_state")


def test_fixed_sky_plan_separates_anchor_and_local_observer_time(tmp_path):
    anchor = datetime(
        2026, 8, 21, 21, tzinfo=timezone(timedelta(hours=-4))
    )
    sequence = FixedSkyRotatingHorizonSequenceRequest(
        chart=chart_request(tmp_path / "frames"),
        timeline=timeline(),
        celestial_anchor_time=anchor,
        playback=PlaybackSpec(timedelta(seconds=1.5), 2),
    )

    assert sequence.celestial_anchor_time == datetime(
        2026, 8, 22, 1, tzinfo=timezone.utc
    )
    assert sequence.frame_count == 3
    assert tuple(frame.name for frame in sequence.frames) == (
        "frame-0000.png",
        "frame-0001.png",
        "frame-0002.png",
    )
    assert {
        frame.celestial_request.observer.time
        for frame in sequence.frames
    } == {sequence.celestial_anchor_time}
    assert tuple(
        frame.local_observer.time for frame in sequence.frames
    ) == sequence.timeline.instants
    assert tuple(
        frame.expected_output for frame in sequence.frames
    ) == tuple(
        tmp_path / "frames" / f"frame-{index:04d}.png"
        for index in range(3)
    )


def test_fixed_sky_plan_preserves_location_for_both_time_owners(tmp_path):
    request = chart_request(tmp_path / "frames")
    sequence = FixedSkyRotatingHorizonSequenceRequest(
        chart=request,
        timeline=timeline(),
        celestial_anchor_time=timeline().instants[1],
    )

    assert sequence.celestial_observer.location == "La Ligua"
    assert all(
        frame.local_observer.location == "La Ligua"
        for frame in sequence.frames
    )
    assert all(
        frame.celestial_request.observer.location == "La Ligua"
        for frame in sequence.frames
    )


def test_anchor_is_not_inferred_from_timeline_or_catalogue_epoch(tmp_path):
    explicit = datetime(2035, 1, 1, tzinfo=timezone.utc)
    sequence = FixedSkyRotatingHorizonSequenceRequest(
        chart=chart_request(tmp_path / "frames"),
        timeline=timeline(),
        celestial_anchor_time=explicit,
    )

    assert sequence.celestial_anchor_time == explicit
    assert sequence.celestial_anchor_time not in sequence.timeline.instants
    assert not hasattr(sequence, "catalogue_reference_epoch")


@pytest.mark.parametrize(
    ("value", "error"),
    [
        ("2026-08-22T01:00:00Z", TypeError),
        (datetime(2026, 8, 22, 1), ValueError),
    ],
)
def test_fixed_sky_anchor_requires_an_aware_datetime(
    tmp_path,
    value,
    error,
):
    with pytest.raises(error, match="celestial_anchor_time"):
        FixedSkyRotatingHorizonSequenceRequest(
            chart=chart_request(tmp_path / "frames"),
            timeline=timeline(),
            celestial_anchor_time=value,
        )


def test_fixed_sky_sequence_retains_single_product_constraints(tmp_path):
    request = chart_request(tmp_path / "frames")

    with pytest.raises(ValueError, match="explicit output format"):
        FixedSkyRotatingHorizonSequenceRequest(
            chart=replace(
                request,
                product=ChartProductOptions(output=tmp_path / "frames"),
            ),
            timeline=timeline(),
            celestial_anchor_time=timeline().instants[0],
        )

    with pytest.raises(ValueError, match="must be a directory"):
        FixedSkyRotatingHorizonSequenceRequest(
            chart=replace(
                request,
                product=replace(
                    request.product,
                    output=tmp_path / "frame.png",
                ),
            ),
            timeline=timeline(),
            celestial_anchor_time=timeline().instants[0],
        )



def test_resolved_frames_use_local_time_and_anchor_relative_rotation(tmp_path):
    sequence = FixedSkyRotatingHorizonSequenceRequest(
        chart=chart_request(tmp_path / "frames"),
        timeline=timeline(),
        celestial_anchor_time=timeline().instants[0],
    )

    first = resolve_fixed_sky_rotating_horizon_frame(sequence.frames[0])
    last = resolve_fixed_sky_rotating_horizon_frame(sequence.frames[-1])

    assert first.chart_request.observer == sequence.frames[0].local_observer
    assert last.chart_request.observer == sequence.frames[-1].local_observer
    assert first.orientation.position_angle_deg == 0.0
    assert first.chart_request.frame.position_angle_deg == 0.0
    assert last.orientation.position_angle_deg != 0.0
    assert (
        last.chart_request.frame.position_angle_deg
        == last.orientation.position_angle_deg
    )
    assert all(
        frame.celestial_request.observer.time
        == sequence.celestial_anchor_time
        for frame in sequence.frames
    )


def test_resolved_frame_preserves_explicit_anchor_position_angle(tmp_path):
    request = chart_request(tmp_path / "frames")
    request = replace(
        request,
        frame=replace(request.frame, position_angle_deg=17.5),
    )
    sequence = FixedSkyRotatingHorizonSequenceRequest(
        chart=request,
        timeline=timeline(),
        celestial_anchor_time=timeline().instants[1],
    )

    resolved = resolve_fixed_sky_rotating_horizon_frame(sequence.frames[1])

    assert resolved.orientation.position_angle_deg == 17.5
    assert resolved.chart_request.frame.position_angle_deg == 17.5


def test_resolved_frame_rejects_unproved_chart_families(tmp_path):
    request = chart_request(tmp_path / "frames")
    frame = sequence_frame = FixedSkyRotatingHorizonSequenceRequest(
        chart=request,
        timeline=timeline(),
        celestial_anchor_time=timeline().instants[0],
    ).frames[0]
    unsupported_request = replace(
        sequence_frame.celestial_request,
        family="planisphere",
        frame=ChartFrameRequest(),
    )
    unsupported = replace(frame, celestial_request=unsupported_request)

    with pytest.raises(ValueError, match="currently supports circumpolar"):
        resolve_fixed_sky_rotating_horizon_frame(unsupported)



def test_uncached_reference_renderer_uses_canonical_request_per_frame(
    tmp_path,
    monkeypatch,
):
    sequence = FixedSkyRotatingHorizonSequenceRequest(
        chart=chart_request(tmp_path / "frames"),
        timeline=timeline(),
        celestial_anchor_time=timeline().instants[0],
    )
    rendered = []

    def fake_generate(request, *, configuration=None):
        rendered.append((request, configuration))
        return SimpleNamespace(outputs=(request.product.output,))

    monkeypatch.setattr(
        "wenu.charts.request_generation.generate_chart_request",
        fake_generate,
    )

    result = generate_fixed_sky_rotating_horizon_sequence(sequence)

    assert result.outputs == tuple(
        frame.expected_output for frame in sequence.frames
    )
    assert tuple(
        request.observer.time for request, _ in rendered
    ) == sequence.timeline.instants
    assert rendered[0][0].frame.position_angle_deg == 0.0
    assert rendered[-1][0].frame.position_angle_deg != 0.0
    assert all(configuration is None for _, configuration in rendered)


def test_uncached_reference_renderer_rejects_unexpected_output(
    tmp_path,
    monkeypatch,
):
    sequence = FixedSkyRotatingHorizonSequenceRequest(
        chart=chart_request(tmp_path / "frames"),
        timeline=timeline(),
        celestial_anchor_time=timeline().instants[0],
    )

    monkeypatch.setattr(
        "wenu.charts.request_generation.generate_chart_request",
        lambda request, **kwargs: SimpleNamespace(
            outputs=(tmp_path / "wrong.png",)
        ),
    )

    with pytest.raises(RuntimeError, match="unexpected output"):
        generate_fixed_sky_rotating_horizon_sequence(sequence)


def test_reuse_mode_loads_one_unbound_sphere_and_closes_each_observer(
    tmp_path,
    monkeypatch,
):
    sequence = FixedSkyRotatingHorizonSequenceRequest(
        chart=chart_request(tmp_path / "frames"),
        timeline=timeline(),
        celestial_anchor_time=timeline().instants[0],
    )
    sky = SimpleNamespace(
        observer=None,
        load_profile=CANONICAL_MAXIMAL_SPHERE_PROFILE,
    )
    loaded = []
    observers = []
    rendered = []

    class FrameObserver:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.closed = False
            observers.append(self)

        def close(self):
            self.closed = True

    monkeypatch.setattr(
        "wenu.sky.maximal_sphere.generate_celestial_sphere",
        lambda: loaded.append(True) or sky,
    )
    monkeypatch.setattr(
        "wenu.charts.fixed_sky_sequence.Observer",
        FrameObserver,
    )
    monkeypatch.setattr(
        "wenu.charts.fixed_sky_sequence.resolve_fixed_sky_rotating_horizon_frame",
        lambda frame: SimpleNamespace(
            chart_request=replace(
                frame.celestial_request,
                observer=frame.local_observer,
            ),
            orientation=object(),
        ),
    )

    def generate(request, *, configuration, sky, observer):
        rendered.append((request, configuration, sky, observer))
        return SimpleNamespace(outputs=(request.product.output,))

    monkeypatch.setattr(
        "wenu.charts.request_generation.generate_chart_request",
        generate,
    )

    result = generate_fixed_sky_rotating_horizon_sequence(
        sequence,
        execution="reuse_loaded_sphere",
    )

    assert result.execution is FixedSkySequenceExecution.REUSE_LOADED_SPHERE
    assert result.canonical_sphere_build_count == 1
    assert result.reused_load_profile is CANONICAL_MAXIMAL_SPHERE_PROFILE
    assert loaded == [True]
    assert len(rendered) == sequence.frame_count
    assert all(item[2] is sky for item in rendered)
    assert [item[3] for item in rendered] == observers
    assert all(observer.closed for observer in observers)
    assert sky.observer is None

    def fail(request, *, configuration, sky, observer):
        del request, configuration, sky, observer
        raise RuntimeError("render failure")

    monkeypatch.setattr(
        "wenu.charts.request_generation.generate_chart_request",
        fail,
    )
    with pytest.raises(RuntimeError, match="render failure"):
        generate_fixed_sky_rotating_horizon_sequence(
            sequence,
            execution=FixedSkySequenceExecution.REUSE_LOADED_SPHERE,
        )
    assert observers[-1].closed is True


def test_fixed_sky_execution_mode_is_explicit_and_consistent(tmp_path):
    sequence = FixedSkyRotatingHorizonSequenceRequest(
        chart=chart_request(tmp_path / "frames"),
        timeline=timeline(),
        celestial_anchor_time=timeline().instants[0],
    )

    with pytest.raises(ValueError, match="execution must be"):
        generate_fixed_sky_rotating_horizon_sequence(
            sequence,
            execution="automatic",
        )

    with pytest.raises(ValueError, match="build count contradicts"):
        FixedSkyRotatingHorizonGeneration(
            frames=(),
            execution=FixedSkySequenceExecution.REUSE_LOADED_SPHERE,
            canonical_sphere_build_count=2,
        )
