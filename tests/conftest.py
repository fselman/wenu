"""Shared pytest fixtures for canonical integration contracts."""

import importlib.util
from pathlib import Path

import pytest


class CanonicalBuildRegistry:
    """Cache identical canonical example builds for one test session."""

    def __init__(self):
        self._modules = {}
        self._builds = {}

    def module(self, path):
        path = Path(path).resolve()
        if path not in self._modules:
            spec = importlib.util.spec_from_file_location(path.stem, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self._modules[path] = module
        return self._modules[path]

    def build(self, path, *args, **kwargs):
        path = Path(path).resolve()
        key = (path, args, tuple(sorted(kwargs.items())))
        if key not in self._builds:
            self._builds[key] = self.module(path).build_chart(
                *args,
                **kwargs,
            )
        return self._builds[key]

    def close(self):
        observers = {
            id(result[0].observer): result[0].observer
            for result in self._builds.values()
        }
        for observer in observers.values():
            observer.close()


@pytest.fixture(scope="session")
def canonical_builds():
    registry = CanonicalBuildRegistry()
    yield registry
    registry.close()
