"""All non-Earth major planets reuse the apparent symbolic-point path."""

from wenu.charts.chart_arguments import _SYMBOLIC_BODY_KEYS
from wenu.charts.detail import ResolvedDetail, SkyContentSelection
from wenu.charts.detail_application import apply_resolved_detail
from wenu.charts.styles import PublicationStyle
from wenu.sky.celestial_sphere import CelestialSphere
from wenu.sky.major_planets import APPARENT_MAJOR_PLANETS
from wenu.sky.mercury import MERCURY_BODY
from wenu.sky.semantic_identity import semantic_layer_identity
from wenu.sky.solar_system_bodies import SYMBOLIC_POINT
from wenu.sky.solar_system_catalog import SOLAR_SYSTEM_BODY_CATALOG


EXPECTED = {
    "mercury": ("mercury", "199", "Mercurio", "☿"),
    "venus": ("venus", "299", "Venus", "♀"),
    "mars": ("mars barycenter", "499", "Marte", "♂"),
    "jupiter": ("jupiter barycenter", "599", "Júpiter", "♃"),
    "saturn": ("saturn barycenter", "699", "Saturno", "♄"),
    "uranus": ("uranus barycenter", "799", "Urano", "♅"),
    "neptune": ("neptune barycenter", "899", "Neptuno", "♆"),
}


def test_catalog_data_separates_provider_targets_from_physical_planet_ids():
    assert set(_SYMBOLIC_BODY_KEYS) == set(EXPECTED)
    assert "earth" not in _SYMBOLIC_BODY_KEYS
    for key, (target, physical_id, spanish_name, symbol) in EXPECTED.items():
        descriptor = SOLAR_SYSTEM_BODY_CATALOG.resolve(key)
        assert descriptor.target == target
        assert descriptor.physical_body_id == physical_id
        assert descriptor.body_class == "planet"
        assert descriptor.supports(SYMBOLIC_POINT)
        assert descriptor.display_name_for("es") == spanish_name
        assert descriptor.astronomical_symbol == symbol
    assert MERCURY_BODY not in APPARENT_MAJOR_PLANETS


def test_every_planet_uses_one_generic_layer_style_and_semantic_path():
    sky = CelestialSphere(None)
    layers = tuple(
        sky.add_solar_system_body(SOLAR_SYSTEM_BODY_CATALOG.resolve(key))
        for key in EXPECTED
    )
    selected = apply_resolved_detail(
        sky,
        ResolvedDetail(
            enabled_layers=set(EXPECTED),
            content_selection=SkyContentSelection(
                solar_system_objects=set(EXPECTED)
            ),
        ),
        base_layer_options=PublicationStyle().layer_options(sky),
    )
    for layer in layers:
        key = layer.body_descriptor.entity_key
        options = selected.layer_options[layer]
        assert options["enabled"] is True
        assert options["geometry"]["selected"] == set(EXPECTED)
        assert options["render"]["style"]["marker"] == "o"
        assert options["render"]["style"]["s"] == 10.5
        identity = semantic_layer_identity(layer)
        assert identity.semantic_path_text == (
            f"sky/solar_system/planets/{key}"
        )
        assert identity.display_name == layer.body_descriptor.display_name


