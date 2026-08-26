"""Milestone 44I structured user-guide and README provenance contracts."""

from hashlib import sha256
from pathlib import Path
import struct


ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "docs/user_guide"
IMAGE = GUIDE / "assets/la-ligua-planisphere.png"
IMAGE_SHA256 = (
    "5f4d7a17f6e7334e39cd3d28a158010ce59c80dbabd58f112a52fe62f1cedbba"
)
GUIDE_PAGES = (
    "index.md",
    "all_sky.md",
    "planisphere.md",
    "regional_charts.md",
    "circumpolar_charts.md",
    "binocular_charts.md",
    "styles_modes_detail.md",
    "configuration.md",
    "svg_output.md",
)
EXAMPLES = (
    "all_sky.py",
    "planisphere.py",
    "regional_constellation_group.py",
    "regional_constellation.py",
    "circumpolar.py",
    "binocular_object.py",
)


def png_dimensions(path):
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert data[12:16] == b"IHDR"
    return struct.unpack(">II", data[16:24])


def test_structured_user_guide_has_the_target_pages():
    assert {path.name for path in GUIDE.glob("*.md")} == set(GUIDE_PAGES)


def test_guide_index_names_all_canonical_examples():
    text = (GUIDE / "index.md").read_text(encoding="utf-8")
    for filename in EXAMPLES:
        assert f"examples/{filename}" in text


def test_regional_guide_uses_arbitrary_constellation_sets():
    text = (GUIDE / "regional_charts.md").read_text(encoding="utf-8")

    assert "--constellations Sgr,Sco,Oph,Ser" in text
    assert "--constellations Cen,Cru,Mus --mask" in text
    assert "--group summer-triangle" in text

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


def test_planisphere_guide_documents_disjoint_visible_masks():
    text = (GUIDE / "planisphere.md").read_text(encoding="utf-8")

    assert "--constellations Cru,Cyg,UMa --mask" in text
    assert "wholly below" in text
    assert "crossing" in text


def test_all_sky_guide_documents_galactic_mollweide_geometry():
    text = (GUIDE / "all_sky.md").read_text(encoding="utf-8")

    for value in (
        "examples/all_sky.py",
        'family="all_sky"',
        'projection="mollweide"',
        'coordinate_frame="galactic"',
        "Galactic longitude zero",
        "180° seam",
        "--constellations Cru,Cyg,UMa --mask",
    ):
        assert value in text


def test_shared_guide_documents_independent_horizon_roles():
    text = " ".join(
        (GUIDE / "styles_modes_detail.md").read_text(encoding="utf-8").split()
    )

    for value in (
        "--horizon",
        "--horizon-mask",
        "one translucent mask",
        "intentional no-ops",
        "Galactic Mollweide",
    ):
        assert value in text


def test_configuration_guide_documents_template_and_profiles():
    text = (GUIDE / "configuration.md").read_text(encoding="utf-8")

    for value in (
        "wenu_chart defaults --write profiles/publication.toml",
        "packaged defaults.toml < --config TOML < explicit CLI arguments",
        "`solid`",
        "`dashed`",
        "`dotted`",
        "`dash_dot`",
        "`none`",
        "publication.toml",
        "presentation.toml",
        "outreach.toml",
        "papudo.toml",
        "binocular-observing.toml",
        "no profile inheritance or multi-file stacking",
    ):
        assert value in text


def test_circumpolar_guide_documents_horizon_crossing_framing():
    text = (GUIDE / "circumpolar_charts.md").read_text(encoding="utf-8")

    assert "--limiting-declination -30 --horizon --horizon-mask" in text
    assert "--declination-step 10" in text


def test_english_and_spanish_readmes_link_the_structured_guide():
    for filename in ("README.md", "README.es.md"):
        text = (ROOT / filename).read_text(encoding="utf-8")
        assert "docs/user_guide/index.md" in text


def test_legacy_user_guide_paths_point_to_the_structured_guide():
    for filename in ("docs/user_guide.md", "docs/user_guide.es.md"):
        text = (ROOT / filename).read_text(encoding="utf-8")
        assert "user_guide/index.md" in text


def test_svg_guide_documents_editable_vector_contract():
    text = (GUIDE / "svg_output.md").read_text(encoding="utf-8")

    for value in (
        "--format png",
        "--format pdf",
        "--format svg",
        'data-wenu-edit="style"',
        'data-wenu-edit="layout"',
        "genuine SVG `<text>` elements",
        "does not embed the font file",
        "scientifically modified derivative",
        "Inkscape",
    ):
        assert value in text

    index = (GUIDE / "index.md").read_text(encoding="utf-8")
    assert "--format png|pdf|svg" in index
    assert "(svg_output.md)" in index
