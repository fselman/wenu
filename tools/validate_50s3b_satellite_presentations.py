"""Build the network-free 50S.3B report and visual acceptance specimen."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from wenu.antisolar import offset_direction_deg
from wenu.coordinates import CoordinateSpec, PositionStatus
from wenu.geometry.frame import SphericalFrame
from wenu.geometry.spherical import SphericalCurves
from wenu.geometry.viewport import Viewport
from wenu.projections.stereographic import StereographicProjection
from wenu.rendering import MatplotlibRenderer
from wenu.satellite_crossings import (
    InclusiveTimeInterval,
    SatelliteCrossingCandidate,
    SatelliteFieldOfView,
    SatelliteIdentity,
    SatelliteObserver,
)
from wenu.satellite_presentations import SatCheckerPresentation
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
from wenu.sky.sky_layer import SkyLayer


class FieldBoundaryLayer(SkyLayer):
    """Acceptance-only closed FoV boundary through the ordinary layer path."""

    layer_name = "satellite_acceptance_fov"

    def __init__(self, field):
        self.field = field

    def realize(self, context, observer, **geometry_options):
        del observer
        if geometry_options:
            raise TypeError("FieldBoundaryLayer accepts no geometry options.")
        position_angles = np.linspace(0.0, 360.0, 181)
        positions = tuple(
            offset_direction_deg(
                (
                    self.field.center_longitude_deg,
                    self.field.center_latitude_deg,
                ),
                angle,
                self.field.angular_radius_deg,
            )
            for angle in position_angles
        )
        return SphericalCurves(
            lon_deg=(np.asarray([value[0] for value in positions]),),
            lat_deg=(np.asarray([value[1] for value in positions]),),
            coordinate_spec=context.product_coordinate_spec,
            closed=np.asarray((True,)),
            ids=np.asarray(("requested_closed_fov",), dtype=object),
            metadata={"boundary": "requested closed circular FoV"},
        )

    def spherical_geometry(self, observer):
        del observer
        raise RuntimeError("FieldBoundaryLayer requires a realization context.")


def specimen():
    observer = SatelliteObserver(
        "la-ligua",
        -71.230289,
        -32.443342,
        52.0,
        earth_orientation_policy="astropy",
    )
    coordinate_spec = CoordinateSpec(
        frame="icrs",
        origin="topocentric-direction",
        position_status=PositionStatus.GEOMETRIC,
        instant="2026-09-15T01:00:00Z",
        time_scale="utc",
        provider="synthetic 50S.3B acceptance specimen",
    )
    field = SatelliteFieldOfView(
        "synthetic-field",
        157.5,
        -60.0,
        3.0,
        coordinate_spec,
    )
    interval = InclusiveTimeInterval(
        "2026-09-15T01:00:00Z",
        "2026-09-15T01:00:04Z",
    )
    query = SatCheckerQuery(
        observer,
        field,
        interval,
        2461298.5416667,
        4.0,
        "synthetic no-network EOP identity",
    )
    candidate = SatelliteCrossingCandidate(
        SatelliteIdentity(
            123456,
            object_name="SYNTHETIC SAT",
            international_designator="2026-001A",
        ),
        observer,
        field,
        interval,
        SATCHECKER_PROVIDER,
        orbit_solution_id="synthetic-omm",
        element_epoch="2026-09-15T00:00:00Z",
        provenance=("synthetic 50S.3B visual specimen",),
        warnings=("sampled candidate; not an exact crossing",),
    )
    longitudes = (151.6, 155.5, 159.5, 163.4)
    distances = (2.95, 1.0, 1.0, 2.95)
    samples = tuple(
        SatCheckerSample(
            f"2026-09-15T01:00:0{index}Z",
            2461298.5416667 + index / 86400.0,
            longitude,
            -60.0,
            distance,
            illuminated=(index % 2 == 1),
        )
        for index, (longitude, distance) in enumerate(
            zip(longitudes, distances)
        )
    )
    receipt = SatCheckerReceipt(
        query.endpoint,
        "2026-09-15T12:00:00Z",
        200,
        "application/json",
        (("content-type", "application/json"),),
        b'{"status":"SUCCESS","specimen":"50S.3B"}',
    )
    evidence = SatCheckerCandidateEvidence(
        candidate,
        samples,
        receipt.body_sha256,
        "synthetic-1",
    )
    response = SatCheckerResponse(
        SatCheckerTaskState.SUCCESS,
        "synthetic-task",
        None,
        "network-free acceptance specimen",
        receipt,
        (evidence,),
    )
    return query, response, evidence


def build(output_directory):
    output_directory.mkdir(parents=True, exist_ok=True)
    query, response, evidence = specimen()
    presentation = SatCheckerPresentation(
        query,
        response,
        cache_provenance=("synthetic in-memory evidence; no cache read",),
    )
    (output_directory / "satellite_candidate_report.txt").write_text(
        presentation.to_text(),
        encoding="utf-8",
    )
    (output_directory / "satellite_candidate_report.json").write_text(
        presentation.to_json(),
        encoding="utf-8",
    )

    product_spec = CoordinateSpec(
        frame="icrs",
        origin="topocentric-direction",
        position_status=PositionStatus.GEOMETRIC,
        provider="Wenu 50S.3B acceptance chart",
    )
    context = LayerRealizationContext(product_spec)
    projection = StereographicProjection(
        radius=2.0,
        flip_ew=True,
        frame=SphericalFrame(
            query.field_of_view.center_longitude_deg,
            query.field_of_view.center_latitude_deg,
        ),
    )
    extent = projection.projected_radius(3.6)
    viewport = Viewport.centered(
        width=2.0 * extent,
        height=2.0 * extent,
    )
    boundary = FieldBoundaryLayer(query.field_of_view)
    track = SatelliteCandidateTrackLayer(evidence)
    points = SatelliteCandidateSamplesLayer(evidence, label_times=False)
    sphere = CelestialSphere(object())
    sphere.extend((boundary, track, points))

    figure, axes = plt.subplots(figsize=(7.0, 7.0), constrained_layout=True)
    axes.set_facecolor("#f6f4ee")
    sphere.draw_chart(
        projection=projection,
        renderer=MatplotlibRenderer(axes),
        realization_context=context,
        viewport=viewport,
        layer_options={
            boundary: {
                "style": {
                    "color": "#333333",
                    "linewidth": 1.2,
                    "linestyle": "--",
                    "zorder": 2,
                },
            },
            track: {
                "style": {
                    "color": "#b21f2d",
                    "linewidth": 2.0,
                    "zorder": 4,
                },
            },
            points: {
                "style": {
                    "c": "#b21f2d",
                    "s": 28.0,
                    "zorder": 5,
                },
            },
        },
    )
    projected = projection.project_spherical(
        [sample.right_ascension_deg for sample in evidence.samples],
        [sample.declination_deg for sample in evidence.samples],
    )
    for index, (x, y, sample) in enumerate(
        zip(projected[0], projected[1], evidence.samples)
    ):
        axes.annotate(
            f"{index}: {sample.instant_utc[11:19]} UTC",
            (x, y),
            xytext=(6, 5 if index % 2 == 0 else -13),
            textcoords="offset points",
            fontsize=8,
            color="#5a1018",
        )
    axes.set_aspect("equal")
    axes.set_xticks(())
    axes.set_yticks(())
    axes.set_title(
        "SatChecker sampled candidate evidence — not verified crossings",
        fontsize=11,
        pad=28,
    )
    axes.text(
        0.5,
        1.015,
        (
            f"FoV: {query.field_of_view.field_id} — closed circular, "
            f"ICRS center "
            f"({query.field_of_view.center_longitude_deg:.3f}°, "
            f"{query.field_of_view.center_latitude_deg:.3f}°), "
            f"radius {query.field_of_view.angular_radius_deg:.3f}°"
        ),
        transform=axes.transAxes,
        ha="center",
        va="bottom",
        fontsize=8.5,
    )
    axes.text(
        0.5,
        0.02,
        "Dashed circle: requested closed FoV   •   red: supplied samples in time order",
        transform=axes.transAxes,
        ha="center",
        va="bottom",
        fontsize=8,
    )
    for format_ in ("png", "pdf", "svg"):
        figure.savefig(
            output_directory / f"satellite_candidate_chart.{format_}",
            format=format_,
            dpi=180,
        )
    plt.close(figure)
    return tuple(sorted(output_directory.iterdir()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for the network-free acceptance products.",
    )
    args = parser.parse_args()
    for path in build(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
