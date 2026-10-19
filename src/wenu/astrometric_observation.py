"""Offline, explicitly admitted reception inputs for catalogue astrometry.

This service prepares reception inputs and realizes already-evaluated nominal
Cartesian batches. It never propagates objects, solves light time or draws
charts. ERFA EPV00 is an analytic model, not the Observer's JPL SPK.
"""
from dataclasses import asdict, dataclass, replace
from fractions import Fraction
from hashlib import sha256
import json
from math import hypot, isfinite, pi, radians
from pathlib import Path
import re
import warnings

import astropy
import numpy as np
from astropy import units as u
from astropy.time import Time
from astropy.utils import iers
import erfa

from wenu.astrometric_coordinates import BarycentricBatchConversion, TcbTdbAdapter, convert_barycentric_batch, _upper
from wenu.coordinates import CoordinateSpec, PositionStatus
from wenu_kernel.errors import AccuracyUnavailable, InvalidQuery, OutsideCoverage, ResourceMismatch
from wenu_kernel.records import ModelAdmission, ModelRef, ObjectKey, ResourceRef, StateBatch, TimePoint, TimeSpan
from wenu_kernel.time import TimeConversion, TimeConversionAdmission, TimeService


def _digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def reception_backend_identity():
    """Inspect installed code for caller admission; no astronomical data opened."""
    return (astropy.__version__, erfa.__version__, erfa.version.erfa_version,
            sha256(Path(erfa.ufunc.__file__).read_bytes()).hexdigest())


def _leap_rows():
    return tuple((int(r['year']), int(r['month']), float(r['tai_utc']))
                 for r in erfa.leap_seconds.get() if r['year'] >= 1972)


def _split(day, scale):
    whole = (day + Fraction(1, 2)).__floor__()
    small = float(day - whole)
    if small == .5:
        whole, small = whole + 1, -.5
    time = TimePoint(whole, small, scale)
    error = _upper(abs(Fraction(whole) + Fraction(small) - day) * 86400)
    return time, error


def _point(first, second, scale):
    return _split(Fraction(float(first)) + Fraction(float(second)), scale)[0]


def _utc_tt(utc):
    tai = erfa.utctai(utc.jd1, utc.jd2)
    return _point(*erfa.taitt(*tai), 'tt')


@dataclass(frozen=True, slots=True)
class ReceptionContext:
    original: str | TimePoint
    site_wgs84: tuple[float, float, float]
    utc_jd: tuple[float, float]
    tai: TimePoint
    tt: TimePoint
    ut1_jd: tuple[float, float]
    tdb: TimePoint
    tcb: TimePoint
    tdb_tcb_conversion: TimeConversion
    tdb_time_admission: TimeConversionAdmission
    model: ModelRef
    backend_identity: tuple[str, str, str, str]
    earth_orientation: tuple[float, float, float, float, float]
    earth_position_tdb_m: tuple[float, float, float]
    earth_velocity_tdb_m_s: tuple[float, float, float]
    observer_position_tdb_m: tuple[float, float, float]
    observer_velocity_tdb_m_s: tuple[float, float, float]
    tdb_minus_tt_s: float
    tdb_addition_rounding_s: float
    numerical_error_s: None = None
    physical_error_s: None = None
    position_error_m: None = None
    velocity_error_m_s: None = None
    operations: tuple[str, ...] = ('UTC/TAI/TT reception mapping', 'topocentric DTDB',
        'explicit TDB-to-TCB', 'EPV00 Earth PV', 'final IERS-B orientation', 'WGS84 APCO observer PV')
    unapplied: tuple[str, ...] = ('target propagation', 'parallax', 'target light time',
        'target aberration/deflection', 'refraction')
    astrometry: tuple[tuple[str, tuple[float, ...]], ...] = ()
    sun_position_tdb_m: tuple[float, float, float] | None = None
    utc_isot: str | None = None
    identity: str = ''


def _context_identity(context):
    record = asdict(context)
    record.pop('identity')
    return _digest(record)