def test_major_planet_and_moon_default_points_consume_kernel_states_and_refusal(monkeypatch):
    """Constructed SPK/observer/apparent seam; no physical-accuracy claim."""
    from dataclasses import replace
    from types import SimpleNamespace
    import numpy as np
    import pytest
    from astropy.time import Time
    from wenu.coordinates import CoordinateSpec, ObservationContext, PositionStatus
    from wenu.ephemeris import EphemerisResourceIdentity, EphemerisState
    from wenu.sky.realization import LayerRealizationContext
    from wenu.sky.solar_system_points import SolarSystemPointLayer
    from wenu.skyfield_ephemeris import SkyfieldEphemerisStateSource
    from wenu.solar_system_directions import ObserverBarycentricState
    from wenu_kernel.kernel import KernelSession
    from wenu_kernel.errors import UnsupportedCapability

    resource = EphemerisResourceIdentity(
        'synthetic', 'constructed', 'synthetic.bsp', 'a' * 64,
        'JD 2400000.5', 'JD 2500000.5', 'tdb', ('constructed fixture',))
    instant = '2026-08-30T00:00:00.000'
    received = []
    source = object.__new__(SkyfieldEphemerisStateSource)
    source._kernel = object()
    source.resource = resource
    def state(request):
        received.append(request)
        return EphemerisState(request, (1.0, 1.0, .1), (.001, .002, .003),
                              'au', 'au/day', resource, '301' if request.target == 'moon' else '299', '0')
    source.state = state
    monkeypatch.setattr(SkyfieldEphemerisStateSource, 'from_observer',
                        classmethod(lambda cls, observer: source))
    observer_pv = ObserverBarycentricState(
        'synthetic site', 'solar system barycenter', 'icrf', instant, 'tdb',
        (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 'au', 'au/day', resource)
    centre = SimpleNamespace(target='site', position=SimpleNamespace(au=observer_pv.position),
                             velocity=SimpleNamespace(au_per_d=observer_pv.velocity))
    observer = SimpleNamespace(ephemeris=source._kernel, t=object(),
                               t_astropy=Time(instant, scale='tdb'),
                               skyfield=SimpleNamespace(at=lambda t: centre))
    def apparent(self, deflectors):
        assert self.light_time > 0
        assert deflectors == (10, 599, 699)
        x, y, z = self.position.au
        return SimpleNamespace(radec=lambda: (
            SimpleNamespace(hours=float(np.degrees(np.arctan2(y, x)) % 360) / 15),
            SimpleNamespace(degrees=float(np.degrees(np.arctan2(z, np.hypot(x, y))))), None))
    monkeypatch.setattr('wenu.skyfield_ephemeris.SkyfieldAstrometric.apparent', apparent)
    product = CoordinateSpec(frame='icrs', origin='observer',
                            position_status=PositionStatus.APPARENT, instant=instant, time_scale='tdb')
    observation = ObservationContext(longitude_deg=0, latitude_deg=0, elevation_m=0,
                                     instant=instant, time_scale='tdb')
    context = LayerRealizationContext(product_coordinate_spec=product,
        observation=observation, evaluation_instant=instant, evaluation_time_scale='tdb')
    class Coordinates:
        def transform(self, geometry, target, observation):
            return geometry
    original = KernelSession.evaluate
    queries = []
    def changed(session, query):
        queries.append(query)
        batch = original(session, query)
        row = batch.states[0]
        x, y, z = row.position_m
        return replace(batch, states=(replace(row, position_m=(-y, x, z)),))
    for key in (*EXPECTED, 'moon'):
        descriptor = SOLAR_SYSTEM_BODY_CATALOG.resolve(key)
        layer = SolarSystemPointLayer(descriptor,
            observer_state_factory=lambda observer, *, source: observer_pv,
            coordinate_service=Coordinates())
        monkeypatch.setattr(KernelSession, 'evaluate', original)
        baseline = layer.realize(context, observer)
        monkeypatch.setattr(KernelSession, 'evaluate', changed)
        result = layer.realize(context, observer)
        assert result.lon_deg[0] == pytest.approx((baseline.lon_deg[0] + 90) % 360)
        assert result.lat_deg == pytest.approx(baseline.lat_deg)
        assert result.ids.tolist() == [key]
        assert result.metadata['ephemeris_sha256'] == resource.sha256
        assert received[-1].target == descriptor.target
        assert Time(received[-1].instant, scale='tdb') < Time(instant, scale='tdb')
        def refuse(session, query):
            raise UnsupportedCapability('point route refusal')
        monkeypatch.setattr(KernelSession, 'evaluate', refuse)
        with pytest.raises(UnsupportedCapability, match='point route refusal'):
            layer.realize(context, observer)
    assert queries


def test_real_major_planet_and_moon_kernel_adapter_matches_existing_raw_science():
    """Offline Mac DE440s oracle: preserve the already-accepted raw route."""
    import pytest
    from pathlib import Path
    from wenu.observer import Observer, DEFAULT_DATA_DIRECTORY, DEFAULT_EPHEMERIS
    from wenu.ephemeris_state import KernelEphemerisStateSource
    from wenu.skyfield_ephemeris import (
        SkyfieldEphemerisStateSource, SkyfieldApparentDirectionRealizer,
        skyfield_observer_barycentric_state,
    )
    from wenu.solar_system_directions import AstrometricDirectionRealizer, AstrometricDirectionRequest

    resource_path = Path(DEFAULT_DATA_DIRECTORY) / DEFAULT_EPHEMERIS
    if not resource_path.is_file():
        raise FileNotFoundError(f'Offline DE440s acceptance requires {resource_path}')
    observer = Observer(lat_deg=-33.0, lon_deg=-71.0, elevation_m=52.0,
                        timezone_name='UTC', time='2026-08-30T00:00:00')
    try:
        source = SkyfieldEphemerisStateSource.from_observer(observer)
        wrapped = KernelEphemerisStateSource(source)
        reception = skyfield_observer_barycentric_state(observer, source=source)
        expected_ids = dict(mercury='199', venus='299', mars='4', jupiter='5',
                            saturn='6', uranus='7', neptune='8', moon='301')
        for key, provider_id in expected_ids.items():
            descriptor = SOLAR_SYSTEM_BODY_CATALOG.resolve(key)
            request = AstrometricDirectionRequest(descriptor.target, descriptor.centre,
                                                  reception.instant, reception.time_scale)
            raw = AstrometricDirectionRealizer().direction(source, request, reception)
            routed = AstrometricDirectionRealizer().direction(wrapped, request, reception)
            assert routed.target_provider_id == raw.target_provider_id == provider_id
            assert routed.light_time_days == pytest.approx(raw.light_time_days, rel=1e-14, abs=1e-15)
            assert routed.distance_au == pytest.approx(raw.distance_au, rel=1e-14, abs=1e-15)
            assert routed.relative_velocity_au_per_day == pytest.approx(raw.relative_velocity_au_per_day, rel=1e-14, abs=1e-15)
            actual = SkyfieldApparentDirectionRealizer().direction(routed, observer=observer, source=source)
            expected = SkyfieldApparentDirectionRealizer().direction(raw, observer=observer, source=source)
            assert actual.geometry.lon_deg == pytest.approx(expected.geometry.lon_deg, rel=0, abs=1e-11)
            assert actual.geometry.lat_deg == pytest.approx(expected.geometry.lat_deg, rel=0, abs=1e-11)
    finally:
        observer.close()
