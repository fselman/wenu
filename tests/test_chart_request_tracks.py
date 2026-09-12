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
)
from wenu.sky.celestial_sphere import CelestialSphere
from wenu.sky.ceres import CERES_BODY
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