class ErfaReceptionBackend:
    """Borrow no handles; copy final IERS data from digest-verified local files.

    coverage is a finite TT caller domain, intersected with actual final EOP,
    leap expiry and conservative 1950--2050 model support. Unknown total error
    remains unknown. Supported UTC inputs are ISO UTC strings ending in Z;
    timezone/DST resolution stays with the caller. TT inputs use TimePoint.
    """
    def __init__(self, *, leap_seconds_path, leap_seconds_sha256, eop_path,
                 eop_sha256, coverage, backend_identity):
        if (type(coverage) is not TimeSpan or coverage.start.scale != 'tt'
                or tuple(backend_identity) != reception_backend_identity()):
            raise ResourceMismatch('Explicit finite TT domain and installed backend identity are required.')
        paths = (Path(leap_seconds_path), Path(eop_path))
        expected = (leap_seconds_sha256, eop_sha256)
        if any(sha256(p.read_bytes()).hexdigest() != digest for p, digest in zip(paths, expected)):
            raise ResourceMismatch('Reception resource bytes differ from caller admission.')
        # Explicit local readers do not use IERS_Auto or leap auto_open/update.
        leaps = iers.LeapSeconds.from_iers_leap_seconds(str(paths[0]))
        eop = iers.IERS_B.read(str(paths[1])).copy(copy_data=True)
        if any(sha256(p.read_bytes()).hexdigest() != digest for p, digest in zip(paths, expected)):
            raise ResourceMismatch('Reception resource changed during admission.')
        rows = tuple((int(r['year']), int(r['month']), float(r['tai_utc'])) for r in leaps)
        if rows != _leap_rows():
            raise ResourceMismatch('Installed ERFA leap table is not the admitted IERS table.')
        if (len(eop) < 2 or any(not isfinite(float(x.value)) for name in
                ('MJD', 'UT1_UTC', 'PM_x', 'PM_y', 'dX_2000A', 'dY_2000A') for x in eop[name])
                or any(b <= a for a, b in zip(eop['MJD'][:-1], eop['MJD'][1:]))):
            raise InvalidQuery('Invalid final IERS-B data.')
        self._leaps, self._eop = rows, eop
        self._identity, self.coverage = tuple(backend_identity), coverage
        with warnings.catch_warnings():
            warnings.simplefilter('error', erfa.ErfaWarning)
            leap_start = Time('1972-01-01T00:00:00', format='isot', scale='utc')
            # Astropy stores the expiry at midnight TAI. Use that conservative
            # instant directly, rather than relabelling its JD as UTC.
            if leaps.expires.scale != 'tai':
                raise InvalidQuery('Unsupported leap-table expiry convention.')
            leap_end = _point(*erfa.taitt(leaps.expires.jd1, leaps.expires.jd2), 'tt')
            leap_span = TimeSpan(_utc_tt(leap_start), leap_end)
            # The UTC adapter admits only the post-1972 leap regime. Do not
            # derive even a metadata boundary from unadmitted pre-1972 drift.
            eop_bounds = (max(41317., float(eop['MJD'][0].value)), float(eop['MJD'][-1].value))
            eop_span = TimeSpan(*(_utc_tt(Time(day, format='mjd', scale='utc')) for day in eop_bounds))
        model_span = TimeSpan(_point(2433282.5, 0, 'tt'), _point(2469807.5, 0, 'tt'))
        if any(not span.contains(t) for span in (leap_span, eop_span, model_span)
               for t in (coverage.start, coverage.stop)):
            raise OutsideCoverage('Caller domain exceeds leap, final EOP or 1950--2050 model coverage.')
        provenance = ('Local bytes verified at admission; no downloads or resource substitution',)
        resources = (
            ResourceRef('iers-leap-seconds', '1', expected[0], leap_span, 'UTC/TAI leap table expiry', provenance),
            ResourceRef('iers-final-eop-b', '1', expected[1], eop_span, 'Final IERS-B interpolation only', provenance),
            ResourceRef('erfa-compiled-backend', self._identity[2], self._identity[3], model_span,
                        'EPV00 analytic Earth model and DTDB approximation; not a JPL SPK', provenance))
        self.model = ModelRef('wenu.astrometry:erfa-reception', '2', _digest(dict(
            backend=self._identity, coverage=[(t.jd1, t.jd2, t.scale) for t in (coverage.start, coverage.stop)],
            policy='final-IERS-B;WGS84-height-minus1000-to10000m;EPV00;DTDB-topocentric;CIP-dX-dY;APCO;vacuum;frozen-astrom-context/1;no-target')), resources)

    def prepare(self, reception, *, longitude_deg, latitude_deg, height_m):
        """Prepare one event. Return no target direction; retain unknown errors."""
        if self._identity != reception_backend_identity() or self._leaps != _leap_rows():
            raise ResourceMismatch('Reception backend or global ERFA leap table changed.')
        inputs = (longitude_deg, latitude_deg, height_m)
        if any(isinstance(x, bool) for x in inputs):
            raise InvalidQuery('WGS84 site coordinates cannot be booleans.')
        site = tuple(float(x) for x in inputs)
        if (not all(isfinite(x) for x in site) or not -180 <= site[0] <= 180
                or not -90 <= site[1] <= 90 or not -1000 <= site[2] <= 10000):
            raise InvalidQuery('WGS84 site requires east longitude, geodetic latitude and -1000..10000 m ellipsoid height.')
        with warnings.catch_warnings():
            warnings.simplefilter('error', erfa.ErfaWarning)
            if isinstance(reception, str):
                if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z', reception):
                    raise InvalidQuery('An explicit ISO UTC reception ending in Z is required.')
                utc = Time(reception[:-1], format='isot', scale='utc')
                tai = _point(*erfa.utctai(utc.jd1, utc.jd2), 'tai')
                tt = _point(*erfa.taitt(tai.jd1, tai.jd2), 'tt')
            elif type(reception) is TimePoint and reception.scale == 'tt':
                tt = reception
                tai = _point(*erfa.tttai(tt.jd1, tt.jd2), 'tai')
                utc = Time(*erfa.taiutc(tai.jd1, tai.jd2), format='jd', scale='utc')
            else:
                raise InvalidQuery('Reception must be explicit UTC or a TT TimePoint.')
            if not self.coverage.contains(tt) or any(not r.coverage.contains(tt) for r in self.model.dependencies):
                raise OutsideCoverage('Reception is outside admitted time/EOP/backend coverage.', time=tt)
            dut1, status = self._eop.ut1_utc(utc, return_status=True)
            xp, yp, pm_status = self._eop.pm_xy(utc, return_status=True)
            dx, dy, cip_status = self._eop.dcip_xy(utc, return_status=True)
            if any(int(s) != iers.FROM_IERS_B for s in (status, pm_status, cip_status)):
                raise OutsideCoverage('Final IERS-B data unavailable; extrapolation is refused.', time=tt)
            dut1 = float(dut1.to_value(u.s))
            xp, yp, dx, dy = (float(v.to_value(u.rad)) for v in (xp, yp, dx, dy))
            ut1 = tuple(map(float, erfa.utcut1(utc.jd1, utc.jd2, dut1)))
            lon, lat = map(radians, site[:2])
            xyz = erfa.gd2gc(1, lon, lat, site[2])  # WGS84, metres
            ut_fraction = float((Fraction(ut1[0]) + Fraction(ut1[1]) + Fraction(1, 2)) % 1)
            offset = float(erfa.dtdb(tt.jd1, tt.jd2, ut_fraction, lon,
                                    hypot(xyz[0], xyz[1])/1000, float(xyz[2])/1000))
            tdb, rounding = _split(Fraction(tt.jd1) + Fraction(tt.jd2) + Fraction(offset)/86400, 'tdb')
            # This direct pair is explicitly registered; no hidden state-query conversion.
            adapter = TcbTdbAdapter(TimeSpan(tdb, tdb))
            conversion = TimeService((adapter,), admissions=(adapter.describe(),)).convert(tdb, 'tcb')
            pvh, pvb = erfa.epv00(tdb.jd1, tdb.jd2)
            x, y, _ = erfa.xys06a(tt.jd1, tt.jd2)
            x, y = x + dx, y + dy
            s = erfa.s06(tt.jd1, tt.jd2, x, y)
            astrom = erfa.apco(tdb.jd1, tdb.jd2, pvb, pvh['p'], x, y, s,
                erfa.era00(*ut1), lon, lat, site[2], xp, yp,
                erfa.sp00(tt.jd1, tt.jd2), 0., 0.)
        if self._leaps != _leap_rows():
            raise ResourceMismatch('Global leap table changed during reception preparation.')
        au, c = 149597870700., 299792458.  # IAU 2012 au; SI speed of light
        utc.precision = 9
        context = ReceptionContext(reception, site, (float(utc.jd1), float(utc.jd2)), tai, tt, ut1,
            tdb, conversion.target, conversion, adapter.describe(), self.model, self._identity,
            (dut1, xp, yp, dx, dy), tuple(map(float, pvb['p']*au)),
            tuple(map(float, pvb['v']*(au/86400))), tuple(map(float, astrom['eb']*au)),
            tuple(map(float, astrom['v']*c)), offset, rounding,
            astrometry=tuple((name, tuple(float(x) for x in np.asarray(astrom[name]).flat))
                             for name in astrom.dtype.names),
            sun_position_tdb_m=tuple(map(float, (pvb['p']-pvh['p'])*au)), utc_isot=utc.isot)
        return replace(context, identity=_context_identity(context))


