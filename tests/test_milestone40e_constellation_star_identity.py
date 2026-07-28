from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from wenu.sky.constellation_lines import ConstellationLines


def make_lines(tmp_path, *, available=(1, 2, 3, 4, 5)):
    filename = tmp_path / "test.fab"
    filename.write_text(
        "AAA 3 1 2 3\n"
        "BBB 3 3 4 5\n",
        encoding="utf-8",
    )
    stars = SimpleNamespace(
        catalog=pd.DataFrame(index=list(available)),
    )
    return ConstellationLines(stars, filename=filename)


def test_star_ids_are_immutable_and_deduplicated(tmp_path):
    lines = make_lines(tmp_path)
    assert lines.star_ids == frozenset({1, 2, 3, 4, 5})
    with pytest.raises(AttributeError):
        lines.star_ids.add(6)


def test_ids_are_available_by_constellation(tmp_path):
    lines = make_lines(tmp_path)
    assert lines.star_ids_by_constellation["AAA"] == frozenset({1, 2, 3})
    assert lines.star_ids_by_constellation["BBB"] == frozenset({3, 4, 5})
    with pytest.raises(TypeError):
        lines.star_ids_by_constellation["AAA"] = frozenset()


def test_selected_constellation_ids_are_deduplicated(tmp_path):
    lines = make_lines(tmp_path)
    assert lines.star_ids_for(["AAA"]) == frozenset({1, 2, 3})
    assert lines.star_ids_for(["AAA", "BBB"]) == lines.star_ids


def test_unknown_loaded_constellation_is_explicit(tmp_path):
    lines = make_lines(tmp_path)
    with pytest.raises(KeyError, match="CCC"):
        lines.star_ids_for(["CCC"])


def test_missing_catalogue_identifiers_are_reported(tmp_path):
    lines = make_lines(tmp_path, available=(1, 2, 4, 5))
    assert lines.resolvable_star_ids == frozenset({1, 2, 4, 5})
    assert lines.unresolved_star_ids == frozenset({3})
    with pytest.raises(LookupError, match="3"):
        lines.require_resolved_star_ids()


def test_selected_load_exposes_only_requested_figure(tmp_path):
    filename = tmp_path / "test.fab"
    filename.write_text(
        "AAA 3 1 2 3\n"
        "BBB 3 3 4 5\n",
        encoding="utf-8",
    )
    stars = SimpleNamespace(
        catalog=pd.DataFrame(index=[1, 2, 3, 4, 5]),
    )
    lines = ConstellationLines(
        stars,
        filename=filename,
        constellations=["BBB"],
    )
    assert lines.star_ids == frozenset({3, 4, 5})
    assert set(lines.star_ids_by_constellation) == {"BBB"}


def test_source_contains_no_chart_style_or_renderer_dependency():
    import wenu.sky.constellation_lines as module

    source = Path(module.__file__).read_text(encoding="utf-8").lower()
    assert "matplotlib" not in source
    assert "chartstyle" not in source
    assert "cartoon" not in source
