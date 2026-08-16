"""Milestone 22 package-boundary and clean-break audit."""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import wenu


ROOT = Path(__file__).parents[1]
SOURCE = ROOT / "src/wenu"

PACKAGE_RULES = {
    "geometry": (
        "matplotlib",
        "wenu.objects",
        "wenu.sky",
        "wenu.projections",
        "wenu.charts",
        "wenu.rendering",
    ),
    "objects": (
        "matplotlib",
        "wenu.geometry.projected",
        "wenu.projections",
        "wenu.charts",
        "wenu.rendering",
    ),
    "sky": (
        "matplotlib",
        "wenu.geometry.projected",
        "wenu.projections",
        "wenu.charts",
        "wenu.rendering",
    ),
    "projections": (
        "matplotlib",
        "wenu.objects",
        "wenu.sky",
        "wenu.charts",
        "wenu.rendering",
    ),
    "rendering": (
        "wenu.objects",
        "wenu.sky",
        "wenu.projections",
        "wenu.charts",
    ),
}

OBSOLETE_PATHS = (
    "src/wenu/geometry.py",
    "src/wenu/spherical.py",
    "src/wenu/projected.py",
    "src/wenu/spherical_frame.py",
    "src/wenu/clipping.py",
    "src/wenu/viewport.py",
    "src/wenu/projection.py",
    "src/wenu/chart.py",
    "src/wenu/regional.py",
    "src/wenu/styles.py",
    "src/wenu/rendering.py",
    "src/wenu/renderers",
)

OBSOLETE_MODULES = (
    "wenu.spherical",
    "wenu.projected",
    "wenu.spherical_frame",
    "wenu.clipping",
    "wenu.viewport",
    "wenu.projection",
    "wenu.chart",
    "wenu.regional",
    "wenu.styles",
    "wenu.renderers",
)

REQUIRED_MODULES = (
    "wenu.coordinates",
    "wenu.geometry.spherical",
    "wenu.geometry.projected",
    "wenu.geometry.frame",
    "wenu.geometry.clipping",
    "wenu.geometry.viewport",
    "wenu.projections.mollweide",
    "wenu.projections.polar_azimuthal_equidistant",
    "wenu.projections.stereographic",
    "wenu.charts.projection_selection",
    "wenu.sky.rendering_results",
    "wenu.charts.regional",
    "wenu.charts.polar_planisphere",
    "wenu.charts.polar_planisphere_pair",
    "wenu.charts.polar_calendar",
    "wenu.charts.polar_calendar_furniture",
    "wenu.charts.polar_page_furniture",
    "wenu.charts.polar_page_rendering",
    "wenu.charts.polar_page_export",
    "wenu.charts.polar_planisphere_style",
    "wenu.charts.styles",
    "wenu.rendering.preparation",
    "wenu.rendering.matplotlib",
)

PUBLIC_EXPORTS = (
    "ChartRenderingResult",
    "LayerRenderingResult",
    "Observer",
    "ExportOptions",
    "RegionalChart",
    "PublicationStyle",
    "MatplotlibRenderer",
    "MollweideProjection",
    "PolarAzimuthalEquidistantProjection",
    "PolarPlanisphereChart",
    "PolarPlanispherePairRequest",
    "CommonYearCalendarRequest",
    "PolarCalendarFurnitureRequest",
    "PolarPlanisphereDetailPolicy",
    "PolarPlanisphereStylePalette",
    "polar_planisphere_chart_style",
    "ProjectionSelection",
    "StereographicProjection",
    "CelestialSphere",
    "SphericalCoordinates",
    "SphericalFrame",
    "Viewport",
    "ProjectedCurve",
    "ProjectedPoint",
    "ProjectedPolygon",
)


def _python_files(path):
    yield from sorted(path.rglob("*.py"))


def _imports(path):
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


def _dynamic_import_references(path):
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        function = node.func
        is_dynamic_import = (
            isinstance(function, ast.Name)
            and function.id == "__import__"
        ) or (
            isinstance(function, ast.Attribute)
            and isinstance(function.value, ast.Name)
            and function.value.id == "importlib"
            and function.attr == "import_module"
        )
        if not is_dynamic_import:
            continue
        argument = node.args[0]
        if not (
            isinstance(argument, ast.Constant)
            and isinstance(argument.value, str)
        ):
            continue
        value = argument.value
        for obsolete in OBSOLETE_MODULES:
            if value == obsolete or value.startswith(obsolete + "."):
                yield value


def test_target_packages_exist():
    for name in (
        "geometry",
        "projections",
        "charts",
        "rendering",
    ):
        path = SOURCE / name
        assert path.is_dir(), path
        assert (path / "__init__.py").is_file(), path


def test_obsolete_paths_are_absent():
    assert [
        path
        for path in OBSOLETE_PATHS
        if (ROOT / path).exists()
    ] == []


def test_package_dependency_directions():
    violations = []
    for package, forbidden in PACKAGE_RULES.items():
        for path in _python_files(SOURCE / package):
            for imported in _imports(path):
                if imported.startswith(forbidden):
                    violations.append(
                        f"{path.relative_to(ROOT)} imports {imported}"
                    )
    assert violations == []


def test_obsolete_imports_and_dynamic_import_strings_are_absent():
    violations = []
    roots = (
        ROOT / "src",
        ROOT / "tests",
        ROOT / "examples",
    )
    this_test = Path(__file__).resolve()
    for root in roots:
        for path in _python_files(root):
            if path.resolve() == this_test:
                continue
            for imported in _imports(path):
                if imported in OBSOLETE_MODULES or any(
                    imported.startswith(name + ".")
                    for name in OBSOLETE_MODULES
                ):
                    violations.append(
                        f"{path.relative_to(ROOT)} imports {imported}"
                    )
            for referenced in _dynamic_import_references(path):
                violations.append(
                    f"{path.relative_to(ROOT)} references {referenced}"
                )
    assert violations == []


def test_required_modules_are_importable():
    for module in REQUIRED_MODULES:
        imported = importlib.import_module(module)
        assert imported is not None


def test_intentional_top_level_exports_are_available():
    assert set(PUBLIC_EXPORTS) <= set(wenu.__all__)
    for name in PUBLIC_EXPORTS:
        assert getattr(wenu, name) is not None
