"""Canonical maximal-sphere load-profile and factory contracts."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from wenu import (
    CANONICAL_MAXIMAL_SPHERE_PROFILE,
    CelestialSphereLoadProfile,
    build_maximal_sphere,
    generate_celestial_sphere,
)
from wenu.sky import maximal_sphere


def test_load_profile_is_immutable_comparable_and_normalizes_sources():
    first = CelestialSphereLoadProfile(star_filename="stars.dat")
    second = CelestialSphereLoadProfile(star_filename=Path("stars.dat"))

    assert first == second
    assert hash(first) == hash(second)
    assert first.star_filename == Path("stars.dat")
    with pytest.raises(FrozenInstanceError):
        first.star_magnitude_limit = 12.0


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("star_magnitude_limit", 11.1),
        ("galaxy_magnitude_limit", 12.1),
        ("globular_cluster_magnitude_limit", 12.1),
        ("extended_object_samples", 98),
    ],
)
def test_load_profile_rejects_requests_beyond_available_content(
    field, value
):
    with pytest.raises(ValueError, match=field):
        CANONICAL_MAXIMAL_SPHERE_PROFILE.require(**{field: value})


def test_load_profile_accepts_shallower_render_requests():
    profile = CANONICAL_MAXIMAL_SPHERE_PROFILE

    assert profile.require(
        star_magnitude_limit=6.5,
        galaxy_magnitude_limit=11.0,
        globular_cluster_magnitude_limit=9.0,
        extended_object_samples=73,
    ) is profile


def test_factory_registers_complete_content_without_chart_decisions(
    monkeypatch,
):
    calls = []

    class RecordingSphere:
        def __init__(self, observer):
            self.observer = observer
            self.load_profile = None

        def __getattr__(self, name):
            if not name.startswith("add_"):
                raise AttributeError(name)

            def record(*args, **kwargs):
                calls.append((name, args, kwargs))

            return record

    monkeypatch.setattr(maximal_sphere, "CelestialSphere", RecordingSphere)
    observer = object()

    sphere = build_maximal_sphere(observer)

    assert isinstance(sphere, RecordingSphere)
    assert sphere.observer is observer
    assert sphere.load_profile is CANONICAL_MAXIMAL_SPHERE_PROFILE
    assert [name for name, _, _ in calls] == [
        "add_milky_way_isophotes",
        "add_magellanic_cloud_isophotes",
        "add_magellanic_cloud_isophotes",
        "add_stars",
        "add_nonstellar",
        "add_galaxies",
        "add_open_clusters",
        "add_globular_clusters",
        "add_supernova_remnants",
        "add_planetary_nebulae",
        "add_constellations",
        "add_constellation_boundaries",
    ]
    assert not any("grid" in name for name, _, _ in calls)
    assert all(
        key not in kwargs
        for _, _, kwargs in calls
        for key in (
            "projection",
            "viewport",
            "style",
            "mask",
            "renderer",
            "output",
        )
    )


def test_factory_rejects_an_untyped_profile():
    with pytest.raises(TypeError, match="CelestialSphereLoadProfile"):
        build_maximal_sphere(object(), profile=object())


def test_ordinary_factory_generates_an_observer_independent_sphere(
    monkeypatch,
):
    calls = []

    def build(observer, *, profile):
        calls.append((observer, profile))
        return object()

    monkeypatch.setattr(maximal_sphere, "build_maximal_sphere", build)

    sphere = generate_celestial_sphere()

    assert sphere is not None
    assert calls == [(None, CANONICAL_MAXIMAL_SPHERE_PROFILE)]


def test_ordinary_factory_rejects_an_untyped_profile():
    with pytest.raises(TypeError, match="CelestialSphereLoadProfile"):
        generate_celestial_sphere(profile=object())


@pytest.mark.integration
def test_ordinary_factory_loads_canonical_layers_without_an_observer():
    sphere = generate_celestial_sphere()

    assert sphere.observer is None
    assert sphere.load_profile is CANONICAL_MAXIMAL_SPHERE_PROFILE
    assert len(sphere.layers) == 13
    assert all(
        getattr(layer, "observer", None) is None
        for layer in sphere.layers
    )
