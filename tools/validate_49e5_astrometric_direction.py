"""Validate 49E.5 astrometric Venus direction against direct Skyfield."""

from __future__ import annotations

from pathlib import Path

from astropy.time import Time, TimeDelta

from wenu.observer import DEFAULT_DATA_DIRECTORY, DEFAULT_EPHEMERIS, Observer
from wenu.skyfield_ephemeris import (
    SkyfieldEphemerisStateSource,
    skyfield_observer_barycentric_state,
)
from wenu.solar_system_directions import (
    LIGHT_SPEED_AU_PER_DAY,
    AstrometricDirectionRealizer,
    AstrometricDirectionRequest,
)

INSTANT = "2026-08-30T00:00:00Z"


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
        request = AstrometricDirectionRequest(
            target="venus",
            centre="solar system barycenter",
            reception_instant=observer.t_astropy.isot,
            reception_time_scale=observer.t_astropy.scale,
        )
        result = AstrometricDirectionRealizer().direction(
            source,
            request,
            observer_state,
        )

        direct = observer.skyfield.at(observer.t).observe(
            observer.ephemeris["venus"]
        )
        ra, dec, distance = direct.radec()
        direct_ra_deg = float(ra.hours) * 15.0
        direct_dec_deg = float(dec.degrees)
        direct_distance_au = float(distance.au)
        direct_light_time_days = float(direct.light_time)

        ra_residual_deg = result.geometry.lon_deg[0] - direct_ra_deg
        dec_residual_deg = result.geometry.lat_deg[0] - direct_dec_deg
        distance_residual_au = result.distance_au - direct_distance_au
        light_time_residual_days = (
            result.light_time_days - direct_light_time_days
        )
        distance_tolerance_au = (
            LIGHT_SPEED_AU_PER_DAY * request.light_time_tolerance_days
        )

        expected_emission = Time(observer.t_astropy) - TimeDelta(
            direct_light_time_days,
            format="jd",
        )
        actual_emission = Time(
            result.emission_instant,
            scale=result.emission_time_scale,
        )
        emission_residual_days = float(
            (actual_emission - expected_emission).to_value("day")
        )

        print(f"model: {source.resource.model}")
        print(f"file: {source.resource.filename}")
        print(f"sha256: {source.resource.sha256}")
        print(f"observer: {observer_state.observer_id}")
        print(f"reception: {request.reception_instant} UTC")
        print(
            "emission: "
            f"{result.emission_instant} "
            f"{result.emission_time_scale.upper()}"
        )
        print(f"iterations: {result.iterations}")
        print(f"distance AU: {result.distance_au:.16g}")
        print(f"light time days: {result.light_time_days:.16g}")
        print(f"ICRS RA deg: {result.geometry.lon_deg[0]:.16g}")
        print(f"ICRS Dec deg: {result.geometry.lat_deg[0]:.16g}")
        print(f"RA residual deg: {ra_residual_deg:.3e}")
        print(f"Dec residual deg: {dec_residual_deg:.3e}")
        print(f"distance residual AU: {distance_residual_au:.3e}")
        print(f"distance tolerance AU: {distance_tolerance_au:.3e}")
        print(f"light-time residual days: {light_time_residual_days:.3e}")
        print(f"emission residual days: {emission_residual_days:.3e}")

        assert abs(ra_residual_deg) <= 1.0e-10
        assert abs(dec_residual_deg) <= 1.0e-10
        assert abs(distance_residual_au) <= distance_tolerance_au
        assert abs(light_time_residual_days) <= 1.0e-12
        assert abs(emission_residual_days) <= 1.0e-12


if __name__ == "__main__":
    main()
