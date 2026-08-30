"""Validate 49I.2A apparent Moon direction and topocentric parallax."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from skyfield.api import wgs84

from wenu.observer import DEFAULT_DATA_DIRECTORY, DEFAULT_EPHEMERIS, Observer
from wenu.skyfield_ephemeris import (
    SkyfieldApparentDirectionRealizer,
    SkyfieldEphemerisStateSource,
    skyfield_observer_barycentric_state,
)
from wenu.solar_system_directions import (
    AstrometricDirectionRealizer,
    AstrometricDirectionRequest,
)

INSTANT = "2026-08-30T00:00:00Z"
TARGET = "moon"
CENTRE = "solar system barycenter"


def _wenu_direction(observer, source):
    observer_state = skyfield_observer_barycentric_state(
        observer,
        source=source,
    )
    request = AstrometricDirectionRequest(
        target=TARGET,
        centre=CENTRE,
        reception_instant=observer.t_astropy.isot,
        reception_time_scale=observer.t_astropy.scale,
    )
    astrometric = AstrometricDirectionRealizer().direction(
        source,
        request,
        observer_state,
    )
    apparent = SkyfieldApparentDirectionRealizer().direction(
        astrometric,
        observer=observer,
        source=source,
    )
    return observer_state, request, astrometric, apparent


def _observer_at_height(observer, height_m):
    location = wgs84.latlon(
        latitude_degrees=observer.lat_deg,
        longitude_degrees=observer.lon_deg,
        elevation_m=height_m,
    )
    return SimpleNamespace(
        ephemeris=observer.ephemeris,
        t=observer.t,
        t_astropy=observer.t_astropy,
        skyfield=observer.earth + location,
        lat_deg=observer.lat_deg,
        lon_deg=observer.lon_deg,
        elevation_m=float(height_m),
        location_name=f"La Ligua height {height_m:.0f} m",
    )


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
        state, request, astrometric, apparent = _wenu_direction(
            observer,
            source,
        )

        moon = observer.ephemeris[TARGET]
        direct_topocentric = observer.skyfield.at(observer.t).observe(
            moon
        ).apparent()
        direct_geocentric = observer.earth.at(observer.t).observe(
            moon
        ).apparent()
        direct_ra, direct_dec, _ = direct_topocentric.radec()
        direct_ra_deg = float(direct_ra.hours) * 15.0
        direct_dec_deg = float(direct_dec.degrees)
        ra_residual_deg = apparent.geometry.lon_deg[0] - direct_ra_deg
        dec_residual_deg = apparent.geometry.lat_deg[0] - direct_dec_deg
        parallax_deg = float(
            direct_topocentric.separation_from(direct_geocentric).degrees
        )

        zero_height = _observer_at_height(observer, 0.0)
        _, _, _, zero_apparent = _wenu_direction(zero_height, source)
        height_shift_ra_deg = (
            apparent.geometry.lon_deg[0]
            - zero_apparent.geometry.lon_deg[0]
        )
        height_shift_dec_deg = (
            apparent.geometry.lat_deg[0]
            - zero_apparent.geometry.lat_deg[0]
        )
        height_shift_norm_deg = (
            height_shift_ra_deg * height_shift_ra_deg
            + height_shift_dec_deg * height_shift_dec_deg
        ) ** 0.5

        print(f"model: {source.resource.model}")
        print(f"file: {source.resource.filename}")
        print(f"sha256: {source.resource.sha256}")
        print(f"observer: {state.observer_id}")
        print(
            "observer geodetic: "
            f"lat {observer.lat_deg:.9f} deg, "
            f"lon {observer.lon_deg:.9f} deg, "
            f"height {observer.elevation_m:.3f} m"
        )
        print(f"reception: {request.reception_instant} UTC")
        print(
            "emission: "
            f"{astrometric.emission_instant} "
            f"{astrometric.emission_time_scale.upper()}"
        )
        print(f"iterations: {astrometric.iterations}")
        print(f"target NAIF ID: {astrometric.target_provider_id}")
        print(f"centre NAIF ID: {state.provider_centre_id}")
        print(f"distance AU: {astrometric.distance_au:.16g}")
        print(f"light time days: {astrometric.light_time_days:.16g}")
        print(
            "deflector NAIF IDs: "
            f"{apparent.policy.deflector_naif_ids}"
        )
        print(
            "corrections: "
            f"{sorted(apparent.geometry.coordinate_spec.corrections)}"
        )
        print(f"apparent ICRS RA deg: {apparent.geometry.lon_deg[0]:.16g}")
        print(f"apparent ICRS Dec deg: {apparent.geometry.lat_deg[0]:.16g}")
        print(f"RA residual deg: {ra_residual_deg:.3e}")
        print(f"Dec residual deg: {dec_residual_deg:.3e}")
        print(f"topocentric-geocentric parallax deg: {parallax_deg:.9e}")
        print(f"52m-minus-0m RA deg: {height_shift_ra_deg:.9e}")
        print(f"52m-minus-0m Dec deg: {height_shift_dec_deg:.9e}")
        print(f"52m-minus-0m norm deg: {height_shift_norm_deg:.9e}")

        assert astrometric.target_provider_id == "301"
        assert state.provider_centre_id == "0"
        assert abs(ra_residual_deg) <= 1.0e-10
        assert abs(dec_residual_deg) <= 1.0e-10
        assert parallax_deg > 0.1
        assert height_shift_norm_deg > 0.0


if __name__ == "__main__":
    main()
