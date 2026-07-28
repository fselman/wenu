from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

from wenu import AtlasChartStyle, legend_symbol_descriptors
from wenu.charts.legend import (
    _legend_handle,
    _legend_handler_map,
)


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "legend_symbols.py"


def galaxy_descriptor():
    sky = SimpleNamespace(
        open_clusters=None,
        globular_clusters=None,
        planetary_nebulae=None,
        supernova_remnants=None,
        galaxies=object(),
        milky_way_isophotes=None,
    )
    return legend_symbol_descriptors(
        sky,
        AtlasChartStyle(),
    )[0]


def load_example():
    spec = spec_from_file_location("legend_symbols_example", EXAMPLE)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_galaxy_descriptor_has_a_filled_face():
    descriptor = galaxy_descriptor()
    assert descriptor.face_color not in (None, "none")
    assert descriptor.face_color == descriptor.edge_color


def test_galaxy_legend_handle_is_an_elongated_ellipse():
    handle = _legend_handle(galaxy_descriptor())
    assert isinstance(handle, Ellipse)
    assert handle.width > handle.height
    assert handle.get_fill()


def test_ellipse_has_a_dedicated_legend_handler():
    handler_map = _legend_handler_map()
    assert Ellipse in handler_map


def test_visual_reference_draws_a_galaxy_ellipse():
    module = load_example()
    figure, ax, _, _ = module.draw_reference()
    try:
        ellipses = [
            patch
            for patch in ax.patches
            if isinstance(patch, Ellipse)
        ]
        assert len(ellipses) == 1
        assert ellipses[0].width > ellipses[0].height
        assert ellipses[0].get_fill()
    finally:
        plt.close(figure)


def test_visual_reference_can_be_saved(tmp_path):
    module = load_example()
    destination = tmp_path / "galaxy-ellipse.png"
    figure, _, _, _ = module.draw_reference(destination, dpi=72)
    try:
        assert destination.is_file()
        assert destination.stat().st_size > 0
    finally:
        plt.close(figure)
