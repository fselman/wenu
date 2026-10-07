"""Offline resource admission and unsafe stellar-identity regression checks."""

import hashlib
import importlib.util
import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from wenu.resources import star_designations_manifest_path
from wenu.star_designations import load_star_designations


@pytest.fixture
def snapshot(tmp_path):
    resource = star_designations_manifest_path()
    (tmp_path / "manifest.json").write_bytes(resource.read_bytes())
    (tmp_path / "wikidata.json").write_bytes(
        resource.parent.joinpath("wikidata.json").read_bytes()
    )
    return tmp_path / "manifest.json"


def edit_snapshot(path, edit):
    data_path = path.parent / "wikidata.json"
    document = json.loads(data_path.read_bytes())
    edit(document)
    payload = json.dumps(document, ensure_ascii=False).encode()
    data_path.write_bytes(payload)
    manifest = json.loads(path.read_bytes())
    manifest["sha256"] = hashlib.sha256(payload).hexdigest()
    path.write_text(json.dumps(manifest))


def test_packaged_candidates_keep_identity_alternatives_and_review():
    catalogue = load_star_designations()
    assert len(catalogue.by_hip) == 3606
    antares = catalogue.get(80763)
    assert "Q12166" in antares.item_ids
    assert any(
        n.value == "Antares" and n.role == "label" for n in antares.names
    )
    alpheratz = catalogue.get(677)
    assert {s.code for s in alpheratz.candidates("bayer")} == {
        "α And",
        "δ Peg",
    }
    assert alpheratz.review_fields == ("bayer",)
    assert catalogue.get(999999999) is None
    assert not hasattr(antares, "preferred_name")
    with pytest.raises(FrozenInstanceError):
        antares.hip = 123
    with pytest.raises(TypeError):
        catalogue.by_hip[123] = antares
    all_claims = [s for r in catalogue.by_hip.values() for s in r.statements]
    assert len(all_claims) + len(catalogue.unjoined_statements) == 4864
    assert any(not s.references for s in all_claims)
    assert any(
        s.rank == "DeprecatedRank"
        for s in all_claims + list(catalogue.unjoined_statements)
    )
    assert all(
        s.rank != "DeprecatedRank"
        for r in catalogue.by_hip.values()
        for kind in ("bayer", "flamsteed")
        for s in r.candidates(kind)
    )


def test_altered_bytes_fail_digest(snapshot):
    with (snapshot.parent / "wikidata.json").open("ab") as stream:
        stream.write(b" ")
    with pytest.raises(ValueError, match="digest mismatch"):
        load_star_designations(snapshot)


@pytest.mark.parametrize(
    "mutation, message",
    [
        (lambda d: d["records"].append(d["records"][0]), "duplicate HIP"),
        (lambda d: d["records"][0].update(hip=True), "duplicate HIP"),
        (lambda d: d.update(schema="future/2"), "Unsupported snapshot"),
        (
            lambda d: d["records"][0]["statements"][0]["hip_links"][
                0
            ].__setitem__(1, "HIP 999999"),
            "Unsafe HIP join",
        ),
        (
            lambda d: d["records"][0]["statements"].append(
                d["records"][0]["statements"][0]
            ),
            "Duplicate designation",
        ),
        (
            lambda d: d["records"][0]["statements"][0].update(
                rank="UnknownRank"
            ),
            "Invalid Wikidata statement rank",
        ),
    ],
)
def test_rehashed_invalid_data_still_fails(snapshot, mutation, message):
    edit_snapshot(snapshot, mutation)
    with pytest.raises(ValueError, match=message):
        load_star_designations(snapshot)


def test_snapshot_filename_cannot_escape_resource(snapshot):
    manifest = json.loads(snapshot.read_bytes())
    manifest["file"] = "../wikidata.json"
    snapshot.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="filename"):
        load_star_designations(snapshot)


def test_offline_rebuild_matches_installed_bytes(tmp_path):
    root = Path(__file__).parents[1]
    script = root / "tools/build_wikidata_star_designations.py"
    spec = importlib.util.spec_from_file_location("wikidata_builder", script)
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    resource = star_designations_manifest_path()
    builder.compile_snapshot(
        Path(str(resource.parent)) / "source",
        root / "docs/developer/data/stellar_designations_review.json",
        tmp_path,
    )
    assert (
        tmp_path / "wikidata.json"
    ).read_bytes() == resource.parent.joinpath("wikidata.json").read_bytes()
    assert (tmp_path / "manifest.json").read_bytes() == resource.read_bytes()
    assert (
        load_star_designations(tmp_path / "manifest.json").source_sha256
        == load_star_designations().source_sha256
    )


