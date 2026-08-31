"""Validate 49I.3C.1 physical Venus disk geometry with installed DE440."""

from __future__ import annotations

from math import atan2, cos, degrees, pi, radians, sin
from pathlib import Path

import numpy as np

from wenu.observer import DEFAULT_DATA_DIRECTORY, DEFAULT_EPHEMERIS, Observer
from wenu.sky.venus import VENUS_POINT
from wenu.skyfield_ephemeris import (
    SkyfieldApparentDirectionRealizer,
    SkyfieldEphemerisStateSource,
    skyfield_observer_barycentric_state,
)
from wenu.solar_system_appearance import (
    SolarSystemAppearanceRealizer,
    VENUS_MEAN_RADIUS_KM,
)
from wenu.solar_system_directions import (
    ApparentCorrectionPolicy,
    AstrometricDirectionRealizer,
    AstrometricDirectionRequest,
)
from wenu.solar_system_disk_geometry import (
    DEFAULT_SOLAR_SYSTEM_DISK_SAMPLES,
    SolarSystemDiskGeometryRealizer,
)

INSTANT = "2026-08-30T00:00:00Z"
LIMB_RADIUS_TOLERANCE_ARCSEC = 1.0e-7
ENDPOINT_TOLERANCE_ARCSEC = 1.0e-7
ILLUMINATED_AREA_TOLERANCE = 2.0e-5
POSITION_ANGLE_TOLERANCE_DEG = 1.0e-9


def _direction(observer, source, observer_state, *, target, policy):
    request = AstrometricDirectionRequest(
        target=target,
        centre="solar system barycenter",
        reception_instant=observer.t_astropy.isot,
        reception_time_scale=observer.t_astropy.scale,
    )
    astrometric = AstrometricDirectionRealizer().direction(
        source,
        request,
        observer_state,
    )
    return SkyfieldApparentDirectionRealizer().direction(
        astrometric,
        observer=observer,
        source=source,
        policy=policy,
    )


def _vectors(longitude_deg, latitude_deg):
    longitude = np.radians(np.asarray(longitude_deg, dtype=float))
    latitude = np.radians(np.asarray(latitude_deg, dtype=float))
    cos_latitude = np.cos(latitude)
    return np.column_stack((
        cos_latitude * np.cos(longitude),
        cos_latitude * np.sin(longitude),
        np.sin(latitude),
    ))


def _angular_separation_arcsec(left, right):
    dot = np.clip(np.sum(left * right, axis=-1), -1.0, 1.0)
    cross = np.linalg.norm(np.cross(left, right), axis=-1)
    return np.degrees(np.arctan2(cross, dot)) * 3600.0


def _disk_coordinates(longitude_deg, latitude_deg, appearance):
    longitude = radians(
        float(appearance.apparent_direction.geometry.lon_deg[0])
    )
    latitude = radians(
        float(appearance.apparent_direction.geometry.lat_deg[0])
    )
    centre = np.asarray((
        cos(latitude) * cos(longitude),
        cos(latitude) * sin(longitude),
        sin(latitude),
    ))
    north = np.asarray((
        -sin(latitude) * cos(longitude),
        -sin(latitude) * sin(longitude),
        cos(latitude),
    ))
    east = np.asarray((-sin(longitude), cos(longitude), 0.0))
    angle = radians(appearance.bright_limb_position_angle_deg)
    bright = cos(angle) * north + sin(angle) * east
    perpendicular = -sin(angle) * north + cos(angle) * east

    vectors = _vectors(longitude_deg, latitude_deg)
    dot = np.clip(vectors @ centre, -1.0, 1.0)
    radial = np.arctan2(
        np.linalg.norm(np.cross(centre, vectors), axis=1),
        dot,
    )
    tangent = vectors - dot[:, np.newaxis] * centre
    length = np.linalg.norm(tangent, axis=1)
    unit = np.zeros_like(tangent)
    nonzero = length > 1.0e-15
    unit[nonzero] = tangent[nonzero] / length[nonzero, np.newaxis]
    angular_radius = radians(
        appearance.angular_diameter_arcsec / 7200.0
    )
    fraction = radial / angular_radius
    return (
        fraction * (unit @ bright),
        fraction * (unit @ perpendicular),
    )


def _polygon_area(x, y):
    return 0.5 * abs(
        np.dot(x, np.roll(y, -1))
        - np.dot(y, np.roll(x, -1))
    )


def _position_angle_deg(centre_lon, centre_lat, point_lon, point_lat):
    centre_lon = radians(float(centre_lon))
    centre_lat = radians(float(centre_lat))
    point_lon = radians(float(point_lon))
    point_lat = radians(float(point_lat))
    delta = point_lon - centre_lon
    return degrees(atan2(
        cos(point_lat) * sin(delta),
        (
            sin(point_lat) * cos(centre_lat)
            - cos(point_lat) * sin(centre_lat) * cos(delta)
        ),
    )) % 360.0


def _wrapped_residual(actual, reference):
    return (actual - reference + 180.0) % 360.0 - 180.0


