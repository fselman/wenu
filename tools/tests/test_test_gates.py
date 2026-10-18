"""Independent stdlib tests of gate selection and execution, not Wenu science."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "run_test_gate.py"
spec = importlib.util.spec_from_file_location("run_test_gate", SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class GateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "tools").mkdir()
        (self.root / "tests").mkdir()
        (self.root / "tests/test_owner.py").write_text("def test_one(): pass\ndef test_two(): pass\n")
        self.gates = {"owner": {"scope": "synthetic owner", "limits": "synthetic only",
                                 "selections": [{"node": "tests/test_owner.py::test_one", "reason": "fault"}]}}
        self.write()

    def write(self):
        (self.root / gate.MANIFEST).write_text(json.dumps({"schema": "wenu-test-gates/1", "gates": self.gates}))

    def test_selection_preserves_explicit_order_and_whole_owner_deduplicates(self):
        self.gates["seam"] = {"scope": "seam", "limits": "synthetic", "extends": ["owner"],
                              "selections": [{"node": "tests/test_owner.py", "reason": "whole owner"}]}
        self.write()
        self.assertEqual(gate.selected_tests(self.root, "seam"), ("tests/test_owner.py",))

    def test_unknown_cycle_empty_and_missing_tests_refuse_without_fallback(self):
        with self.assertRaisesRegex(ValueError, "Unknown"):
            gate.selected_tests(self.root, "unknown")
        for change in ({"extends": ["owner"]}, {"selections": []},
                       {"selections": [{"node": "tests/test_owner.py::test_deleted", "reason": "fault"}]},
                       {"selections": [{"node": "tests/test_missing.py", "reason": "fault"}]}):
            with self.subTest(change=change):
                original = self.gates["owner"].copy()
                self.gates["owner"].update(change); self.write()
                with self.assertRaises(ValueError):
                    gate.selected_tests(self.root, "owner")
                self.gates["owner"] = original

    def test_outside_paths_filters_and_class_or_parameter_selectors_refuse(self):
        for node in ("../tests/test_owner.py", "/tests/test_owner.py", "-k", "tests/test_owner.py::test_one[x]",
                     "tests/test_owner.py::Class::test_one"):
            with self.subTest(node=node):
                self.gates["owner"]["selections"][0]["node"] = node; self.write()
                with self.assertRaises(ValueError):
                    gate.selected_tests(self.root, "owner")

    def test_no_execution_without_explicit_run(self):
        with patch.object(gate, "ROOT", self.root), patch.object(gate.subprocess, "run") as run:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(gate.main(["owner"]), 0)
            run.assert_not_called()

    def test_execution_is_once_uses_current_python_and_preserves_failure(self):
        with patch.object(gate, "ROOT", self.root), patch.object(gate.subprocess, "run", return_value=SimpleNamespace(returncode=5)) as run:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(gate.main(["owner", "--run"]), 5)
            run.assert_called_once()
            args, kwargs = run.call_args
            self.assertEqual(args[0][:4], [gate.sys.executable, "-m", "pytest", "-q"])
            self.assertEqual(args[0][4:], ["tests/test_owner.py::test_one", "--durations=15"])
            self.assertEqual(kwargs["env"]["PYTEST_DISABLE_PLUGIN_AUTOLOAD"], "1")
            self.assertEqual(kwargs["env"]["PYTEST_ADDOPTS"], "")
            self.assertEqual(kwargs["cwd"], self.root)

    def test_collect_uses_same_selection_without_running_tests(self):
        normal = gate.pytest_command(self.root, "owner")
        collected = gate.pytest_command(self.root, "owner", collect=True)
        self.assertEqual(normal[:-1], collected[:-1])
        self.assertEqual(collected[-1], "--collect-only")

    def test_reviewed_request_gates_retain_distinct_public_routes(self):
        selected = set(gate.selected_tests(gate.ROOT, "request-lifecycle"))
        self.assertTrue({"tests/test_request_generation.py", "tests/test_chart_drawing.py",
                         "tests/test_wenu_chart_cli.py", "tests/test_chart_sequence.py",
                         "tests/test_fixed_sky_sequence.py"} <= selected)
        broader = set(gate.selected_tests(gate.ROOT, "request-configuration"))
        self.assertIn("tests/test_moon_disk_sequence.py", broader)
        self.assertIn("tests/test_reference_policy.py", broader)
        self.assertNotIn("tests/test_satellite_crossing_oracle.py", broader)

    def test_repository_gates_resolve_without_product_imports(self):
        for name in gate.load_gates(gate.ROOT):
            with self.subTest(gate=name):
                self.assertTrue(gate.selected_tests(gate.ROOT, name))


if __name__ == "__main__":
    unittest.main()