FINITE_OBSERVER_POLICY = 'solar-monopole-aberration-vacuum/1'


@dataclass(frozen=True, slots=True)
class NominalObservationAdmission:
    """Explicit binding of source and reception models, with one correction policy."""
    state: ModelAdmission
    reception_model: ModelRef
    light_time: str = 'no-additional-correction'
    corrections: str = FINITE_OBSERVER_POLICY

    def __post_init__(self):
        if (type(self.state) is not ModelAdmission or type(self.reception_model) is not ModelRef
                or self.reception_model.model_id != 'wenu.astrometry:erfa-reception'
                or self.reception_model.version != '2' or self.light_time != 'no-additional-correction'
                or self.corrections != FINITE_OBSERVER_POLICY):
            raise InvalidQuery('Unsupported nominal observation admission or correction policy.')


@dataclass(frozen=True, slots=True)
class ObservedAstrometricState:
    object_key: ObjectKey
    range_m: float
    geometric_vector: tuple[float, float, float]
    natural_vector: tuple[float, float, float]
    proper_bcrs_vector: tuple[float, float, float]
    apparent_cirs_vector: tuple[float, float, float]
    azimuth_rad: float
    altitude_rad: float
    angular_error_rad: None = None
    range_error_m: None = None
    emission_time: None = None


