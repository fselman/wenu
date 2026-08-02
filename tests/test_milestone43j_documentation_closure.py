"""Milestone 43J v0.5 documentation closure contracts."""

from pathlib import Path
import ast


ROOT = Path(__file__).resolve().parents[1]


def fenced_python(path):
    """Return Python code blocks from one Markdown document."""
    blocks = []
    current = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line == "```python":
            current = []
        elif line == "```" and current is not None:
            blocks.append("\n".join(current))
            current = None
        elif current is not None:
            current.append(line)
    return blocks


def test_documented_python_is_syntactically_valid():
    documents = (
        ROOT / "README.md",
        ROOT / "docs/developer/implementation_reference.md",
    )
    for document in documents:
        for block in fenced_python(document):
            ast.parse(block, filename=str(document))


def test_documented_canonical_public_imports_execute():
    namespace = {}
    import_block = fenced_python(
        ROOT / "docs/developer/implementation_reference.md"
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


def test_public_documents_recommend_canonical_composition():
    for relative in (
        "README.md",
        "README.es.md",
        "docs/developer/implementation_reference.md",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "v0.5" in text
    for relative in (
        "README.md",
        "docs/developer/implementation_reference.md",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "compose_chart" in text
        assert "LegendOptions" in text


def test_superseded_composition_roadmap_is_archived():
    active = ROOT / "docs/developer/milestone40_chart_composition_roadmap.md"
    archived = (
        ROOT
        / "docs/developer/archive/milestone40_chart_composition_roadmap.md"
    )
    assert not active.exists()
    assert archived.is_file()


def test_v05_compatibility_and_extension_procedures_are_documented():
    reference = (
        ROOT / "docs/developer/implementation_reference.md"
    ).read_text(encoding="utf-8")
    deprecations = (
        ROOT / "docs/developer/deprecations_v0.5.md"
    ).read_text(encoding="utf-8")
    for concept in ("style", "output mode", "detail policy", "legend"):
        assert concept in reference.lower()
    assert "compose_cartoon_chart" in deprecations
    assert "compose_chart" in deprecations
