"""Milestone 44I structured user-guide and README provenance contracts."""

from hashlib import sha256
import importlib.util
from pathlib import Path
import struct

import pytest

from wenu import chart_product_options


ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "docs/user_guide"
IMAGE = GUIDE / "assets/la-ligua-planisphere.png"
IMAGE_SHA256 = (
    "5f4d7a17f6e7334e39cd3d28a158010ce59c80dbabd58f112a52fe62f1cedbba"
)
GUIDE_PAGES = (
    "index.md",
    "planisphere.md",
    "regional_charts.md",
    "circumpolar_charts.md",
    "binocular_charts.md",
    "styles_modes_detail.md",
)
EXAMPLES = (
    "planisphere.py",
    "regional_constellation_group.py",
    "regional_constellation.py",
    "circumpolar.py",
    "binocular_object.py",
)


def load_example(filename):
    path = ROOT / "examples" / filename
    spec = importlib.util.spec_from_file_location(
        f"documented_{path.stem}", path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def png_dimensions(path):
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert data[12:16] == b"IHDR"
    return struct.unpack(">II", data[16:24])


def test_structured_user_guide_has_the_target_pages():
    assert {path.name for path in GUIDE.glob("*.md")} == set(GUIDE_PAGES)


def test_guide_index_names_all_five_canonical_examples():
    text = (GUIDE / "index.md").read_text(encoding="utf-8")
    for filename in EXAMPLES:
        assert f"examples/{filename}" in text


@pytest.mark.parametrize("filename", EXAMPLES)
def test_documented_examples_expose_the_shared_product_contract(filename):
    module = load_example(filename)
    arguments = module.parser().parse_args([
        "--style", "cartoon",
        "--mode", "presentation",
        "--output", "output/documented.png",
    ])
    options = chart_product_options(arguments)

    assert options.style == "cartoon"
    assert options.mode == "presentation"
    assert options.output == Path("output/documented.png")
    assert len(options.products) == 1


def test_readme_quick_start_uses_the_canonical_planisphere_interface():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "python examples/planisphere.py" in text
    assert "--style cartoon --mode presentation" in text
    assert "--output output/la-ligua-planisphere.png" in text
    assert "--credits" in text
    assert "docs/user_guide/assets/la-ligua-planisphere.png" in text


def test_readme_image_matches_its_recorded_binary_contract():
    assert png_dimensions(IMAGE) == (1129, 1030)
    assert sha256(IMAGE.read_bytes()).hexdigest() == IMAGE_SHA256


def test_planisphere_provenance_is_complete_and_reproducible():
    text = (GUIDE / "planisphere.md").read_text(encoding="utf-8")
    for value in (
        "examples/planisphere.py",
        "44c16fd",
        "5fcde48",
        "1129 × 1030",
        IMAGE_SHA256,
        "--style cartoon --mode presentation",
        "--output docs/user_guide/assets/la-ligua-planisphere.png",
        "--credits",
        "visual approval",
    ):
        assert value in text


def test_english_and_spanish_readmes_link_the_structured_guide():
    for filename in ("README.md", "README.es.md"):
        text = (ROOT / filename).read_text(encoding="utf-8")
        assert "docs/user_guide/index.md" in text


def test_legacy_user_guide_paths_point_to_the_structured_guide():
    for filename in ("docs/user_guide.md", "docs/user_guide.es.md"):
        text = (ROOT / filename).read_text(encoding="utf-8")
        assert "user_guide/index.md" in text
