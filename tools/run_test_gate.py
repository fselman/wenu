"""Run explicitly reviewed test selections without importing Wenu.

This is a gate runner, not an automatic dependency/coverage analyser. Read each
manifest scope and review the actual diff before choosing a gate.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "tools/test_gates_v1.json"


def load_gates(root):
    data = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
    if data.get("schema") != "wenu-test-gates/1":
        raise ValueError("Unsupported test-gate schema")
    gates = data["gates"]
    if not isinstance(gates, dict) or not gates:
        raise ValueError("No test gates declared")
    return gates


def selected_tests(root, name):
    gates = load_gates(root)
    visiting, finished, selected = set(), set(), []

    def visit(key):
        if key in visiting:
            raise ValueError(f"Cyclic gate dependency: {key}")
        if key in finished:
            return
        if key not in gates:
            raise ValueError(f"Unknown test gate: {key}")
        visiting.add(key)
        gate = gates[key]
        if not gate.get("scope") or not gate.get("limits"):
            raise ValueError(f"Gate lacks scope/limits: {key}")
        for parent in gate.get("extends", []):
            visit(parent)
        for entry in gate["selections"]:
            if not entry.get("reason"):
                raise ValueError(f"Selection lacks rationale: {key}")
            node = entry["node"]
            parts = node.split("::")
            path = PurePosixPath(parts[0])
            if (path.is_absolute() or ".." in path.parts or not path.parts
                    or path.parts[0] != "tests" or path.suffix != ".py"
                    or len(parts) > 2):
                raise ValueError(f"Invalid test selection: {node}")
            source = root / path
            if not source.is_file() or not source.resolve().is_relative_to(root.resolve()):
                raise ValueError(f"Missing/outside test file: {node}")
            if len(parts) == 2:
                names = {n.name for n in ast.parse(source.read_text(encoding="utf-8")).body
                         if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
                if not parts[1].startswith("test_") or parts[1] not in names:
                    raise ValueError(f"Missing test function: {node}")
            if node not in selected:
                selected.append(node)
        visiting.remove(key)
        finished.add(key)

    visit(name)
    if not selected:
        raise ValueError(f"Empty test gate: {name}")
    # Selecting a whole owner includes its explicitly selected individual tests.
    whole_files = {node for node in selected if "::" not in node}
    return tuple(node for node in selected
                 if "::" not in node or node.split("::")[0] not in whole_files)


def pytest_command(root, name, *, collect=False):
    return [sys.executable, "-m", "pytest", "-q", *selected_tests(root, name),
            *( ["--collect-only"] if collect else ["--durations=15"] )]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gate", help="Reviewed gate name; see tools/test_gates_v1.json")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--run", action="store_true", help="Execute once; return pytest's status")
    mode.add_argument("--collect", action="store_true", help="Collect selected tests without executing")
    args = parser.parse_args(argv)
    try:
        gates = load_gates(ROOT)
        command = pytest_command(ROOT, args.gate, collect=args.collect)
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.error(str(error))
    print(json.dumps({"gate": args.gate, "scope": gates[args.gate]["scope"],
                      "limits": gates[args.gate]["limits"], "command": command}, indent=2), flush=True)
    if not (args.run or args.collect):
        return 0
    environment = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTEST_ADDOPTS="")
    return subprocess.run(command, cwd=ROOT, env=environment, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
