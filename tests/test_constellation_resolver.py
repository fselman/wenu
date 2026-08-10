"""Offline constellation-set and packaged-group resolution contracts."""

import pytest

from wenu import (
    ChartSubjectRequest,
    UnknownConstellationError,
    UnknownConstellationGroupError,
    constellation_group_catalogue_path,
    load_constellation_groups,
    normalize_constellations,
    resolve_constellation_subject,
)


def test_explicit_iau_set_preserves_order_and_normalizes_case():
    resolved = resolve_constellation_subject(
        ChartSubjectRequest(constellations=("cru", "CEN"))
    )

    assert resolved.constellations == ("Cru", "Cen")
    assert resolved.line_constellations == ("Cru", "Cen")
    assert resolved.boundary_constellations == ("Cru", "Cen")
    assert resolved.label_constellations == ("Cru", "Cen")


def test_serpens_expands_internal_line_and_label_identities():
    resolved = resolve_constellation_subject(
        ChartSubjectRequest(constellations=("Oph", "Ser"))
    )

    assert resolved.constellations == ("Oph", "Ser")
    assert resolved.line_constellations == ("Oph", "Ser1", "Ser2")
    assert resolved.boundary_constellations == ("Oph", "Ser")
    assert resolved.label_constellations == (
        "Oph", "SerCap", "SerCau"
    )


def test_summer_triangle_is_packaged_data_not_example_logic():
    resolved = resolve_constellation_subject(
        ChartSubjectRequest(group="Summer Triangle")
    )

    assert resolved.key == "summer-triangle"
    assert resolved.constellations == ("Cyg", "Lyr", "Vul", "Sge", "Aql")
    assert resolved.field_width_deg == pytest.approx(143.52)
    assert resolved.field_height_deg == pytest.approx(104.0)
    assert "NGC 6811" in resolved.open_clusters
    assert "PN G063.1+13.9" in resolved.planetary_nebulae
    assert "G074.0-08.5" in resolved.supernova_remnants
    assert resolved.provenance


@pytest.mark.parametrize("alias", ["galactic-center", "sgr-sco-oph-ser"])
def test_galactic_center_aliases_share_one_serpens_safe_declaration(alias):
    resolved = resolve_constellation_subject(
        ChartSubjectRequest(group=alias)
    )

    assert resolved.key == "galactic-center"
    assert resolved.constellations == ("Sgr", "Sco", "Oph", "Ser")
    assert resolved.line_constellations == (
        "Sgr", "Sco", "Oph", "Ser1", "Ser2"
    )
    assert resolved.boundary_constellations == (
        "Sgr", "Sco", "Oph", "Ser"
    )
    assert resolved.label_constellations == (
        "Sgr", "Sco", "Oph", "SerCap", "SerCau"
    )


def test_unknown_constellation_and_group_are_diagnostic():
    with pytest.raises(UnknownConstellationError, match="NotIAU"):
        normalize_constellations(("Cru", "NotIAU"))
    with pytest.raises(
        UnknownConstellationGroupError, match="not-a-group"
    ):
        resolve_constellation_subject(
            ChartSubjectRequest(group="not-a-group")
        )


def test_group_catalogue_is_packaged_and_provenance_controlled():
    assert constellation_group_catalogue_path().is_file()
    provenance, groups = load_constellation_groups()
    assert "Wenu packaged" in provenance
    assert len(groups) == 2
