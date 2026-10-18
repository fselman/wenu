"""Current documentation integrity and runnable public-interface contracts.

Historical milestone phrase checks are archived with an exact-blob ledger.
Scientific and product tests are unchanged by this documentation cleanup.
"""

import ast
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DEVELOPER = ROOT / "docs/developer"
LEDGER = DEVELOPER / "documentation_cleanup_v1.json"
ACTIVE_DEVELOPER = {
    "README.md", "assistant_instructions.md", "current_architecture_v0.9.md",
    "implementation_reference.md", "source_tree.md", "configuration_schema_v2.md",
    "coordinate_system_guide_v0.9.5.md", "satellite_guide.md",
    "stellar_designation_review.md", "scientific_contracts.md",
    "testing_policy.md", "kernel_roadmap_v0.9.5.md", "kernel_contract_k1.md",
    "kernel_migration_audit_v1.md",
}
OBSOLETE_IMPORTS = (
    "wenu.spherical", "wenu.projected", "wenu.spherical_frame", "wenu.clipping",
    "wenu.viewport", "wenu.projection", "wenu.chart", "wenu.regional",
    "wenu.styles", "wenu.renderers",
)


def read(path):
    return path.read_text(encoding="utf-8")


def active_documents():
    return [ROOT / "AGENTS.md", ROOT / "README.md", ROOT / "README.es.md"] + [
        p for p in sorted((ROOT / "docs").rglob("*.md"))
        if "archive" not in p.relative_to(ROOT / "docs").parts
    ]


def fenced_python(path):
    return re.findall(r"```python\n(.*?)```", read(path), re.S)


def git_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def markdown_anchors(text):
    anchors = set(re.findall(r'<a\s+id="([^"]+)"', text))
    counts = {}
    for heading in re.findall(r"^#{1,6} +(.+)$", text, re.M):
        heading = re.sub(r"<[^>]+>", "", heading).strip().lower()
        heading = re.sub(r"[^\w\- ]", "", heading).replace(" ", "-")
        count = counts.get(heading, 0)
        counts[heading] = count + 1
        anchors.add(heading if count == 0 else f"{heading}-{count}")
    return anchors


def local_link_targets(path):
    # Ignore links inside examples/code; parse inline links/images and definitions.
    prose = re.sub(r"```.*?```", "", read(path), flags=re.S)
    targets = re.findall(r"!?\[[^]\n]*\]\(([^\s)]+)(?:\s+[^)]*)?\)", prose)
    targets += re.findall(r"^\[[^]]+\]:\s*(\S+)", prose, re.M)
    for target in targets:
        target = target.strip("<>")
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc:
            continue
        destination = path.parent / unquote(parsed.path) if parsed.path else path
        yield destination.resolve(), unquote(parsed.fragment)


def test_developer_root_contains_only_current_authority():
    assert {p.name for p in DEVELOPER.glob("*.md")} == ACTIVE_DEVELOPER
    index = read(DEVELOPER / "README.md")
    for name in ACTIVE_DEVELOPER - {"README.md"}:
        assert f"]({name})" in index, name


def test_active_relative_links_and_anchors_resolve():
    failures = []
    for path in active_documents():
        for destination, fragment in local_link_targets(path):
            if not destination.exists():
                failures.append(f"{path.relative_to(ROOT)} -> {destination}")
            elif fragment and destination.suffix == ".md" and "archive" not in destination.parts:
                if fragment not in markdown_anchors(read(destination)):
                    failures.append(f"{path.relative_to(ROOT)} -> {destination.name}#{fragment}")
    assert failures == [], "\n".join(failures)


def test_preserved_editions_match_exact_original_git_blobs():
    ledger = json.loads(read(LEDGER))
    assert ledger["baseline_commit"] == "6708f54a0d8984c0be348b2c8cb02b311646a02b"
    assert len({r["original_path"] for r in ledger["preserved_editions"]}) == len(ledger["preserved_editions"])
    for record in ledger["preserved_editions"]:
        path = ROOT / record["archive_path"]
        assert path.is_file(), record
        assert git_blob(path.read_bytes()) == record["original_git_blob_sha"], record


