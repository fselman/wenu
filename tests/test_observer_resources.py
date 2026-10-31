"""Milestone 45G.1 observer ephemeris resource contracts."""

from wenu import Observer


def test_observer_close_is_idempotent():
    observer = Observer(
        location="La Ligua",
        time="2026-08-15 21:00",
    )

    assert observer._ephemeris_finalizer.alive
    observer.close()
    assert not observer._ephemeris_finalizer.alive
    observer.close()


def test_observer_context_manager_closes_ephemeris():
    with Observer(
        location="La Ligua",
        time="2026-08-15 21:00",
    ) as observer:
        finalizer = observer._ephemeris_finalizer
        assert finalizer.alive

    assert not finalizer.alive


def _resolve_site(name, **overrides):
    arguments = dict(
        location=name, lat_deg=None, lon_deg=None,
        elevation_m=None, timezone_name=None,
    )
    arguments.update(overrides)
    return Observer._resolve_location(**arguments)


def test_packaged_locations_cover_municipalities_and_preserve_legacy_sites():
    import math
    from zoneinfo import ZoneInfo
    from wenu.observer import _registered_locations

    records = _registered_locations()
    seats = [site for site in records if site["kind"] == "municipal_seat"]
    assert len(seats) == 345
    assert len({site["commune_code"] for site in seats}) == 345
    assert len({site["region_code"] for site in seats}) == 16
    assert any(site["kind"] == "observatory" for site in records)
    for site in records:
        assert site["country"] == "Chile"
        assert site["country_code"] == "CL"
        assert -90 <= site["lat_deg"] <= 90
        assert -180 <= site["lon_deg"] <= 180
        assert math.isfinite(site["lat_deg"])
        assert math.isfinite(site["lon_deg"])
        ZoneInfo(site["timezone"])
        resolved = _resolve_site(site["qualified_name"])
        assert resolved[:2] == (site["lat_deg"], site["lon_deg"])
        assert _resolve_site(site["id"]) == resolved
        if site["runtime_height_reference"] != "legacy_wenu_unspecified":
            assert abs(
                site["elevation_m"] - site["height_m"]
                - site["geoid_undulation_m"]
            ) < 0.0011
    assert _resolve_site("La Ligua") == (
        -32.443342, -71.230289, 52.0, "America/Santiago", "La Ligua"
    )
    assert _resolve_site("Papudo") == (
        -32.5078, -71.4411, 15.0, "America/Santiago", "Papudo"
    )


def test_location_suffixes_accents_and_regional_timezone_defaults():
    assert _resolve_site("Chile:Valparaíso:Petorca:La Ligua:La Ligua") == (
        _resolve_site("La Ligua")
    )
    assert _resolve_site("Valparaíso:Petorca:La Ligua:La Ligua") == (
        _resolve_site("la ligua")
    )
    assert _resolve_site("Petorca:La Ligua:La Ligua") == _resolve_site(
        "La Ligua:La Ligua"
    )
    assert _resolve_site("  NUBLE:DIGUILLIN:CHILLAN:CHILLAN  ")[4] == "Chillán"
    assert _resolve_site("Coyhaique")[3] == "America/Coyhaique"
    assert _resolve_site("Punta Arenas")[3] == "America/Punta_Arenas"
    assert _resolve_site("Hanga Roa")[3] == "Pacific/Easter"
    assert _resolve_site("Cabo de Hornos")[4] == "Puerto Williams"
    assert _resolve_site("Camarones")[4] == "Cuya"
    assert _resolve_site("Paranal")[4] == "Observatorio Paranal"
    assert _resolve_site("La Ligua", elevation_m=75, timezone_name="UTC") == (
        -32.443342, -71.230289, 75.0, "UTC", "La Ligua"
    )


def test_location_ambiguity_is_not_silently_resolved(monkeypatch):
    import pytest
    import wenu.observer as module

    records = (
        dict(id="one", name="San Pedro", country="Chile", region="R1", province="P1",
             commune="C1", qualified_name="Chile:R1:P1:C1:San Pedro",
             aliases=(), region_aliases=()),
        dict(id="two", name="San Pedro", country="Chile", region="R2", province="P2",
             commune="C2", qualified_name="Chile:R2:P2:C2:San Pedro",
             aliases=(), region_aliases=()),
    )
    monkeypatch.setattr(module, "_registered_locations", lambda: records)
    with pytest.raises(ValueError, match="Ambiguous location") as error:
        module._resolve_registered_location("San Pedro")
    assert "R1:P1:C1:San Pedro" in str(error.value)
    assert "R2:P2:C2:San Pedro" in str(error.value)
    assert module._resolve_registered_location("C2:San Pedro")["id"] == "two"
    with pytest.raises(ValueError, match="Unknown location"):
        module._resolve_registered_location("R2:P1:C1:San Pedro")
    with pytest.raises(ValueError, match="Unknown location"):
        module._resolve_registered_location("Argentina:R1:P1:C1:San Pedro")
    with pytest.raises(ValueError, match="Location must"):
        module._resolve_registered_location("R1::C1:San Pedro")
    foreign = dict(records[0], id="foreign", country="Argentina",
                   qualified_name="Argentina:R1:P1:C1:San Pedro")
    monkeypatch.setattr(module, "_registered_locations", lambda: (*records, foreign))
    assert module._resolve_registered_location(
        "Chile:R1:P1:C1:San Pedro"
    )["id"] == "one"
    assert module._resolve_registered_location(
        "Argentina:R1:P1:C1:San Pedro"
    )["id"] == "foreign"
    with pytest.raises(ValueError, match="Ambiguous location"):
        module._resolve_registered_location("R1:P1:C1:San Pedro")


