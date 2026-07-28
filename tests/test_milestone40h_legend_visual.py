from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from wenu.rendering.symbols import DEFAULT_SYMBOLS


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "legend_symbols.py"


def load_example():
    spec = spec_from_file_location("legend_symbols_example", EXAMPLE)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reference_contains_every_supported_symbol():
    module = load_example()
    figure, _, descriptors, handles = module.draw_reference()
    try:
        assert [item.key for item in descriptors] == [
            "open_cluster",
            "globular_cluster",
            "planetary_nebula",
            "supernova_remnant",
            "galaxy",
            "milky_way",
        ]
        assert len(handles) == len(descriptors)
    finally:
        plt.close(figure)


def test_reference_uses_canonical_fixed_marker_paths():
    module = load_example()
    figure, _, descriptors, handles = module.draw_reference()
    try:
        by_key = dict(zip((item.key for item in descriptors), handles))
        assert (
            by_key["open_cluster"].get_marker()
            is DEFAULT_SYMBOLS.open_cluster
        )
        assert (
            by_key["planetary_nebula"].get_marker()
            is DEFAULT_SYMBOLS.planetary_nebula
        )
    finally:
        plt.close(figure)


def test_reference_uses_marker_and_patch_handle_families():
    module = load_example()
    figure, _, descriptors, handles = module.draw_reference()
    try:
        pairs = dict(zip((item.key for item in descriptors), handles))
        assert isinstance(pairs["open_cluster"], Line2D)
        assert isinstance(pairs["globular_cluster"], Line2D)
        assert isinstance(pairs["planetary_nebula"], Line2D)
        assert isinstance(pairs["supernova_remnant"], Line2D)
        assert isinstance(pairs["galaxy"], Patch)
        assert isinstance(pairs["milky_way"], Patch)
    finally:
        plt.close(figure)


def test_reference_writes_to_requested_destination(tmp_path):
    module = load_example()
    destination = tmp_path / "legend-reference.png"
    figure, _, _, _ = module.draw_reference(destination, dpi=72)
    try:
        assert destination.is_file()
        assert destination.stat().st_size > 0
    finally:
        plt.close(figure)


def test_default_output_keeps_repository_root_clean():
    module = load_example()
    assert module.OUTPUT == Path("output/legend-symbols")
