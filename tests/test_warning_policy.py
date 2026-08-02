"""Warning hygiene contracts for the Wenu test suite."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_pytest_disables_unused_remote_data_plugin():
    configuration = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'addopts = "-p no:remotedata"' in configuration


def test_future_warnings_are_errors():
    configuration = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert '"error::FutureWarning"' in configuration