@dataclass(frozen=True, slots=True)
class ObservedAstrometricBatch:
    original: StateBatch
    converted: BarycentricBatchConversion
    reception: ReceptionContext
    admission: NominalObservationAdmission
    model: ModelRef
    coordinate_spec: CoordinateSpec
    states: tuple[ObservedAstrometricState, ...]
    applied: tuple[str, ...] = ('observer displacement/parallax', 'finite-source solar monopole',
        'annual/diurnal aberration with solar potential', 'IAU2006/2000A plus final CIP offsets',
        'Earth rotation/polar motion', 'vacuum local horizon')
    omitted: tuple[str, ...] = ('additional target light time', 'deflector retardation',
        'planetary deflection', 'multipoles', 'refraction')


def _unit(vector):
    values = tuple(map(float, vector))
    radius = hypot(*values)
    if len(values) != 3 or not isfinite(radius) or radius <= 0:
        raise InvalidQuery('Singular or non-finite observer/deflector geometry.')
    return tuple(x/radius for x in values), radius


def _admitted_astrometry(context, model):
    if (type(context) is not ReceptionContext or context.model != model
            or context.backend_identity != reception_backend_identity() or not context.utc_isot
            or context.sun_position_tdb_m is None or not context.astrometry):
        raise ResourceMismatch('Reception context does not match the admitted backend/model.')
    try:
        if context.identity != _context_identity(context):
            raise ResourceMismatch('Reception context binding changed.')
    except (ValueError, TypeError) as exc:
        raise ResourceMismatch('Invalid reception context binding.') from exc
    if any(not resource.coverage.contains(context.tt) for resource in model.dependencies):
        raise OutsideCoverage('Reception resources do not cover this event.', time=context.tt)
    adapter = TcbTdbAdapter(context.tdb_time_admission.validity)
    if (adapter.describe() != context.tdb_time_admission
            or adapter.convert(context.tdb, 'tcb') != context.tdb_tcb_conversion
            or context.tdb_tcb_conversion.target != context.tcb):
        raise ResourceMismatch('Reception conversion does not bind the evaluation event.')
    astrom = np.zeros((), dtype=erfa.dt_eraASTROM)
    if tuple(name for name, _ in context.astrometry) != astrom.dtype.names:
        raise ResourceMismatch('Unsupported frozen ERFA astrometry layout.')
    for name, values in context.astrometry:
        data = np.asarray(values, dtype=float)
        if not np.isfinite(data).all():
            raise InvalidQuery('Non-finite astrometry context.')
        astrom[name] = data.reshape(astrom[name].shape)
    if (any(float(astrom[name]) != 0 for name in ('diurab', 'refa', 'refb'))
            or tuple(map(float, astrom['eb']*149597870700.)) != context.observer_position_tdb_m
            or tuple(map(float, astrom['v']*299792458.)) != context.observer_velocity_tdb_m_s):
        raise ResourceMismatch('Observer PV, vacuum or aberration ownership mismatch.')
    return astrom


