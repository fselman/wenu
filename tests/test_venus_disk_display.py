"""Contracts for the first drawable resolved Venus disk."""

from argparse import Namespace
from types import SimpleNamespace

import numpy as np
import pytest

from wenu.charts.chart_arguments import chart_disk_options
from wenu.charts.request_disks import (
    SolarSystemDiskDisplayRequest,
    configure_chart_request_disks,
)
from wenu.charts.solar_system_disk_preparation import MagnifyProjectedDisk
from wenu.geometry.projected import (
    ProjectedCurve,
    ProjectedCurves,
    ProjectedPoints,
    ProjectedPolygon,
    ProjectedPolygons,
)
from wenu.sky.semantic_identity import semantic_layer_identity
from wenu.sky.venus_disk import venus_disk_layers


def arguments(*, appearances=(), magnifications=()):
    return Namespace(
        planet_appearance=list(appearances),
        planet_disk_magnification=list(magnifications),
    )


def test_cli_resolves_object_specific_post_projection_magnification():
    assert chart_disk_options(
        arguments(
            appearances=("venus=resolved",),
            magnifications=("venus=40",),
        )
    ) == (SolarSystemDiskDisplayRequest("venus", 40.0),)


def test_resolved_appearance_defaults_to_physical_scale():
    assert chart_disk_options(
        arguments(appearances=("venus=resolved",))
    )[0].magnification == 1.0


def test_magnification_cannot_silently_enable_a_disk():
    with pytest.raises(
        ValueError,
        match="requires resolved appearance",
    ):
        chart_disk_options(
            arguments(magnifications=("venus=40",))
        )


@pytest.mark.parametrize("factor", (0, float("inf"), 1001))
def test_disk_magnification_is_governed(factor):
    with pytest.raises(ValueError):
        SolarSystemDiskDisplayRequest("venus", factor)


def test_component_layers_share_one_realization_and_magnification():
    layers = venus_disk_layers(magnification=40)
    assert tuple(layer.layer_name for layer in layers) == (
        "venus_disk_illuminated",
        "venus_disk_limb",
        "venus_disk_terminator",
    )
    assert len({id(layer.disk_realization) for layer in layers}) == 1
    assert {layer.magnification for layer in layers} == {40.0}


def test_curve_magnification_preserves_exact_projected_centre():
    realization = SimpleNamespace(
        transformed=SimpleNamespace(centre=object())
    )
    preparation = MagnifyProjectedDisk(realization, 4.0)
    projected = ProjectedCurves([
        ProjectedCurve(
            x=np.asarray((1.0, 3.0)),
            y=np.asarray((2.0, 4.0)),
        )
    ])

    def project(value):
        assert value is realization.transformed.centre
        return ProjectedPoints(
            x=np.asarray((1.0,)),
            y=np.asarray((2.0,)),
        )

    result = preparation.bind_project_geometry(project)(None, projected)
    assert np.allclose(result[0].x, (1.0, 9.0))
    assert np.allclose(result[0].y, (2.0, 10.0))
    assert result.metadata["display_magnification"] == 4.0


def test_polygon_magnification_preserves_component_identity():
    realization = SimpleNamespace(
        transformed=SimpleNamespace(centre=object())
    )
    preparation = MagnifyProjectedDisk(realization, 2.0)
    projected = ProjectedPolygons([
        ProjectedPolygon(
            x=np.asarray((0.0, 1.0, 0.0)),
            y=np.asarray((0.0, 0.0, 1.0)),
            name="illuminated",
        )
    ])
    project = lambda value: ProjectedPoints(
        x=np.asarray((0.0,)), y=np.asarray((0.0,))
    )
    result = preparation.bind_project_geometry(project)(None, projected)
    assert result[0].name == "illuminated"
    assert np.allclose(result[0].x, (0.0, 2.0, 0.0))
    assert np.allclose(result[0].y, (0.0, 0.0, 2.0))


def test_disk_components_have_independent_semantic_paths():
    identities = tuple(
        semantic_layer_identity(layer)
        for layer in venus_disk_layers()
    )
    assert tuple(identity.semantic_path_text for identity in identities) == (
        "sky/solar_system/planets/venus/disk/illuminated",
        "sky/solar_system/planets/venus/disk/limb",
        "sky/solar_system/planets/venus/disk/terminator",
    )


