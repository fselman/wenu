from pathlib import Path
import runpy

from wenu import compose_chart


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "tests" / "fixtures" / "example_regressions" / "cartoon_modes.py"


def example_namespace():
    return runpy.run_path(EXAMPLE)


def test_example_declares_one_shared_scene_for_both_modes():
    namespace = example_namespace()
    assert namespace["CONSTELLATIONS"] == (
        "Cyg",
        "Lyr",
        "Vul",
        "Sge",
        "Aql",
    )
    source = EXAMPLE.read_text()
    assert source.count("build_scene()") == 2
    assert 'for mode in ("print", "presentation")' in source


def test_example_outputs_live_below_output_directory():
    namespace = example_namespace()
    assert namespace["DEFAULT_OUTPUT"] == Path("output/cartoon-modes")


def test_mode_pair_preserves_context_and_content(monkeypatch):
    namespace = example_namespace()
    sky, chart = namespace["build_scene"]()
    printed = compose_chart(chart, style="cartoon", mode="print")
    presented = compose_chart(
        chart,
        style="cartoon",
        mode="presentation",
    )
    assert printed.context == presented.context
    assert printed.detail == presented.detail
    assert printed.style.canvas.sky_color == "white"
    assert presented.style.canvas.sky_color == "#1677A6"


def test_cartoon_scene_contains_only_required_registered_layers():
    namespace = example_namespace()
    sky, _ = namespace["build_scene"]()
    assert sky.stars is not None
    assert sky.constellation_lines is not None
    assert sky.constellation_labels is not None
    assert sky.open_clusters is None
    assert sky.galaxies is None
    assert sky.milky_way_isophotes is None


def test_example_uses_resolved_dimensions_and_canonical_export():
    source = EXAMPLE.read_text()
    assert "resolved.width_inches" in source
    assert "resolved.height_inches" in source
    assert "composition=composition" in source
    assert "composition.layer_options" not in source
    assert "figure.savefig" not in source
    assert "compose_cartoon_chart" not in source


def test_crowded_constellation_labels_have_explicit_offsets():
    source = EXAMPLE.read_text()
    assert '"Lyr": (0.34, 0.22)' in source
    assert '"Vul": (-0.48, -0.16)' in source
    assert '"Sge": (0.38, -0.30)' in source


def test_presentation_palette_avoids_red_on_blue():
    namespace = example_namespace()
    _, chart = namespace["build_scene"]()
    composition = compose_chart(
        chart,
        style="cartoon",
        mode="presentation",
    )
    style = composition.style
    assert style.canvas.sky_color == "#1677A6"
    assert style.stars.color == "#FFE066"
    assert style.grids.constellation_line_color == "#FFE066"
    assert style.grids.constellation_label_color == "#FFE066"
