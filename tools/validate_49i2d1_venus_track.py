"""Validate a 28-day scientific Venus track against direct Skyfield."""

from __future__ import annotations

from datetime import timezone
from pathlib import Path

from astropy.time import Time

from wenu.coordinates import observer_altaz_spec
from wenu.observer import DEFAULT_DATA_DIRECTORY, DEFAULT_EPHEMERIS, Observer
from wenu.sky.realization import LayerRealizationContext
from wenu.sky.solar_system_tracks import (
    SolarSystemTrackRealizer,
    SolarSystemTrackRequest,
)
from wenu.sky.venus import VENUS_POINT
from wenu.coordinates import PositionStatus

START = "2026-08-30T00:00:00Z"


def _wrapped_longitude_residual(actual, reference):
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
        time=START,
        ephemeris_name=DEFAULT_EPHEMERIS,
        data_directory=DEFAULT_DATA_DIRECTORY,
    ) as observer:
        context = LayerRealizationContext(
            product_coordinate_spec=observer_altaz_spec(
                observer,
                position_status=PositionStatus.APPARENT,
                provider="49I.2D.1 fixed chart frame",
                model="vacuum apparent Solar-System track",
            ),
            observation=observer.observation_context,
        )
        request = SolarSystemTrackRequest(
            descriptor=VENUS_POINT,
            start_instant=START,
            start_time_scale="utc",
            sample_step_days=1.0,
            tick_step_days=7.0,
            tick_count=4,
        )
        result = SolarSystemTrackRealizer().curve(
            request,
            context=context,
            observer=observer,
        )

        venus = observer.ephemeris["venus"]
        ra_residuals = []
        dec_residuals = []
        for instant, direction in zip(
            result.sample_instants,
            result.apparent_directions,
        ):
            sample = Time(instant, scale=result.sample_time_scale)
            skyfield_time = observer.timescale.from_datetime(
                sample.utc.to_datetime(timezone=timezone.utc)
            )
            direct = observer.skyfield.at(skyfield_time).observe(
                venus
            ).apparent()
            ra, dec, _ = direct.radec()
            ra_residuals.append(
                _wrapped_longitude_residual(
                    float(direction.geometry.lon_deg[0]),
                    float(ra.hours) * 15.0,
                )
            )
            dec_residuals.append(
                float(direction.geometry.lat_deg[0])
                - float(dec.degrees)
            )

        source = result.apparent_directions[0].astrometric.observer_state.resource
        print(f"model: {source.model}")
        print(f"file: {source.filename}")
        print(f"sha256: {source.sha256}")
        print(f"observer: {observer.location_name}")
        print(f"start: {result.sample_instants[0]} {result.sample_time_scale.upper()}")
        print(f"end: {result.sample_instants[-1]} {result.sample_time_scale.upper()}")
        print(f"samples: {len(result.sample_instants)}")
        print(f"tick sample indices: {result.tick_sample_indices}")
        print("major ticks in fixed chart frame:")
        previous = None
        latitude_deltas = []
        longitude_deltas = []
        for ordinal, index in enumerate(result.tick_sample_indices):
            longitude = float(result.geometry.lon_deg[0][index])
            latitude = float(result.geometry.lat_deg[0][index])
            print(
                f"  {ordinal}: sample {index:3d}, "
                f"{result.sample_instants[index]} "
                f"{result.sample_time_scale.upper()}, "
                f"lon {longitude:.12f} deg, "
                f"lat {latitude:.12f} deg"
            )
            if previous is not None:
                longitude_deltas.append(
                    _wrapped_longitude_residual(longitude, previous[0])
                )
                latitude_deltas.append(latitude - previous[1])
            previous = (longitude, latitude)
        print(
            "successive major-tick longitude deltas deg: "
            + ", ".join(f"{value:+.12f}" for value in longitude_deltas)
        )
        print(
            "successive major-tick latitude deltas deg: "
            + ", ".join(f"{value:+.12f}" for value in latitude_deltas)
        )
        print(
            "maximum direct-Skyfield RA residual deg: "
            f"{max(abs(value) for value in ra_residuals):.3e}"
        )
        print(
            "maximum direct-Skyfield Dec residual deg: "
            f"{max(abs(value) for value in dec_residuals):.3e}"
        )
        print(
            "fixed-frame first lon/lat deg: "
            f"{result.geometry.lon_deg[0][0]:.12f}, "
            f"{result.geometry.lat_deg[0][0]:.12f}"
        )
        print(
            "fixed-frame last lon/lat deg: "
            f"{result.geometry.lon_deg[0][-1]:.12f}, "
            f"{result.geometry.lat_deg[0][-1]:.12f}"
        )

        assert result.tick_sample_indices == (0, 7, 14, 21, 28)
        assert max(abs(value) for value in ra_residuals) <= 1.0e-7
        assert max(abs(value) for value in dec_residuals) <= 1.0e-7


if __name__ == "__main__":
    main()
