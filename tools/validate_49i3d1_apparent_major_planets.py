"""Validate every catalog planet point against direct installed-DE440 Skyfield."""

from pathlib import Path

from wenu.observer import DEFAULT_DATA_DIRECTORY, DEFAULT_EPHEMERIS, Observer
from wenu.sky.solar_system_bodies import SYMBOLIC_POINT
from wenu.sky.solar_system_catalog import SOLAR_SYSTEM_BODY_CATALOG
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
TOLERANCE_DEG = 1.0e-7
EXPECTED_PROVIDER_IDS = {
    "mercury": "199",
    "venus": "299",
    "mars": "4",
    "jupiter": "5",
    "saturn": "6",
    "uranus": "7",
    "neptune": "8",
}


def _wrapped(value):
    return (value + 180.0) % 360.0 - 180.0


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
            observer, source=source
        )
        print(f"model: {source.resource.model}")
        print(f"file: {source.resource.filename}")
        print(f"sha256: {source.resource.sha256}")
        print(f"reception: {observer.t_astropy.isot} UTC")
        maxima = {"ra": 0.0, "dec": 0.0}
        for descriptor in SOLAR_SYSTEM_BODY_CATALOG.supporting(SYMBOLIC_POINT):
            request = AstrometricDirectionRequest(
                target=descriptor.target,
                centre=descriptor.centre,
                reception_instant=observer.t_astropy.isot,
                reception_time_scale=observer.t_astropy.scale,
            )
            astrometric = AstrometricDirectionRealizer().direction(
                source, request, observer_state
            )
            apparent = SkyfieldApparentDirectionRealizer().direction(
                astrometric, observer=observer, source=source
            )
            direct = observer.skyfield.at(observer.t).observe(
                observer.ephemeris[descriptor.target]
            ).apparent()
            direct_ra, direct_dec, _ = direct.radec()
            ra = float(direct_ra.hours) * 15.0
            dec = float(direct_dec.degrees)
            ra_residual = _wrapped(apparent.geometry.lon_deg[0] - ra)
            dec_residual = apparent.geometry.lat_deg[0] - dec
            maxima["ra"] = max(maxima["ra"], abs(ra_residual))
            maxima["dec"] = max(maxima["dec"], abs(dec_residual))
            expected_provider = EXPECTED_PROVIDER_IDS[descriptor.selection_key]
            print(
                f"{descriptor.display_name}: physical {descriptor.physical_body_id}; "
                f"provider target/centre {astrometric.target_provider_id}/"
                f"{observer_state.provider_centre_id}; target {descriptor.target!r}; "
                f"RA/Dec {apparent.geometry.lon_deg[0]:.12f}/"
                f"{apparent.geometry.lat_deg[0]:.12f} deg; residual "
                f"{ra_residual:.3e}/{dec_residual:.3e} deg"
            )
            assert astrometric.target_provider_id == expected_provider
            assert abs(ra_residual) <= TOLERANCE_DEG
            assert abs(dec_residual) <= TOLERANCE_DEG
        print(
            f"maximum residuals: RA {maxima['ra']:.3e} deg; "
            f"Dec {maxima['dec']:.3e} deg; tolerance {TOLERANCE_DEG:.3e} deg"
        )


if __name__ == "__main__":
    main()
