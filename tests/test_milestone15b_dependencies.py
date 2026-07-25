"""Milestone 15B dependency-direction and legacy-removal tests."""

from __future__ import annotations

import ast
from pathlib import Path

from wenu.sky.celestial_sphere import CelestialSphere
from wenu.sky.constellations import Constellations


ROOT = Path(__file__).parents[1]
DOMAIN_ROOTS = (
    ROOT / "src/wenu/objects",
    ROOT / "src/wenu/sky",
)
FORBIDDEN_IMPORTS = (
    "matplotlib",
    "wenu.projected",
    "wenu.projection",
    "wenu.renderers",
)
REMOVED_PATHS = (
    "src/wenu/regional_chart.py",
    "src/wenu/sky/curves.py",
    "src/wenu/renderers/stars.py",
    "src/wenu/renderers/celestial_points.py",
    "src/wenu/renderers/constellation_lines.py",
    "src/wenu/renderers/constellation_boundaries.py",
    "src/wenu/renderers/coordinate_grids.py",
)


def _domain_modules():
    for root in DOMAIN_ROOTS:
        yield from root.rglob("*.py")


def _imports(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


def test_domain_packages_have_no_reverse_dependencies():
    violations = []
    for path in _domain_modules():
        tree = ast.parse(path.read_text(), filename=str(path))
        for imported in _imports(tree):
            if imported.startswith(FORBIDDEN_IMPORTS):
                violations.append(
                    f"{path.relative_to(ROOT)} imports {imported}"
                )
    assert violations == []


def test_domain_layers_have_no_direct_draw_methods():
    violations = []
    for path in _domain_modules():
        if path.name == "celestial_sphere.py":
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == "draw":
                    violations.append(
                        f"{path.relative_to(ROOT)}:{node.lineno}"
                    )
    assert violations == []


def test_temporary_modules_are_removed():
    assert [
        path for path in REMOVED_PATHS
        if (ROOT / path).exists()
    ] == []


def test_celestial_sphere_has_no_renderer_state():
    sphere = CelestialSphere(observer=object())
    for name in (
        "star_renderer",
        "point_renderer",
        "constellation_boundary_renderer",
    ):
        assert not hasattr(sphere, name)


def test_legacy_drawing_api_is_removed():
    for name in (
        "draw_equatorial",
        "draw_equatorial_grid",
        "draw_ecliptic",
        "draw_ecliptic_grid",
        "draw_galactic_plane",
        "draw_galactic_grid",
        "draw",
    ):
        assert not hasattr(CelestialSphere, name)
    assert not hasattr(Constellations, "draw")


def test_obsolete_altaz_helpers_are_removed():
    import wenu.geometry as geometry

    for name in (
        "constant_declination_altaz",
        "equator_altaz",
        "ecliptic_altaz",
        "ecliptic_keypoints_altaz",
        "galactic_plane_altaz",
        "galactic_center_altaz",
    ):
        assert not hasattr(geometry, name)
    assert callable(geometry.radec_to_altaz)
