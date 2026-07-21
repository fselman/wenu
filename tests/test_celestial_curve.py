from types import SimpleNamespace

import numpy as np

from wenu.sky.curves import CelestialCurve


class StubSphericalFrame:
    """Minimal frame used to verify coordinate transformation."""

    def transform(self, lon_deg, lat_deg):
        return SimpleNamespace(
            lon_deg=np.asarray(lon_deg) + 10.0,
            lat_deg=np.asarray(lat_deg) - 5.0,
        )


def test_from_spherical_transforms_coordinates_into_horizontal_curve():
    frame = StubSphericalFrame()

    curve = CelestialCurve.from_spherical(
        lon_deg=np.array([0.0, 20.0, 40.0]),
        lat_deg=np.array([10.0, 15.0, 20.0]),
        frame=frame,
        name="test curve",
        closed=True,
        style={"linewidth": 1.5},
    )

    np.testing.assert_allclose(
        curve.az_deg,
        [10.0, 30.0, 50.0],
    )
    np.testing.assert_allclose(
        curve.alt_deg,
        [5.0, 10.0, 15.0],
    )

    assert curve.name == "test curve"
    assert curve.closed is True
    assert curve.style == {"linewidth": 1.5}


