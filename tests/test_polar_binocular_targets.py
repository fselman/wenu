"""Packaged binocular selection for the paired physical star disks."""

from types import MappingProxyType

import numpy as np
import pytest

from wenu import PolarPlanisphereDetailPolicy
from wenu.objects.galaxies import Galaxies
from wenu.objects.globular_clusters import GlobularClusters
from wenu.objects.nonstellar import NonStellar
from wenu.objects.open_clusters import OpenClusters
from wenu.objects.planetary_nebulae import PlanetaryNebulae
from wenu.charts.polar_binocular_targets import polar_binocular_targets


def _loaded_catalogue(layer):
    layer.load()
    return layer.catalog


def _positions(table, selected):
    identifiers = np.asarray(table["identifier"], dtype=str)
    coordinates = {}
    for requested in selected:
        matches = np.flatnonzero(
            np.char.lower(identifiers) == requested.casefold()
        )
        assert matches.size == 1, requested
        coordinates[requested] = float(table["dec_deg"][matches[0]])
    return coordinates


@pytest.fixture(scope="module")
def catalogue_positions():
    """Freeze the read-only catalogue evidence shared by two assertions."""

    selection = PolarPlanisphereDetailPolicy().resolve(
        object(), object()
    ).content_selection
    catalogues = {
        "nonstellar_objects": _loaded_catalogue(NonStellar(None)),
        "galaxies": _loaded_catalogue(Galaxies(None)),
        "open_clusters": _loaded_catalogue(OpenClusters(None)),
        "globular_clusters": _loaded_catalogue(GlobularClusters(None)),
        "planetary_nebulae": _loaded_catalogue(PlanetaryNebulae(None)),
    }
    return MappingProxyType({
        name: MappingProxyType(
            _positions(table, getattr(selection, name))
        )
        for name, table in catalogues.items()
    })


def test_every_curated_identifier_exists_in_its_canonical_catalogue(
    catalogue_positions,
):
    selection = PolarPlanisphereDetailPolicy().resolve(
        object(), object()
    ).content_selection

    assert set(catalogue_positions) == {
        "nonstellar_objects",
        "galaxies",
        "open_clusters",
        "globular_clusters",
        "planetary_nebulae",
    }
    for name, positions in catalogue_positions.items():
        assert tuple(positions) == tuple(getattr(selection, name))
    with pytest.raises(TypeError):
        catalogue_positions["galaxies"] = {}
    with pytest.raises(TypeError):
        catalogue_positions["galaxies"]["NGC0224"] = 0.0


def test_default_overlap_places_at_most_fifteen_targets_on_each_face(
    catalogue_positions,
):
    declinations = [
        declination
        for positions in catalogue_positions.values()
        for declination in positions.values()
    ]

    north_count = sum(value >= -20.0 for value in declinations)
    south_count = sum(value <= 20.0 for value in declinations) + 2

    assert north_count == 15
    assert south_count == 15


def test_curated_print_labels_prefer_names_and_messier_designations():
    targets = polar_binocular_targets()
    labels = {
        (family, identifier): label
        for family, identifier, label in targets.label_overrides
    }

    assert labels[("galaxies", "NGC0224")] == "M31"
    assert labels[("galaxies", "NGC0598")] == "M33"
    assert labels[("galaxies", "NGC3031")] == "M81/82"
    assert labels[("galaxies", "NGC3034")] is None
    assert labels[("open_clusters", "Melotte 22")] == "Pléyades"
    assert labels[("open_clusters", "IC 2602")] == "Pléyades S"
    assert labels[("open_clusters", "NGC 3532")] == "N3532"
    assert labels[("open_clusters", "NGC 4755")] is None
    assert labels[("open_clusters", "NGC 6475")] == "Ptolomeo"
    assert labels[("open_clusters", "NGC 884")] is None
    assert labels[("globular_clusters", "NGC 5139")] == "ω"
    assert labels[("globular_clusters", "Omega Cen")] == "ω"
    assert labels[("planetary_nebulae", "PN G060.8-03.6")] == "M27"