def test_request_disk_configuration_replaces_prior_dynamic_layers():
    class Sky:
        def __init__(self):
            self._layers = []

        @property
        def layers(self):
            return tuple(self._layers)

        def add(self, layer):
            self._layers.append(layer)

        def remove(self, layer):
            self._layers.remove(layer)

    sky = Sky()
    first = SimpleNamespace(
        solar_system_disks=(SolarSystemDiskDisplayRequest("venus", 20),)
    )
    second = SimpleNamespace(
        solar_system_disks=(SolarSystemDiskDisplayRequest("venus", 200),)
    )
    configure_chart_request_disks(sky, first)
    configure_chart_request_disks(sky, second)

    assert len(sky.layers) == 3
    assert {layer.magnification for layer in sky.layers} == {200.0}
    assert sky.venus_disk_illuminated in sky.layers
    assert sky.venus_disk_limb in sky.layers
    assert sky.venus_disk_terminator in sky.layers


@pytest.mark.parametrize('kind', ('single', 'observed', 'frozen'))
def test_disk_component_reuse_checks_live_resources_and_request_identity(kind):
    """One coherent component result per request, never a cross-request cache."""
    from dataclasses import replace
    from astropy.time import Time
    from wenu.coordinates import CoordinateSpec, ObservationContext, PositionStatus
    from wenu.sky.realization import LayerRealizationContext
    from wenu.sky.venus import VENUS_POINT
    from wenu.sky.venus_disk import SolarSystemDiskRealization
    from wenu.sky.venus_disk_sequence import ObservedSolarSystemDiskSequenceRealization
    from wenu.sky.frozen_earth_venus_disk_sequence import FrozenEarthSolarSystemDiskSequenceRealization
    from test_solar_system_disk_sequences import (
        Source, Astrometric, Apparent, observer_state, realized, request,
    )
    from test_frozen_earth_disk_sequences import realize as frozen, request as frozen_request

    generation = [0]
    def resource():
        if generation[0] == 'closed':
            raise RuntimeError('borrowed observer resource closed')
        return generation[0]
    observer = SimpleNamespace(t_astropy=Time('2026-08-30T00:00:00', scale='utc'),
                               geometry_resource_identity=resource)
    observation = ObservationContext(longitude_deg=0, latitude_deg=0, elevation_m=0,
                                    instant='2026-08-30T00:00:00', time_scale='utc')
    product = CoordinateSpec(frame='icrs', origin='observer',
                            position_status=PositionStatus.APPARENT)
    if kind == 'frozen':
        product = CoordinateSpec(frame='barycentric-mean-ecliptic', origin='frozen-earth',
                                position_status=PositionStatus.GEOMETRIC, equinox='J2000.0')
    context = LayerRealizationContext(product_coordinate_spec=product,
        observation=observation, evaluation_instant=observation.instant, evaluation_time_scale='utc')
    calls = []
    fail = [False]
    def acquire(value):
        calls.append(value)
        if fail[0]:
            raise RuntimeError('fresh admission refused')
        return Source()
    coordinates = SimpleNamespace(transform=lambda geometry, *args: geometry)
    if kind == 'single':
        owner = SolarSystemDiskRealization(VENUS_POINT, source_factory=acquire,
            observer_state_factory=observer_state, astrometric_realizer=Astrometric(),
            apparent_realizer=Apparent(), coordinate_service=coordinates)
    else:
        physical = frozen()[0] if kind == 'frozen' else realized()[0]
        def sequence(value, *, observer):
            acquire(observer)
            return physical
        factory = SimpleNamespace(sequence=sequence)
        if kind == 'frozen':
            owner = FrozenEarthSolarSystemDiskSequenceRealization(frozen_request(), sequence_realizer=factory)
        else:
            owner = ObservedSolarSystemDiskSequenceRealization(request(), sequence_realizer=factory,
                                                               coordinate_service=coordinates)
    first = owner.realize(context, observer)
    assert owner.realize(context, observer) is first
    assert len(calls) == 1
    generation[0] = 'closed'
    with pytest.raises(RuntimeError, match='resource closed'):
        owner.realize(context, observer)
    generation[0] = 1
    refreshed = owner.realize(context, observer)
    assert refreshed is not first
    assert len(calls) == 2
    fail[0] = True
    equal_but_new_request = replace(context)
    assert equal_but_new_request == context
    with pytest.raises(RuntimeError, match='fresh admission refused'):
        owner.realize(equal_but_new_request, observer)
    assert len(calls) == 3


