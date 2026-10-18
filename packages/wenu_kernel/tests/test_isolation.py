"""Import and test-collection barriers execute without astronomy dependencies."""

import json
from pathlib import Path
import subprocess
import sys
import unittest

import wenu_kernel


class IsolationTests(unittest.TestCase):
    def test_sdk_import_with_site_packages_disabled(self):
        root = str(Path(wenu_kernel.__file__).resolve().parent.parent)
        code = """
import json, sys
sys.path.insert(0, ROOT)
import wenu_kernel
from wenu_kernel import records, errors
for forbidden in ('wenu', 'numpy', 'astropy', 'matplotlib', 'skyfield', 'sgp4', 'pandas', 'spiceypy'):
    assert not any(name == forbidden or name.startswith(forbidden + '.') for name in sys.modules), forbidden
print(json.dumps(wenu_kernel.__all__))
""".replace("ROOT", repr(root))
        result = subprocess.run([sys.executable, "-I", "-S", "-c", code],
                                capture_output=True, text=True, check=True)
        self.assertIn("Kernel", json.loads(result.stdout))

    def test_local_provider_gate_collects_without_wenu_or_backends(self):
        # Ordinary unittest discovery is the package gate; no pytest plugin or
        # root Wenu imports are needed even to enumerate its tests.
        suite = unittest.defaultTestLoader.discover(str(Path(__file__).parent))
        self.assertGreater(suite.countTestCases(), 0)
        self.assertEqual(unittest.defaultTestLoader.errors, [])
        for forbidden in ("wenu", "numpy", "astropy", "matplotlib", "skyfield", "sgp4"):
            self.assertFalse(any(n == forbidden or n.startswith(forbidden + ".") for n in sys.modules))


if __name__ == "__main__":
    unittest.main()