def realize_astrometric_batch(batch, reception, *, admission, maximum_error_rad=None):
    """Realize one complete kernel batch at one admitted reception event.

    No provider callbacks, second space motion, retarded-time solver, fallback
    or observation cache. Every call performs the corrections once per object.
    The synchronous nominal range is not a measured/retarded range certificate.
    """
    if maximum_error_rad is not None:
        raise AccuracyUnavailable('Observed numerical/physical error bounds are not qualified.')
    if type(batch) is not StateBatch or type(admission) is not NominalObservationAdmission:
        raise InvalidQuery('Typed kernel batch and explicit nominal observation admission required.')
    astrom = _admitted_astrometry(reception, admission.reception_model)
    if batch.query.times != (reception.tcb,):
        raise ResourceMismatch('Kernel states must be evaluated at the admitted reception TCB event.')
    accuracy = batch.query.accuracy
    if any(value is not None for value in (accuracy.angular_rad, accuracy.position_m, accuracy.velocity_m_s)):
        raise AccuracyUnavailable('Native state requests do not certify translated observed accuracy.')
    adapter = TcbTdbAdapter(admission.state.coverage)
    receipt = adapter.convert(reception.tcb, 'tdb')
    converted = convert_barycentric_batch(batch, admission=admission.state,
        source_coordinate_scale='tcb', time_admission=adapter.describe(), conversions=(receipt,))
    dependencies = tuple(dict.fromkeys((*admission.state.catalogue.resources,
        *admission.state.model.dependencies, *reception.model.dependencies)))
    model = ModelRef('wenu.astrometry:finite-observer', '1', _digest(dict(
        admission=asdict(admission), solar_body_epoch='reception',
        limiter='1e-6/max(1,solar-range-au-squared)', cache='none')), dependencies)
    states = []
    for state in converted.states:
        geometric, radius = _unit(tuple(p-o for p,o in zip(state.position_m, reception.observer_position_tdb_m)))
        source_from_sun, _ = _unit(tuple(p-s for p,s in zip(state.position_m, reception.sun_position_tdb_m)))
        em = float(astrom['em'])
        natural, _ = _unit(erfa.ld(1., geometric, source_from_sun, astrom['eh'], em,
                                   1e-6/max(1., em*em)))
        proper, _ = _unit(erfa.ab(natural, astrom['v'], em, float(astrom['bm1'])))
        cirs, _ = _unit(astrom['bpn'] @ np.asarray(proper))
        ra, dec = erfa.c2s(cirs)
        az, zenith, _, _, _ = erfa.atioq(ra, dec, astrom)
        if not all(isfinite(float(x)) for x in (az, zenith)):
            raise InvalidQuery('Non-finite observed direction.')
        states.append(ObservedAstrometricState(state.original.object_key, radius,
            geometric, natural, proper, cirs, float(az) % (2*pi), pi/2-float(zenith)))
    spec = CoordinateSpec(frame='altaz', origin='observer', position_status=PositionStatus.OBSERVED,
        instant=reception.utc_isot, time_scale='utc', longitude_unit='rad', latitude_unit='rad',
        provider='ERFA', model=model.model_id+'/'+model.version,
        provenance=(model.configuration_digest, reception.identity),
        corrections=frozenset(('parallax', 'solar-deflection', 'aberration', 'earth-orientation', 'vacuum')))
    return ObservedAstrometricBatch(batch, converted, reception, admission, model, spec, tuple(states))
