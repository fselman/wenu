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
