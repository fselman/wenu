"""Verified resource bundles and independent wheel/source installation seams."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys

import pytest
from astropy.table import Table
from pypdf import PdfWriter

from wenu import resources

ROOT = Path(__file__).resolve().parents[1]


def _bundle(root, domain, *, criteria=True):
    """Synthetic accepted data/evidence; no provider capture is claimed."""
    directory = root / domain
    directory.mkdir(parents=True)
    catalogue = directory / (domain + '_v1.ecsv')
    Table(dict(identifier=['synthetic object'], ra_deg=[10.], dec_deg=[20.],
        apparent_diameter_arcmin=[2.], major_axis_arcmin=[2.], minor_axis_arcmin=[2.],
        object_type=['open cluster' if domain == 'open_clusters' else 'planetary nebula'])).write(catalogue)
    evidence = directory / (domain + '_v1_review.csv')
    evidence.write_text('identifier,review\nsynthetic object,unassessed\n')
    products = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (catalogue, evidence)}
    summary = directory / (domain + '_v1_summary.json')
    summary.write_text(json.dumps(dict(products=products)))
    (directory / 'active.ecsv').symlink_to(catalogue.name)
    if criteria:
        pdf = directory / (domain + '_criteria_v1.pdf')
        with PdfWriter() as writer:
            writer.add_blank_page(width=200, height=300)
            writer.write(pdf)
        digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
        record = dict(schema_version=1, document_kind='wenu-catalogue-selection-criteria',
            catalogue=dict(file=catalogue.name, sha256=products[catalogue.name]),
            products={pdf.name:digest}, pages=[dict(file=pdf.name, sha256=digest, title='Synthetic criteria')])
        (directory / (domain + '_criteria_v1.json')).write_text(json.dumps(record))
    return catalogue, evidence


def test_curated_manifest_admits_all_bound_evidence_and_rejects_corruption(tmp_path, monkeypatch):
    root = tmp_path / 'curated_catalogs'
    catalogue, evidence = _bundle(root, 'open_clusters')
    _bundle(root, 'massive_star_ejecta_nebulae', criteria=False)
    data = resources.build_curated_catalogue_manifest(root)
    assert set(data['catalogues']) == {'open_clusters', 'massive_star_ejecta_nebulae'}
    selector = root / 'open_clusters/active.ecsv'
    selector.unlink(); selector.write_text(catalogue.name)
    assert resources.build_curated_catalogue_manifest(root) == data
    record = data['catalogues']['open_clusters']
    assert len(record['products']) == 5
    # Portable index works without symlinks, as in an installed wheel or sdist.
    (root / 'manifest.json').write_text(json.dumps(data))
    (root / 'open_clusters/active.ecsv').unlink()
    monkeypatch.setattr(resources, 'files', lambda package: tmp_path)
    assert resources.nonstellar_catalog_path('open_clusters') == catalogue
    assert resources.curated_catalogue_bundle('open_clusters')['products'][evidence.name] == evidence
    assert resources.curated_catalogue_bundle('galaxies') is None
    before = evidence.read_bytes()
    evidence.write_bytes(before + b'corrupted')
    assert evidence.read_bytes() != before
    with pytest.raises(ValueError, match='checksum'):
        resources.nonstellar_catalog_path('open_clusters')
    with pytest.raises(ValueError, match='checksum'):
        resources.build_curated_catalogue_manifest(root)


def test_curated_manifest_refuses_escaping_selector_and_unbound_catalogue(tmp_path):
    root = tmp_path / 'curated_catalogs'
    catalogue, _ = _bundle(root, 'planetary_nebulae')
    selector = catalogue.parent / 'active.ecsv'
    selector.unlink()
    selector.symlink_to('../outside.ecsv')
    with pytest.raises(ValueError, match='filename'):
        resources.build_curated_catalogue_manifest(root)
    selector.unlink(); selector.symlink_to(catalogue.name)
    before = catalogue.read_bytes()
    catalogue.write_bytes(before + b'corrupted')
    assert catalogue.read_bytes() != before
    with pytest.raises(ValueError, match='matching completion summary'):
        resources.build_curated_catalogue_manifest(root)
    catalogue.write_bytes(before)
    criteria = catalogue.parent / 'planetary_nebulae_criteria_v1.json'
    original = json.loads(criteria.read_text())
    changed = dict(original, catalogue=dict(original['catalogue'], sha256='0'*64))
    assert changed['catalogue'] != original['catalogue']
    criteria.write_text(json.dumps(changed))
    with pytest.raises(ValueError, match='Criteria catalogue checksum'):
        resources.build_curated_catalogue_manifest(root)


def _assert_source_products_ship(tmp_path, names, modules=()):
    # Same build seam as the installed-consumer test below, restricted to the
    # new data products: no changed runtime/dependency needs reinstalling here.
    from zipfile import ZipFile
    import tarfile
    project = tmp_path/'project'
    project.mkdir()
    shutil.copytree(ROOT/'src/wenu', project/'src/wenu',
        ignore=shutil.ignore_patterns('__pycache__', 'curated_catalogs', 'observing_lists'))
    for name in ('pyproject.toml', 'MANIFEST.in', 'README.md'):
        shutil.copyfile(ROOT/name, project/name)
    shutil.copyfile(ROOT/'src/curated_catalogue_packaging.py', project/'src/curated_catalogue_packaging.py')
    for domain in ('open_clusters', 'planetary_nebulae'):
        _bundle(project/'src/wenu/data/curated_catalogs', domain)
    with (project/'MANIFEST.in').open('a') as stream:
        stream.write('recursive-include src/wenu *\n')
    release = tmp_path/'release'
    release.mkdir()
    commands = [
        [sys.executable, '-c', 'from setuptools.build_meta import build_sdist; build_sdist(' + repr(str(release)) + ')'],
        [sys.executable, '-m', 'pip', 'wheel', '--no-deps', '--no-build-isolation',
         '--wheel-dir', str(release), str(project)],
    ]
    for command in commands:
        result = subprocess.run(command, cwd=project, capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr
    data = ROOT/'src/wenu/data/catalogs/open_clusters'
    with ZipFile(next(release.glob('*.whl'))) as wheel, tarfile.open(next(release.glob('*.tar.gz'))) as sdist:
        for name in names:
            assert wheel.read('wenu/data/catalogs/open_clusters/' + name) == (data/name).read_bytes()
            member = next(item for item in sdist.getmembers()
                          if item.name.endswith('/src/wenu/data/catalogs/open_clusters/' + name))
            assert sdist.extractfile(member).read() == (data/name).read_bytes()
        for module in modules:
            assert wheel.read(module) == (ROOT/'src'/module).read_bytes()
            member = next(item for item in sdist.getmembers() if item.name.endswith('/src/' + module))
            assert sdist.extractfile(member).read() == (ROOT/'src'/module).read_bytes()
    return next(release.glob('*.whl'))


def test_hunt_astrometry_companion_bytes_ship_in_wheel_and_sdist(tmp_path):
    _assert_source_products_ship(tmp_path, ('open_clusters_hunt_astrometry_v1.ecsv',
        'open_clusters_hunt_astrometry_v1.provenance.json', 'open_clusters_hunt_astrometry_source_v1.json'))


def test_cluster_motion_module_and_admission_ship_and_evaluate_from_installed_wheel(tmp_path):
    from zipfile import ZipFile
    import wenu_kernel
    wheel = _assert_source_products_ship(tmp_path, ('open_clusters_hunt_motion_admission_v1.json',),
        modules=('wenu/cluster_state.py', 'wenu/astrometric_state.py'))
    installed=tmp_path/'installed'
    with ZipFile(wheel) as archive: archive.extractall(installed)
    # Explicit accepted SDK path works for both regular and editable SDK hosts;
    # -I -S disables ambient Wenu editable finders and .pth execution.
    sdk_root=Path(wenu_kernel.__file__).resolve().parent.parent
    dependencies=[p for p in sys.path if Path(p).name in ('site-packages','dist-packages')]
    script=r'''
import sys,json
from pathlib import Path
sys.path[:0]=[sys.argv[1],sys.argv[2],*json.loads(sys.argv[3])]
import wenu, wenu_kernel
from wenu import cluster_state, astrometric_state
assert Path(astrometric_state.__file__).is_relative_to(Path(sys.argv[1]))
assert issubclass(cluster_state.ClusterMotionProvider, astrometric_state.RectilinearAstrometricProvider)
assert Path(wenu.__file__).is_relative_to(Path(sys.argv[1]))
assert Path(cluster_state.__file__).is_relative_to(Path(sys.argv[1]))
assert Path(wenu_kernel.__file__).is_relative_to(Path(sys.argv[2]))
from wenu_kernel import Kernel
from wenu_kernel.records import TimePoint,TimeSpan,StateQuery,AccuracyRequest,SessionPolicy
data=Path(wenu.__file__).parent/'data/catalogs/open_clusters'
catalogue=cluster_state.load_cluster_motion(data/'open_clusters_hunt_astrometry_v1.ecsv',
    data/'open_clusters_hunt_motion_admission_v1.json',
    coverage=TimeSpan(TimePoint(2451545,0,'tcb'),TimePoint(2462503,-.5,'tcb')))
provider=cluster_state.ClusterMotionProvider(catalogue)
a=provider.describe().admissions[0]
assert len(catalogue.rows)==513 and len(a.objects)==502
with Kernel(references=(a.reference,)) as kernel:
    kernel.register(provider,ownership='owned')
    with kernel.open_session(SessionPolicy(provider.describe().catalogues)) as session:
        q=StateQuery(a.catalogue,a.model,(a.objects[0],),
            (TimePoint(2457389,0,'tcb'),TimePoint(2457754,.25,'tcb')),a.reference,AccuracyRequest())
        result=session.evaluate(q)
        assert result.states[0].vector!=result.states[1].vector
    with kernel.open_session(SessionPolicy(provider.describe().catalogues,
            reproducibility='interactive_bounded')) as session:
        from dataclasses import replace
        request=replace(q,times=q.times[:1],evaluation_policy='bounded_reuse',
                        accuracy=AccuracyRequest(angular_rad=1e-5))
        first=session.evaluate(request)
        later=session.evaluate(replace(request,times=(TimePoint(2457389,.001,'tcb'),)))
        assert first.reuse_certificates and later.states[0].certificate_id
        assert later.states[0].anchor_time==request.times[0]
        assert later.states[0].vector==first.states[0].vector
from wenu.objects.open_clusters import OpenClusters
default=OpenClusters(None)
default.load()
assert len(default.catalog)==1  # The packaging fixture's original default.
assert default.position().metadata['catalogue_position_model']=='catalogue_lookup'
'''
    result=subprocess.run([sys.executable,'-I','-S','-c',script,str(installed),str(sdk_root),json.dumps(dependencies)],
        cwd=tmp_path,capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr


def test_curated_wheel_and_sdist_install_same_defaults_reports_and_explicit_override(tmp_path):
    # -I -S intentionally ignores editable .pth finders. Install the accepted
    # SDK wheel into an explicit, separate target instead of borrowing an
    # ambient Wenu/kernel installation. Build only local source, without network.
    sdk_project = tmp_path / 'sdk-project'
    shutil.copytree(ROOT / 'packages/wenu_kernel', sdk_project,
        ignore=shutil.ignore_patterns('build', 'dist', '*.egg-info', '__pycache__', 'tests'))
    sdk_wheels = tmp_path / 'sdk-wheels'
    sdk_wheels.mkdir()
    result = subprocess.run([sys.executable, '-m', 'pip', 'wheel', '--no-deps',
        '--no-build-isolation', '--wheel-dir', str(sdk_wheels), str(sdk_project)],
        cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    sdk_wheel = next(sdk_wheels.glob('*.whl'))
    sdk_installed = tmp_path / 'sdk-installed'
    result = subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-deps', '--no-index',
        '--target', str(sdk_installed), str(sdk_wheel)],
        cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    project = tmp_path / 'project'
    project.mkdir()
    shutil.copytree(ROOT / 'src/wenu', project / 'src/wenu',
        ignore=shutil.ignore_patterns('__pycache__', 'curated_catalogs', 'observing_lists'))
    (project / 'README.md').write_text('Synthetic packaging acceptance project.\n')
    for name in ('pyproject.toml', 'MANIFEST.in'):
        shutil.copyfile(ROOT / name, project / name)
    shutil.copyfile(ROOT / 'src/curated_catalogue_packaging.py', project / 'src/curated_catalogue_packaging.py')
    root = project / 'src/wenu/data/curated_catalogs'
    _bundle(root, 'open_clusters')
    _bundle(root, 'planetary_nebulae')
    # Source archives cannot depend on Git discovery for the fixture's Python/data.
    with (project / 'MANIFEST.in').open('a') as stream:
        stream.write('recursive-include src/wenu *\n')
    release = tmp_path / 'releases'; release.mkdir()
    result = subprocess.run([sys.executable, '-c',
        'from setuptools.build_meta import build_sdist; build_sdist(' + repr(str(release)) + ')'],
        cwd=project, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    archive = next(release.glob('*.tar.gz'))
    unpacked = tmp_path / 'unpacked'; unpacked.mkdir()
    if sys.version_info >= (3, 12):
        shutil.unpack_archive(archive, unpacked, filter='data')
    else:
        shutil.unpack_archive(archive, unpacked)
    source = next(unpacked.iterdir())
    assert not (source / 'src/wenu/data/curated_catalogs/open_clusters/active.ecsv').exists()
    assert json.loads((source / 'src/wenu/data/curated_catalogs/manifest.json').read_text())['catalogues'].keys() == {'open_clusters','planetary_nebulae'}
    for i, build_root in enumerate((project, source)):
        wheel_dir = tmp_path / f'wheel_{i}'; wheel_dir.mkdir()
        result = subprocess.run([sys.executable, '-m', 'pip', 'wheel', '--no-deps',
            '--no-build-isolation', '--wheel-dir', str(wheel_dir), str(build_root)],
            cwd=tmp_path, capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr
        wheel = next(wheel_dir.glob('*.whl'))
        # The SDK is a separate dependency, never copied into the Wenu wheel.
        from zipfile import ZipFile
        from email.parser import Parser
        with ZipFile(wheel) as built:
            assert not any(name.startswith('wenu_kernel/') for name in built.namelist())
            metadata_path = next(name for name in built.namelist() if name.endswith('.dist-info/METADATA'))
            metadata = Parser().parsestr(built.read(metadata_path).decode('utf-8'))
            from packaging.requirements import Requirement
            requirements = [Requirement(value) for value in metadata.get_all('Requires-Dist', [])]
            sdk = [value for value in requirements if value.name.replace('_', '-').lower() == 'wenu-kernel']
            assert len(sdk) == 1
            assert sdk[0].url == ('git+https://github.com/fselman/wenu.git@'
                '9dd1909f36986f8c8aa7e2a309427f7ce6ef0ee4#subdirectory=packages/wenu_kernel')
        installed = tmp_path / f'installed_{i}'
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-deps',
            '--target', str(installed), str(wheel)], cwd=tmp_path, capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr
        script = '''
import sys
import json
import site
from pathlib import Path
dependencies = json.loads(sys.argv[2])
# -I -S prevents startup .pth files and editable finders from installing
# an ambient Wenu before this script runs. Process only the fixture's .pth;
# dependency directories supply libraries without executing their .pth files.
sys.path[:] = [p for p in sys.path if p not in dependencies]
site.addsitedir(sys.argv[1])
sys.path.insert(0, sys.argv[1])
sys.path.insert(0, sys.argv[4])
sys.path.extend(dependencies)
import wenu
from wenu import resources
from wenu.objects.open_clusters import OpenClusters
from wenu.objects.planetary_nebulae import PlanetaryNebulae
assert Path(wenu.__file__).is_relative_to(Path(sys.argv[3])), wenu.__file__
from wenu.configuration import load_configuration_defaults
from wenu.cli.chart import main as chart_main
assert chart_main(['presets']) == 0
assert load_configuration_defaults(family='regional').style_mode.atlas.stars.diameter_scale == 1.7
for name in ('b4-landscape-five-band', 'b4-portrait'):
    path = resources.configuration_preset_path(name, kind='atlas-layout')
    layout = json.loads(path.read_text())
    assert len(layout['geometry']['sheets']) == (34 if name == 'b4-landscape-five-band' else 36)
assert resources.configuration_preset_path('atlas-v6', kind='atlas-style').is_file()
assert resources.configuration_preset_path('scorpius-v1', kind='chart').is_file()
# Exercise an actual installed Wenu -> separately installed SDK native call.
import numpy as np
import pandas as pd
import wenu_kernel
from wenu.objects.stars import Stars
from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
assert not Path(wenu_kernel.__file__).is_relative_to(Path(sys.argv[3]))
assert Path(wenu_kernel.__file__).is_relative_to(Path(sys.argv[4]))
stars = Stars(None)
stars.catalog = pd.DataFrame(dict(ra_degrees=[90.], dec_degrees=[30.],
    magnitude=[1.], is_constellation_vertex=[False]), index=[11])
stars.source_catalog = stars.catalog.copy()
from wenu.stellar_catalogue import packaged_stellar_metadata, ingest_stellar_catalogue
metadata = packaged_stellar_metadata('hipparcos')
stars.catalog['epoch_year'] = float(metadata.astropy_epoch.jyear)
stars.catalog = ingest_stellar_catalogue(stars.catalog, metadata).table
stars.source_catalog = stars.catalog.copy()
assert metadata.to_record()['source_metadata']['description_file'] == 'ReadMe'
points = stars.realize(LayerRealizationContext(NATIVE_ICRS_SPEC), None)
np.testing.assert_allclose(points.lon_deg, [90.], atol=1e-12, rtol=0)
np.testing.assert_allclose(points.lat_deg, [30.], atol=1e-12, rtol=0)
assert points.ids.tolist() == [11] and points.coordinate_spec.epoch == 'J1991.25'
# The installed galaxy path exercises dev7's static capability independently
# of the interpreter's editable SDK or Wenu source tree.
from astropy.table import Table
from wenu.objects.galaxies import Galaxies
from wenu_kernel import KernelSession
seen = []
evaluate = KernelSession.evaluate
def capture(session, query):
    result = evaluate(session, query)
    seen.append(result)
    return result
KernelSession.evaluate = capture
try:
    galaxies = Galaxies(None)
    galaxies.catalog = galaxies.source_catalog = Table(dict(identifier=['synthetic'],
        ra_deg=[12.], dec_deg=[-20.]))
    points = galaxies.position()
    np.testing.assert_array_equal(points.lon_deg, [12.])
    assert seen and seen[-1].states[0].source_epoch is None
    clusters = OpenClusters(None)
    clusters.load()
    points = clusters.position()
    np.testing.assert_array_equal(points.lon_deg, [10.])
    assert points.metadata['catalogue_position_model'] == 'catalogue_lookup'
    assert seen[-1].query.reference.status == 'catalogue-lookup'
    assert seen[-1].states[0].source_epoch is None
finally:
    KernelSession.evaluate = evaluate
assert len(OpenClusters(None).load()) == 1
assert len(PlanetaryNebulae(None).load()) == 1
for domain in ('open_clusters','planetary_nebulae'):
    bundle = resources.curated_catalogue_bundle(domain)
    assert bundle['criteria'][0].is_file()
    assert any(p.suffix == '.pdf' for p in bundle['products'].values())
    assert not bundle['catalogue'].is_symlink()
original = resources.nonstellar_catalog_path('planetary_nebulae', curated=False)
assert len(PlanetaryNebulae(None).load(filename=original)) == 1143
print('Independent installed defaults, evidence and explicit scientific override verified.')
'''
        dependencies = [p for p in sys.path if Path(p).name in ('site-packages', 'dist-packages')]
        ambient = tmp_path / 'ambient/site-packages'
        (ambient / 'wenu').mkdir(parents=True, exist_ok=True)
        (ambient / 'wenu/__init__.py').write_text(
            'raise AssertionError("Ambient Wenu installation shadowed the fixture")\n')
        (ambient / 'wenu_kernel').mkdir(exist_ok=True)
        (ambient / 'wenu_kernel/__init__.py').write_text(
            'raise AssertionError("Ambient SDK shadowed the explicit installed dependency")\n')
        dependencies.insert(0, str(ambient))
        result = subprocess.run([sys.executable, '-I', '-S', '-c', script, str(installed), json.dumps(dependencies), str(installed), str(sdk_installed)],
            cwd=tmp_path, capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr
    editable = tmp_path / 'editable'
    result = subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-deps',
        '--no-build-isolation', '--target', str(editable), '--editable', str(project)],
        cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    result = subprocess.run([sys.executable, '-I', '-S', '-c', script, str(editable),
        json.dumps(dependencies), str(project / 'src'), str(sdk_installed)], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