@pytest.mark.parametrize('body', ('venus', 'moon'))
def test_default_single_disk_routes_target_and_reception_sun_through_kernel(monkeypatch, body):
    from dataclasses import replace
    from test_solar_system_disk_sequences import _kernel_disk_dependencies
    from wenu.coordinates import CoordinateSpec, ObservationContext, PositionStatus
    from wenu.sky.realization import LayerRealizationContext
    from wenu.sky.solar_system_catalog import SOLAR_SYSTEM_BODY_CATALOG
    from wenu.sky.venus_disk import SolarSystemDiskRealization
    from wenu_kernel.kernel import KernelSession
    from wenu_kernel.errors import UnsupportedCapability
    from astropy import units as u
    source, observer, _, dependencies = _kernel_disk_dependencies(monkeypatch)
    dependencies.pop('sample_observer_factory')
    descriptor = SOLAR_SYSTEM_BODY_CATALOG.resolve(body)
    instant = '2026-08-30T00:00:00.000000000'
    observation = ObservationContext(longitude_deg=0, latitude_deg=0, elevation_m=0,
                                    instant=instant, time_scale='tdb')
    context = LayerRealizationContext(product_coordinate_spec=CoordinateSpec(
        frame='icrs', origin='observer', position_status=PositionStatus.APPARENT,
        instant=instant, time_scale='tdb'), observation=observation,
        evaluation_instant=instant, evaluation_time_scale='tdb')
    baseline = SolarSystemDiskRealization(descriptor, source_factory=lambda observer: source,
                                         **dependencies).realize(context, observer)
    evaluate = KernelSession.evaluate
    queries = []
    def record(session, query):
        queries.append(query)
        return evaluate(session, query)
    monkeypatch.setattr(KernelSession, 'evaluate', record)
    owner = SolarSystemDiskRealization(descriptor, **dependencies)
    routed = owner.realize(context, observer)
    physical = routed.physical.appearance
    expected = baseline.physical.appearance
    assert physical.angular_diameter_arcsec == pytest.approx(expected.angular_diameter_arcsec, rel=1e-12)
    assert physical.illuminated_fraction == pytest.approx(expected.illuminated_fraction, abs=1e-13)
    assert np.allclose(routed.limb.lon_deg[0], baseline.limb.lon_deg[0], rtol=0, atol=1e-10)
    assert {q.objects[0].value for q in queries} == {'ephemeris:sun', 'ephemeris:' + descriptor.target}
    assert queries[-1].objects[0].value == 'ephemeris:sun'
    assert not hasattr(physical, 'display_magnification')
    def change_sun(session, query):
        batch = record(session, query)
        row = batch.states[0]
        if query.objects[0].value == 'ephemeris:sun':
            x, y, z = row.position_m
            row = replace(row, position_m=(x, y + .2 * u.au.to(u.m), z))
        return replace(batch, states=(row,))
    monkeypatch.setattr(KernelSession, 'evaluate', change_sun)
    changed = owner.realize(replace(context), observer).physical.appearance
    assert changed.angular_diameter_arcsec == pytest.approx(physical.angular_diameter_arcsec)
    assert changed.illuminated_fraction != pytest.approx(physical.illuminated_fraction, abs=1e-5)
    def refuse(session, query):
        raise UnsupportedCapability('single disk state refusal')
    monkeypatch.setattr(KernelSession, 'evaluate', refuse)
    with pytest.raises(UnsupportedCapability, match='single disk state refusal'):
        owner.realize(replace(context), observer)


