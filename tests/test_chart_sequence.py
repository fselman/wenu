"""Canonical observer-time sequence planning and orchestration tests."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
import struct

import pytest

import wenu
import wenu.charts.sequence as sequence_module
from wenu.charts.product_options import ChartProductOptions
from wenu.charts.request import (
    ChartFrameRequest,
    ChartObserverRequest,
    ChartRequest,
)
from wenu.charts.request_generation import ChartRequestGeneration
from wenu.charts.sequence import (
    ObserverTimeChartSequenceFrameResult,
    ObserverTimeChartSequenceRequest,
    generate_observer_time_chart_sequence,
)
from wenu.configuration import load_configuration_defaults
from wenu.output_policy import OutputFormat
from wenu.temporal import PlaybackSpec, TemporalTimeline


def test_sequence_rejects_stellar_reports_before_rendering(tmp_path):
    request = replace(chart_request(tmp_path / "frames"), stellar_report=True)
    with pytest.raises(ValueError, match="static chart"):
        ObserverTimeChartSequenceRequest(chart=request, timeline=timeline())


def chart_request(output: Path, **product_options):
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
            **product_options,
        ),
    )


def timeline(count=3):
    return TemporalTimeline.uniform(
        datetime(2026, 8, 22, 1, tzinfo=timezone.utc),
        datetime(2026, 8, 22, 3, tzinfo=timezone.utc),
        count,
        display_timezone="America/Santiago",
    )


def _kernel_sequence_environment(monkeypatch):
    """Synthetic observation backend; real kernel, request, draw and saver paths."""
    import numpy as np
    import pandas as pd
    from astropy.time import Time
    from astropy.coordinates import AltAz, EarthLocation, ICRS
    import astropy.units as u
    from stellar_catalogue_fixtures import native_table
    from test_stars import FakeApparent
    from wenu.objects.stars import Stars
    from wenu.sky.celestial_sphere import CelestialSphere
    from wenu.charts import request_generation

    observers, skies, realized = [], [], []

    def observer(**kwargs):
        instant = kwargs["time"]
        site = EarthLocation.from_geodetic(-71 * u.deg, -33 * u.deg, 0 * u.m)
        value = SimpleNamespace(
            utc_datetime=instant, local_datetime=instant, timezone_name="UTC",
            lat_deg=-33.0, lon_deg=-71.0, elevation_m=0.0,
            t_astropy=Time(instant), t=instant, icrs_frame=ICRS(), closed=False,
        )
        value.altaz_frame = AltAz(obstime=value.t_astropy, location=site)

        def observe(target):
            # Deliberately synthetic observation, not an astronomical oracle.
            return FakeApparent(
                np.asarray(target.dec.degrees) + 60,
                (np.asarray(target.ra.hours) * 15 + instant.hour * 15) % 360,
            )

        value.skyfield = SimpleNamespace(at=lambda time: SimpleNamespace(observe=observe))
        value.close = lambda: setattr(value, "closed", True)
        observers.append(value)
        return value

    def sphere(observer, *, profile):
        sky = CelestialSphere(observer)
        sky.load_profile = profile
        stars = Stars(observer, magnitude_limit=5)
        stars.source_catalog = native_table(pd.DataFrame(
            dict(ra_hours=[1.0, 4.0], dec_degrees=[-10.0, -20.0], magnitude=[1.0, 2.0]),
            index=[100, 200],
        ))
        stars.catalog = stars.source_catalog.copy(deep=True)
        sky.stars = sky.add(stars)
        skies.append(sky)
        return sky

    original = Stars.realize

    def realize(self, context, observer, **kwargs):
        result = original(self, context, observer, **kwargs)
        realized.append((context, observer, result))
        return result

    monkeypatch.setattr(request_generation, "Observer", observer)
    monkeypatch.setattr(request_generation, "build_maximal_sphere", sphere)
    monkeypatch.setattr(Stars, "realize", realize)
    return observers, skies, realized


def _kernel_sequence_request(output):
    from wenu.charts.detail import DetailOverrides

    chart = ChartRequest(
        family="planisphere",
        observer=ChartObserverRequest(time="2000-01-01T00:00:00Z", lat_deg=-33, lon_deg=-71),
        product=ChartProductOptions(output=output, output_format=OutputFormat.PNG),
        detail=DetailOverrides(enabled_layers=frozenset({"stars"})),
    )
    return ObserverTimeChartSequenceRequest(chart=chart, timeline=timeline(2))


def test_sequence_real_generator_consumes_kernel_results_at_each_frame_time(tmp_path, monkeypatch):
    import numpy as np
    from wenu_kernel import KernelSession

    observers, skies, realized = _kernel_sequence_environment(monkeypatch)
    planned = _kernel_sequence_request(tmp_path / "baseline")
    baseline = generate_observer_time_chart_sequence(planned)
    first = tuple(result.lon_deg.copy() for _, _, result in realized)
    assert len(first) == 2
    assert not np.array_equal(first[0], first[1])
    assert tuple(observer.utc_datetime for observer in observers) == planned.timeline.instants
    for context, observer, _ in realized:
        assert context.evaluation_instant == observer.t_astropy.utc.isot
        assert context.observation.instant == context.evaluation_instant
        assert context.product_coordinate_spec.instant == context.evaluation_instant
    evaluate = KernelSession.evaluate
    queries = []

    def rotate(session, query):
        queries.append(query)
        batch = evaluate(session, query)
        return replace(batch, states=tuple(replace(state,
            vector=(-state.vector[1], state.vector[0], state.vector[2])) for state in batch.states))

    monkeypatch.setattr(KernelSession, "evaluate", rotate)
    changed = generate_observer_time_chart_sequence(replace(planned,
        chart=replace(planned.chart, product=replace(planned.chart.product, output=tmp_path / "changed"))))
    assert len(queries) == 2
    for before, (_, _, after) in zip(first, realized[2:], strict=True):
        np.testing.assert_allclose(after.lon_deg, (before + 90) % 360, atol=1e-10)
    assert all(a.read_bytes() != b.read_bytes() for a, b in zip(baseline.outputs, changed.outputs, strict=True))
    assert all(value.closed for value in observers)
    assert all(not hasattr(sky, "_active_chart_request_state") for sky in skies)
    assert all(sky.layers == (sky.stars,) for sky in skies)


def test_sequence_kernel_refusal_keeps_partial_manifest_and_resumes_missing_frame(tmp_path, monkeypatch):
    from wenu_kernel import KernelSession
    from wenu.charts.sequence_manifest import read_observer_time_sequence_manifest, SEQUENCE_MANIFEST_NAME

    observers, skies, _ = _kernel_sequence_environment(monkeypatch)
    planned = _kernel_sequence_request(tmp_path / "frames")
    evaluate = KernelSession.evaluate
    calls = []

    def second_refuses(session, query):
        calls.append(query)
        if len(calls) == 2:
            raise RuntimeError("second frame kernel refusal")
        return evaluate(session, query)

    monkeypatch.setattr(KernelSession, "evaluate", second_refuses)
    with pytest.raises(RuntimeError, match="second frame kernel refusal"):
        generate_observer_time_chart_sequence(planned)
    manifest_path = planned.chart.product.output / SEQUENCE_MANIFEST_NAME
    progress = read_observer_time_sequence_manifest(manifest_path)
    assert tuple(frame.is_complete for frame in progress.frames) == (True, False)
    first_bytes = planned.frames[0].expected_output.read_bytes()
    assert not planned.frames[1].expected_output.exists()
    assert all(value.closed for value in observers)
    assert all(not hasattr(sky, "_active_chart_request_state") for sky in skies)
    monkeypatch.setattr(KernelSession, "evaluate", evaluate)
    resumed = generate_observer_time_chart_sequence(planned, restart_policy="resume")
    assert (resumed.rendered_count, resumed.reused_count) == (1, 1)
    assert resumed.outputs[0].read_bytes() == first_bytes
    assert observers[-1].utc_datetime == planned.timeline.instants[1]
    assert all(value.closed for value in observers)



def test_frame_result_has_one_stable_public_name():
    assert (
        ObserverTimeChartSequenceFrameResult.__name__
        == "ObserverTimeChartSequenceFrameResult"
    )
    assert (
        wenu.ObserverTimeChartSequenceFrameResult
        is ObserverTimeChartSequenceFrameResult
    )
    assert not hasattr(
        sequence_module,
        "ObserverTimeObserverTimeChartSequenceFrameResult",
    )

def test_sequence_pairs_one_chart_definition_with_explicit_frames(tmp_path):
    sequence = ObserverTimeChartSequenceRequest(
        chart=chart_request(tmp_path / "frames"),
        timeline=timeline(),
        playback=PlaybackSpec(timedelta(seconds=1.5), 2),
    )

    assert sequence.frame_count == 3
    assert tuple(frame.name for frame in sequence.frames) == (
        "frame-0000.png",
        "frame-0001.png",
        "frame-0002.png",
    )
    assert tuple(frame.expected_output for frame in sequence.frames) == (
        tmp_path / "frames" / "frame-0000.png",
        tmp_path / "frames" / "frame-0001.png",
        tmp_path / "frames" / "frame-0002.png",
    )
    assert tuple(
        frame.request.observer.time for frame in sequence.frames
    ) == sequence.timeline.instants
    assert tuple(
        frame.display_time.isoformat() for frame in sequence.frames
    ) == (
        "2026-08-21T21:00:00-04:00",
        "2026-08-21T22:00:00-04:00",
        "2026-08-21T23:00:00-04:00",
    )


def test_sequence_calls_only_the_canonical_static_generator(
    tmp_path,
    monkeypatch,
):
    sequence = ObserverTimeChartSequenceRequest(
        chart=chart_request(tmp_path / "frames"),
        timeline=timeline(),
    )
    calls = []

    def generator(request):
        calls.append(request)
        request.product.output.parent.mkdir(parents=True, exist_ok=True)
        request.product.output.write_bytes(b"frame")
        return ChartRequestGeneration(
            exports=(SimpleNamespace(output=request.product.output),)
        )

    monkeypatch.setattr(sequence_module, "generate_chart_request", generator)
    result = generate_observer_time_chart_sequence(sequence)

    assert tuple(calls) == tuple(
        frame.request for frame in sequence.frames
    )
    assert result.outputs == tuple(
        tmp_path / "frames" / f"frame-{index:04d}.png"
        for index in range(3)
    )
    assert tuple(
        item.frame.simulation_time for item in result.frames
    ) == sequence.timeline.instants


def test_sequence_requires_one_explicitly_formatted_directory(tmp_path):
    base = chart_request(tmp_path / "frames")

    with pytest.raises(ValueError, match="explicit output format"):
        ObserverTimeChartSequenceRequest(
            chart=ChartRequest(
                observer=base.observer,
                family=base.family,
                frame=base.frame,
                product=ChartProductOptions(output=tmp_path / "frames"),
            ),
            timeline=timeline(),
        )

    with pytest.raises(ValueError, match="must be a directory"):
        ObserverTimeChartSequenceRequest(
            chart=chart_request(tmp_path / "frame.png"),
            timeline=timeline(),
        )

    with pytest.raises(ValueError, match="one chart product"):
        ObserverTimeChartSequenceRequest(
            chart=chart_request(
                tmp_path / "frames",
                all_products=True,
            ),
            timeline=timeline(),
        )


def test_sequence_rejects_static_output_different_from_plan(
    tmp_path,
    monkeypatch,
):
    sequence = ObserverTimeChartSequenceRequest(
        chart=chart_request(tmp_path / "frames"),
        timeline=timeline(count=2),
    )

    def generator(request):
        return ChartRequestGeneration(
            exports=(SimpleNamespace(output=Path("wrong.png")),)
        )

    monkeypatch.setattr(sequence_module, "generate_chart_request", generator)
    with pytest.raises(ValueError, match="do not match"):
        generate_observer_time_chart_sequence(sequence)


@pytest.mark.integration
@pytest.mark.slow
def test_observer_time_sequence_generates_real_canonical_frames(tmp_path):
    sequence = ObserverTimeChartSequenceRequest(
        chart=chart_request(tmp_path / "frames"),
        timeline=TemporalTimeline.uniform(
            datetime(2026, 8, 22, 1, tzinfo=timezone.utc),
            datetime(2026, 8, 22, 7, tzinfo=timezone.utc),
            2,
            display_timezone="America/Santiago",
        ),
    )

    result = generate_observer_time_chart_sequence(sequence)

    assert result.outputs == (
        tmp_path / "frames" / "frame-0000.png",
        tmp_path / "frames" / "frame-0001.png",
    )
    assert all(path.is_file() for path in result.outputs)

    def png_size(path):
        header = path.read_bytes()[:24]
        assert header[:8] == b"\x89PNG\r\n\x1a\n"
        return struct.unpack(">II", header[16:24])

    assert png_size(result.outputs[0]) == png_size(result.outputs[1])
    assert sha256(result.outputs[0].read_bytes()).digest() != sha256(
        result.outputs[1].read_bytes()
    ).digest()

    resumed = generate_observer_time_chart_sequence(
        sequence,
        restart_policy="resume",
    )
    assert resumed.outputs == result.outputs
    assert resumed.rendered_count == 0
    assert resumed.reused_count == 2



def _file_generator(calls):
    def generate(request):
        calls.append(request.product.output)
        request.product.output.parent.mkdir(parents=True, exist_ok=True)
        request.product.output.write_bytes(
            request.observer.time.isoformat().encode("ascii")
        )
        return ChartRequestGeneration(
            exports=(SimpleNamespace(output=request.product.output),)
        )

    return generate


def test_resume_reuses_only_manifest_verified_outputs(
    tmp_path,
    monkeypatch,
):
    planned = ObserverTimeChartSequenceRequest(
        chart=chart_request(tmp_path / "frames"),
        timeline=timeline(count=2),
    )
    first_calls = []
    monkeypatch.setattr(
        sequence_module,
        "generate_chart_request",
        _file_generator(first_calls),
    )
    first = generate_observer_time_chart_sequence(planned)

    assert first.rendered_count == 2
    assert first.reused_count == 0
    assert first.manifest_path.is_file()

    monkeypatch.setattr(
        sequence_module,
        "generate_chart_request",
        lambda request: pytest.fail("verified frame was rendered again"),
    )
    resumed = generate_observer_time_chart_sequence(
        planned,
        restart_policy="resume",
    )

    assert resumed.outputs == first.outputs
    assert resumed.rendered_count == 0
    assert resumed.reused_count == 2
    assert all(frame.generation is None for frame in resumed.frames)


def test_resume_rerenders_an_altered_output_only(tmp_path, monkeypatch):
    planned = ObserverTimeChartSequenceRequest(
        chart=chart_request(tmp_path / "frames"),
        timeline=timeline(count=2),
    )
    monkeypatch.setattr(
        sequence_module,
        "generate_chart_request",
        _file_generator([]),
    )
    first = generate_observer_time_chart_sequence(planned)
    first.outputs[0].write_bytes(b"altered")

    resumed_calls = []
    monkeypatch.setattr(
        sequence_module,
        "generate_chart_request",
        _file_generator(resumed_calls),
    )
    resumed = generate_observer_time_chart_sequence(
        planned,
        restart_policy="resume",
    )

    assert resumed_calls == [first.outputs[0]]
    assert resumed.rendered_count == 1
    assert resumed.reused_count == 1
    assert not resumed.frames[0].reused
    assert resumed.frames[1].reused


def test_resume_checks_same_size_corruption_and_missing_outputs(tmp_path, monkeypatch):
    planned = ObserverTimeChartSequenceRequest(chart=chart_request(tmp_path / "frames"), timeline=timeline())
    monkeypatch.setattr(sequence_module, "generate_chart_request", _file_generator([]))
    first = generate_observer_time_chart_sequence(planned)
    payload = first.outputs[0].read_bytes()
    first.outputs[0].write_bytes(bytes([payload[0] ^ 1]) + payload[1:])
    assert first.outputs[0].stat().st_size == len(payload)
    first.outputs[1].unlink()
    calls = []
    monkeypatch.setattr(sequence_module, "generate_chart_request", _file_generator(calls))
    resumed = generate_observer_time_chart_sequence(planned, restart_policy="resume")
    assert calls == list(first.outputs[:2])
    assert (resumed.rendered_count, resumed.reused_count) == (2, 1)
    assert resumed.outputs[0].read_bytes() == payload


def test_resume_rejects_an_incompatible_manifest_before_rendering(
    tmp_path,
    monkeypatch,
):
    planned = ObserverTimeChartSequenceRequest(
        chart=chart_request(tmp_path / "frames"),
        timeline=timeline(count=2),
    )
    monkeypatch.setattr(
        sequence_module,
        "generate_chart_request",
        _file_generator([]),
    )
    generate_observer_time_chart_sequence(planned)
    incompatible = replace(
        planned,
        chart=replace(planned.chart, title="Different sequence"),
    )
    monkeypatch.setattr(
        sequence_module,
        "generate_chart_request",
        lambda request: pytest.fail("incompatible sequence rendered"),
    )

    with pytest.raises(ValueError, match="incompatible"):
        generate_observer_time_chart_sequence(
            incompatible,
            restart_policy="resume",
        )


def test_restart_renders_every_frame_even_when_manifest_is_complete(
    tmp_path,
    monkeypatch,
):
    planned = ObserverTimeChartSequenceRequest(
        chart=chart_request(tmp_path / "frames"),
        timeline=timeline(count=2),
    )
    monkeypatch.setattr(
        sequence_module,
        "generate_chart_request",
        _file_generator([]),
    )
    generate_observer_time_chart_sequence(planned)
    restart_calls = []
    monkeypatch.setattr(
        sequence_module,
        "generate_chart_request",
        _file_generator(restart_calls),
    )

    restarted = generate_observer_time_chart_sequence(
        planned,
        restart_policy="restart",
    )

    assert restart_calls == list(restarted.outputs)
    assert restarted.rendered_count == 2
    assert restarted.reused_count == 0


def test_sequence_passes_effective_configuration_to_every_static_frame(
    tmp_path,
    monkeypatch,
):
    configuration = load_configuration_defaults()
    planned = ObserverTimeChartSequenceRequest(
        chart=chart_request(tmp_path / "frames"),
        timeline=timeline(count=2),
        configuration=configuration,
    )
    calls = []

    def generator(request, *, configuration=None):
        calls.append((request, configuration))
        request.product.output.parent.mkdir(parents=True, exist_ok=True)
        request.product.output.write_bytes(b"configured frame")
        return ChartRequestGeneration(
            exports=(SimpleNamespace(output=request.product.output),)
        )

    monkeypatch.setattr(sequence_module, "generate_chart_request", generator)

    generate_observer_time_chart_sequence(planned)

    assert tuple(request for request, _ in calls) == tuple(
        frame.request for frame in planned.frames
    )
    assert all(item is configuration for _, item in calls)


def test_sequence_rejects_untranslated_configuration(tmp_path):
    with pytest.raises(TypeError, match="ConfigurationDefaults"):
        ObserverTimeChartSequenceRequest(
            chart=chart_request(tmp_path / "frames"),
            timeline=timeline(),
            configuration={"style": "not translated"},
        )
