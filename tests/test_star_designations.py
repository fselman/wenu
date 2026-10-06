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
