"""50S.3B reports and drawable SatChecker sampled-candidate evidence."""

from io import BytesIO
import json

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from wenu.coordinates import CoordinateSpec, PositionStatus
from wenu.geometry.spherical import SphericalCurves, SphericalPoints
from wenu.projections.stereographic import StereographicProjection
from wenu.rendering import MatplotlibRenderer
from wenu.satellite_crossings import (
    InclusiveTimeInterval,
    SatelliteCrossingCandidate,
    SatelliteFieldOfView,
    SatelliteIdentity,
    SatelliteObserver,
)
from wenu.satellite_presentations import (
    SATELLITE_PRESENTATION_PRODUCT,
    SATELLITE_PRESENTATION_SCHEMA_VERSION,
    SATELLITE_PRESENTATION_STATUS,
    SatCheckerPresentation,
)
from wenu.satchecker import (
    SATCHECKER_PROVIDER,
    SatCheckerCandidateEvidence,
    SatCheckerQuery,
    SatCheckerReceipt,
    SatCheckerResponse,
    SatCheckerSample,
    SatCheckerTaskState,
)
from wenu.sky.celestial_sphere import CelestialSphere
from wenu.sky.realization import LayerRealizationContext
from wenu.sky.satellite_candidate_layer import (
    SatelliteCandidateSamplesLayer,
    SatelliteCandidateTrackLayer,
)
from wenu.sky.semantic_identity import semantic_layer_identity


DIGEST = "a" * 64


def query():
    observer = SatelliteObserver(
        "la-ligua",
        -71.230289,
        -32.443342,
        52.0,
        earth_orientation_policy="astropy",
    )
    field = SatelliteFieldOfView(
        "crux-field",
        157.5,
        -60.0,
        3.0,
        CoordinateSpec(
            frame="icrs",
            origin="topocentric-direction",
            position_status=PositionStatus.GEOMETRIC,
            instant="2026-09-15T01:00:00Z",
            time_scale="utc",
            provider="SatChecker request",
        ),
    )
    interval = InclusiveTimeInterval(
        "2026-09-15T01:00:00Z",
        "2026-09-15T01:00:02Z",
    )
    return SatCheckerQuery(
        observer,
        field,
        interval,
        2461298.5416667,
        2.0,
        "test IERS identity",
    )


def sample(index, *, illuminated=None):
    return SatCheckerSample(
        f"2026-09-15T01:00:0{index}Z",
        2461298.5416667 + index / 86400.0,
        157.0 + 0.2 * index,
        -60.2 + 0.1 * index,
        0.7 - 0.2 * index,
        altitude_deg=45.0 + index,
        azimuth_deg=120.0 + index,
        range_km=550.0 - index,
        illuminated=illuminated,
    )


def evidence(identifier=123456, *, samples=None, name="TEST SAT"):
    value = query()
    candidate = SatelliteCrossingCandidate(
        SatelliteIdentity(
            identifier,
            object_name=name,
            international_designator="2026-001A",
            classification="U",
        ),
        value.observer,
        value.field_of_view,
        value.interval,
        SATCHECKER_PROVIDER,
        orbit_solution_id="omm",
        element_epoch="2026-09-15T00:00:00Z",
        provenance=("synthetic provider specimen",),
        warnings=("sampled candidate; not an exact crossing",),
    )
    return SatCheckerCandidateEvidence(
        candidate,
        tuple((sample(0), sample(1, illuminated=True)) if samples is None else samples),
        DIGEST,
        "1.8.0",
    )


def receipt():
    return SatCheckerReceipt(
        query().endpoint,
        "2026-09-15T12:00:00Z",
        200,
        "application/json",
        (("content-type", "application/json"),),
        b'{"status":"SUCCESS"}',
    )


def response(*values, state=SatCheckerTaskState.SUCCESS):
    return SatCheckerResponse(
        state,
        "task-1",
        None,
        "complete",
        receipt(),
        tuple(values),
    )


def product_spec():
    return CoordinateSpec(
        frame="icrs",
        origin="topocentric-direction",
        position_status=PositionStatus.GEOMETRIC,
        provider="Wenu chart",
    )