@pytest.mark.parametrize("value,expected", [
    ("alpha", "α"), ("IOTA1", "ι¹"), ("ι¹", "ι¹"),
    ("i", "i"), ("I", "I"), ("k2", "k²"),
])
def test_bayer_normalization_preserves_latin_case_and_suffix(value, expected):
    from wenu.star_designations import bayer_token
    assert bayer_token(value) == expected


@pytest.mark.parametrize("scopes,expected", [
    (("Peg",), "δ Peg"), (("And",), "α And"),
    (("And", "Peg"), "α And"), (("Peg", "And"), "α And"),
    ((), "α And"),
])
def test_shared_star_context_and_conflict_are_order_independent(scopes, expected):
    from wenu.star_designations import preferred_designation
    from wenu.stellar_research import load_stellar_research
    record = load_star_designations().get(677)
    assert preferred_designation(record, "bayer", scopes, preferred=load_stellar_research().shared_preference(677, "bayer")) == expected


def test_explicit_labels_deduplicate_and_names_take_precedence():
    from wenu.star_designations import StarLabelSelection, resolve_star_labels
    labels = resolve_star_labels(StarLabelSelection(
        names=("Sco:Antares,Shaula",), bayer=("Sco:alpha,lambda",),
    ))
    assert labels.labels == ((80763, "Antares"), (85927, "Shaula"))
    assert labels(1) is None
    full = resolve_star_labels(StarLabelSelection(bayer=("Peg:delta",), show_full_bayer_designation=True))
    assert full.labels == ((677, "δ Peg"),)
    conflict = resolve_star_labels(StarLabelSelection(bayer=("Peg:delta", "And:alpha"), show_full_bayer_designation=True))
    assert conflict.labels == ((677, "α And"),)


@pytest.mark.parametrize("selector", ["Sco:unicorn", "Sco:iota", "Sco:beta"])
def test_unknown_or_ambiguous_bayer_never_selects_arbitrary_hip(selector):
    from wenu.star_designations import StarLabelSelection, resolve_star_labels
    with pytest.raises(ValueError, match="stellar bayer|Unknown Greek spelling"):
        resolve_star_labels(StarLabelSelection(bayer=(selector,)))


def test_research_index_is_exact_frozen_dossier_and_does_not_mutate():
    from wenu.stellar_research import load_stellar_research
    index = load_stellar_research()
    root = Path(__file__).parents[1]
    original = root / "docs/developer/data/stellar_designation_research/wenu-77-case-research.json"
    assert hashlib.sha256(original.read_bytes()).hexdigest() == index.source_sha256
    assert len(index.by_hip) == 77 and 677 in index and 1 not in index
    value = index.get(677)
    value["research"]["assessment"] = "changed"
    assert "genuine shared star" in index.get(677)["research"]["assessment"]
    with pytest.raises(TypeError):
        index.by_hip[677] = "changed"
    catalogue = load_star_designations()
    for (hip, kind), preferred in index.shared_preferences.items():
        assert preferred in {s.code for s in catalogue.get(hip).candidates(kind)}
    for hip in (86614, 86620, 95947, 100345):
        record = catalogue.get(hip)
        assert record is None or not record.candidates("bayer")


def test_curated_hip_associations_preserve_raw_claims_and_numeric_identity():
    from wenu.star_designations import (
        load_effective_star_designations, load_stellar_curation,
        StarLabelSelection, resolve_star_labels,
    )
    raw = load_star_designations()
    effective = load_effective_star_designations(raw)
    assert raw.get(78820).candidates("bayer") == ()
    assert effective.get(78820).candidates("bayer") == ()
    assert [c.code for c in effective.get(78820).assignments("bayer")] == ["β¹ Sco"]
    assert effective.hips_for_designation("β² Sco") == {78821}
    assert effective.hips_for_designation("β Sco") == {78820, 78821}
    assert effective.hips_for_designation("8 Sco", "flamsteed") == {78820, 78821}
    assert effective.get(677).statements is raw.get(677).statements
    assert effective.unjoined_statements is raw.unjoined_statements
    assert effective.source_sha256 == raw.source_sha256
    assert effective.curation_sha256 == load_stellar_curation().source_sha256
    labels = resolve_star_labels(StarLabelSelection(
        bayer=("Sco:beta1,beta2",), show_full_bayer_designation=True,
    ))
    assert labels.labels == ((78820, "β¹ Sco"), (78821, "β² Sco"))
    assert resolve_star_labels(StarLabelSelection(
        names=("Sco:Acrab",),
    )).labels == ((78820, "Acrab"),)


