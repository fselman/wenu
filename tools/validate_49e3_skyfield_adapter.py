"""Validate the 49E.3 adapter against one installed de440s.bsp kernel."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from astropy.time import Time

from wenu.ephemeris import EphemerisStateRequest
from wenu.observer import DEFAULT_DATA_DIRECTORY, DEFAULT_EPHEMERIS, Observer
from wenu.skyfield_ephemeris import SkyfieldEphemerisStateSource


INSTANT = "2026-08-30T00:00:00"


def main():
    path = Path(DEFAULT_DATA_DIRECTORY) / DEFAULT_EPHEMERIS
    if not path.is_file():
        raise SystemExit(
            f"Installed kernel required; refusing download because {path} "
            "does not exist."
        )

    with Observer(
        location="La Ligua",
        time=f"{INSTANT}Z",
        ephemeris_name=DEFAULT_EPHEMERIS,
        data_directory=DEFAULT_DATA_DIRECTORY,
    ) as observer:
        source = SkyfieldEphemerisStateSource.from_observer(observer)
        request = EphemerisStateRequest(
            target="venus",
            centre="solar system barycenter",
            frame="icrf",
            instant=INSTANT,
            time_scale="tdb",
        )
        state = source.state(request)

        time = observer.timescale.from_astropy(Time(INSTANT, scale="tdb"))
        direct = (
            observer.ephemeris["venus"]
            - observer.ephemeris["solar system barycenter"]
        ).at(time)
        np.testing.assert_allclose(
            state.position,
            direct.position.au,
            rtol=0.0,
            atol=1e-15,
        )
        np.testing.assert_allclose(
            state.velocity,
            direct.velocity.au_per_d,
            rtol=0.0,
            atol=1e-15,
        )

        print(f"model: {state.resource.model}")
        print(f"file: {state.resource.filename}")
        print(f"sha256: {state.resource.sha256}")
        print(
            "coverage: "
            f"{state.resource.coverage_start} through "
            f"{state.resource.coverage_end} "
            f"{state.resource.coverage_time_scale.upper()}"
        )
        print(f"target NAIF ID: {state.provider_target_id}")
        print(f"centre NAIF ID: {state.provider_centre_id}")
        print(f"position AU: {state.position}")
        print(f"velocity AU/day: {state.velocity}")
        print("adapter/direct residual: zero within 1e-15")


if __name__ == "__main__":
    main()
