"""Current fixed-sky API discovery and scientific-ownership documentation."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEVELOPER = ROOT / "docs/developer"


def documented_names(module, names):
    source = ROOT / "src/wenu/charts" / (module + ".py")
    definitions = {n.name for n in ast.parse(source.read_text()).body
                   if isinstance(n, (ast.ClassDef, ast.FunctionDef))}
    reference = (DEVELOPER / "implementation_reference.md").read_text()
    source_map = (DEVELOPER / "source_tree.md").read_text()
    assert set(names) <= definitions
    assert "charts/" + module + ".py" in source_map
    for name in names:
        assert "`" + name + "`" in reference


def test_fixed_sky_contract_separates_celestial_and_local_time_owners():
    documented_names("fixed_sky_sequence", ("FixedSkyRotatingHorizonSequenceRequest",))
    contract = (DEVELOPER / "scientific_contracts.md").read_text()
    for field in ("celestial_anchor_time", "simulation_time", "catalogue reference epoch"):
        assert "`" + field + "`" in contract


def test_fixed_sky_baseline_documents_complete_rendering_limits():
    documented_names("fixed_sky_baseline", (
        "PngFrameComparisonTolerance", "generate_fixed_sky_complete_render_baseline"))
    contract = (DEVELOPER / "scientific_contracts.md").read_text()
    assert "Graphical tolerance is separate from angular state tolerance" in contract


def test_fixed_sky_reference_documents_accepted_target_behavior():
    documented_names("fixed_sky_orientation", ("fixed_sky_circumpolar_orientation",))
    documented_names("fixed_sky_sequence", ("generate_fixed_sky_rotating_horizon_sequence",))
    contract = (DEVELOPER / "scientific_contracts.md").read_text()
    assert "fixed celestial scene" in contract
    assert "rotating local horizon" in contract