@pytest.mark.parametrize('kind', ('single', 'observed', 'frozen'))
def test_raw_and_kernel_disk_paths_preserve_canonical_png_outputs(monkeypatch, tmp_path, kind):
    """Actual projection/preparation/renderer; constructed observation backend."""
    from test_solar_system_disk_sequences import _kernel_disk_dependencies, request
    from test_frozen_earth_disk_sequences import request as frozen_request
    from wenu.sky.solar_system_catalog import SOLAR_SYSTEM_BODY_CATALOG
    from wenu.sky.venus_disk import SolarSystemDiskRealization, solar_system_disk_layers
    from wenu.sky.venus_disk_sequence import (
        ObservedSolarSystemDiskSequenceRealization, observed_solar_system_disk_sequence_layers,
    )
    from wenu.sky.solar_system_disk_sequences import ObservedSolarSystemDiskSequenceRealizer
    from wenu.sky.frozen_earth_disk_sequences import FrozenEarthDiskSequenceRealizer
    from wenu.sky.frozen_earth_venus_disk_sequence import (
        FrozenEarthSolarSystemDiskSequenceRealization, frozen_earth_solar_system_disk_sequence_layers,
    )
    from wenu.sky.celestial_sphere import CelestialSphere
    from wenu.sky.realization import LayerRealizationContext
    from wenu.coordinates import CoordinateSpec, ObservationContext, PositionStatus
    from wenu.projections import StereographicProjection
    from wenu.rendering import MatplotlibRenderer
    import matplotlib.pyplot as plt
    from matplotlib.image import imread
    from wenu.charts.solar_system_disk_preparation import MagnifyProjectedDiskSequence

    source, observer, _, dependencies = _kernel_disk_dependencies(monkeypatch)
    instant = '2026-08-30T00:00:00.000000000'
    observation = ObservationContext(longitude_deg=0, latitude_deg=0, elevation_m=0,
                                    instant=instant, time_scale='tdb')
    body = 'moon' if kind == 'single' else ('mercury' if kind == 'frozen' else 'venus')
    descriptor = SOLAR_SYSTEM_BODY_CATALOG.resolve(body)
    product = CoordinateSpec(frame='icrs', origin='observer', position_status=PositionStatus.APPARENT,
                            instant=instant, time_scale='tdb')
    if kind == 'frozen':
        product = CoordinateSpec(frame='barycentric-mean-ecliptic', origin='frozen-earth',
            position_status=PositionStatus.GEOMETRIC, equinox='J2000.0')
    context = LayerRealizationContext(product_coordinate_spec=product, observation=observation,
        evaluation_instant=instant, evaluation_time_scale='tdb')
    projection = StereographicProjection()
    images, geometry_receipts = [], []
    bounds = None
    for routed in (False, True):
        factory = {} if routed else {'source_factory': lambda observer: source}
        if kind == 'single':
            deps = {k: v for k, v in dependencies.items() if k != 'sample_observer_factory'}
            owner = SolarSystemDiskRealization(descriptor, **factory, **deps)
            layers = solar_system_disk_layers(descriptor, magnification=40.)
            prepare = MagnifyProjectedDisk(owner, 40.)
        else:
            if kind == 'observed':
                value = request(descriptor=descriptor, display_name=descriptor.display_name,
                    physical_radius_km=descriptor.physical_radius_km, radius_model=descriptor.radius_model,
                    start_time_scale='tdb', step_days=1., n_steps=1)
                owner = ObservedSolarSystemDiskSequenceRealization(value,
                    sequence_realizer=ObservedSolarSystemDiskSequenceRealizer(**factory, **dependencies))
                layers = observed_solar_system_disk_sequence_layers(value, magnification=500.)
            else:
                value = frozen_request(descriptor=descriptor, display_name=descriptor.display_name,
                    physical_radius_km=descriptor.physical_radius_km, radius_model=descriptor.radius_model,
                    start_time_scale='tdb', step_days=1., n_steps=1)
                owner = FrozenEarthSolarSystemDiskSequenceRealization(value,
                    sequence_realizer=FrozenEarthDiskSequenceRealizer(**factory))
                layers = frozen_earth_solar_system_disk_sequence_layers(value, magnification=500.)[:-1]
            prepare = MagnifyProjectedDiskSequence(owner, 500.)
        sky = CelestialSphere(None)
        options = {}
        for layer in layers:
            layer.disk_realization = owner
            sky.add(layer)
            style = ({'facecolor': '#6e9dcc', 'edgecolor': 'none'}
                     if layer.component_role == 'illuminated' else {'color': 'black', 'linewidth': .8})
            options[layer] = {'prepare': prepare, 'render': {'style': style}}
        figure, axes = plt.subplots(figsize=(3, 3), dpi=90)
        try:
            result = sky.draw_chart(observer=observer, realization_context=context,
                projection=projection, renderer=MatplotlibRenderer(axes), layer_options=options)
            centre = owner.transformed.centre if kind == 'single' else owner.transformed.centres
            projected = projection.project_geometry(centre)
            if bounds is None:
                bounds = (float(np.mean(projected.x)), float(np.mean(projected.y)))
            axes.set(xlim=(bounds[0]-.3, bounds[0]+.3), ylim=(bounds[1]-.3, bounds[1]+.3), aspect='equal')
            axes.set_axis_off()
            output = tmp_path / f'{kind}-{routed}.png'
            figure.savefig(output)
            images.append(imread(output))
            geometry_receipts.append(tuple(item.spherical for item in result.layers))
        finally:
            plt.close(figure)
    np.testing.assert_array_equal(images[0], images[1])
    assert np.any(images[0][:, :, :3] < .5)
    for raw, routed in zip(*geometry_receipts):
        for a, b in zip(raw.lon_deg, routed.lon_deg):
            np.testing.assert_allclose(a, b, rtol=0, atol=1e-10)
        for a, b in zip(raw.lat_deg, routed.lat_deg):
            np.testing.assert_allclose(a, b, rtol=0, atol=1e-10)
