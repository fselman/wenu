import importlib.util
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse


def load_example():
    path = Path("tests/fixtures/example_regressions/stellar_magnitude_legend.py")
    specification = importlib.util.spec_from_file_location(
        "stellar_magnitude_legend_example_repaired",
        path,
    )
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_visual_uses_separate_stars_and_objects_legends(tmp_path):
    module = load_example()
    destination = tmp_path / "reference.png"
    figure, _, object_legend, result = module.draw_reference(
        destination,
        dpi=80,
    )
    assert destination.is_file()
    assert object_legend.get_title().get_text() == "Objects"
    assert result.artist.get_title().get_text() == "Stars"
    assert object_legend is not result.artist
    plt.close(figure)


def test_plotted_stars_do_not_obscure_the_stars_legend():
    module = load_example()
    figure, ax, _, result = module.draw_reference()
    figure.canvas.draw()
    legend_box = result.artist.get_window_extent(
        figure.canvas.get_renderer()
    )
    star_collection = ax.collections[0]
    display_points = ax.transData.transform(
        star_collection.get_offsets()
    )
    assert not any(
        legend_box.contains(float(x), float(y))
        for x, y in display_points
    )
    plt.close(figure)


def test_object_legend_galaxy_handle_is_elliptical():
    module = load_example()
    figure, _, object_legend, _ = module.draw_reference()
    handles = object_legend.legend_handles
    assert len(handles) == 1
    assert isinstance(handles[0], Ellipse)
    assert handles[0].width > handles[0].height
    assert handles[0].get_facecolor()[-1] > 0.0
    plt.close(figure)
