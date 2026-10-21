"""Coverage contract for the shared repository-source inventory."""

from pathlib import Path

from repository_sources import ROOT, SOURCE_ROOT_NAMES, repository_sources


def test_repository_source_inventory_includes_every_applicable_python_file():
    expected = {
        path
        for name in SOURCE_ROOT_NAMES
        if (root := ROOT / name).is_dir()
        for path in root.rglob("*.py")
    }
    indexed = {source.path for source in repository_sources()}

    assert indexed == expected
    assert all(isinstance(path, Path) for path in indexed)


def test_maintenance_inventory_covers_tools_and_explicit_resource_owners():
    import json
    inventory = json.loads((ROOT / "docs/developer/kernel_migration_inventory_v1.json").read_text())
    rows = inventory["maintenance_resource_routing"]["consumers"]
    owners = {"src/curated_catalogue_packaging.py", "src/wenu/resources.py",
              "src/wenu/minor_body_acquisition.py", "src/wenu/minor_body_resources.py",
              "src/wenu/comet_discovery.py", "src/wenu/satchecker.py",
              "src/wenu/satellites/snapshot_acquisition.py"}
    expected = {str(p.relative_to(ROOT)) for p in (ROOT / "tools").rglob("*.py")} | owners
    assert set(rows) == expected
    assert all(row["classification"] in {
        "source-maintenance", "explicit-acquisition", "application-consumer",
        "independent-validation", "fixture-preparation", "manual-benchmark",
        "build-resource", "test-tooling", "external-development-helper",
    } and row["boundary"] for row in rows.values())


def _consumer_reconciliation():
    import json
    inventory = json.loads((ROOT / "docs/developer/kernel_migration_inventory_v1.json").read_text())
    return inventory, inventory["consumer_reconciliation"]


def test_consumer_reconciliation_covers_exact_current_sources_and_routes():
    import hashlib

    _, audit = _consumer_reconciliation()
    expected = {str(p.relative_to(ROOT))
                for name in ("src", "tools", "examples", "packages/wenu_kernel/src")
                for p in (ROOT / name).rglob("*.py")}
    assert set(audit["sources"]) == expected
    for path, row in audit["sources"].items():
        payload = (ROOT / path).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()
        assert row["git_blob_sha"] == actual, path
        assert row["group"] in audit["groups"] and row["purpose"], path
        assert audit["groups"][row["group"]]["route"], path
        assert row["evidence_ids"] and set(row["evidence_ids"]) <= audit["receipts"].keys(), path
    # A generic public-interface receipt cannot replace family routing evidence.
    anchors = {"objects/stars.py": "K3.05", "objects/nonstellar.py": "K3.12",
        "objects/galaxies.py": "K3.10", "objects/open_clusters.py": "K3.11",
        "objects/globular_clusters.py": "K3.13", "objects/planetary_nebulae.py": "K3.14",
        "objects/supernova_remnants.py": "K3.15", "sky/milky_way.py": "K3.16",
        "sky/coordinate_grids.py": "K3.17", "observer.py": "K3.18",
        "sky/assembly.py": "K3.19", "charts/atlas_sheet.py": "K3.21",
        "charts/polar_pouch_sheet.py": "K3.22", "charts/sequence.py": "K3.23",
        "charts/fixed_sky_sequence.py": "K3.24", "ephemeris_state.py": "K3.25",
        "sky/venus_disk.py": "K3.26", "sky/solar_system_tracks.py": "K3.27",
        "sky/ceres.py": "K3.28", "comet_discovery.py": "K3.29",
        "antisolar.py": "K3.30", "satellites/sgp4.py": "K3.31",
        "satchecker.py": "K3.32", "satellites/crossing_batch.py": "K3.33",
        "satellite_crossing_reports.py": "K3.34", "satellites/illumination.py": "K3.35",
        "satellites/radiometry.py": "K3.36", "configuration/translation.py": "K3.37",
        "resources.py": "K3.38", "rendering/matplotlib.py": "K3.39"}
    for path, evidence in anchors.items():
        assert evidence in audit["sources"]["src/wenu/" + path]["evidence_ids"], path


def test_consumer_reconciliation_covers_public_commands_notebooks_and_export_modules():
    import ast
    import hashlib
    import importlib
    import tomllib

    _, audit = _consumer_reconciliation()
    import wenu
    assert set(audit["public_exports"]) == set(wenu.__all__)
    for name, row in audit["public_exports"].items():
        module, symbol = row["target"].split(":")
        assert getattr(wenu, name) is getattr(importlib.import_module(module), symbol), name
        assert row["owner"] in audit["sources"] and row["public_surface_evidence"] == "K3.37"
    commands = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["scripts"]
    assert {k: v["target"] for k, v in audit["entry_points"].items()} == commands
    for row in audit["entry_points"].values():
        module, symbol = row["target"].split(":")
        assert callable(getattr(importlib.import_module(module), symbol))
        assert row["owner"] in audit["sources"]
    notebooks = {str(p.relative_to(ROOT)) for p in (ROOT / "src/wenu/notebooks").rglob("*.ipynb")}
    assert set(audit["notebooks"]) == notebooks
    for path, row in audit["notebooks"].items():
        payload = (ROOT / path).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()
        assert row["git_blob_sha"] == actual, path
    declared = {}
    for path in audit["sources"]:
        if not path.startswith(("src/", "packages/wenu_kernel/src/")):
            continue
        for node in ast.parse((ROOT / path).read_text()).body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
                declared[path] = list(ast.literal_eval(node.value))
    assert {v["owner"]: v["names"] for v in audit["package_exports"].values()} == declared
    for module, row in audit["package_exports"].items():
        loaded = importlib.import_module(module)
        assert all(hasattr(loaded, name) for name in row["names"]), module


def test_consumer_reconciliation_binds_receipts_scientific_calls_and_limits():
    import ast
    import json
    import re

    inventory, audit = _consumer_reconciliation()
    assert {f"K3.{n:02}" for n in range(1, 40)} <= audit["receipts"].keys()
    gates = json.loads((ROOT / "tools/test_gates_v1.json").read_text())["gates"]
    for row in audit["receipts"].values():
        assert row["evidence_record"] in inventory
        assert type(row["delivery_pr"]) is int and row["delivery_pr"] > 0
        assert re.fullmatch(r"[0-9a-f]{40}", row["delivery_head"])
        assert re.fullmatch(r"[0-9a-f]{40}", row["merged_commit"])
        assert row["acceptance"] and row["limits"]
        assert row["gate"] is None or row["gate"] in gates
    expected = set()
    for path in audit["sources"]:
        if path.startswith("src/wenu/"):
            for node in ast.walk(ast.parse((ROOT / path).read_text())):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and node.func.attr in {"evaluate", "observe", "at", "transform_to", "position"}):
                    expected.add((path, node.lineno, ast.unparse(node.func)))
    assert {(r["path"], r["line"], r["call"]) for r in audit["scientific_call_sites"]} == expected
    assert all(set(r["evidence_ids"]) <= audit["receipts"].keys() and r["classification"]
               for r in audit["scientific_call_sites"])
    assert set(audit["limits"]) == {"source-qualification", "ephemeris-model", "stellar-motion",
        "snapshot", "satellite-domain", "resource-and-permission", "lifecycle",
        "reuse-and-errors", "freeze-and-extraction", "product-review"}
    assert all(audit["limits"].values())
    assert audit["unresolved_baseline_service_bypasses"] == []
