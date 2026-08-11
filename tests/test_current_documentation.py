"""Current public-documentation and architecture-authority contracts."""

from pathlib import Path
import ast
import re


ROOT = Path(__file__).resolve().parents[1]
DEVELOPER = ROOT / "docs" / "developer"
CURRENT = DEVELOPER / "current_architecture_v0.7.md"
IMPLEMENTED = DEVELOPER / "target_architecture_v0.7.md"
TARGET = DEVELOPER / "target_architecture_v0.8.md"
ROADMAP = DEVELOPER / "wenu_migration_0.7_to_0.8.md"
INSTRUCTIONS = DEVELOPER / "assistant_instructions.md"
PUBLIC_DOCUMENTS = (
    ROOT / "README.md",
    ROOT / "README.es.md",
    DEVELOPER / "implementation_reference.md",
    DEVELOPER / "source_tree.md",
    *sorted((ROOT / "docs" / "user_guide").glob("*.md")),
)
OBSOLETE_IMPORTS = (
    "wenu.spherical",
    "wenu.projected",
    "wenu.spherical_frame",
    "wenu.clipping",
    "wenu.viewport",
    "wenu.projection",
    "wenu.chart",
    "wenu.regional",
    "wenu.styles",
    "wenu.renderers",
)


def read(path):
    return path.read_text(encoding="utf-8")


def fenced_python(path):
    """Return Python code blocks from one Markdown document."""
    blocks = []
    current = None
    for line in read(path).splitlines():
        if line == "```python":
            current = []
        elif line == "```" and current is not None:
            blocks.append("\n".join(current))
            current = None
        elif current is not None:
            current.append(line)
    return blocks


def test_current_architecture_authorities_exist_and_cross_reference():
    assert [
        path
        for path in (CURRENT, IMPLEMENTED, TARGET, ROADMAP, INSTRUCTIONS)
        if not path.is_file()
    ] == []

    current = read(CURRENT)
    target = read(TARGET)
    roadmap = read(ROADMAP)

    assert "target_architecture_v0.7.md" in current
    assert "current_architecture_v0.7.md" in target
    assert "wenu_migration_0.7_to_0.8.md" in target
    assert "current_architecture_v0.7.md" in roadmap
    assert "target_architecture_v0.8.md" in roadmap


def test_assistant_instructions_name_current_architecture_authorities():
    instructions = read(INSTRUCTIONS)
    for name in (
        "current_architecture_v0.7.md",
        "target_architecture_v0.7.md",
        "target_architecture_v0.8.md",
        "wenu_migration_0.7_to_0.8.md",
        "implementation_reference.md",
        "source_tree.md",
    ):
        assert name in instructions


def test_v08_roadmap_records_ordinary_interface_and_static_sequences():
    target = read(TARGET)
    roadmap = read(ROADMAP)

    for phrase in (
        "Three-stage ordinary Python interface",
        "observer-independent loaded-content container",
        "Defining a projection and applying it are separate operations",
        "fewer than 70 lines",
        "Reproducible image-frame sequences",
        "does not encode movies",
    ):
        assert phrase in target

    for phrase in (
        "Milestone 46C.8G",
        "Milestone 46C.8O",
        "Pass observer explicitly through canonical execution",
        "Decouple maximal-sphere construction",
        "one observer-independent canonical maximal sphere",
        "fewer-than-70-line declarative examples",
        "movie encoding",
        "Hawaii-to-Tahiti",
        "coordinate-epoch precession",
    ):
        assert phrase in roadmap


def test_documented_python_is_syntactically_valid():
    for document in (
        ROOT / "README.md",
        DEVELOPER / "implementation_reference.md",
    ):
        for block in fenced_python(document):
            ast.parse(block, filename=str(document))


def test_documented_canonical_public_imports_execute():
    namespace = {}
    import_block = fenced_python(
        DEVELOPER / "implementation_reference.md"
    )[0]
    exec(import_block, namespace)
    for name in (
        "compose_chart",
        "LegendOptions",
        "RegionalChart",
        "FullSkyChart",
        "CircumpolarChart",
        "BinocularChart",
    ):
        assert name in namespace


def test_public_documents_do_not_recommend_obsolete_imports():
    violations = []
    for path in PUBLIC_DOCUMENTS:
        text = read(path)
        for obsolete in OBSOLETE_IMPORTS:
            pattern = re.compile(
                rf"\b(?:from|import)\s+{re.escape(obsolete)}(?=\s|$)"
            )
            if pattern.search(text):
                violations.append(f"{path.relative_to(ROOT)}: {obsolete}")
    assert violations == []