def test_report_is_versioned_deterministic_and_sorted_by_norad_identity():
    high = evidence(900002, name="HIGH")
    low = evidence(100001, name="LOW")
    report = SatCheckerPresentation(
        query(),
        response(high, low),
        cache_provenance=("content-addressed cache hit",),
    )

    first = report.to_json()
    second = report.to_json()
    document = json.loads(first)

    assert first == second
    assert first.endswith("\n")
    assert document["schema_version"] == SATELLITE_PRESENTATION_SCHEMA_VERSION
    assert document["product"] == SATELLITE_PRESENTATION_PRODUCT
    assert document["scientific_status"] == SATELLITE_PRESENTATION_STATUS
    assert document["sample_coordinate_spec"]["frame"] == "icrs"
    assert document["sample_coordinate_spec"]["origin"] == (
        "topocentric-direction"
    )
    assert [
        value["identity"]["norad_catalog_id"]
        for value in document["candidates"]
    ] == [100001, 900002]
    assert document["response"]["candidate_count"] == 2
    assert document["response"]["sample_count"] == 4
    assert document["response"]["receipt"]["response_sha256"] == (
        receipt().body_sha256
    )
    assert document["response"]["cache_provenance"] == [
        "content-addressed cache hit"
    ]
    assert document["candidates"][0]["samples"][1][
        "provider_illuminated"
    ] is True


def test_human_report_is_explicitly_candidate_only_and_uses_same_counts():
    report = SatCheckerPresentation(query(), response(evidence()))
    text = report.to_text()

    assert text.startswith(SATELLITE_PRESENTATION_STATUS)
    assert "Evidence: 1 candidates, 2 samples" in text
    assert "Candidate NORAD 123456: TEST SAT" in text
    assert "2026-09-15T01:00:01Z UTC" in text
    assert "provider illuminated true" in text
    assert "Entry:" not in text
    assert "Exit:" not in text
    assert "Closest approach:" not in text


def test_terminal_failure_report_has_no_candidate_geometry_claim():
    value = SatCheckerPresentation(
        query(),
        response(state=SatCheckerTaskState.FAILURE),
    )
    document = value.document

    assert document["response"]["state"] == "FAILURE"
    assert document["response"]["candidate_count"] == 0
    assert document["candidates"] == []


def test_presentation_rejects_nonterminal_mismatched_and_duplicate_evidence():
    pending = response(state=SatCheckerTaskState.PENDING)
    with pytest.raises(ValueError, match="terminal"):
        SatCheckerPresentation(query(), pending)

    one = evidence()
    with pytest.raises(ValueError, match="unique NORAD"):
        SatCheckerPresentation(query(), response(one, one))

    other_query = query()
    other_field = SatelliteFieldOfView(
        "other-field",
        157.5,
        -60.0,
        3.0,
        other_query.field_of_view.coordinate_spec,
    )
    mismatched = SatCheckerQuery(
        other_query.observer,
        other_field,
        other_query.interval,
        other_query.start_time_ut1_jd,
        other_query.duration_seconds,
        other_query.earth_orientation_identity,
    )
    with pytest.raises(ValueError, match="does not match"):
        SatCheckerPresentation(mismatched, response(one))


def test_track_layer_returns_one_open_curve_without_crossing_events():
    value = evidence()
    layer = SatelliteCandidateTrackLayer(value)
    geometry = layer.realize(
        LayerRealizationContext(product_spec()),
        observer=None,
    )

    assert isinstance(geometry, SphericalCurves)
    assert len(geometry) == 1
    assert not geometry.closed[0]
    np.testing.assert_allclose(geometry.lon_deg[0], [157.0, 157.2])
    np.testing.assert_allclose(geometry.lat_deg[0], [-60.2, -60.1])
    assert geometry.coordinate_spec == product_spec()
    assert geometry.metadata["sample_order"] == "provider temporal order"
    assert geometry.metadata["continuous_containment_verified"] is False
    assert geometry.metadata["exact_crossing_events"] is False
    assert "entry" not in geometry.metadata
    assert "exit" not in geometry.metadata
    assert "closest_approach" not in geometry.metadata


def test_singleton_track_is_one_point_and_never_an_invented_segment():
    value = evidence(samples=(sample(0),))
    geometry = SatelliteCandidateTrackLayer(value).realize(
        LayerRealizationContext(product_spec()),
        observer=None,
    )

    assert isinstance(geometry, SphericalPoints)
    assert len(geometry) == 1
    assert geometry.metadata["geometry_status"] == (
        "singleton sample; no segment"
    )


