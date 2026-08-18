"""Packaged binocular selection for the paired physical star disks."""

import numpy as np

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


def test_every_curated_identifier_exists_in_its_canonical_catalogue():
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

    for name, table in catalogues.items():
        _positions(table, getattr(selection, name))


def test_default_overlap_places_at_most_fifteen_targets_on_each_face():
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
    declinations = []
    for name, table in catalogues.items():
        declinations.extend(
            _positions(table, getattr(selection, name)).values()
        )

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