def test_curated_multiple_designation_does_not_select_brightest_component():
    from wenu.star_designations import StarLabelSelection, resolve_star_labels
    with pytest.raises(ValueError, match="Ambiguous stellar bayer"):
        resolve_star_labels(StarLabelSelection(bayer=("Psc:psi1",)))


def test_curated_inventory_is_immutable_and_pending_gaps_remain_unassigned():
    from wenu.star_designations import (
        load_stellar_curation, load_effective_star_designations,
    )
    curation = load_stellar_curation()
    assert len(curation.associations) == 158
    note = curation.get(102431)
    assert note["coverage_gaps"][0]["status"] == "pending"
    note["coverage_gaps"][0]["status"] = "changed"
    assert curation.get(102431)["coverage_gaps"][0]["status"] == "pending"
    with pytest.raises(TypeError):
        curation.by_hip[102431] = "changed"
    record = load_effective_star_designations().get(102431)
    assert record is None or not record.assignments("bayer")


@pytest.mark.parametrize("fault", ["digest", "duplicate", "hip", "snapshot"])
def test_curated_byte_admission_rejects_corruption_and_identity_faults(fault):
    from importlib.resources import files
    from wenu.star_designations import _load_stellar_curation
    root = files("wenu.data.catalogs.star_designations")
    payload = root.joinpath("curation.json").read_bytes()
    manifest = json.loads(root.joinpath("curation_manifest.json").read_bytes())
    if fault == "digest":
        changed = payload + b" "
    else:
        document = json.loads(payload)
        if fault == "duplicate":
            document["associations"].append(document["associations"][0])
        elif fault == "hip":
            document["associations"][0]["hip"] = 0
        else:
            document["snapshot_sha256"] = "0" * 64
        changed = json.dumps(document, ensure_ascii=False).encode()
        manifest["sha256"] = hashlib.sha256(changed).hexdigest()
    assert changed != payload
    with pytest.raises(ValueError):
        _load_stellar_curation(changed, json.dumps(manifest).encode())


def test_curated_overlay_rejects_an_active_source_assignment():
    from dataclasses import replace
    from types import MappingProxyType
    from wenu.star_designations import (
        load_stellar_curation, load_effective_star_designations,
    )
    raw = load_star_designations()
    index = dict(raw.by_hip)
    index[78820] = replace(raw.get(677), hip=78820)
    changed = replace(raw, by_hip=MappingProxyType(index))
    assert changed.get(78820).candidates("bayer")
    with pytest.raises(ValueError, match="may not overwrite"):
        load_effective_star_designations(changed, curation=load_stellar_curation())


def test_albireo_curated_name_preserves_raw_names_and_beta2_identity():
    from wenu.star_designations import (
        load_effective_star_designations, load_stellar_curation,
        resolve_star_labels, StarLabelSelection,
    )
    raw = load_star_designations()
    effective = load_effective_star_designations(raw)
    assert effective.get(95947).names == raw.get(95947).names
    assert all(n.value != "Albireo" for n in raw.get(95947).names)
    name = effective.get(95947).curated_names[0]
    assert name.value == "Albireo"
    assert name.evidence()["component"] == "Aa"
    assert effective.get(95951).curated_names == ()
    assert load_stellar_curation().get(95947)["name_associations"][0]["hip"] == 95947
    labels = resolve_star_labels(StarLabelSelection(
        names=("Cyg:Albireo",), bayer=("Cyg:beta1,beta2",),
        show_full_bayer_designation=True,
    ), catalogue=effective)
    assert labels.labels == ((95947, "Albireo"), (95951, "β² Cyg"))
    with pytest.raises(ValueError, match="Unknown or unavailable"):
        resolve_star_labels(StarLabelSelection(names=("Lyr:Albireo",)), catalogue=effective)


@pytest.mark.parametrize("fault", ["duplicate", "source", "scope", "hip"])
def test_curated_names_reject_unsafe_component_associations(fault):
    from wenu.star_designations import _load_stellar_curation, load_effective_star_designations
    root = star_designations_manifest_path().parent
    original = json.loads(root.joinpath("curation.json").read_bytes())
    changed = json.loads(json.dumps(original))
    entry = changed["name_associations"][0]
    if fault == "duplicate":
        changed["name_associations"].append(dict(entry))
    elif fault == "source":
        entry["sources"] = []
    elif fault == "scope":
        entry["constellation"] = "Lyr"
    else:
        entry["hip"] = 95951
    assert changed != original
    payload = json.dumps(changed).encode()
    manifest = json.loads(root.joinpath("curation_manifest.json").read_bytes())
    manifest["sha256"] = hashlib.sha256(payload).hexdigest()
    with pytest.raises(ValueError):
        curation = _load_stellar_curation(payload, json.dumps(manifest).encode())
        load_effective_star_designations(curation=curation)
