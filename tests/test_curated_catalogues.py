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


def test_geometry_kernel_wheel_isolated_imports_metadata_and_numeric_consumer(tmp_path):
    """Installed geometry must not borrow Wenu or an ambient SDK checkout."""
    import importlib.util
    from email.parser import Parser
    from packaging.requirements import Requirement
    from zipfile import ZipFile
    project = tmp_path / 'kernel-project'
    shutil.copytree(ROOT / 'packages/wenu_kernel', project,
        ignore=shutil.ignore_patterns('build','dist','*.egg-info','__pycache__','tests'))
    wheels = tmp_path / 'wheels'; wheels.mkdir()
    build = subprocess.run([sys.executable,'-m','pip','wheel','--no-deps',
        '--no-build-isolation','--wheel-dir',str(wheels),str(project)],
        cwd=tmp_path,capture_output=True,text=True)
    assert build.returncode == 0, build.stdout + build.stderr
    wheel = next(wheels.glob('*.whl'))
    with ZipFile(wheel) as archive:
        metadata_file = next(p for p in archive.namelist() if p.endswith('.dist-info/METADATA'))
        metadata = Parser().parsestr(archive.read(metadata_file).decode())
        assert metadata['Version'] == '0.0.0.dev12'
        requirements = [Requirement(r) for r in metadata.get_all('Requires-Dist',[])]
        assert requirements and all(r.marker is not None for r in requirements)
        assert all(not r.marker.evaluate({'extra':''}) for r in requirements)
        enabled = [r for r in requirements if r.marker.evaluate({'extra':'geometry'})]
        assert len(enabled) == 1 and enabled[0].name == 'numpy'
        assert '1.26' in enabled[0].specifier and '2.0' not in enabled[0].specifier
    installed = tmp_path / 'kernel-installed'
    install = subprocess.run([sys.executable,'-m','pip','install','--no-deps','--no-index',
        '--target',str(installed),str(wheel)],cwd=tmp_path,capture_output=True,text=True)
    assert install.returncode == 0, install.stdout + install.stderr
    # First process has no site packages at all, including NumPy.
    base = r'''
import sys
sys.path.insert(0,sys.argv[1])
from wenu_kernel import Kernel
from wenu_kernel.coordinates import CoordinateSpec
assert CoordinateSpec('icrs','ssb').epoch is None
assert 'numpy' not in sys.modules and 'wenu' not in sys.modules
'''
    checked = subprocess.run([sys.executable,'-I','-S','-c',base,str(installed)],
        cwd=tmp_path,capture_output=True,text=True)
    assert checked.returncode == 0, checked.stdout + checked.stderr
    numpy_root = Path(importlib.util.find_spec('numpy').origin).resolve().parent.parent
    numeric = r'''
import importlib.abc, pathlib, sys
sys.path[:0]=sys.argv[1:3]
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0] in ('wenu','astropy','skyfield','matplotlib','pandas','spiceypy'):
            raise AssertionError(fullname)
sys.meta_path.insert(0,Block())
import wenu_kernel, numpy as np
assert pathlib.Path(wenu_kernel.__file__).is_relative_to(pathlib.Path(sys.argv[1]))
from wenu_kernel.coordinates import GENERIC_SPHERICAL_SPEC
from wenu_kernel.geometry import SphericalPolygons, SphericalFrame, ProjectedPoints
from wenu_kernel.geometry.topology import ring_interior
ring=np.array([[0.,0.],[90.,0.],[0.,90.]])
area=ring_interior(ring,False)[1]
assert np.isclose(area,np.pi/2,atol=1e-14)
assert np.isclose(ring_interior(ring,True)[1],4*np.pi-area,atol=1e-14)
polygons=SphericalPolygons((ring[:,0],ring[::-1,0]),(ring[:,1],ring[::-1,1]),
    coordinate_spec=GENERIC_SPHERICAL_SPEC,ids=['outer','hole'],
    metadata={'is_hole':np.array([False,True]),'compound_id':np.array([0,0])})
assert polygons.metadata['is_hole'].tolist()==[False,True]
frame=SphericalFrame(25.,45.,10.)
q=frame.transform([10.,20.],[30.,40.]);p=frame.inverse_transform(q.lon_deg,q.lat_deg)
assert np.allclose(p.lon_deg,[10.,20.]) and np.allclose(p.lat_deg,[30.,40.])
assert ProjectedPoints([0.,np.nan],[0.,1.]).finite.tolist()==[True,False]
from wenu_kernel.projections import StereographicProjection, PolarAzimuthalEquidistantProjection, MollweideProjection
from wenu_kernel.geometry import domain
from wenu_kernel.geometry.clipping import clip_curve_to_viewport
from wenu_kernel.geometry import ProjectedCurve, Viewport
from wenu_kernel.geometry import SphericalCurves
segments=SphericalCurves(([0.,180.],),([-80.,-80.],),
    coordinate_spec=GENERIC_SPHERICAL_SPEC,ids=['far'],
    metadata={'segment_geometry':'minor_great_circle'})
assert len(domain.project_geometry_for_viewport(segments,
    projection=StereographicProjection(),viewport=Viewport(-.8,.8,-.7,.7)))==0
stereo=StereographicProjection(radius=2.,flip_ew=False)
assert np.allclose(stereo.project_spherical(90.,0.),(2.,0.),atol=1e-14)
assert np.allclose(PolarAzimuthalEquidistantProjection(radius=2.,flip_ew=False).project_spherical(90.,0.),(2.,0.),atol=1e-14)
assert np.allclose(MollweideProjection().project_spherical(0.,0.),(0.,0.),atol=1e-14)
curve=ProjectedCurve([-2.,2.],[0.,0.])
pieces=clip_curve_to_viewport(curve,Viewport(-1.,1.,-1.,1.))
assert len(pieces)==1 and np.allclose(pieces[0].x,[-1.,1.])
near=SphericalPolygons(([0.,90.,180.],),([70.,70.,70.],),coordinate_spec=GENERIC_SPHERICAL_SPEC,ids=['ring'])
safe=domain.project_geometry_for_viewport(near,projection=stereo,viewport=Viewport(-.5,.5,-.5,.5))
assert len(safe)==1 and safe.metadata['ids'].tolist()==['ring']
assert safe.metadata['projection_domain_clipped']
assert domain.projection_cap_for_viewport(MollweideProjection(),Viewport(-1.,1.,-1.,1.)) is None
assert not hasattr(domain,'magnitude_sizes')
# Actual corrected mixed point batch from the isolated installed wheel.
from wenu_kernel.geometry import SphericalPoints
points=SphericalPoints([20.,np.nan,60.],[45.,0.,-10.],
    coordinate_spec=GENERIC_SPHERICAL_SPEC,ids=['a','missing','b'])
for pole in ('south','north'):
    projection=PolarAzimuthalEquidistantProjection(pole=pole)
    projected=projection.project_geometry(points)
    assert projected.ids.tolist()==['a','missing','b']
    assert projected.finite.tolist()==[True,False,True]
    x,y=projection.project_spherical([20.,60.],[45.,-10.])
    assert np.array_equal(projected.x[[0,2]],x) and np.array_equal(projected.y[[0,2]],y)
    try:
        projection.project_spherical(np.nan,0.)
    except ValueError:
        pass
    else:
        raise AssertionError('strict numerical validation must remain')
'''
    checked = subprocess.run([sys.executable,'-I','-S','-c',numeric,
        str(installed),str(numpy_root)],cwd=tmp_path,capture_output=True,text=True)
    assert checked.returncode == 0, checked.stdout + checked.stderr


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


