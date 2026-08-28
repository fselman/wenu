"""Milestone 49B.3 native astronomical position-provider contracts."""

import numpy as np
import pandas as pd
import pytest
from astropy.table import Table

from wenu.geometry import SphericalPoints
from wenu.objects.galaxies import Galaxies
from wenu.objects.nonstellar import NonStellar
from wenu.objects.open_clusters import OpenClusters
from wenu.objects.planetary_nebulae import PlanetaryNebulae
from wenu.objects.stars import Stars
from wenu.positions import PositionProvider
from wenu.sky.horizon import HorizonReference


def test_stars_provide_static_native_icrs_positions():
    stars = Stars(None, catalog="hipparcos")
    stars.catalog = pd.DataFrame(
        {
            "ra_hours": [1.0, 2.0],
            "dec_degrees": [-30.0, 45.0],
            "magnitude": [1.5, 2.5],
        },
        index=[100, 200],
    )

    geometry = stars.position("2026-08-28T00:00:00")

    assert isinstance(stars, PositionProvider)
    assert isinstance(geometry, SphericalPoints)
    np.testing.assert_allclose(geometry.lon_deg, [15.0, 30.0])
    np.testing.assert_allclose(geometry.lat_deg, [-30.0, 45.0])
    assert geometry.ids.tolist() == [100, 200]
    assert geometry.coordinate_spec.frame == "icrs"
    assert geometry.coordinate_spec.origin == "solar-system-barycenter"
    assert geometry.coordinate_spec.instant is None


def test_nonstellar_catalogues_provide_native_centres_not_morphology():
    objects = NonStellar(None, catalog="messier")
    objects.catalog = Table(
        {
            "identifier": ["M1", "M31"],
            "ra_deg": [83.633, 10.685],
            "dec_deg": [22.014, 41.269],
            "magnitude": [8.4, 3.4],
        }
    )

    geometry = objects.position()

    assert isinstance(objects, PositionProvider)
    np.testing.assert_allclose(geometry.lon_deg, [83.633, 10.685])
    np.testing.assert_allclose(geometry.lat_deg, [22.014, 41.269])
    assert geometry.names.tolist() == ["M1", "M31"]
    assert geometry.coordinate_spec.frame == "icrs"


def test_open_clusters_provide_selected_native_centres():
    clusters = OpenClusters(None, selected=("NGC 2516",))
    clusters.catalog = Table(
        {
            "identifier": ["NGC 2516", "NGC 3532"],
            "ra_deg": [119.5, 166.4],
            "dec_deg": [-60.8, -58.7],
            "apparent_diameter_arcmin": [30.0, 50.0],
            "object_type": ["Open Cluster", "Open Cluster"],
        }
    )

    geometry = clusters.position()

    assert isinstance(clusters, PositionProvider)
    assert geometry.ids.tolist() == ["NGC 2516"]
    np.testing.assert_allclose(geometry.lon_deg, [119.5])
    np.testing.assert_allclose(geometry.lat_deg, [-60.8])


def test_nonstellar_subclasses_share_the_centre_provider_boundary():
    assert Galaxies.position is NonStellar.position
    assert PlanetaryNebulae.position is NonStellar.position


def test_constructed_reference_geometry_is_not_a_position_provider():
    assert not isinstance(HorizonReference(), PositionProvider)


@pytest.mark.parametrize(
    "provider",
    (Stars(None), NonStellar(None), OpenClusters(None)),
)
def test_unloaded_providers_reject_position_requests(provider):
    with pytest.raises(RuntimeError, match="catalogue has not been loaded"):
        provider.position()