def test_historical_documentation_suite_is_preserved_but_not_collected():
    ledger = json.loads(read(LEDGER))
    original = next(r for r in ledger["preserved_editions"]
                    if r["original_path"] == "tests/test_current_documentation.py")
    archived = ROOT / original["archive_path"]
    assert archived.name.endswith(".py.txt")
    tree = ast.parse(read(archived))
    tests = [n.name for n in tree.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
    assert len(tests) == ledger["historical_documentation_test_count"]
    assert not list((DEVELOPER / "archive/pre_kernel_20261017").rglob("test_*.py"))


def test_documented_python_is_syntactically_valid():
    for path in (ROOT / "README.md", DEVELOPER / "implementation_reference.md",
                 DEVELOPER / "kernel_contract_k1.md"):
        blocks = fenced_python(path)
        assert blocks, path
        for block in blocks:
            ast.parse(block, filename=str(path))


def test_documented_canonical_public_imports_execute():
    # Retained public-import execution contract from the original suite.
    namespace = {}
    exec(fenced_python(DEVELOPER / "implementation_reference.md")[0], namespace)
    for name in ("AllSkyChart", "compose_chart", "LegendOptions", "RegionalChart",
                 "FullSkyChart", "CircumpolarChart", "BinocularChart"):
        assert name in namespace


def test_public_documents_do_not_recommend_obsolete_imports():
    violations = []
    for path in active_documents():
        text = read(path)
        for obsolete in OBSOLETE_IMPORTS:
            if re.search(rf"\b(?:from|import)\s+{re.escape(obsolete)}(?=\s|$)", text):
                violations.append(f"{path.relative_to(ROOT)}: {obsolete}")
    assert violations == []


def test_source_map_covers_exactly_current_production_modules():
    actual = {str(p.relative_to(ROOT / "src/wenu")) for p in (ROOT / "src/wenu").rglob("*.py")}
    source_map = read(DEVELOPER / "source_tree.md")
    listed = re.findall(r"\| \[`([^`]+\.py)`\]\(../../src/wenu/[^)]+\)", source_map)
    assert len(listed) == len(set(listed))
    assert set(listed) == actual
    # A new source, test module or installed command must enter the migration
    # ledger; otherwise the K5 all-consumer review could silently omit it.
    audit = json.loads(read(DEVELOPER / "kernel_migration_inventory_v1.json"))
    assert {r["path"] for r in audit["production_modules"]} == {
        "src/wenu/" + path for path in actual}
    assert {r["path"] for r in audit["test_side_python_files"]} == {
        str(p.relative_to(ROOT)) for p in (ROOT / "tests").rglob("*.py")}
    import tomllib
    scripts = tomllib.loads(read(ROOT / "pyproject.toml"))["project"]["scripts"]
    assert audit["entry_points"] == scripts
    for record in audit["preserved_test_editions"]:
        assert git_blob((ROOT / record["archive_path"]).read_bytes()) == record["original_git_blob_sha"]


def test_atlas_guide_documents_all_registered_atlas_presets():
    tree = ast.parse(read(ROOT / "src/wenu/resources.py"))
    registry = next(n.value for n in tree.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "_CONFIGURATION_PRESETS" for t in n.targets))
    presets = ast.literal_eval(registry)
    guide = read(ROOT / "docs/user_guide/atlas.md")
    for kind in ("atlas-style", "atlas-layout", "atlas-index"):
        for name in presets[kind]:
            assert f"`{name}`" in guide, (kind, name)


def test_atlas_guide_uses_existing_cli_options():
    source = ast.parse(read(ROOT / "src/wenu/cli/atlas.py"))
    options = {n.value for n in ast.walk(source)
               if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.startswith("--")}
    options |= {"--no-" + option[2:] for option in options if not option.startswith("--no-")}
    guide = read(ROOT / "docs/user_guide/atlas.md")
    assert set(re.findall(r"(?<![\w-])--[a-z][a-z0-9-]*", guide)) <= options


def test_user_guide_documents_every_chart_family_with_examples():
    examples = read(ROOT / "docs/user_guide/chart_examples.md")
    for family in ("all-sky", "planisphere", "regional", "circumpolar", "binocular"):
        assert f"wenu_chart {family}" in examples
    for script in ("all_sky.py", "planisphere.py", "regional_constellation.py",
                   "regional_constellation_group.py", "circumpolar.py", "binocular_object.py"):
        assert f"examples/{script}" in examples


def test_stellar_review_cells_remain_unchanged():
    ledger = json.loads(read(DEVELOPER / "data/stellar_designations_review.json"))
    assert len(ledger["cases"]) == 77
    assert all(c["status"] == "pending_fernando" and c["decision"] is None
               and c["selman"] is None for c in ledger["cases"])
    table = read(DEVELOPER / "stellar_designation_review.md")
    rows = [line for line in table.splitlines() if line.startswith("|")]
    assert len(rows) == 79
    assert rows[0].endswith(" Selman |")
    assert all(line.split("|")[-2].strip() == "" for line in rows[2:])


def test_roadmap_has_both_diagrams_and_ordered_exit_gates():
    roadmap = read(DEVELOPER / "kernel_roadmap_v0.9.5.md")
    assert roadmap.count("```mermaid") == 2
    assert {"current-architecture", "proposed-architecture"} <= markdown_anchors(roadmap)
    ids = re.findall(r"^\| (K[0-9]+[ab]?) \|", roadmap, re.M)
    assert ids == ["K0", "K1", "K2", "K3", "K4a", "K4b", "K5", "K6", "K7", "K8", "K9"]


def test_configuration_schema_and_current_cli_examples_remain_version_two():
    import tomllib
    defaults = tomllib.loads(read(ROOT / "src/wenu/configuration/defaults.toml"))
    assert defaults["schema_version"] == 2
    assert defaults["constellations"]["system"] == "western"
    assert "subjects" not in defaults
    assert all(v["constellations"] == [] for v in defaults["masks"].values())
    guide = read(ROOT / "docs/user_guide/configuration.md")
    schema = read(DEVELOPER / "configuration_schema_v2.md")
    for kind in ("labels", "lines", "boundaries"):
        assert f"--constellation-{kind} all" in guide
        assert f"--constellation-{kind}-exclude" in guide
        assert f".{kind}_exclude" in schema


def test_release_version_still_comes_from_scm():
    project = read(ROOT / "pyproject.toml")
    assert 'dynamic = ["version"]' in project
    assert '[tool.setuptools_scm]' in project
    assert 'fallback_version = "0.8.0"' in project
