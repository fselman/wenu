from pathlib import Path
import runpy


EXAMPLE = (
    Path(__file__).parents[1]
    / "examples/cartoon_modes_explicit_labels.py"
)


def namespace():
    return runpy.run_path(str(EXAMPLE))


def test_example_exposes_all_requested_label_positions():
    values = namespace()
    assert values["CONSTELLATION_LABEL_POSITIONS"] == {
        "Cyg": "cl",
        "Lyr": "ur",
        "Vul": "ll",
        "Sge": "lr",
        "Aql": "ur",
    }
    assert set(values["CONSTELLATION_LABEL_OFFSETS"]) == {
        "Cyg", "Lyr", "Vul", "Sge", "Aql"
    }


def test_only_presentation_enables_milky_way():
    values = namespace()
    assert "milky_way" not in values["content_layers"]("print")
    assert (
        "milky_way"
        in values["content_layers"]("presentation")
    )


def test_example_loads_milky_way_isophotes():
    source = EXAMPLE.read_text(encoding="utf-8")
    assert "sky.add_milky_way_isophotes()" in source