def test_location_snapshot_is_immutable_and_missing_height_requires_override(
    monkeypatch,
):
    import pytest
    import wenu.observer as module

    site = module._resolve_registered_location("La Ligua")
    with pytest.raises(TypeError):
        site["lat_deg"] = 0
    missing = dict(site, elevation_m=None)
    monkeypatch.setattr(module, "_resolve_registered_location", lambda _: missing)
    with pytest.raises(ValueError, match="No usable height"):
        _resolve_site("La Ligua")
    assert _resolve_site("La Ligua", elevation_m=123)[2] == 123


def test_location_snapshot_rejects_changed_packaged_bytes(monkeypatch, tmp_path):
    import json
    import pytest
    import wenu.observer as module

    (tmp_path / "chile_locations_v1.json").write_text("{}")
    (tmp_path / "chile_locations_manifest_v1.json").write_text(
        json.dumps({"catalogue_sha256": "0" * 64})
    )
    monkeypatch.setattr(module, "files", lambda _: tmp_path)
    with pytest.raises(ValueError, match="digest mismatch"):
        module._registered_locations.__wrapped__()


# The closest existing owner protects observer resource identity/lifetime.
# These additive cases protect reception scales, resource coverage and the
# star-independent backend; they do not admit target apparent-place accuracy.
def _reception_backend(**changes):
    from hashlib import sha256
    from pathlib import Path
    from astropy.utils import iers
    from wenu.astrometric_observation import ErfaReceptionBackend,reception_backend_identity
    from wenu_kernel.records import TimePoint,TimeSpan
    args=dict(leap_seconds_path=iers.IERS_LEAP_SECOND_FILE,
        leap_seconds_sha256=sha256(Path(iers.IERS_LEAP_SECOND_FILE).read_bytes()).hexdigest(),
        eop_path=iers.IERS_B_FILE,eop_sha256=sha256(Path(iers.IERS_B_FILE).read_bytes()).hexdigest(),
        coverage=TimeSpan(TimePoint(2456300,0,'tt'),TimePoint(2458000,0,'tt')),
        backend_identity=reception_backend_identity())
    args.update(changes)
    return ErfaReceptionBackend(**args)


def _prepare_reception(backend, reception='2016-12-31T23:59:60Z', **site):
    args=dict(longitude_deg=-71.23,latitude_deg=-32.44,height_m=52.)
    args.update(site)
    return backend.prepare(reception,**args)


def test_reception_leap_second_analytic_tt_tai_and_equivalent_tt_input():
    from fractions import Fraction
    from dataclasses import FrozenInstanceError
    import pytest
    b=_reception_backend()
    events=tuple(_prepare_reception(b,t) for t in ('2016-12-31T23:59:59Z',
        '2016-12-31T23:59:60Z','2017-01-01T00:00:00Z'))
    day=lambda t:Fraction(t.jd1)+Fraction(t.jd2)
    for r in events:
        # Analytic definition, independently checked without Time.tt.
        assert abs(float((day(r.tt)-day(r.tai))*86400)-32.184)<1e-11
        assert r.original.endswith('Z') and r.tcb.scale=='tcb'
        assert r.tdb_tcb_conversion.source==r.tdb
        assert r.tdb_tcb_conversion.target==r.tcb
        assert r.numerical_error_s is r.physical_error_s is r.position_error_m is None
        assert r.model.dependencies[0].sha256 and r.model.dependencies[1].sha256
        assert _prepare_reception(b,r.tt).tdb==r.tdb
    for a,c in zip(events,events[1:]):
        assert abs(float((day(c.tai)-day(a.tai))*86400)-1)<1e-11
    expected=Fraction(2457754)+Fraction(1,2)+Fraction('68.184')/86400
    assert abs(float((day(events[1].tt)-expected)*86400))<1e-11
    with pytest.raises(FrozenInstanceError):events[0].site_wgs84=(0,0,0)


def test_reception_resources_backend_coverage_and_global_leaps_refuse(monkeypatch):
    from dataclasses import replace
    import pytest
    import erfa
    from wenu_kernel.errors import KernelError
    from wenu_kernel.records import TimePoint,TimeSpan
    for changes in (dict(leap_seconds_sha256='0'*64),dict(eop_sha256='0'*64),
        dict(backend_identity=('wrong',)*4),
        dict(coverage=TimeSpan(TimePoint(2400000,0,'tt'),TimePoint(2500000,0,'tt')))):
        with pytest.raises(KernelError):_reception_backend(**changes)
    b=_reception_backend();good=_prepare_reception(b)
    for time in (b.coverage.start,b.coverage.stop):
        assert _prepare_reception(b,time).tt is time
    from astropy import units as u
    from astropy.utils import iers
    with monkeypatch.context() as patch:
        patch.setattr(b._eop,'pm_xy',lambda *a,**k:(0*u.rad,0*u.rad,iers.FROM_IERS_A_PREDICTION))
        with pytest.raises(KernelError,match='Final IERS-B'):_prepare_reception(b)
    assert _prepare_reception(b)==good
    for value in ('2011-01-01T00:00:00Z','2051-01-01T00:00:00Z',
                  '2016-12-31T23:59:60','2017-01-01T00:00:00+00:00',
                  replace(good.tt,scale='tdb')):
        with pytest.raises((KernelError,erfa.ErfaWarning)):_prepare_reception(b,value)
        assert _prepare_reception(b)==good
    for site in (dict(latitude_deg=91),dict(longitude_deg=181),dict(height_m=float('nan')),dict(height_m=10001),dict(latitude_deg=True)):
        with pytest.raises(KernelError):_prepare_reception(b,**site)
    import wenu.astrometric_observation as module
    monkeypatch.setattr(module,'_leap_rows',lambda:())
    with pytest.raises(KernelError,match='leap table changed'):_prepare_reception(b)


