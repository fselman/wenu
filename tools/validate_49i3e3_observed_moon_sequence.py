"""Validate 49I.3E.3 observed Moon sequence against direct Skyfield."""

from __future__ import annotations

from pathlib import Path

from wenu.observer import DEFAULT_DATA_DIRECTORY, DEFAULT_EPHEMERIS, Observer
from wenu.sky.moon import MOON_BODY
from wenu.skyfield_ephemeris import SkyfieldEphemerisStateSource
from wenu.sky.solar_system_disk_sequences import (
    ObservedSolarSystemDiskSequenceRealizer,
    ObservedSolarSystemDiskSequenceRequest,
)

from validate_49i3e1_lunar_appearance import (
    DEC_TOLERANCE_DEG,
    DIAMETER_TOLERANCE_ARCSEC,
    DISTANCE_TOLERANCE_AU,
    FRACTION_TOLERANCE,
    PHASE_TOLERANCE_DEG,
    POSITION_ANGLE_TOLERANCE_DEG,
    RA_TOLERANCE_DEG,
    _direct_values,
    _sample_observer,
    _wrapped_residual,
)


START = "2026-09-05T00:00:00Z"
STEP_DAYS = 7.0
N_STEPS = 4
CHART_EPOCH = "2026-09-16T12:00:00Z"


def _request():
    return ObservedSolarSystemDiskSequenceRequest(
        descriptor=MOON_BODY,
        start_instant=START,
        start_time_scale="utc",
        step_days=STEP_DAYS,
        n_steps=N_STEPS,
        display_name=MOON_BODY.display_name,
        physical_radius_km=MOON_BODY.physical_radius_km,
        radius_model=MOON_BODY.radius_model,
    )


def main():
    path = Path(DEFAULT_DATA_DIRECTORY) / DEFAULT_EPHEMERIS
    if not path.is_file():
        raise SystemExit(
            f"Installed kernel required; refusing download because {path} "
            "does not exist."
        )

    maxima = {
        "ra": 0.0,
        "dec": 0.0,
        "distance": 0.0,
        "diameter": 0.0,
        "phase": 0.0,
        "fraction": 0.0,
        "position_angle": 0.0,
    }
    minimum_parallax = float("inf")

    with Observer(
        location="La Ligua",
        time=CHART_EPOCH,
        ephemeris_name=DEFAULT_EPHEMERIS,
        data_directory=DEFAULT_DATA_DIRECTORY,
    ) as observer:
        result = ObservedSolarSystemDiskSequenceRealizer().sequence(
            _request(), observer=observer
        )
        resource = SkyfieldEphemerisStateSource.from_observer(
            observer
        ).resource
        print(f"model: {resource.model}")
        print(f"file: {resource.filename}")
        print(f"sha256: {resource.sha256}")
        print(
            "coverage: "
            f"{resource.coverage_start} through {resource.coverage_end} "
            f"{resource.coverage_time_scale.upper()}"
        )
        print(f"chart epoch: {CHART_EPOCH}")
        print(
            "observer: La Ligua; "
            f"lat {observer.lat_deg:.9f} deg; "
            f"lon {observer.lon_deg:.9f} deg; "
            f"height {observer.elevation_m:.3f} m"
        )
        print(f"Moon physical body ID: {MOON_BODY.physical_body_id}")
        print(f"Moon mean radius km: {MOON_BODY.physical_radius_km:.1f}")
        print(f"radius model: {MOON_BODY.radius_model}")
        print(f"sample count: {len(result.sample_instants)}")

        assert len(result.sample_instants) == N_STEPS + 1
        assert CHART_EPOCH.replace("Z", "") not in result.sample_instants
        assert len({id(value) for value in result.appearances}) == len(
            result.appearances
        )

        for instant, appearance, distance in zip(
            result.sample_instants,
            result.appearances,
            result.distances,
        ):
            sample_observer = _sample_observer(observer, instant)
            direct = _direct_values(sample_observer)
            direction = appearance.apparent_direction.geometry
            residuals = {
                "ra": _wrapped_residual(
                    float(direction.lon_deg[0]), direct["ra"]
                ),
                "dec": float(direction.lat_deg[0]) - direct["dec"],
                "distance": distance - direct["distance"],
                "diameter": (
                    appearance.angular_diameter_arcsec - direct["diameter"]
                ),
                "phase": appearance.phase_angle_deg - direct["phase"],
                "fraction": (
                    appearance.illuminated_fraction - direct["fraction"]
                ),
                "position_angle": _wrapped_residual(
                    appearance.bright_limb_position_angle_deg,
                    direct["position_angle"],
                ),
            }
            for name, value in residuals.items():
                maxima[name] = max(maxima[name], abs(float(value)))
            minimum_parallax = min(minimum_parallax, direct["parallax"])
            print(
                f"sample {instant}: "
                f"phase {appearance.phase_angle_deg:.6f} deg; "
                f"distance {distance:.12f} au; "
                f"diameter {appearance.angular_diameter_arcsec:.6f} arcsec; "
                f"PA {appearance.bright_limb_position_angle_deg:.6f} deg; "
                f"parallax {direct['parallax']:.6f} deg"
            )

        print("maximum absolute residuals:")
        print(f"  apparent RA deg: {maxima['ra']:.3e}")
        print(f"  apparent Dec deg: {maxima['dec']:.3e}")
        print(f"  topocentric distance au: {maxima['distance']:.3e}")
        print(f"  angular diameter arcsec: {maxima['diameter']:.3e}")
        print(f"  phase angle deg: {maxima['phase']:.3e}")
        print(f"  illuminated fraction: {maxima['fraction']:.3e}")
        print(f"  bright-limb PA deg: {maxima['position_angle']:.3e}")
        print(f"minimum topocentric parallax deg: {minimum_parallax:.6f}")

        assert maxima["ra"] <= RA_TOLERANCE_DEG
        assert maxima["dec"] <= DEC_TOLERANCE_DEG
        assert maxima["distance"] <= DISTANCE_TOLERANCE_AU
        assert maxima["diameter"] <= DIAMETER_TOLERANCE_ARCSEC
        assert maxima["phase"] <= PHASE_TOLERANCE_DEG
        assert maxima["fraction"] <= FRACTION_TOLERANCE
        assert maxima["position_angle"] <= POSITION_ANGLE_TOLERANCE_DEG
        assert minimum_parallax > 0.1


if __name__ == "__main__":
    main()
