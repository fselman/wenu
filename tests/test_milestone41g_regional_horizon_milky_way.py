from pathlib import Path
from types import SimpleNamespace

from wenu.charts.context import BoundaryKind
from wenu.charts.detail_application import composition_layer_options


class RecordingStyle:
    def __init__(self):
        self.horizon_altitude_deg = "not called"

    def layer_options(self, sky, *, horizon_altitude_deg=None):
        self.horizon_altitude_deg = horizon_altitude_deg
        return {}


class EmptySky:
    layers = ()


class EmptyDetail:
    star_magnitude_limit = None
    galaxy_magnitude_limit = None
    constellation_star_mode = None
    extra_star_ids = frozenset()

    def layer_enabled(self, name):
        return True


def composition(boundary_kind):
    style = RecordingStyle()
    value = SimpleNamespace(
        style=style,
        detail=EmptyDetail(),
        context=SimpleNamespace(boundary_kind=boundary_kind),
    )
    return value, style


def test_rectangular_regional_composition_disables_horizon_clipping():
    value, style = composition(BoundaryKind.RECTANGULAR)
    composition_layer_options(
        value,
        EmptySky(),
        reload_catalogues=False,
    )
    assert style.horizon_altitude_deg == -90.0


def test_non_rectangular_chart_retains_style_horizon_default():
    value, style = composition(BoundaryKind.CIRCULAR)
    composition_layer_options(
        value,
        EmptySky(),
        reload_catalogues=False,
    )
    assert style.horizon_altitude_deg is None


def test_cartoon_example_enables_milky_way_only_in_presentation():
    namespace = {}
    source = Path("tests/fixtures/example_regressions/cartoon_modes_explicit_labels.py").read_text()
    exec(compile(source, "cartoon_modes_explicit_labels.py", "exec"), namespace)
    assert "milky_way" not in namespace["content_layers"]("print")
    assert "milky_way" in namespace["content_layers"]("presentation")


def test_cartoon_example_uses_canonical_polygon_projection():
    source = Path("tests/fixtures/example_regressions/cartoon_modes_explicit_labels.py").read_text()
    assert "clip_polygons_to_projection_cap" not in source
    assert 'milky_way_options["prepare"]' not in source
    assert "horizon_altitude_deg=-90.0" not in source