def test_reception_offline_local_copy_survives_file_changes_and_never_loads_observer(monkeypatch,tmp_path):
    from pathlib import Path
    from astropy.utils import iers
    from wenu.observer import Observer
    leap=tmp_path/'leaps.dat';eop=tmp_path/'eop.dat'
    leap.write_bytes(Path(iers.IERS_LEAP_SECOND_FILE).read_bytes())
    eop.write_bytes(Path(iers.IERS_B_FILE).read_bytes())
    def forbidden(*a,**k):raise AssertionError('No implicit resource/Observer path')
    monkeypatch.setattr(iers.IERS_Auto,'open',forbidden)
    monkeypatch.setattr(iers.LeapSeconds,'auto_open',forbidden)
    monkeypatch.setattr(Observer,'__init__',forbidden)
    import astropy.utils.data
    monkeypatch.setattr(astropy.utils.data,'download_file',forbidden)
    b=_reception_backend(leap_seconds_path=leap,eop_path=eop)
    first=_prepare_reception(b)
    leap.write_text('changed after admission');eop.write_text('changed after admission')
    assert _prepare_reception(b)==first
    assert [r.resource_id for r in first.model.dependencies]==[
        'iers-leap-seconds','iers-final-eop-b','erfa-compiled-backend']


def test_reception_observer_displacement_and_time_depend_on_site_and_eop(monkeypatch):
    from math import sqrt
    import pytest
    b=_reception_backend()
    first=_prepare_reception(b)
    opposite=_prepare_reception(b,longitude_deg=108.77)
    separation=sqrt(sum((a-c)**2 for a,c in zip(first.observer_position_tdb_m,
                                               opposite.observer_position_tdb_m)))
    assert 1e7<separation<1.3e7
    assert first.earth_position_tdb_m!=opposite.earth_position_tdb_m  # topocentric reception TDB
    assert abs(first.tdb_minus_tt_s-opposite.tdb_minus_tt_s)>1e-7
    assert first.site_wgs84!=opposite.site_wgs84
    # Independent scale/range sanity, not a physical accuracy bound.
    assert 1.4e11<sqrt(sum(x*x for x in first.earth_position_tdb_m))<1.6e11
    assert 29000<sqrt(sum(x*x for x in first.earth_velocity_tdb_m_s))<31000
    import wenu.astrometric_observation as module
    dut1=b._eop.ut1_utc
    def shifted(*a,**k):
        value,status=dut1(*a,**k)
        from astropy import units as u
        return value+1*u.s,status
    with monkeypatch.context() as patch:
        patch.setattr(b._eop,'ut1_utc',shifted)  # synthetic UT1 fault; no real source rewrite
        changed=_prepare_reception(b)
        distance=sqrt(sum((a-c)**2 for a,c in zip(first.observer_position_tdb_m,
                                                changed.observer_position_tdb_m)))
        assert 300<distance<500
        assert changed.earth_orientation[0]==first.earth_orientation[0]+1
    original=module.erfa.dtdb
    monkeypatch.setattr(module.erfa,'dtdb',lambda *a:0.)
    broken=_prepare_reception(b)
    assert broken.tdb!=first.tdb and broken.tcb!=first.tcb
    monkeypatch.setattr(module.erfa,'dtdb',original)


def test_reception_published_erfa_observer_reference_with_synthetic_eop(monkeypatch):
    # Published ERFA t_apco13 numerical reference; constructed EOP inputs,
    # not a captured IERS observation. Source blob d1c82cf66b4d56a0deaeee6f3ff58bc565f5aa5c
    # https://github.com/liberfa/erfa/blob/master/src/t_erfa_c.c (reviewed 2026-10-19).
    # apco13 uses TT as its ephemeris argument; correct its quoted PV linearly
    # for our explicit TDB evaluation. This is a numerical composition oracle.
    import numpy as np
    from astropy import units as u
    from astropy.time import Time
    from math import degrees
    from wenu_kernel.records import TimePoint
    import erfa
    b=_reception_backend()
    class ConstructedEop:
        def ut1_utc(self,*a,**k):return .1550675*u.s,0
        def pm_xy(self,*a,**k):return 2.47230737e-7*u.rad,1.82640464e-6*u.rad,0
        def dcip_xy(self,*a,**k):return 0*u.rad,0*u.rad,0
    b._eop=ConstructedEop()
    tai=erfa.utctai(2456384.5,.969254051)
    tt=Time(*erfa.taitt(*tai),format='jd',scale='tt')
    carry=int(tt.jd2>=.5)
    reception=TimePoint(int(tt.jd1)+carry,float(tt.jd2)-carry,'tt')
    r=b.prepare(reception,longitude_deg=degrees(-.527800806),
                latitude_deg=degrees(-1.2345856),height_m=2738.)
    expected_p=np.array([-.9741827107320875162,-.2115130190489716682,-.09179840189496755339])*149597870700.
    expected_v=np.array([.2078704994520489246e-4,-.8955360133238868938e-4,-.3863338993055887398e-4])*299792458.
    # Earth's velocity owns the epoch correction; the site rotation event is unchanged.
    expected_p+=np.array(r.earth_velocity_tdb_m_s)*r.tdb_minus_tt_s
    assert np.max(np.abs(np.array(r.observer_position_tdb_m)-expected_p))<.2
    assert np.max(np.abs(np.array(r.observer_velocity_tdb_m_s)-expected_v))<2e-5


