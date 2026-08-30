"""Validate 49E.6 apparent Venus direction against direct Skyfield."""

from __future__ import annotations

from pathlib import Path

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
        astrometric = AstrometricDirectionRealizer().direction(
            source,
            request,
            observer_state,
        )
        result = SkyfieldApparentDirectionRealizer().direction(
            astrometric,
            observer=observer,
            source=source,
        )

        direct_astrometric = observer.skyfield.at(observer.t).observe(
            observer.ephemeris["venus"]
        )
        direct = direct_astrometric.apparent()
        ra, dec, _ = direct.radec()
        direct_ra_deg = float(ra.hours) * 15.0
        direct_dec_deg = float(dec.degrees)
        ra_residual_deg = result.geometry.lon_deg[0] - direct_ra_deg
        dec_residual_deg = result.geometry.lat_deg[0] - direct_dec_deg
        shift_ra_deg = (
            result.geometry.lon_deg[0] - astrometric.geometry.lon_deg[0]
        )
        shift_dec_deg = (
            result.geometry.lat_deg[0] - astrometric.geometry.lat_deg[0]
        )

        print(f"model: {source.resource.model}")
        print(f"file: {source.resource.filename}")
        print(f"sha256: {source.resource.sha256}")
        print(f"observer: {observer_state.observer_id}")
        print(f"reception: {request.reception_instant} UTC")
        print(f"deflector NAIF IDs: {result.policy.deflector_naif_ids}")
        print(f"corrections: {sorted(result.geometry.coordinate_spec.corrections)}")
        print(f"apparent ICRS RA deg: {result.geometry.lon_deg[0]:.16g}")
        print(f"apparent ICRS Dec deg: {result.geometry.lat_deg[0]:.16g}")
        print(f"apparent-minus-astrometric RA deg: {shift_ra_deg:.9e}")
        print(f"apparent-minus-astrometric Dec deg: {shift_dec_deg:.9e}")
        print(f"RA residual deg: {ra_residual_deg:.3e}")
        print(f"Dec residual deg: {dec_residual_deg:.3e}")

        assert abs(ra_residual_deg) <= 1.0e-10
        assert abs(dec_residual_deg) <= 1.0e-10


if __name__ == "__main__":
    main()