def test_build_publication_consumes_returned_manifest_and_rechecks_before_replacement(tmp_path, monkeypatch):
    """The build adapter delegates admission; it never interprets catalogue rows."""
    import importlib.util
    from types import SimpleNamespace
    spec = importlib.util.spec_from_file_location("curated_build_consumer", ROOT / "src/curated_catalogue_packaging.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = tmp_path / "source"
    catalogue, evidence = _bundle(source, "open_clusters")
    _bundle(source, "planetary_nebulae")
    admitted = resources.build_curated_catalogue_manifest(source)
    selected = dict(admitted, catalogues={"open_clusters": admitted["catalogues"]["open_clusters"]})
    calls = []
    def admission(root):
        calls.append(root)
        resources.build_curated_catalogue_manifest(root)  # actual fresh byte admission
        return selected
    monkeypatch.setattr(module, "_resources", lambda: SimpleNamespace(
        build_curated_catalogue_manifest=admission,
        _verify_curated_products=resources._verify_curated_products))
    destination = tmp_path / "published"
    outputs = module._publish(source, destination)
    assert calls == [source]
    assert json.loads((destination / "manifest.json").read_text()) == selected
    assert not (destination / "planetary_nebulae").exists()
    expected = selected["catalogues"]["open_clusters"]["products"]
    assert set(outputs) == {str(destination / "open_clusters" / name) for name in expected} | {str(destination / "manifest.json")}
    assert all((destination / "open_clusters" / name).read_bytes() == (catalogue.parent / name).read_bytes() for name in expected)
    before = {p.relative_to(destination):p.read_bytes() for p in destination.rglob("*") if p.is_file()}
    evidence.write_bytes(evidence.read_bytes() + b"corruption")
    with pytest.raises(ValueError, match="checksum"):
        module._publish(source, destination)
    assert calls == [source, source]
    assert {p.relative_to(destination):p.read_bytes() for p in destination.rglob("*") if p.is_file()} == before


def test_build_resource_admission_runs_without_wenu_or_numerical_runtime(tmp_path):
    """Build-only source loader must not import the Wenu application facade."""
    source = tmp_path / "source"
    _bundle(source, "open_clusters")
    expected = resources.build_curated_catalogue_manifest(source)
    dependencies = [p for p in sys.path if Path(p).name in ("site-packages", "dist-packages")]
    script = r'''
import sys,json,importlib.util,importlib.abc
from pathlib import Path
sys.path.extend(json.loads(sys.argv[1]))
blocked=('wenu','wenu_kernel','astropy','numpy','pandas','matplotlib','skyfield','sgp4','spiceypy')
class NoRuntime(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0] in blocked:raise AssertionError('build imported runtime: '+fullname)
sys.meta_path.insert(0,NoRuntime())
spec=importlib.util.spec_from_file_location('isolated_curated_build',sys.argv[2])
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
reader=module._resources()
source,destination=Path(sys.argv[3]),Path(sys.argv[4])
expected=json.loads(sys.argv[5])
assert reader.build_curated_catalogue_manifest(source)==expected
module._publish(source,destination)
assert json.loads((destination/'manifest.json').read_text())==expected
assert not any(name.split('.')[0] in blocked for name in sys.modules)
'''
    result = subprocess.run([sys.executable, "-I", "-S", "-c", script,
        json.dumps(dependencies), str(ROOT / "src/curated_catalogue_packaging.py"),
        str(source), str(tmp_path / "destination"), json.dumps(expected)],
        cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


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
        modules=('wenu/cluster_state.py', 'wenu/astrometric_state.py', 'wenu/astrometric_coordinates.py', 'wenu/astrometric_observation.py',
                 'wenu/configuration/defaults.toml', 'wenu/charts/request.py',
                 'wenu/charts/request_realization.py', 'wenu/cli/chart.py'))
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
from wenu import cluster_state, astrometric_state, astrometric_coordinates, astrometric_observation
assert Path(astrometric_observation.__file__).is_relative_to(Path(sys.argv[1]))
assert Path(astrometric_coordinates.__file__).is_relative_to(Path(sys.argv[1]))
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
pv=cluster_state.ClusterMotionProvider(catalogue,representation='cartesian')
pa=pv.describe().admissions[0]
assert pa.objects==a.objects
with Kernel(references=(pa.reference,)) as kernel:
    kernel.register(pv,ownership='owned')
    with kernel.open_session(SessionPolicy((pa.catalogue,))) as session:
        query=StateQuery(pa.catalogue,pa.model,(pa.objects[0],),
            (TimePoint(2457389,0,'tcb'),TimePoint(2457754,.25,'tcb')),pa.reference,
            AccuracyRequest(metric='euclidean_norm'),require_velocity=True)
        result=session.evaluate(query)
        assert all(state.velocity_available for state in result.states)
        assert result.states[0].position_m!=result.states[1].position_m
        assert result.states[0].velocity_m_s==result.states[1].velocity_m_s
        from wenu_kernel.time import TimeService
        adapter=astrometric_coordinates.TcbTdbAdapter(pa.coverage)
        service=TimeService((adapter,),admissions=(adapter.describe(),))
        receipts=tuple(service.convert(t,'tdb') for t in query.times)
        converted=astrometric_coordinates.convert_barycentric_batch(result,admission=pa,
            source_coordinate_scale='tcb',time_admission=adapter.describe(),conversions=receipts)
        assert converted.original is result and len(converted.states)==2
        assert converted.states[0].original is result.states[0]
        assert converted.states[0].position_m!=result.states[0].position_m
        assert converted.states[0].velocity_m_s==result.states[0].velocity_m_s
        from astropy.utils import iers
        from hashlib import sha256
        backend=astrometric_observation.ErfaReceptionBackend(
            leap_seconds_path=iers.IERS_LEAP_SECOND_FILE,
            leap_seconds_sha256=sha256(Path(iers.IERS_LEAP_SECOND_FILE).read_bytes()).hexdigest(),
            eop_path=iers.IERS_B_FILE,eop_sha256=sha256(Path(iers.IERS_B_FILE).read_bytes()).hexdigest(),
            coverage=TimeSpan(TimePoint(2456300,0,'tt'),TimePoint(2458000,0,'tt')),
            backend_identity=astrometric_observation.reception_backend_identity())
        reception=backend.prepare('2016-12-31T23:59:60Z',longitude_deg=-71.23,
                                  latitude_deg=-32.44,height_m=52.)
        from dataclasses import replace
        received=session.evaluate(replace(query,times=(reception.tcb,)))
        assert received.states[0].time==reception.tcb
        assert received.states[0].source_epoch==result.states[0].source_epoch
        assert reception.position_error_m is None
        observed=astrometric_observation.realize_astrometric_batch(received,reception,
            admission=astrometric_observation.NominalObservationAdmission(pa,backend.model))
        assert observed.original is received and len(observed.states)==1
        assert observed.states[0].object_key==pa.objects[0]
        assert observed.states[0].range_m>0 and observed.states[0].emission_time is None
        assert 0<=observed.states[0].azimuth_rad<2*3.141592653589793
        assert observed.coordinate_spec.frame=='altaz'
        assert observed.coordinate_spec.origin=='observer'
        assert observed.converted.states[0].original.source_epoch==received.states[0].source_epoch
from wenu.objects.open_clusters import OpenClusters
default=OpenClusters(None)
default.load()
assert len(default.catalog)==1  # The packaging fixture's original default.
assert default.position().metadata['catalogue_position_model']=='catalogue_lookup'
from wenu.sky.realization import LayerRealizationContext
layer=OpenClusters(None)
layer.load(filename=sys.argv[4])
selected=[row.identifier for row in catalogue.rows if row.unavailable_reason is None][:2]
geometry=layer.realize(LayerRealizationContext.from_reception(reception),None,
    motion=catalogue,selected=selected)
assert geometry.ids.tolist()==selected and geometry.coordinate_spec.frame=='altaz'
assert geometry.coordinate_spec.longitude_unit=='deg'
assert geometry.metadata['astrometric_observation'].reception==reception
assert layer.position().metadata['catalogue_position_model']=='catalogue_lookup'
from wenu.configuration import load_configuration,translate_configuration_defaults
from wenu.charts.request import ClusterMotionRequest
assert translate_configuration_defaults(load_configuration()).cluster_motion==ClusterMotionRequest()
from wenu.cli.chart import parser
assert parser().parse_args(['planisphere','--open-cluster-model','lookup']).open_cluster_model=='lookup'
'''
    from wenu.resources import nonstellar_catalog_path
    selected_source=tmp_path/'selected-source.ecsv'
    shutil.copyfile(nonstellar_catalog_path('open_clusters'),selected_source)
    result=subprocess.run([sys.executable,'-I','-S','-c',script,str(installed),str(sdk_root),json.dumps(dependencies),str(selected_source)],
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
            assert sdk[0].extras == {"geometry"}
            assert sdk[0].url == ('git+https://github.com/fselman/wenu.git@'
                'f0a2e247d9ed0061d256891fcf4962d1c41fd4f9#subdirectory=packages/wenu_kernel')
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


def test_application_assembly_ships_and_runs_without_source_checkout(tmp_path):
    """Existing root build owner: moved construction must ship in wheel/sdist."""
    from zipfile import ZipFile
    import wenu_kernel
    wheel = _assert_source_products_ship(tmp_path, (), modules=(
        'wenu/sky/assembly.py', 'wenu/sky/celestial_sphere.py',
        'wenu/sky/maximal_sphere.py', 'wenu/sky/native_snapshot.py'))
    installed = tmp_path/'installed'
    with ZipFile(wheel) as archive:archive.extractall(installed)
    sdk_root = Path(wenu_kernel.__file__).resolve().parent.parent
    dependencies = [p for p in sys.path if Path(p).name in ('site-packages', 'dist-packages')]
    script = r'''
import sys,json
from pathlib import Path
sys.path[:0]=[sys.argv[1],sys.argv[2],*json.loads(sys.argv[3])]
from wenu.sky import assembly, maximal_sphere, native_snapshot
from wenu.sky.celestial_sphere import CelestialSphere
for module in (assembly,maximal_sphere,native_snapshot):
    assert Path(module.__file__).is_relative_to(Path(sys.argv[1]))
sky=CelestialSphere(None)
points=sky.add_points()
assert sky.layers==(points,) and sky.points is points
assert points.__class__.__module__=='wenu.sky.points'
class Supplied:
    def restore_snapshot(self,snapshot):return snapshot
snapshot=object.__new__(native_snapshot.NativeSkySnapshot)
assert snapshot.make_sky(assembly=Supplied()) is snapshot
'''
    result = subprocess.run([sys.executable,'-I','-S','-c',script,str(installed),
        str(sdk_root),json.dumps(dependencies)], cwd=tmp_path, capture_output=True,text=True)
    assert result.returncode == 0, result.stdout+result.stderr


def test_ceres_solution_manifest_ships_and_loads_without_source_checkout(tmp_path):
    from zipfile import ZipFile
    import wenu_kernel
    wheel = _assert_source_products_ship(tmp_path, (), modules=(
        'wenu/data/ceres_solution_v1.json', 'wenu/sky/ceres.py',
        'wenu/ephemeris_state.py', 'wenu/minor_body_resources.py'))
    installed = tmp_path/'installed'
    with ZipFile(wheel) as archive:
        archive.extractall(installed)
    sdk_root = Path(wenu_kernel.__file__).resolve().parent.parent
    dependencies = [p for p in sys.path if Path(p).name in ('site-packages','dist-packages')]
    script = r'''
import sys,json
from pathlib import Path
sys.path[:0]=[sys.argv[1],sys.argv[2],*json.loads(sys.argv[3])]
from importlib.resources import files
from wenu.sky import ceres
from wenu.ephemeris_state import KernelEphemerisStateSource
assert Path(ceres.__file__).is_relative_to(Path(sys.argv[1]))
manifest=files('wenu.data').joinpath('ceres_solution_v1.json')
assert Path(str(manifest)).is_relative_to(Path(sys.argv[1]))
document=json.loads(manifest.read_text())
assert document['schema_version']==1
assert ceres.CERES_SOLUTION.orbit_solution_id==document['solution']['orbit_solution_id']=='JPL#48'
assert ceres.CERES_SOLUTION.provider_spk_id==ceres.CERES_BODY.physical_body_id=='20000001'
'''
    result = subprocess.run([sys.executable,'-I','-S','-c',script,str(installed),
        str(sdk_root),json.dumps(dependencies)],cwd=tmp_path,capture_output=True,text=True)
    assert result.returncode == 0, result.stdout+result.stderr


def test_atlas_sheet_contract_ships_and_runs_without_source_checkout(tmp_path):
    from zipfile import ZipFile
    import wenu_kernel
    wheel = _assert_source_products_ship(tmp_path, (), modules=(
        'wenu/charts/atlas_sheet.py', 'wenu/charts/atlas_publication.py', 'wenu/charts/request_generation.py',
        'wenu/charts/stellar_sizing_report.py', 'wenu/cli/chart.py'))
    installed = tmp_path/'installed'
    with ZipFile(wheel) as archive:
        archive.extractall(installed)
    sdk_root = Path(wenu_kernel.__file__).resolve().parent.parent
    dependencies = [p for p in sys.path if Path(p).name in ('site-packages','dist-packages')]
    script = r'''
import sys,json
from pathlib import Path
sys.path[:0]=[sys.argv[1],sys.argv[2],*json.loads(sys.argv[3])]
from types import SimpleNamespace
from wenu.charts import atlas_sheet, atlas_publication, request_generation, stellar_sizing_report
from wenu.geometry.spherical import SphericalPoints
from wenu.coordinates import GENERIC_SPHERICAL_SPEC
for module in (atlas_sheet,atlas_publication,request_generation,stellar_sizing_report):
    assert Path(module.__file__).is_relative_to(Path(sys.argv[1]))
assert atlas_sheet.AtlasSheetChartRequest is atlas_publication.AtlasSheetChartRequest is request_generation.AtlasSheetChartRequest
assert callable(atlas_publication.render_atlas_sheet)
geometry=SphericalPoints([10.],[20.],ids=[1],metadata={"magnitude":[2.]},coordinate_spec=GENERIC_SPHERICAL_SPEC)
source=SimpleNamespace(native_positions=lambda:geometry)
data,ids,values=stellar_sizing_report.catalogue_star_counts(source,6)
assert data["selected_count"]==1 and ids.tolist()==[1] and values.tolist()==[2.]
def refuse():raise RuntimeError("installed native refusal")
source.native_positions=refuse
try:stellar_sizing_report.catalogue_star_counts(source,6)
except RuntimeError as exc:assert str(exc)=="installed native refusal"
else:raise AssertionError("installed count consumer concealed refusal")
'''
    result = subprocess.run([sys.executable,'-I','-S','-c',script,str(installed),
        str(sdk_root),json.dumps(dependencies)],cwd=tmp_path,capture_output=True,text=True)
    assert result.returncode == 0, result.stdout+result.stderr



def test_solar_spectral_metadata_ships_and_loads_without_source_checkout(tmp_path):
    """Use unmodified build rules; packaged metadata is an import dependency."""
    from zipfile import ZipFile
    import tarfile
    import wenu_kernel
    project = tmp_path / "project"
    project.mkdir()
    shutil.copytree(ROOT / "src/wenu", project / "src/wenu",
                    ignore=shutil.ignore_patterns("__pycache__", "curated_catalogs", "observing_lists"))
    for name in ("pyproject.toml", "MANIFEST.in", "README.md"):
        shutil.copyfile(ROOT / name, project / name)
    shutil.copyfile(ROOT / "src/curated_catalogue_packaging.py", project / "src/curated_catalogue_packaging.py")
    for domain in ("open_clusters", "planetary_nebulae"):
        _bundle(project / "src/wenu/data/curated_catalogs", domain)
    release = tmp_path / "release"
    release.mkdir()
    for command in ([sys.executable, "-c", "from setuptools.build_meta import build_sdist; build_sdist("+repr(str(release))+")"],
                    [sys.executable, "-m", "pip", "wheel", "--no-index", "--no-deps", "--no-build-isolation", "--wheel-dir", str(release), str(project)]):
        result = subprocess.run(command, cwd=project, capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr
    resource = "wenu/data/solar_spectral_resource_tsis1_hsrs_v2.json"
    payload = (ROOT / "src" / resource).read_bytes()
    installed = tmp_path / "installed"
    with ZipFile(next(release.glob("*.whl"))) as wheel, tarfile.open(next(release.glob("*.tar.gz"))) as sdist:
        assert wheel.read(resource) == payload
        member = next(m for m in sdist.getmembers() if m.name.endswith("/src/"+resource))
        assert sdist.extractfile(member).read() == payload
        wheel.extractall(installed)
    dependencies = [p for p in sys.path if Path(p).name in ("site-packages", "dist-packages")]
    sdk = Path(wenu_kernel.__file__).resolve().parent.parent
    script = r"""
import sys,json
from pathlib import Path
sys.path[:0]=[sys.argv[1],sys.argv[2],*json.loads(sys.argv[3])]
from importlib.resources import files
from wenu.satellites import radiometry as r
assert Path(r.__file__).is_relative_to(Path(sys.argv[1]))
path=files('wenu.data').joinpath('solar_spectral_resource_tsis1_hsrs_v2.json')
assert Path(str(path)).is_relative_to(Path(sys.argv[1]))
assert r.TSIS1_HSRS_V2_IDENTITY.sample_count==25281
assert r.TSIS1_HSRS_V2_IDENTITY.content_sha256==json.loads(path.read_text())['content_sha256']
assert abs(r._native_integral((202.,202.1,202.2),(1.,2.,3.),202.,202.2)-.4)<1e-12
try:r.load_solar_spectral_irradiance_resource(Path(sys.argv[1])/'missing.csv')
except r.SolarSpectralRadiometryError as e:assert e.code is r.SolarSpectralRadiometryFailureCode.RESOURCE_NOT_FOUND
else:raise AssertionError('missing external spectrum admitted')
"""
    command = [sys.executable, "-I", "-S", "-c", script, str(installed), str(sdk), json.dumps(dependencies)]
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    # A fresh process must fail instead of falling back to embedded edition facts.
    packaged = installed / resource
    packaged.unlink()
    refused = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert refused.returncode != 0 and "solar_spectral_resource_tsis1_hsrs_v2.json" in refused.stderr
    assert "FileNotFoundError" in refused.stderr


def test_public_commands_teaching_and_configuration_ship_without_checkout(tmp_path):
    """Build from the sdist; run generated scripts with checkout access absent."""
    import tarfile
    import tomllib
    from zipfile import ZipFile
    import wenu_kernel
    project = tmp_path / "project"
    project.mkdir()
    shutil.copytree(ROOT / "src/wenu", project / "src/wenu",
                    ignore=shutil.ignore_patterns("__pycache__", "curated_catalogs", "observing_lists"))
    for name in ("pyproject.toml", "MANIFEST.in", "README.md"):
        shutil.copyfile(ROOT / name, project / name)
    shutil.copyfile(ROOT / "src/curated_catalogue_packaging.py", project / "src/curated_catalogue_packaging.py")
    for domain in ("open_clusters", "planetary_nebulae"):
        _bundle(project / "src/wenu/data/curated_catalogs", domain)
    release = tmp_path / "release"
    release.mkdir()
    result = subprocess.run([sys.executable, "-c", "from setuptools.build_meta import build_sdist; build_sdist("+repr(str(release))+")"],
                            cwd=project, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    resources = {}
    for pattern in ("notebooks/**/*.ipynb", "example_scripts/*.py", "configuration/defaults.toml",
                    "configuration/presets/*.toml", "configuration/presets/*.json", "data/translations.json"):
        resources.update({str(p.relative_to(ROOT / "src")): p.read_bytes()
                          for p in (ROOT / "src/wenu").glob(pattern)})
    assert len([p for p in resources if p.endswith(".ipynb")]) == 5
    assert len([p for p in resources if p.endswith(".py") and not p.endswith("__init__.py")]) == 6
    with tarfile.open(next(release.glob("*.tar.gz"))) as archive:
        members = {m.name.split("/src/", 1)[1]: m for m in archive.getmembers() if "/src/" in m.name}
        for path, payload in resources.items():
            assert path in members, f"sdist omits {path}"
            assert archive.extractfile(members[path]).read() == payload
    wheel_build = subprocess.run([sys.executable, "-m", "pip", "wheel", "--no-index", "--no-deps", "--no-build-isolation",
                                 "--wheel-dir", str(release), str(next(release.glob("*.tar.gz")))],
                                cwd=tmp_path, capture_output=True, text=True)
    assert wheel_build.returncode == 0, wheel_build.stdout + wheel_build.stderr
    wheel = next(release.glob("*.whl"))
    with ZipFile(wheel) as archive:
        for path, payload in resources.items():
            assert archive.read(path) == payload
    installed = tmp_path / "installed"
    result = subprocess.run([sys.executable, "-m", "pip", "install", "--no-index", "--no-deps", "--target", str(installed), str(wheel)],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    # The test does not execute acquisition commands beyond --help.
    script = r'''
import sys,json,runpy,socket,os
from pathlib import Path
sys.path[:0]=[sys.argv[1],sys.argv[2],*json.loads(sys.argv[3])]
installed=Path(sys.argv[1]); destination=Path(sys.argv[4])
expected=json.loads(sys.argv[5])
import wenu
assert Path(wenu.__file__).is_relative_to(installed)
for name in wenu.__all__: assert getattr(wenu,name) is not None,name
from importlib.metadata import distribution
entries={e.name:e.value for e in distribution('wenu').entry_points if e.group=='console_scripts'}
assert entries==expected
def no_network(*args,**kwargs):raise AssertionError('public smoke attempted network')
socket.create_connection=no_network;socket.socket.connect=no_network
for name in expected:
    sys.argv=[name,'--help']
    try:runpy.run_path(str(installed/'bin'/name),run_name='__main__')
    except SystemExit as exc:assert exc.code==0,(name,exc.code)
    else:raise AssertionError('help did not exit: '+name)
destination.mkdir();os.chdir(destination)
for name,args in [('wenu_examples',[]),('wenu_notebooks',['notebooks'])]:
    for options in (args,args,[*args,'--force']):
        sys.argv=[name,*options]
        try:runpy.run_path(str(installed/'bin'/name),run_name='__main__')
        except SystemExit as exc:assert exc.code==0
from importlib.resources import files
for path in (installed/'wenu/example_scripts').glob('*.py'):
    if path.name!='__init__.py':
        assert (destination/'wenu_examples'/path.name).read_bytes()==path.read_bytes()
        sys.argv=[str(path),'--help']
        try:runpy.run_path(str(destination/'wenu_examples'/path.name),run_name='__main__')
        except SystemExit as exc:assert exc.code==0
for path in (installed/'wenu/notebooks').rglob('*.ipynb'):
    copied=destination/'notebooks'/path.relative_to(installed/'wenu/notebooks')
    assert copied.read_bytes()==path.read_bytes()
    for cell in json.loads(copied.read_text())['cells']:
        if cell['cell_type']=='code':compile(''.join(cell['source']),str(copied),'exec')
from wenu.configuration import load_packaged_defaults,validate_configuration
validate_configuration(load_packaged_defaults())
from wenu.translations import translate_label
assert translate_label('Ecliptic','es')=='Eclíptica'
'''
    dependencies = [p for p in sys.path if Path(p).name in ("site-packages", "dist-packages")]
    sdk = Path(wenu_kernel.__file__).resolve().parent.parent
    entries = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["scripts"]
    assert len(entries) == 8
    result = subprocess.run([sys.executable, "-I", "-S", "-c", script, str(installed), str(sdk),
                             json.dumps(dependencies), str(tmp_path / "consumer"), json.dumps(entries)],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