# Extend the existing reception/observer numerical owner. Protect translation,
# correction ownership and refusal on actual SDK-returned Cartesian batches.
def _finite_batch(context, positions=None):
    from dataclasses import replace
    from wenu.astrometric_state import RectilinearAstrometricProvider,SpaceMotionRow
    from wenu_kernel import Kernel
    from wenu_kernel.records import (ProviderKey,ResourceRef,CatalogueRef,ModelRef,ReferenceSpec,
        ObjectKey,ObjectRecord,ExternalId,CatalogueSnapshot,ModelAdmission,ProviderDescriptor,
        TimeSpan,UncertaintyChannel,UncertaintyEvidence,StateQuery,AccuracyRequest,SessionPolicy)
    positions=positions or tuple((d,0.,0.) for d in (2e12,5e13,1e15,1e27))
    epoch=replace(context.tcb,jd1=context.tcb.jd1-1)
    span=TimeSpan(replace(epoch,jd1=epoch.jd1-1),replace(context.tcb,jd1=context.tcb.jd1+1))
    pk=ProviderKey('constructed-finite-observer','1')
    resource=ResourceRef('constructed-pv','1','1'*64,span,'synthetic nominal inputs',('Constructed test inputs',))
    catalogue=CatalogueRef(pk,(resource,),'2'*64)
    model=ModelRef('constructed-rectilinear','1','3'*64,(resource,))
    reference=ReferenceSpec('icrs','solar-system-barycenter','nominal-astrometric','cartesian','m,m/s',
                            'synthetic no additional light-time correction')
    caps=('cartesian_state','batch_evaluation')
    kinds=('star','open-cluster','planetary-nebula','supernova-remnant')
    keys=tuple(ObjectKey('constructed:'+k) for k in kinds[:len(positions)])
    records=tuple(ObjectRecord(k,(ExternalId('constructed','1',kind),),kind,(epoch,),caps,
                  ('Constructed test inputs',)) for k,kind in zip(keys,kinds))
    snapshot=CatalogueSnapshot(catalogue,records)
    admission=ModelAdmission(catalogue,model,reference,keys,caps,span)
    def unknown(unit):return UncertaintyEvidence(*(UncertaintyChannel('not_evaluated',None,unit,s)
        for s in ('source measurement','nominal model','euclidean_norm')))
    velocity=(1000.,-2000.,300.)
    rows=tuple((key,SpaceMotionRow(str(key),epoch,tuple(x-v*86400 for x,v in zip(p,velocity)),
                                 velocity,None)) for key,p in zip(keys,positions))
    provider=RectilinearAstrometricProvider(rows,descriptor=ProviderDescriptor(pk,(catalogue,),
        (admission,),'synthetic mixed-family provider'),catalogue=snapshot,admission=admission,
        evidence=unknown('m'),velocity_evidence=unknown('m/s'))
    query=StateQuery(catalogue,model,tuple(reversed(keys)),(context.tcb,),reference,
                     AccuracyRequest(metric='euclidean_norm'),require_velocity=True)
    with Kernel(references=(reference,)) as kernel:
        kernel.register(provider,ownership='owned')
        with kernel.open_session(SessionPolicy((catalogue,))) as session:batch=session.evaluate(query)
    return batch,admission


def _realize_finite(batch, source, context, **kwargs):
    from wenu.astrometric_observation import NominalObservationAdmission,realize_astrometric_batch
    return realize_astrometric_batch(batch,context,
        admission=NominalObservationAdmission(source,context.model),**kwargs)


def test_finite_observer_analytic_parallax_range_order_and_unknown_errors():
    from decimal import Decimal,localcontext
    from math import atan2,hypot,ulp
    from dataclasses import FrozenInstanceError
    import pytest
    context=_prepare_reception(_reception_backend())
    batch,a=_finite_batch(context)
    result=_realize_finite(batch,a,context)
    assert result.original is batch and result.reception is context
    assert [s.object_key for s in result.states]==list(batch.query.objects)
    for original,state,converted in zip(batch.states,result.states,result.converted.states):
        with localcontext() as ctx:
            ctx.prec=90
            position=tuple(float(Decimal(x)*(1-Decimal('1.550519768e-8'))) for x in original.position_m)
        delta=tuple(p-o for p,o in zip(position,context.observer_position_tdb_m))
        expected_ra=atan2(delta[1],delta[0]);expected_dec=atan2(delta[2],hypot(*delta[:2]))
        assert abs(atan2(state.geometric_vector[1],state.geometric_vector[0])-expected_ra)<2e-15
        assert abs(atan2(state.geometric_vector[2],hypot(*state.geometric_vector[:2]))-expected_dec)<2e-15
        assert abs(state.range_m-hypot(*delta))<=2*ulp(state.range_m)
        assert converted.original is original
        assert original.source_epoch!=context.tcb  # model was already propagated once
        assert state.angular_error_rad is state.range_error_m is state.emission_time is None
        assert original.position_evidence.physical_model.status=='not_evaluated'
    assert hypot(result.states[0].geometric_vector[1],result.states[0].geometric_vector[2])<2e-16
    # Same native RA/Dec at different ranges gives different observer directions.
    assert result.states[-1].geometric_vector!=result.states[-2].geometric_vector
    assert result.coordinate_spec.frame=='altaz' and result.coordinate_spec.origin=='observer'
    assert result.coordinate_spec.longitude_unit==result.coordinate_spec.latitude_unit=='rad'
    assert result.coordinate_spec.time_scale=='utc' and '60.' in result.coordinate_spec.instant
    assert result.coordinate_spec.position_status.value=='observed'
    with pytest.raises(FrozenInstanceError):result.states[0].range_m=0


