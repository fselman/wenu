"""Offline packaged target resolution contracts."""

import pytest

from wenu import (
    AmbiguousTargetError,
    ChartSubjectRequest,
    UnknownTargetError,
    load_target_catalogue,
    resolve_target,
    target_catalogue_path,
)
from wenu.charts import target_resolver


@pytest.mark.parametrize(
    ("alias", "key", "family", "identifier"),
    [
        ("Cen A", "centaurus-a", "galaxies", "NGC5128"),
        ("NGC 5139", "omega-centauri", "globular_clusters", "NGC 5139"),
        ("M13", "m13", "globular_clusters", "NGC 6205"),
        ("Eagle Nebula", "m16", "open_clusters", "NGC 6611"),
        ("M17", "m17", "nonstellar_objects", "M 17"),
        ("NGC6720", "m57", "planetary_nebulae", "PN G063.1+13.9"),
        ("Ptolemy's Cluster", "m7", "open_clusters", "NGC 6475"),
        ("Cygnus Loop", "veil-nebula", "supernova_remnants", "G074.0-08.5"),
    ],
)
def test_recent_binocular_targets_resolve_to_drawable_components(
    alias, key, family, identifier
):
    target = resolve_target(ChartSubjectRequest(target=alias))

    assert target.key == key
    assert target.components[0].family == family
    assert target.components[0].identifier == identifier
    assert target.required_families == {family}
    assert target.provenance


def test_explicit_coordinate_target_needs_no_packaged_component():
    target = resolve_target(
        ChartSubjectRequest(
            ra_deg=12.5,
            dec_deg=-30.0,
            display_name="My field",
        )
    )

    assert target.display_name == "My field"
    assert target.components == ()
    assert target.provenance == "user-supplied ICRS coordinate"


def test_resolved_target_exposes_publication_identity_and_icrs_center():
    target = resolve_target(ChartSubjectRequest(target="Centaurus A"))

    assert target.primary_identifier == "NGC 5128"
    assert target.coordinate.icrs.ra.deg == pytest.approx(target.ra_deg)
    assert target.coordinate.icrs.dec.deg == pytest.approx(target.dec_deg)


def test_target_without_components_has_no_primary_identifier():
    target = resolve_target(ChartSubjectRequest(
        ra_deg=10.0, dec_deg=-20.0
    ))

    assert target.primary_identifier is None


def test_unknown_target_is_diagnostic_instead_of_empty_chart():
    with pytest.raises(UnknownTargetError, match="Unknown packaged target"):
        resolve_target(ChartSubjectRequest(target="not a real target"))


def test_ambiguous_alias_lists_every_match(monkeypatch):
    declarations = (
        {"key": "one", "name": "First", "aliases": ["shared"]},
        {"key": "two", "name": "Second", "aliases": ["shared"]},
    )
    monkeypatch.setattr(
        target_resolver,
        "load_target_catalogue",
        lambda: ("test provenance", declarations),
    )

    with pytest.raises(
        AmbiguousTargetError, match="First, Second"
    ):
        resolve_target(ChartSubjectRequest(target="shared"))


def test_target_catalogue_is_packaged_and_has_provenance():
    assert target_catalogue_path().is_file()
    provenance, targets = load_target_catalogue()
    assert "Wenu packaged" in provenance
    assert len(targets) == 8