def main():
    path = Path(DEFAULT_DATA_DIRECTORY) / DEFAULT_EPHEMERIS
    if not path.is_file():
        raise SystemExit(
            f"Installed kernel required; refusing download because {path} "
            "does not exist."
        )

    with Observer(
        location="La Ligua",
        time=INSTANT,
        ephemeris_name=DEFAULT_EPHEMERIS,
        data_directory=DEFAULT_DATA_DIRECTORY,
    ) as observer:
        source = SkyfieldEphemerisStateSource.from_observer(observer)
        observer_state = skyfield_observer_barycentric_state(
            observer,
            source=source,
        )
        venus_direction = _direction(
            observer,
            source,
            observer_state,
            target=VENUS_POINT.target,
            policy=VENUS_POINT.correction_policy,
        )
        sun_direction = _direction(
            observer,
            source,
            observer_state,
            target="sun",
            policy=ApparentCorrectionPolicy(),
        )
        appearance = SolarSystemAppearanceRealizer().appearance(
            source,
            venus_direction,
            sun_direction,
            display_name=VENUS_POINT.display_name,
            physical_radius_km=VENUS_MEAN_RADIUS_KM,
            radius_model=(
                "JPL Planetary Physical Parameters mean radius 6051.8 km"
            ),
        )
        geometry = SolarSystemDiskGeometryRealizer().geometry(appearance)

        centre_vector = _vectors(
            geometry.centre.lon_deg,
            geometry.centre.lat_deg,
        )[0]
        limb_vectors = _vectors(
            geometry.limb.lon_deg[0],
            geometry.limb.lat_deg[0],
        )
        limb_radius = _angular_separation_arcsec(
            limb_vectors,
            centre_vector,
        )
        expected_radius = 0.5 * appearance.angular_diameter_arcsec
        limb_residual = limb_radius - expected_radius

        terminator_vectors = _vectors(
            geometry.terminator.lon_deg[0],
            geometry.terminator.lat_deg[0],
        )
        face_vectors = _vectors(
            geometry.illuminated_face.lon_deg[0],
            geometry.illuminated_face.lat_deg[0],
        )
        endpoint_residual = np.asarray((
            _angular_separation_arcsec(
                terminator_vectors[0],
                face_vectors[DEFAULT_SOLAR_SYSTEM_DISK_SAMPLES // 2],
            ),
            _angular_separation_arcsec(
                terminator_vectors[-1],
                face_vectors[0],
            ),
        ))

        face_x, face_y = _disk_coordinates(
            geometry.illuminated_face.lon_deg[0],
            geometry.illuminated_face.lat_deg[0],
            appearance,
        )
        normalized_area = _polygon_area(face_x, face_y) / pi
        area_residual = (
            normalized_area - appearance.illuminated_fraction
        )

        midpoint = DEFAULT_SOLAR_SYSTEM_DISK_SAMPLES // 4
        midpoint_position_angle = _position_angle_deg(
            geometry.centre.lon_deg[0],
            geometry.centre.lat_deg[0],
            geometry.illuminated_face.lon_deg[0][midpoint],
            geometry.illuminated_face.lat_deg[0][midpoint],
        )
        position_angle_residual = _wrapped_residual(
            midpoint_position_angle,
            appearance.bright_limb_position_angle_deg,
        )

        print(f"model: {source.resource.model}")
        print(f"file: {source.resource.filename}")
        print(f"sha256: {source.resource.sha256}")
        print(f"observer: {observer.location_name}")
        print(
            f"reception: {observer.t_astropy.isot} "
            f"{observer.t_astropy.scale.upper()}"
        )
        print(f"samples: {geometry.samples}")
        print(
            "physical angular radius arcsec: "
            f"{expected_radius:.12f}"
        )
        print(
            "maximum limb-radius residual arcsec: "
            f"{np.max(np.abs(limb_residual)):.3e}"
        )
        print(
            "maximum terminator-endpoint residual arcsec: "
            f"{np.max(np.abs(endpoint_residual)):.3e}"
        )
        print(
            "geometry normalized illuminated area: "
            f"{normalized_area:.12f}"
        )
        print(
            "appearance illuminated fraction: "
            f"{appearance.illuminated_fraction:.12f}"
        )
        print(f"illuminated-area residual: {area_residual:.3e}")
        print(
            "bright-limb midpoint position angle deg: "
            f"{midpoint_position_angle:.12f}"
        )
        print(
            "bright-limb position-angle residual deg: "
            f"{position_angle_residual:.3e}"
        )
        print(
            "geometry components: "
            "centre, illuminated_face, limb, terminator"
        )

        assert (
            np.max(np.abs(limb_residual))
            <= LIMB_RADIUS_TOLERANCE_ARCSEC
        )
        assert (
            np.max(np.abs(endpoint_residual))
            <= ENDPOINT_TOLERANCE_ARCSEC
        )
        assert abs(area_residual) <= ILLUMINATED_AREA_TOLERANCE
        assert (
            abs(position_angle_residual)
            <= POSITION_ANGLE_TOLERANCE_DEG
        )


if __name__ == "__main__":
    main()