def test_finite_observer_aberration_matches_independent_lorentz_boost():
    from math import sqrt,hypot
    context=_prepare_reception(_reception_backend())
    batch,a=_finite_batch(context)
    result=_realize_finite(batch,a,context)
    beta=tuple(v/299792458. for v in context.observer_velocity_tdb_m_s)
    gamma=1/sqrt(1-sum(b*b for b in beta))
    for state in result.states:
        p=state.natural_vector;dot=sum(x*b for x,b in zip(p,beta))
        boosted=tuple((x/gamma+b+gamma/(gamma+1)*dot*b)/(1+dot) for x,b in zip(p,beta))
        expected=tuple(x/hypot(*boosted) for x in boosted)
        # ERFA also includes the documented small solar-potential term.
        assert hypot(*(x-y for x,y in zip(state.proper_bcrs_vector,expected)))<3e-12


def test_finite_observer_matches_separate_astropy_finite_distance_path():
    import numpy as np
    from astropy import units as u
    from astropy.coordinates import SkyCoord,AltAz,EarthLocation,solar_system_ephemeris
    from astropy.time import Time
    from astropy.utils import iers
    from math import cos,sin,hypot
    backend=_reception_backend();context=_prepare_reception(backend)
    positions=((1e17,2e17,3e17),(-2e17,1e17,1e17),(1e16,-1e17,1e17),(-1e17,-2e17,1e17))
    batch,a=_finite_batch(context,positions);result=_realize_finite(batch,a,context)
    location=EarthLocation.from_geodetic(*context.site_wgs84[:2]*u.deg,
        height=context.site_wgs84[2]*u.m)
    utc=Time(*context.utc_jd,format='jd',scale='utc',location=location)
    utc.delta_ut1_utc=context.earth_orientation[0]
    with iers.conf.set_temp('auto_download',False),iers.earth_orientation_table.set(backend._eop),solar_system_ephemeris.set('builtin'):
        for source,actual in zip(result.converted.states,result.states):
            xyz=source.position_m
            coordinate=SkyCoord(x=xyz[0]*u.m,y=xyz[1]*u.m,z=xyz[2]*u.m,
                                representation_type='cartesian',frame='icrs')
            expected=coordinate.transform_to(AltAz(obstime=utc,location=location,pressure=0*u.hPa))
            direction=lambda az,alt:(cos(alt)*sin(az),cos(alt)*cos(az),sin(alt))
            p=direction(actual.azimuth_rad,actual.altitude_rad)
            q=direction(expected.az.rad,expected.alt.rad)
            # Astropy uses theoretical CIP without the final dX/dY offsets.
            assert hypot(*(x-y for x,y in zip(p,q)))<3e-9


def test_finite_observer_correction_counts_no_second_motion_or_hidden_cache(monkeypatch):
    import wenu.astrometric_observation as module
    context=_prepare_reception(_reception_backend());batch,a=_finite_batch(context)
    counts=dict(ld=0,ab=0,atioq=0)
    for name in counts:
        fn=getattr(module.erfa,name)
        def counted(*args,_fn=fn,_name=name,**kwargs):
            counts[_name]+=1
            return _fn(*args,**kwargs)
        monkeypatch.setattr(module.erfa,name,counted)
    def forbidden(*a,**k):raise AssertionError('Second motion or alternate apparent pipeline')
    monkeypatch.setattr(module.erfa,'pmpx',forbidden)
    monkeypatch.setattr(module.erfa,'atciq',forbidden)
    first=_realize_finite(batch,a,context)
    assert counts==dict(ld=4,ab=4,atioq=4)
    assert _realize_finite(batch,a,context)==first
    assert counts==dict(ld=8,ab=8,atioq=8)  # explicit full recomputation, no observer cache
    from dataclasses import replace
    changed=replace(batch,states=tuple(replace(s,position_m=tuple(2*x for x in s.position_m)) for s in batch.states))
    assert _realize_finite(changed,a,context).states[-1].geometric_vector!=first.states[-1].geometric_vector


def test_finite_observer_refuses_tampered_context_state_bounds_and_policies():
    from dataclasses import replace
    import pytest
    from wenu.astrometric_observation import NominalObservationAdmission,realize_astrometric_batch
    from wenu_kernel.errors import KernelError
    context=_prepare_reception(_reception_backend());batch,a=_finite_batch(context)
    accepted=NominalObservationAdmission(a,context.model)
    first=realize_astrometric_batch(batch,context,admission=accepted)
    for bad in (replace(context,observer_position_tdb_m=(0.,0.,0.)),
                replace(context,site_wgs84=(0.,0.,0.)),replace(context,tt=replace(context.tt,jd2=0.)),
                replace(context,backend_identity=('wrong',)*4),replace(context,identity='0'*64),
                replace(context,astrometry=()),replace(context,utc_isot='2000-01-01T00:00:00')):
        with pytest.raises(KernelError):realize_astrometric_batch(batch,bad,admission=accepted)
        assert realize_astrometric_batch(batch,context,admission=accepted)==first
    from wenu_kernel.records import AccuracyRequest
    for bad in (replace(batch,query=replace(batch.query,accuracy=AccuracyRequest(angular_rad=1e-5))),
                replace(batch,states=batch.states[:-1]),replace(batch,states=tuple(reversed(batch.states))),
                replace(batch,query=replace(batch.query,times=(replace(context.tcb,jd2=0.),))),
                replace(batch,states=(replace(batch.states[0],velocity_m_s=None,velocity_evidence=None),*batch.states[1:]))):
        with pytest.raises(KernelError):realize_astrometric_batch(bad,context,admission=accepted)
    with pytest.raises(KernelError):realize_astrometric_batch(batch,context,admission=accepted,maximum_error_rad=1.)
    for policy in (dict(light_time='retarded'),dict(corrections='double-aberration')):
        with pytest.raises(KernelError):NominalObservationAdmission(a,context.model,**policy)
    wrong=replace(a,model=replace(a.model,configuration_digest='f'*64))
    with pytest.raises(KernelError):_realize_finite(batch,wrong,context)


