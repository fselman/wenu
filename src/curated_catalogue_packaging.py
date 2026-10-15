"""Build-only adapter for verified, portable curated catalogue bundles.

The existing resources.py owns resource admission. Loading it directly avoids
importing Wenu's runtime dependencies in an isolated setuptools build.
"""
from pathlib import Path
import importlib.util
import json
import shutil

from setuptools.command.build_py import build_py
from setuptools.command.sdist import sdist


def _resources():
    path = Path(__file__).resolve().parents[1] / 'src/wenu/resources.py'
    spec = importlib.util.spec_from_file_location('_wenu_build_resources', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _publish(root, destination):
    """Copy verified active bundles only, then publish the portable index."""
    if root.resolve() == destination.resolve() or destination.is_symlink():
        raise ValueError('Curated build destination must be separate from source data.')
    resources = _resources()
    data = resources.build_curated_catalogue_manifest(root)
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    outputs = []
    for domain, record in data['catalogues'].items():
        for name in record['products']:
            target = destination / domain / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / domain / name, target)
            outputs.append(str(target))
        resources._verify_curated_products(destination / domain, record['products'])
    manifest = destination / 'manifest.json'
    manifest.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
    return [*outputs, str(manifest)]


class CuratedBuildPy(build_py):
    """Verify editable builds; copy active defaults into wheel resources."""

    def run(self):
        root = Path('src/wenu/data/curated_catalogs')
        _resources().build_curated_catalogue_manifest(root)
        super().run()
        if not self.editable_mode:
            self._curated_outputs = _publish(root, Path(self.build_lib) / 'wenu/data/curated_catalogs')

    def get_outputs(self, include_bytecode=1):
        return list(dict.fromkeys([*super().get_outputs(include_bytecode),
            *getattr(self, '_curated_outputs', [])]))


class CuratedSdist(sdist):
    """Source archives activate the same versions without symlinks."""

    def make_release_tree(self, base_dir, files):
        root = Path('src/wenu/data/curated_catalogs')
        _resources().build_curated_catalogue_manifest(root)
        super().make_release_tree(base_dir, files)
        _publish(root, Path(base_dir) / root)