def test_sample_layer_retains_order_utc_labels_and_stable_identifiers():
    value = evidence()
    geometry = SatelliteCandidateSamplesLayer(value).realize(
        LayerRealizationContext(product_spec()),
        observer=None,
    )

    assert isinstance(geometry, SphericalPoints)
    assert list(geometry.labels) == [
        "2026-09-15T01:00:00Z",
        "2026-09-15T01:00:01Z",
    ]
    assert list(geometry.ids) == [
        "norad_123456__sample_20260915t010000z",
        "norad_123456__sample_20260915t010001z",
    ]
    assert geometry.metadata["utc_labels"] is True
    assert geometry.metadata["provider_illumination"] == (None, True)


def test_sample_labels_can_be_suppressed_without_changing_evidence():
    geometry = SatelliteCandidateSamplesLayer(
        evidence(),
        label_times=False,
    ).realize(
        LayerRealizationContext(product_spec()),
        observer=None,
    )

    assert list(geometry.labels) == [None, None]
    assert len(geometry) == 2
    assert geometry.metadata["sample_instants_utc"] == (
        "2026-09-15T01:00:00Z",
        "2026-09-15T01:00:01Z",
    )


def test_satellite_semantics_are_stable_by_full_norad_identifier():
    track = semantic_layer_identity(
        SatelliteCandidateTrackLayer(evidence(name="RENAMED"))
    )
    samples = semantic_layer_identity(
        SatelliteCandidateSamplesLayer(evidence(name="RENAMED"))
    )

    assert track.semantic_path_text == (
        "sky/artificial_satellites/satchecker_candidates/"
        "norad_123456/sampled_track"
    )
    assert track.svg_id == (
        "satchecker-norad-123456-sampled-track"
    )
    assert samples.semantic_path_text == (
        "sky/artificial_satellites/satchecker_candidates/"
        "norad_123456/samples"
    )
    assert samples.svg_id == "satchecker-norad-123456-samples"
    assert "RENAMED" in track.display_name


def test_layers_require_normalized_evidence_context_and_no_options():
    with pytest.raises(TypeError, match="SatCheckerCandidateEvidence"):
        SatelliteCandidateTrackLayer(object())
    layer = SatelliteCandidateTrackLayer(evidence())
    with pytest.raises(TypeError, match="LayerRealizationContext"):
        layer.realize(object(), observer=None)
    with pytest.raises(TypeError, match="no geometry options"):
        layer.realize(
            LayerRealizationContext(product_spec()),
            observer=None,
            selected=True,
        )
    with pytest.raises(RuntimeError, match="LayerRealizationContext"):
        layer.spherical_geometry(None)



def test_candidate_layers_use_canonical_chart_pipeline_and_all_backends():
    track = SatelliteCandidateTrackLayer(evidence())
    samples = SatelliteCandidateSamplesLayer(
        evidence(),
        label_times=False,
    )
    sphere = CelestialSphere(object())
    sphere.extend((track, samples))
    figure, axes = plt.subplots()

    result = sphere.draw_chart(
        projection=StereographicProjection(
            radius=2.0,
            flip_ew=False,
        ),
        renderer=MatplotlibRenderer(axes),
        realization_context=LayerRealizationContext(product_spec()),
        layer_options={
            track: {
                "style": {
                    "color": "black",
                    "linewidth": 1.0,
                },
            },
            samples: {
                "style": {
                    "c": "black",
                    "s": 8.0,
                },
            },
        },
    )

    assert len(result.layers) == 2
    assert result.layers[0].semantic_identity.semantic_path_text.endswith(
        "norad_123456/sampled_track"
    )
    assert result.layers[1].semantic_identity.semantic_path_text.endswith(
        "norad_123456/samples"
    )
    assert result.layers[0].semantic_artists
    assert result.layers[1].semantic_artists

    products = {}
    for format_ in ("png", "pdf", "svg"):
        stream = BytesIO()
        figure.savefig(stream, format=format_)
        products[format_] = stream.getvalue()
    assert products["png"].startswith(b"\x89PNG")
    assert products["pdf"].startswith(b"%PDF")
    assert b"satchecker-norad-123456-sampled-track" in products["svg"]
    assert b"satchecker-norad-123456-samples" in products["svg"]
    plt.close(figure)


def test_presentation_rejects_untyped_response_evidence():
    malformed = SatCheckerResponse(
        SatCheckerTaskState.SUCCESS,
        "task-1",
        None,
        "complete",
        receipt(),
        (object(),),
    )
    with pytest.raises(TypeError, match="SatCheckerCandidateEvidence"):
        SatCheckerPresentation(query(), malformed)