def test_finite_observer_singular_geometry_refuses_complete_batch():
    from fractions import Fraction
    from math import nextafter,inf
    from dataclasses import replace
    import pytest
    from wenu_kernel.errors import KernelError
    context=_prepare_reception(_reception_backend());batch,a=_finite_batch(context)
    f=1-Fraction('1.550519768e-8')
    def inverse(value):
        guess=float(Fraction(value)/f)
        return next(x for x in (guess,nextafter(guess,inf),nextafter(guess,-inf))
                    if float(Fraction(x)*f)==value)
    for position in (context.observer_position_tdb_m,context.sun_position_tdb_m):
        bad=replace(batch,states=(*batch.states[:-1],replace(batch.states[-1],
            position_m=tuple(inverse(x) for x in position))))
        with pytest.raises(KernelError,match='Singular'):_realize_finite(bad,a,context)
    assert len(_realize_finite(batch,a,context).states)==4



def test_finite_observer_double_translation_and_aberration_break_oracles(monkeypatch):
    from dataclasses import replace
    import pytest
    import wenu.astrometric_observation as module
    # Establish each real oracle before injecting the corresponding science fault.
    test_finite_observer_analytic_parallax_range_order_and_unknown_errors()
    test_finite_observer_aberration_matches_independent_lorentz_boost()
    original=module.convert_barycentric_batch
    context=_prepare_reception(_reception_backend())
    def already_topocentric(*a,**k):
        result=original(*a,**k)
        return replace(result,states=tuple(replace(s,position_m=tuple(p-o for p,o in
            zip(s.position_m,context.observer_position_tdb_m))) for s in result.states))
    with monkeypatch.context() as patch:
        patch.setattr(module,'convert_barycentric_batch',already_topocentric)
        with pytest.raises(AssertionError):test_finite_observer_analytic_parallax_range_order_and_unknown_errors()
    ab=module.erfa.ab
    def doubled(p,v,s,bm1):return ab(ab(p,v,s,bm1),v,s,bm1)
    with monkeypatch.context() as patch:
        patch.setattr(module.erfa,'ab',doubled)
        with pytest.raises(AssertionError):test_finite_observer_aberration_matches_independent_lorentz_boost()


def test_observer_geometry_resource_binds_loaded_bytes_and_refuses_change(tmp_path):
    """Synthetic byte resource exercises real descriptor lifetime, not SPK science."""
    import hashlib
    import weakref
    from types import SimpleNamespace
    import pytest
    path = tmp_path / 'synthetic.bsp'
    path.write_bytes(b'synthetic resource; not a valid ephemeris')
    handle = path.open('rb')
    observer = Observer.__new__(Observer)
    observer.ephemeris = SimpleNamespace(path=str(path),
        spk=SimpleNamespace(daf=SimpleNamespace(file=handle)))
    observer._ephemeris_finalizer = weakref.finalize(observer, handle.close)
    try:
        identity = observer.geometry_resource_identity()
        assert identity == hashlib.sha256(path.read_bytes()).hexdigest()
        assert observer.geometry_resource_identity() == identity
        # A same-name in-place edit cannot be concealed by a cached digest.
        path.write_bytes(b'changed synthetic resource')
        with pytest.raises(RuntimeError, match='changed after admission'):
            observer.geometry_resource_identity()
    finally:
        observer.close()
    observer.close()
    with pytest.raises(RuntimeError, match='closed'):
        observer.geometry_resource_identity()


def test_observer_geometry_resource_refuses_mismatched_loaded_handle(tmp_path):
    import weakref
    from types import SimpleNamespace
    import pytest
    first = tmp_path / 'first'; second = tmp_path / 'second'
    first.write_bytes(b'synthetic first'); second.write_bytes(b'synthetic second')
    handle = first.open('rb')
    observer = Observer.__new__(Observer)
    observer.ephemeris = SimpleNamespace(path=str(second),
        spk=SimpleNamespace(daf=SimpleNamespace(file=handle)))
    observer._ephemeris_finalizer = weakref.finalize(observer, handle.close)
    try:
        with pytest.raises(RuntimeError, match='changed before admission'):
            observer.geometry_resource_identity()
    finally:
        observer.close()

# Earth spin timing belongs beside the existing reception-resource owner.
# Closest existing test: test_reception_leap_second_analytic_tt_tai_and_equivalent_tt_input.
# Protect wrong polynomial pieces, year conventions, silent extrapolation,
# TT/UT1 relabelling, global timescale mutation and post-success domain bypass.
def _rotation_tt(year):
    from fractions import Fraction
    from math import floor
    from wenu_kernel.records import TimePoint
    # Independent Meeus calendar-to-JD expression, not the model's inverse.
    integer = floor(year)
    def jan1(y):
        y -= 1
        a = y//100
        return (floor(365.25*(y+4716))+floor(30.6001*14)
                +1+2-a+a//4-1524.5)
    day = Fraction(jan1(integer))+Fraction(year-integer)*int(jan1(integer+1)-jan1(integer))
    whole = floor(day+Fraction(1, 2))
    return TimePoint(whole, float(day-whole), 'tt')


def _rotation_model(**kwargs):
    from wenu.earth_rotation import EarthRotationModel
    from wenu_kernel.records import TimeSpan
    return EarthRotationModel(coverage=TimeSpan(_rotation_tt(-10000), _rotation_tt(5000)), **kwargs)


def test_earth_rotation_published_pieces_and_independent_oracle():
    # Numeric outputs captured by executing DeltaT_EspenakMeeus at a matched
    # formula year from Astronomy Engine commit:
    # 865d3da7d8112bbc7911238052c6af4aaf877181
    # source/python/astronomy/astronomy.py; evaluated locally 2026-10-31.
    # Its own tropical-year date convention is deliberately NOT adopted.
    # No copied library implementation or new dependency is used here.
    samples = (
        (-8000, 308563.68),
        (-2000, 46675.68000000001),
        (-1000, 25427.68),
        (0, 10583.6),
        (1000, 1574.2),
        (1650, 50.194015991022596),
        (1750, 13.370070272572404),
        (1830, 7.673379999999991),
        (1880, -5.00848698849785),
        (1910, 10.388399999999999),
        (1930, 24.1329),
        (1950, 29.07),
        (1975, 45.45),
        (2000, 63.86),
        (2025, 74.467375),
        (2100, 202.73999999999998),
        (2500, 1459.6799999999998),
        (4000, 15187.68),
        (-500.0001, 17203.681484800032),
        (-499.9999, 17203.65453029105),
        (499.9999, 5710.132763330179),
        (500.0001, 5710.043678630042),
        (1599.9999, 120.25115871366307),
        (1600.0001, 119.99990191984683),
        (1699.9999, 8.992111592064504),
        (1700.0001, 8.830016029940712),
        (1799.9999, 13.756167536490707),
        (1800.0001, 13.719966755368624),
        (1859.9999, 7.569782575453701),
        (1860.0001, 7.620057367482462),
        (1899.9999, -2.7017471595449365),
        (1900.0001, -2.7898505886989704),
        (1919.9999, 21.187596970091036),
        (1920.0001, 21.200084492238982),
        (1940.9999, 24.772217744277977),
        (1941.0001, 24.773199399558365),
        (1960.9999, 33.55021676447715),
        (1961.0001, 33.579916441279295),
        (1985.9999, 54.8678072570764),
        (1986.0001, 54.87778210211242),
        (2004.9999, 64.72062017923291),
        (2005.0001, 64.67061280605589),
        (2049.9999, 93.00091189305572),
        (2050.0001, 93.00020348003244),
        (2149.9999, 328.4797325200314),
        (2150.0001, 328.48021120003244),
    )
    from fractions import Fraction
    model = _rotation_model()
    for year, expected in samples:
        event = _rotation_tt(year)
        result = model.evaluate(event)
        assert abs(result.decimal_year_tt-year) < 1e-10
        assert abs(result.delta_t_s-expected) < 2e-8
        offset = ((Fraction(event.jd1)+Fraction(event.jd2))
                  -(Fraction(result.ut1_jd1)+Fraction(result.ut1_jd2)))*86400
        assert abs(float(offset)-result.delta_t_s) < 2e-10
        assert result.model == model.model and result.coverage == model.coverage
        assert result.physical_error_s is result.numerical_error_s is None


def test_earth_rotation_calendar_and_exact_piece_admission():
    from dataclasses import replace
    import pytest
    from wenu_kernel.records import TimePoint
    model = _rotation_model()
    assert _rotation_tt(2000) == TimePoint(2451545, -.5, 'tt')
    assert _rotation_tt(0) == TimePoint(1721060, -.5, 'tt')
    # Leap-year fraction, including astronomical year zero.
    for year, days in ((0, 366), (1900, 365), (2000, 366)):
        start = _rotation_tt(year)
        event = replace(start, jd1=start.jd1+days//2)
        expected = year+(days//2)/days
        assert model.evaluate(event).decimal_year_tt == expected
    # Exact right-hand pieces at year boundaries; never average/smooth a join.
    for year, expected in ((-500, 17203.6563390625), (500, 5710.0446703125),
                           (1600, 120.), (1700, 8.83), (1800, 13.72),
                           (1860, 7.62), (1900, -2.79), (1920, 21.20),
                           (2005, 64.670575), (2050, 93.), (2150, 328.48)):
        assert model.evaluate(_rotation_tt(year)).delta_t_s == pytest.approx(expected, abs=2e-8)
    # A split instant immediately BEFORE the discontinuous 2005 join must
    # stay on its left piece even if the reported decimal year rounds to 2005.
    event = _rotation_tt(2005)
    left = replace(event, jd1=event.jd1-1, jd2=.5-2**-52)
    assert model.evaluate(left).delta_t_s > 64.72
    assert model.evaluate(event).delta_t_s < 64.68


def test_earth_rotation_nominal_extrapolation_identity_and_isolation():
    from dataclasses import FrozenInstanceError
    import pickle
    import pytest
    from wenu.earth_rotation import DEFAULT_ROTATION_MODEL
    from wenu_kernel.errors import InvalidQuery, OutsideCoverage, TimeConversionUnavailable
    from wenu_kernel.records import TimePoint, TimeSpan
    model = _rotation_model()
    explicit = _rotation_model(name='espenak-meeus-2006/1')
    assert model == explicit and model.name == DEFAULT_ROTATION_MODEL
    assert pickle.loads(pickle.dumps(model)) == model
    good = model.evaluate(_rotation_tt(2000))
    with pytest.raises(FrozenInstanceError):
        model.name = 'other'
    with pytest.raises(FrozenInstanceError):
        good.delta_t_s = 0
    for year, regime, outside in ((-8000, 'extended-parabola', True),
                                  (-2000, 'extended-parabola', True),
                                  (-1999, 'secular-parabola', False),
                                  (2000, 'historical-polynomial', False),
                                  (2026, 'prediction-polynomial', False),
                                  (3000, 'secular-parabola', False),
                                  (3001, 'extended-parabola', True)):
        result = model.evaluate(_rotation_tt(year))
        assert result.regime == regime
        assert result.outside_published_interval is outside
        assert result.extrapolated is (regime != 'historical-polynomial')
    for name in ('unknown', 'espenak-meeus-2006', '', None, True):
        with pytest.raises(InvalidQuery):
            _rotation_model(name=name)
    with pytest.raises(InvalidQuery):
        from wenu.earth_rotation import EarthRotationModel
        EarthRotationModel(coverage=None)
    with pytest.raises(TimeConversionUnavailable):
        model.evaluate(TimePoint(2451545, 0, 'tdb'))
    with pytest.raises(InvalidQuery):
        model.evaluate(2451545.)
    narrow = type(model)(coverage=TimeSpan(_rotation_tt(2000), _rotation_tt(2001)))
    for edge in (narrow.coverage.start, narrow.coverage.stop):
        assert narrow.evaluate(edge).tt == edge
    with pytest.raises(OutsideCoverage):
        narrow.evaluate(_rotation_tt(-8000))
    assert model.evaluate(_rotation_tt(2000)) == good
    assert narrow.model == model.model  # Domain is separate from coefficient identity.
    assert narrow.coverage != model.coverage


def test_earth_rotation_skyfield_callable_arrays_and_refusals():
    import numpy as np
    import pytest
    from wenu_kernel.errors import InvalidQuery, OutsideCoverage
    model = _rotation_model()
    dates = np.array([[-1200955., 990545.], [2451545., 2460000.]])
    result = model(dates)
    assert result.shape == dates.shape
    for date, value in zip(dates.flat, result.flat):
        assert value == model(float(date)) == model([float(date)])[0]
    assert model([]).shape == (0,)
    for bad in (True, '2451545', complex(1, 2), float('nan'), float('inf'),
                [2451545., float('nan')]):
        with pytest.raises(InvalidQuery):
            model(bad)
    for date in (-1e9, 1e9):
        with pytest.raises(OutsideCoverage):
            model([2451545., date])
    np.testing.assert_array_equal(model(dates), result)


def test_earth_rotation_real_skyfield_seam_no_global_mutation(monkeypatch):
    from skyfield.api import load
    import numpy as np
    import pytest
    from wenu_kernel.errors import InvalidQuery, OutsideCoverage
    model = _rotation_model()
    # Builtin leap data only; never a network acquisition.
    base = load.timescale(builtin=True)
    original = base.delta_t_function
    dates, offsets = base.leap_dates.copy(), base.leap_offsets.copy()
    ts = model.skyfield_timescale(leap_dates=dates, leap_offsets=offsets)
    dates[:] = 0
    offsets[:] = 0
    assert base.delta_t_function is original
    assert ts.delta_t_function is model
    np.testing.assert_array_equal(ts.leap_dates, base.leap_dates)
    np.testing.assert_array_equal(ts.leap_offsets, base.leap_offsets)
    for jd in (-1200955., 990545., 2451545.):
        time = ts.tt_jd(jd)
        assert time.delta_t == model(jd)
        # Skyfield's real split UT1 representation, without summed-JD subtraction.
        dt = ((time.whole-time.whole)+(time.tt_fraction-time.ut1_fraction))*86400
        assert dt == pytest.approx(model(jd), abs=2e-9)
    with pytest.raises(OutsideCoverage):
        _ = ts.tt_jd(-1e9).delta_t
    assert ts.tt_jd(2451545.).delta_t == model(2451545.)
    for bad in (dict(leap_dates=[2., 1.], leap_offsets=[1., 2.]),
                dict(leap_dates=[1., 2.], leap_offsets=[1.]),
                dict(leap_dates=[1., float('inf')], leap_offsets=[1., 2.])):
        with pytest.raises(InvalidQuery):
            model.skyfield_timescale(**bad)


def test_earth_rotation_future_named_adapter_uses_same_boundary(monkeypatch):
    from types import MappingProxyType
    import wenu.earth_rotation as module
    from wenu_kernel.records import ModelRef
    original = _rotation_model()
    tt = _rotation_tt(2000)
    before = original.evaluate(tt)
    identity = ModelRef('synthetic:test-rotation', '1', 'a'*64, ())
    # Test-only descriptor simulates adding a future implemented adapter.
    # Numerical policy stays in its evaluator, not the common Skyfield seam.
    def synthetic(event):
        return 2000., 100., 'synthetic-nominal', False, False
    monkeypatch.setattr(module, '_MODEL_SPECS', MappingProxyType({
        **module._MODEL_SPECS,
        'synthetic-test/1': (synthetic, identity, ('Synthetic test only',)),
    }))
    monkeypatch.setattr(module, 'ROTATION_MODELS', tuple(module._MODEL_SPECS))
    other = _rotation_model(name='synthetic-test/1')
    assert other.evaluate(tt).model == identity
    assert other.evaluate(tt).delta_t_s == 100.
    assert other(float(tt.jd1)+tt.jd2) == 100.
    assert other.evaluate(tt).provenance == ('Synthetic test only',)
    assert original.evaluate(tt) == before
    assert _rotation_model().evaluate(tt) == before
