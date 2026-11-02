"""Explicit astrometric time, spatial and long-term frame conventions.

This boundary changes conventions, not a trajectory or an observer origin.
It admits no UTC/TT conversion, ephemeris, apparent place or light-time model.
Authorities reviewed 2026-10-19: IAU 2006 B3 and IERS Conventions (2010) §1.2.
Long-term axes reviewed 2026-10-23: corrected VCW 2011/2012 via ERFA/SOFA.
"""
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from math import fsum, hypot, inf, isfinite, nextafter

from wenu.earth_rotation import EarthRotationModel, RotationResult

from wenu_kernel.errors import (
    AccuracyUnavailable, InvalidProviderResult, InvalidQuery, OutsideCoverage,
    ProviderEvaluationError, ResourceMismatch, TimeConversionUnavailable,
)
from wenu_kernel.records import CartesianState, DirectionState, ModelAdmission, ModelRef, StateBatch, TimePoint, TimeSpan
from wenu_kernel.time import TimeConversion, TimeConversionAdmission
from wenu_kernel.time import TimeService


CALENDAR_MODEL = ModelRef(
    'wenu.astrometry:proleptic-calendar', '1',
    sha256(b'proleptic-gregorian-or-julian;astronomical-or-bce-ce;'
           b'midnight=JDN-1/2;86400-coordinate-seconds;no-reform;v1').hexdigest(), ())
CALENDAR_PROVENANCE = (
    'https://aa.usno.navy.mil/downloads/c15_usb_online.pdf',
    'https://www.iausofa.org/cookbooks',
    'Calendar arithmetic on an explicitly declared continuous time scale; no civil-clock reconstruction',
    'Proleptic calendar, no automatic reform; astronomical year 0 = 1 BCE',
    'Input uncertainty stays on the source scale; numerical bounds exclude historical dating and physical realization error',
)


@dataclass(frozen=True, slots=True, kw_only=True)
class HistoricalDate:
    """Explicit calendar labels on a continuous scale, not a local civil date.

    uncertainty_s is a caller-supplied absolute bound in source coordinate
    seconds, or None for unknown. It is mandatory; exact dating is never inferred
    from the number of digits. Gregorian and Julian are both proleptic.
    """
    year: int
    month: int
    day: int
    calendar: str
    year_numbering: str
    scale: str
    uncertainty_s: float | None
    hour: int = 0
    minute: int = 0
    second: float = 0.

    def __post_init__(self):
        if (any(type(v) is not int for v in
                (self.year, self.month, self.day, self.hour, self.minute))
                or any(type(v) is not str for v in
                       (self.calendar, self.year_numbering, self.scale))
                or self.calendar not in ('gregorian', 'julian')
                or self.year_numbering not in ('astronomical', 'bce', 'ce')
                or self.scale not in ('tai', 'tt', 'tdb', 'tcb')):
            raise InvalidQuery('Explicit calendar, year numbering and continuous scale are required.')
        if self.year_numbering != 'astronomical' and self.year < 1:
            raise InvalidQuery('BCE/CE labels require a positive year; only astronomical numbering has year zero.')
        if not 1 <= self.month <= 12 or not 0 <= self.hour < 24 or not 0 <= self.minute < 60:
            raise InvalidQuery('Invalid calendar month/hour/minute.')
        year = self.astronomical_year
        leap = year % 4 == 0 and (self.calendar == 'julian' or year % 100 != 0 or year % 400 == 0)
        days = (31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
        if not 1 <= self.day <= days[self.month-1]:
            raise InvalidQuery('Invalid day in the declared proleptic calendar.')
        for name, value in (('second', self.second), ('uncertainty_s', self.uncertainty_s)):
            if name == 'uncertainty_s' and value is None:
                continue
            if type(value) not in (int, float):
                raise InvalidQuery('Calendar seconds and uncertainty must be finite numbers.')
            try:
                value = float(value)
            except OverflowError as exc:
                raise InvalidQuery('Calendar seconds/uncertainty overflow.') from exc
            if not isfinite(value) or value < 0 or (name == 'second' and value >= 60):
                raise InvalidQuery('Invalid seconds/uncertainty; leap seconds are not continuous-scale input.')
            if name == 'second':
                object.__setattr__(self, name, value)

    @property
    def astronomical_year(self):
        return 1-self.year if self.year_numbering == 'bce' else self.year


@dataclass(frozen=True, slots=True)
class HistoricalEpoch:
    """Nominal TCB event plus retained calendar/source-uncertainty evidence.

    Calendar rounding is in source-scale seconds; conversion rounding belongs
    to the TimeService receipt. Neither is a total dating/physical error, nor
    does converting the nominal epoch convert a source uncertainty interval.
    Keep this receipt alongside queries made with .time.
    """
    source: HistoricalDate
    calendar_time: TimePoint
    calendar_rounding_error_s: float
    conversion: TimeConversion
    calendar_model: ModelRef = CALENDAR_MODEL
    provenance: tuple[str, ...] = CALENDAR_PROVENANCE

    @property
    def time(self):
        return self.conversion.target


def resolve_historical_date(date, *, time_service, maximum_conversion_error_s=None):
    """Resolve explicit calendar labels and use an admitted direct TCB mapping.

    No implicit adapters, conversion chains, time-zone/EOP/Delta-T resources or
    calendar reform. TT/TAI input without an admitted TCB adapter refuses.
    Julian/Gregorian arithmetic is independent of the declared continuous scale.
    """
    if type(date) is not HistoricalDate or type(time_service) is not TimeService:
        raise InvalidQuery('Typed historical date and explicit TimeService are required.')
    a = (14-date.month)//12
    y, m = date.astronomical_year+4800-a, date.month+12*a-3
    jdn = date.day + (153*m+2)//5 + 365*y + y//4
    jdn += -(y//100) + y//400 - 32045 if date.calendar == 'gregorian' else -32083
    exact_day = (Fraction(jdn)-Fraction(1, 2)
                 + (date.hour*3600 + date.minute*60 + Fraction(date.second))/86400)
    whole = (exact_day+Fraction(1, 2)).__floor__()
    small = float(exact_day-whole)
    if small == .5:
        whole, small = whole+1, -.5
    try:
        if not -(2**53) <= whole <= 2**53:
            raise InvalidQuery('Calendar day exceeds exact binary64 integer range.')
        source = TimePoint(whole, small, date.scale)
    except (ValueError, OverflowError) as exc:
        raise InvalidQuery('Calendar date cannot be represented by TimePoint.') from exc
    error = _upper(abs(Fraction(source.jd1)+Fraction(source.jd2)-exact_day)*86400)
    receipt = time_service.convert(source, 'tcb', maximum_error_s=maximum_conversion_error_s)
    return HistoricalEpoch(date, source, error, receipt)


# Exact defining decimal constants, not estimates or binary64 approximations.
_LB = Fraction('1.550519768e-8')
_F = 1 - _LB
_T0 = Fraction('2443144.5003725')
_TDB0_DAY = Fraction('-0.0000655') / 86400
_POLICY = b'IAU2006B3;LB=1.550519768e-8;T0=2443144.5003725;TDB0_s=-0.0000655;IERS2010-1.2;xTDB=(1-LB)xTCB;vTDB=vTCB;v1'
BARYCENTRIC_CONVENTION_MODEL = ModelRef(
    'wenu.astrometry:tcb-tdb-convention', '1', sha256(_POLICY).hexdigest(), ())
_PROVENANCE = (
    'https://iau-a3.gitlab.io/res.html',
    'https://iers-conventions.obspm.fr/content/tn36.pdf#page=17',
    'Exact IAU 2006 B3 linear definition; IERS 2010 section 1.2 spatial scaling',
    'Numerical rounding only; excludes reception-time uncertainty and source/observer model error',
)


def _upper(value):
    rounded = float(value)
    if not isfinite(rounded):
        raise InvalidQuery('Coordinate conversion overflows binary64.')
    return nextafter(rounded, inf) if Fraction(rounded) < value else rounded


def _convert_time(time, target_scale):
    day = Fraction(time.jd1) + Fraction(time.jd2)
    result = (day - _LB * (day - _T0) + _TDB0_DAY if time.scale == 'tcb'
              else (day - _LB * _T0 - _TDB0_DAY) / _F)
    whole = (result + Fraction(1, 2)).__floor__()
    small = float(result - whole)
    if small == .5:
        whole += 1
        small = -.5
    target = TimePoint(whole, small, target_scale)
    error = abs(Fraction(target.jd1) + Fraction(target.jd2) - result) * 86400
    return target, _upper(error)


@dataclass(frozen=True, slots=True, init=False)
class TcbTdbAdapter:
    """One directed, resource-free conversion over explicitly admitted coverage.

    The finite domain is a caller policy, not historical clock/ephemeris validity.
    Register describe() explicitly with the unchanged SDK TimeService.
    """
    _admission: TimeConversionAdmission

    def __init__(self, validity):
        if type(validity) is not TimeSpan or validity.start.scale not in ('tcb', 'tdb'):
            raise InvalidQuery('Explicit finite TCB or TDB source coverage is required.')
        source = validity.start.scale
        object.__setattr__(self, '_admission', TimeConversionAdmission(
            source, 'tdb' if source == 'tcb' else 'tcb', validity,
            BARYCENTRIC_CONVENTION_MODEL, 2**-36, _PROVENANCE))

    def describe(self):
        return self._admission

    def convert(self, time, target_scale):
        a = self._admission
        if type(time) is not TimePoint or (time.scale, target_scale) != (a.source_scale, a.target_scale):
            raise TimeConversionUnavailable('TCB/TDB adapter pair mismatch.')
        if not a.validity.contains(time):
            raise OutsideCoverage('Outside admitted TCB/TDB conversion domain.', time=time)
        target, error = _convert_time(time, target_scale)
        return TimeConversion(time, target, a.model, error, a.provenance)


@dataclass(frozen=True, slots=True)
class BarycentricStateConversion:
    """Derived convention view; original SDK state/evidence remain authoritative.

    Component rounding bounds apply only to this scaling operation. They do not
    bound position uncertainty, propagation error or time-induced displacement.
    Velocity is unchanged: dxTDB/dtTDB = dxTCB/dtTCB.
    """
    original: CartesianState
    conversion: TimeConversion
    position_m: tuple[float, float, float]
    position_rounding_m: tuple[float, float, float]

    @property
    def time(self):
        return self.conversion.target

    @property
    def coordinate_scale(self):
        return self.time.scale

    @property
    def velocity_m_s(self):
        return self.original.velocity_m_s


@dataclass(frozen=True, slots=True)
class BarycentricBatchConversion:
    original: StateBatch
    admission: ModelAdmission
    time_admission: TimeConversionAdmission
    states: tuple[BarycentricStateConversion, ...]
    model: ModelRef = BARYCENTRIC_CONVENTION_MODEL


def convert_barycentric_batch(batch, *, admission, source_coordinate_scale, time_admission, conversions):
    """Scale a complete actual SDK batch with explicit matching time receipts.

    source_coordinate_scale explicitly admits the spatial convention; a time
    label alone is insufficient. Expected catalogue/model/resource/reference
    bindings are checked against the query before any output is published.
    This view is not a new SDK model/state, observer result or error certificate.
    """
    if type(batch) is not StateBatch or type(admission) is not ModelAdmission:
        raise InvalidQuery('Typed kernel batch and explicit model admission are required.')
    q, ref = batch.query, admission.reference
    if (q.catalogue != admission.catalogue or q.model != admission.model or q.reference != ref
            or not set(q.objects).issubset(admission.objects)):
        raise ResourceMismatch('Cartesian batch does not match expected source/model/reference.')
    if (ref.frame_id != 'icrs' or ref.origin_id != 'solar-system-barycenter'
            or ref.status != 'nominal-astrometric' or ref.representation != 'cartesian'
            or ref.units != 'm,m/s' or 'cartesian_state' not in admission.capabilities
            or type(admission.coverage) is not TimeSpan
            or source_coordinate_scale not in ('tcb', 'tdb')
            or admission.coverage.start.scale != source_coordinate_scale
            or q.evaluation_policy != 'full_model' or q.coverage is not None
            or batch.reuse_certificates or batch.reuse_plan):
        raise InvalidQuery('Unsupported barycentric convention or reused-state admission.')
    for time in q.times:
        if (not admission.coverage.contains(time) or any(not resource.coverage.contains(time)
                for resource in (*admission.catalogue.resources, *admission.model.dependencies))):
            raise OutsideCoverage('Outside Cartesian source/model resource coverage.', time=time)
    if type(time_admission) is not TimeConversionAdmission:
        raise InvalidQuery('Explicit time-conversion admission is required.')
    adapter = TcbTdbAdapter(time_admission.validity)
    if (adapter.describe() != time_admission
            or time_admission.source_scale != source_coordinate_scale):
        raise ResourceMismatch('Unsupported time-conversion admission.')
    if type(conversions) not in (tuple, list):
        raise InvalidQuery('Time conversions must be an explicit tuple/list.')
    receipts = tuple(conversions)
    if len(receipts) != len(q.times):
        raise InvalidQuery('One explicit time conversion per query time is required.')
    for time, receipt in zip(q.times, receipts):
        if (type(receipt) is not TimeConversion or receipt.source != time
                or receipt != adapter.convert(time, adapter.describe().target_scale)):
            raise ResourceMismatch('Time conversion receipt does not match this event/model.')
    expected = [(time, key, receipt) for time, receipt in zip(q.times, receipts) for key in q.objects]
    if len(batch.states) != len(expected):
        raise InvalidQuery('Incomplete Cartesian batch.')
    result = []
    factor = _F if source_coordinate_scale == 'tcb' else 1 / _F
    for state, (time, key, receipt) in zip(batch.states, expected):
        if (type(state) is not CartesianState or state.object_key != key or state.time != time
                or state.anchor_time != time or state.reference != ref or state.source_epoch is None
                or not admission.coverage.contains(state.source_epoch) or not state.velocity_available):
            raise InvalidQuery('Cartesian state identity, epoch, reference or full velocity mismatch.')
        exact_position = tuple(Fraction(x) * factor for x in state.position_m)
        try:
            position = tuple(float(x) for x in exact_position)
        except OverflowError as exc:
            raise InvalidQuery('Coordinate conversion overflows binary64.') from exc
        if not all(isfinite(x) for x in position):
            raise InvalidQuery('Coordinate conversion overflows binary64.')
        errors = tuple(_upper(abs(Fraction(x) - y)) for x, y in zip(position, exact_position))
        result.append(BarycentricStateConversion(state, receipt, position, errors))
    return BarycentricBatchConversion(batch, admission, time_admission, tuple(result))


LONG_TERM_FRAME_POLICY = 'vcw2011-2012-erfa'
LONG_TERM_FRAME_PROVENANCE = (
    'https://doi.org/10.1051/0004-6361/201117274',
    'https://doi.org/10.1051/0004-6361/201117274e',
    'https://www.iausofa.org/s/sofa_pn_c.pdf#page=35',
    'ERFA derived from SOFA; corrected 2011/2012 long-term model, including first-order ICRS frame bias',
    'TT frame equinox is independent of native state evaluation time; no implicit TCB/TT conversion',
    'No nutation, Earth rotation, polar motion, observer translation, aberration or light time',
    'Published qualitative accuracy is not a certified per-epoch physical/total error bound',
)


def _tt_jyear(time):
    return Fraction(2000) + (Fraction(time.jd1-2451545)+Fraction(time.jd2))/Fraction(1461, 4)


def _frame_vector(vector):
    if type(vector) not in (tuple, list) or len(vector) != 3:
        raise InvalidQuery('Expected a three-component unit direction.')
    if any(type(x) not in (int, float) or isinstance(x, bool) for x in vector):
        raise InvalidQuery('Direction components must be finite real numbers.')
    try:
        v = tuple(float(x) for x in vector)
    except OverflowError as exc:
        raise InvalidQuery('Direction component overflow.') from exc
    if not all(isfinite(x) for x in v) or abs(hypot(*v)-1) > 2**-40:
        raise InvalidQuery('Expected a finite unit direction, not a Cartesian position.')
    return v


@dataclass(frozen=True, slots=True, init=False)
class LongTermFrame:
    """Explicit, immutable mean axes at a TT equinox, with finite admission.

    Existing ERFA supplies the corrected Vondrak/Capitaine/Wallace model.
    This is an axis orientation only. Its epoch is not the source epoch or
    native TCB state time. There is no observer model or total accuracy claim.
    Importing this module/native propagation does not import ERFA or NumPy.
    """
    equinox: TimePoint
    validity: TimeSpan
    axes: str
    backend_jyear_tt: float
    epoch_rounding_s: float
    backend_versions: tuple[str, str, str]
    matrix: tuple[tuple[float, float, float], ...]
    model: ModelRef
    provenance: tuple[str, ...]
    physical_error_rad: None = None
    numerical_error_rad: None = None

    def __init__(self, *, equinox, validity, axes, model_policy,
                 maximum_physical_error_rad=None):
        if type(equinox) is not TimePoint:
            raise InvalidQuery('Frame equinox must be an explicit TT TimePoint.')
        if equinox.scale != 'tt':
            raise TimeConversionUnavailable('Long-term frame equinox requires TT; no scale relabelling.')
        if type(validity) is not TimeSpan or validity.start.scale != 'tt':
            raise InvalidQuery('Explicit finite TT frame validity is required.')
        if (type(axes) is not str or axes not in ('mean-equator-equinox', 'mean-ecliptic-equinox')
                or type(model_policy) is not str or model_policy != LONG_TERM_FRAME_POLICY):
            raise InvalidQuery('Explicit supported long-term axes and model policy are required.')
        lower, upper = Fraction(-198000), Fraction(202000)
        if (_tt_jyear(validity.start) < lower or _tt_jyear(validity.stop) > upper
                or not validity.contains(equinox)):
            raise OutsideCoverage('Outside caller/model long-term TT frame domain.', time=equinox)
        if maximum_physical_error_rad is not None:
            try:
                valid_error = (type(maximum_physical_error_rad) in (int, float)
                               and isfinite(maximum_physical_error_rad)
                               and maximum_physical_error_rad >= 0)
            except OverflowError:
                valid_error = False
            if not valid_error:
                raise InvalidQuery('Requested physical error must be finite and nonnegative.')
            raise AccuracyUnavailable('No certified physical frame-error bound is admitted.', time=equinox)
        exact_year = _tt_jyear(equinox)
        epoch = float(exact_year)
        error_s = _upper(abs(Fraction(epoch)-exact_year)*31557600)
        try:
            import erfa
            from pathlib import Path
            hashes = tuple((name, sha256(Path(path).read_bytes()).hexdigest())
                for name, path in (('convention-owner', __file__),
                                   ('erfa-ufunc', erfa.ufunc.__file__),
                                   ('erfa-wrapper', erfa.core.__file__)))
            versions = (str(erfa.__version__), str(erfa.version.erfa_version),
                        str(erfa.version.sofa_version))
            backend = erfa.ltpb if axes == 'mean-equator-equinox' else erfa.ltecm
            raw = backend(epoch)
        except Exception as exc:
            raise ProviderEvaluationError('Long-term frame backend failed.', time=equinox) from exc
        try:
            matrix = tuple(tuple(float(v) for v in row) for row in raw)
            if len(matrix) != 3 or any(len(row) != 3 for row in matrix):
                raise ValueError('shape')
            if not all(isfinite(x) for row in matrix for x in row):
                raise ValueError('nonfinite')
            # First-order frame bias is not an exact 3D rotation. Admit only
            # the documented near-orthogonal right-handed matrix, not a scale,
            # reflection or arbitrary backend payload.
            for i in range(3):
                for j in range(3):
                    if abs(fsum(a*b for a,b in zip(matrix[i],matrix[j]))-(i == j)) > 2**-40:
                        raise ValueError('not near orthogonal')
            a,b,c = matrix
            determinant = (a[0]*(b[1]*c[2]-b[2]*c[1])
                           -a[1]*(b[0]*c[2]-b[2]*c[0])+a[2]*(b[0]*c[1]-b[1]*c[0]))
            if abs(determinant-1) > 2**-39:
                raise ValueError('handedness')
        except Exception as exc:
            raise InvalidProviderResult('Invalid long-term frame matrix.', time=equinox) from exc
        # Identity includes domain, exact TT event, backend versions, actual
        # matrix bytes (hex floats), and the epoch given to the backend.
        import json
        binding = dict(policy=model_policy, axes=axes,
            equinox=(equinox.jd1, equinox.jd2.hex(), equinox.scale),
            validity=((validity.start.jd1, validity.start.jd2.hex()),
                      (validity.stop.jd1, validity.stop.jd2.hex())),
            backend_versions=versions, backend_jyear_tt=epoch.hex(),
            matrix=[[x.hex() for x in row] for row in matrix])
        model = ModelRef('wenu.astrometry:long-term-frame', '1',
            sha256(json.dumps(binding, sort_keys=True, separators=(',', ':')).encode()).hexdigest(), ())
        values = dict(equinox=equinox, validity=validity, axes=axes,
            backend_jyear_tt=epoch, epoch_rounding_s=error_s, backend_versions=versions,
            matrix=matrix, model=model, provenance=LONG_TERM_FRAME_PROVENANCE,
            physical_error_rad=None, numerical_error_rad=None)
        for name,value in values.items():
            object.__setattr__(self, name, value)

    @property
    def pole_icrs(self):
        """Model's pole covector expressed on ICRS axes, normalized."""
        row = self.matrix[2]
        norm = hypot(*row)
        return tuple(v/norm for v in row)

    def rotate(self, vector):
        """Express an ICRS unit direction on these mean axes, not propagate it.

        Normalize after the first-order bias matrix application. No distance,
        PV or uncertainty certificate is created by this derived view.
        """
        v = _frame_vector(vector)
        raw = tuple(fsum(a*b for a,b in zip(row,v)) for row in self.matrix)
        norm = hypot(*raw)
        if not isfinite(norm) or norm == 0:
            raise InvalidProviderResult('Invalid transformed direction.')
        return tuple(x/norm for x in raw)


@dataclass(frozen=True, slots=True)
class OrientedDirection:
    """Derived direction; original native state/evidence remain authoritative."""
    original: DirectionState
    vector: tuple[float, float, float]


@dataclass(frozen=True, slots=True)
class OrientedDirectionBatch:
    original: StateBatch
    admission: ModelAdmission
    orientation: LongTermFrame
    states: tuple[OrientedDirection, ...]


def orient_direction_batch(batch, *, admission, orientation):
    """Explicit full native ICRS batch view; never mutate/adopt native states.

    The TT equinox is chosen independently and may differ from every state's
    TCB time. No equality of physical events is inferred. This is not a new SDK
    batch or reuse certificate, and cannot be fed back as a native query result.
    """
    if (type(batch) is not StateBatch or type(admission) is not ModelAdmission
            or type(orientation) is not LongTermFrame):
        raise InvalidQuery('Typed SDK batch/admission and explicit long-term frame required.')
    q,ref = batch.query,admission.reference
    if (q.catalogue != admission.catalogue or q.model != admission.model or q.reference != ref
            or not set(q.objects).issubset(admission.objects)):
        raise ResourceMismatch('Native direction batch does not match expected admission.')
    if (ref.frame_id != 'icrs' or ref.origin_id != 'solar-system-barycenter'
            or ref.status != 'nominal-astrometric' or ref.representation != 'direction'
            or ref.units != 'rad' or 'epoch_direction' not in admission.capabilities
            or q.evaluation_policy != 'full_model' or q.coverage is not None
            or q.require_velocity or batch.reuse_certificates or batch.reuse_plan):
        raise InvalidQuery('Only full native ICRS epoch-direction batches are admitted.')
    expected = [(t,k) for t in q.times for k in q.objects]
    if len(expected) != len(batch.states):
        raise InvalidQuery('Incomplete native direction batch.')
    result = []
    for state,(time,key) in zip(batch.states,expected):
        if (type(state) is not DirectionState or state.object_key != key or state.time != time
                or state.anchor_time != time or state.reference != ref
                or state.source_epoch is None or state.certificate_id is not None):
            raise InvalidQuery('Native state identity/time/reference mismatch.')
        if (not admission.coverage.contains(time) or any(not r.coverage.contains(time)
                for r in (*admission.catalogue.resources,*admission.model.dependencies))):
            raise OutsideCoverage('Outside native source/model coverage.', time=time)
        result.append(OrientedDirection(state, orientation.rotate(state.vector)))
    return OrientedDirectionBatch(batch, admission, orientation, tuple(result))


# Complete nominal orientation: explicit opt-in, not an observer realization.
NOMINAL_ORIENTATION_POLICY = 'vcw2000a-nonrotating-origin/1'
_NOMINAL_ORIENTATION_PROVENANCE = (
    'https://iers-conventions.obspm.fr/content/tn36.pdf; section 5.4, Eq. 5.8',
    'VCW2011/2012 mean axes + unadjusted classical IAU2000A forced nutation',
    'J2000 c2i06a first row projected onto the nominal equator; full-pole transport',
    'xp=yp=0 omitted polar motion; s-prime=0 fixed terrestrial-origin convention',
    'Unknown physical/total numerical error; refinement estimate is not a bound',
)


@dataclass(frozen=True, slots=True, kw_only=True)
class OriginTransportSettings:
    """Finite geometric-path refinement; tolerance is an estimate, not a bound.

    Success requires at least four nested paths. Shortest-arc transport along
    each polygon converges quadratically to smooth-pole parallel transport.
    Richardson extrapolation removes successive even-power discretization terms.
    No persistent cache or path skipping; a work-budget failure refuses output.
    """
    max_step_days: float = 8.
    tolerance_rad: float = 1e-8
    max_refinements: int = 6
    max_samples: int = 50000000

    def __post_init__(self):
        for name in ('max_step_days', 'tolerance_rad'):
            value = getattr(self, name)
            try:
                valid = type(value) in (int, float) and isfinite(value) and value > 0
            except OverflowError:
                valid = False
            if not valid:
                raise InvalidQuery('Positive finite transport step/tolerance required.')
            object.__setattr__(self, name, float(value))
        if self.max_step_days > 8 or not 1e-13 <= self.tolerance_rad <= 1e-5:
            raise InvalidQuery('Unsupported transport step/tolerance.')
        if (type(self.max_refinements) is not int or not 4 <= self.max_refinements <= 10
                or type(self.max_samples) is not int or not 32 <= self.max_samples <= 200000000):
            raise InvalidQuery('Explicit finite transport refinement/work budget required.')


@dataclass(frozen=True, slots=True)
class OriginTransportReceipt:
    settings: OriginTransportSettings
    history: TimeSpan
    locator_rad: float
    polygon_locators_rad: tuple[float, ...]
    extrapolated_locators_rad: tuple[float, ...]
    convergence_estimate_rad: float
    panels: tuple[int, ...]
    sample_count: int
    elapsed_s: float
    algorithm: str = 'north-gauge-geodesic-polygon-richardson/1'
    numerical_error_rad: None = None


def _orientation_unit(values):
    import numpy as np
    a = np.asarray(values, dtype=float)
    norm = np.linalg.norm(a, axis=-1, keepdims=True)
    if (a.shape[-1:] != (3,) or not np.all(np.isfinite(a))
            or not np.all(np.isfinite(norm)) or np.any(norm < 1e-15)):
        raise InvalidProviderResult('Invalid nominal pole/origin vector.')
    return a / norm


def _orientation_matrix(values):
    import numpy as np
    a = np.asarray(values, dtype=float)
    if (a.shape[-2:] != (3, 3) or not np.all(np.isfinite(a))
            or np.max(np.abs(a @ np.swapaxes(a, -1, -2) - np.eye(3))) > 2**-39
            or np.max(np.abs(np.linalg.det(a) - 1)) > 2**-38):
        raise InvalidProviderResult('Invalid nominal orientation matrix.')
    return a


def _nominal_pole(tt1, tt2):
    """Vectorized convention evaluation; exact split TT at public endpoints.

    Uses the same corrected ERFA ltpb/ltecm owners as LongTermFrame. The
    original first-order biased matrices are never orthogonalized or changed.
    """
    import erfa
    import numpy as np
    year = 2000. + ((np.asarray(tt1) - 2451545.) + np.asarray(tt2)) / 365.25
    p = _orientation_matrix(erfa.ltpb(year))
    e = _orientation_matrix(erfa.ltecm(year))
    mp, ep = _orientation_unit(p[..., 2, :]), _orientation_unit(e[..., 2, :])
    eps = np.arctan2(np.linalg.norm(np.cross(mp, ep), axis=-1),
                     np.sum(mp * ep, axis=-1))
    psi, deps = erfa.nut00a(tt1, tt2)
    n = _orientation_matrix(erfa.numat(eps, psi, deps))
    b = _orientation_matrix(n @ p)
    return _orientation_unit(b[..., 2, :]), b


def _pole_gauge(pole):
    """Exact north-pole gauge triad, including southern Z when nonsingular."""
    import numpy as np
    x, y, z = pole
    if not isfinite(z) or 1 + z < 1e-8:
        raise InvalidProviderResult('Singular celestial-origin locator coordinates.')
    return np.array(((1-x*x/(1+z), -x*y/(1+z), -x),
                     (-x*y/(1+z), 1-y*y/(1+z), -y), pole))


def _orientation_r3(angle):
    from math import cos, sin
    import numpy as np
    c, s = cos(angle), sin(angle)
    return np.array(((c, s, 0.), (-s, c, 0.), (0., 0., 1.)))


def _polygon_origin(poles, *, previous=None):
    """Exact scalar connection integral along shortest great-circle edges.

    Each edge contributes minus the signed solid angle of the triangle
    (north pole, old pole, new pole). No sampled-pole derivatives or small-angle
    approximation. This is the discrete counterpart of IERS Eq. 5.8.
    """
    import numpy as np
    p = np.asarray(poles, dtype=float)
    if p.ndim != 2 or p.shape[1:] != (3,) or not np.all(np.isfinite(p)):
        raise InvalidProviderResult('Invalid sampled pole history.')
    if np.any(np.abs(np.linalg.norm(p, axis=1) - 1) > 2**-40):
        raise InvalidProviderResult('Nonunit sampled pole history.')
    if np.any(1 + p[:, 2] < 1e-8):
        raise InvalidProviderResult('Singular sampled origin locator.')
    if previous is not None:
        p = np.vstack((previous, p))
    a, b = p[:-1], p[1:]
    if np.any(np.sum(a*b, axis=1) < 0):
        raise InvalidProviderResult('Ambiguous or excessively long transport edge.')
    numerator = a[:, 0]*b[:, 1] - a[:, 1]*b[:, 0]
    denominator = ((1+a[:, 2])*(1+b[:, 2])
                   + a[:, 0]*b[:, 0] + a[:, 1]*b[:, 1])
    return fsum(float(v) for v in -2*np.arctan2(numerator, denominator))


def _transport_origin(pole_function, *, duration_days, seed_locator, history, settings):
    """Stream the entire path, then compare nested Richardson diagonals."""
    from math import ceil
    from time import perf_counter
    import numpy as np
    started = perf_counter()
    if duration_days == 0:
        return OriginTransportReceipt(settings, history, seed_locator, (), (),
                                      0., (), 0, perf_counter()-started)
    panels = max(4, ceil(abs(duration_days)/settings.max_step_days))
    raw, diagonal, counts, table = [], [], [], []
    samples = 0
    for level in range(settings.max_refinements):
        count = panels * 2**level
        if samples + count + 1 > settings.max_samples:
            raise AccuracyUnavailable(f'Origin transport work budget exhausted: {samples} samples; next path {count+1}; diagonals {diagonal!r}.')
        pieces, previous = [], None
        for start in range(0, count+1, 16384):
            stop = min(start+16384, count+1)
            offsets = (np.arange(start, stop, dtype=float)/count)*duration_days
            poles = pole_function(offsets)
            pieces.append(_polygon_origin(poles, previous=previous))
            previous = poles[-1]
        samples += count + 1
        value = seed_locator + fsum(pieces)
        row = [value]
        for order in range(1, level+1):
            row.append(row[-1] + (row[-1]-table[-1][order-1])/(4**order-1))
        if not all(isfinite(x) for x in row):
            raise InvalidProviderResult('Nonfinite origin transport refinement.')
        table.append(row)
        raw.append(value)
        diagonal.append(row[-1])
        counts.append(count)
        # Also require the last two estimates to agree; a single accidentally
        # small diagonal difference does not end the refinement.
        if level >= 3:
            estimate = max(abs(diagonal[-1]-diagonal[-2]),
                           abs(diagonal[-2]-diagonal[-3]))
            if estimate <= settings.tolerance_rad:
                return OriginTransportReceipt(settings, history, row[-1],
                    tuple(raw), tuple(diagonal), estimate, tuple(counts), samples,
                    perf_counter()-started)
    raise AccuracyUnavailable(f'Origin transport did not converge: {samples} samples; diagonals {diagonal!r}.')


@dataclass(frozen=True, slots=True)
class NominalOrientationResult:
    """Prepared exact-event orientation, no site/translation/corrections.

    Matrices act on column vectors. The transpose is the inverse of this new
    orthonormal matrix, not of the original first-order-biased LongTermFrame.
    """
    tt: TimePoint
    coverage: TimeSpan
    path_coverage: TimeSpan
    rotation: RotationResult
    mean_equator: LongTermFrame
    mean_ecliptic: LongTermFrame
    backend_versions: tuple[str, ...]
    backend_hashes: tuple[tuple[str, str], ...]
    seed_pole: tuple[float, float, float]
    seed_origin: tuple[float, float, float]
    pole_icrs: tuple[float, float, float]
    origin_icrs: tuple[float, float, float]
    transport: OriginTransportReceipt
    era_rad: float
    celestial_to_intermediate: tuple[tuple[float, float, float], ...]
    celestial_to_terrestrial: tuple[tuple[float, float, float], ...]
    terrestrial_to_celestial: tuple[tuple[float, float, float], ...]
    model: ModelRef
    elapsed_s: float
    polar_motion_policy: str = 'omitted-xp-yp-zero/1'
    terrestrial_origin_policy: str = 'fixed-s-prime-zero/1'
    nutation_policy: str = 'nominal-classical-iau2000a-extrapolated/1'
    physical_error_rad: None = None
    numerical_error_rad: None = None
    provenance: tuple[str, ...] = _NOMINAL_ORIENTATION_PROVENANCE


@dataclass(frozen=True, slots=True, kw_only=True)
class NominalEarthOrientation:
    """Explicit immutable orientation policy over a finite requested domain.

    path_coverage must include J2000 and the complete caller coverage. Each
    evaluate call integrates independently; no process-global or previous-event
    origin cache. Preparing an event may be expensive. Reuse its frozen result
    only for that same event/model/settings. This does not change modern routes.
    """
    coverage: TimeSpan
    path_coverage: TimeSpan
    rotation: EarthRotationModel
    settings: OriginTransportSettings = OriginTransportSettings()
    policy: str = NOMINAL_ORIENTATION_POLICY

    def __post_init__(self):
        if (type(self.coverage) is not TimeSpan or type(self.path_coverage) is not TimeSpan
                or type(self.rotation) is not EarthRotationModel
                or type(self.settings) is not OriginTransportSettings
                or type(self.policy) is not str or self.policy != NOMINAL_ORIENTATION_POLICY):
            raise InvalidQuery('Explicit supported orientation models/settings/coverage required.')
        if self.coverage.start.scale != 'tt' or self.path_coverage.start.scale != 'tt':
            raise TimeConversionUnavailable('Orientation and history coverage require TT.')
        if (_tt_jyear(self.path_coverage.start) < -13000
                or _tt_jyear(self.path_coverage.stop) > 13000
                or not self.path_coverage.contains(TimePoint(2451545, 0, 'tt'))
                or not self.path_coverage.contains(self.coverage.start)
                or not self.path_coverage.contains(self.coverage.stop)
                or not self.rotation.coverage.contains(self.coverage.start)
                or not self.rotation.coverage.contains(self.coverage.stop)):
            raise OutsideCoverage('Missing event/path coverage inside J-13000..J+13000.')

    def evaluate(self, tt, *, maximum_physical_error_rad=None,
                 maximum_numerical_error_rad=None):
        from math import atan2
        from time import perf_counter
        import json
        if type(tt) is not TimePoint:
            raise InvalidQuery('Explicit split TT event required.')
        if tt.scale != 'tt':
            raise TimeConversionUnavailable('Orientation evaluation requires TT.')
        if not self.coverage.contains(tt):
            raise OutsideCoverage('Outside caller orientation coverage.', time=tt)
        for requested in (maximum_physical_error_rad, maximum_numerical_error_rad):
            if requested is not None:
                try:
                    valid = type(requested) in (int, float) and isfinite(requested) and requested >= 0
                except OverflowError:
                    valid = False
                if not valid:
                    raise InvalidQuery('Error requests must be finite and nonnegative.')
                raise AccuracyUnavailable('No certified physical/total numerical bound is available.')
        started = perf_counter()
        try:
            import erfa
            import numpy as np
            from pathlib import Path
            hashes = tuple((name, sha256(Path(path).read_bytes()).hexdigest())
                for name, path in (('convention-owner', __file__),
                                   ('erfa-ufunc', erfa.ufunc.__file__),
                                   ('erfa-wrapper', erfa.core.__file__)))
            versions = (str(erfa.__version__), str(erfa.version.erfa_version),
                        str(erfa.version.sofa_version), str(np.__version__))
            # Public frame receipts preserve exact TT and original matrix identity.
            frames = [LongTermFrame(equinox=tt, validity=self.path_coverage,
                axes=axes, model_policy=LONG_TERM_FRAME_POLICY) for axes in
                ('mean-equator-equinox', 'mean-ecliptic-equinox')]
            seed = TimePoint(2451545, 0, 'tt')
            pole0, _ = _nominal_pole(seed.jd1, seed.jd2)
            modern_seed = _orientation_matrix(erfa.c2i06a(seed.jd1, seed.jd2))[0]
            origin0 = _orientation_unit(modern_seed - np.dot(modern_seed, pole0)*pole0)
            gauge0 = _pole_gauge(pole0)
            s0 = atan2(-float(np.dot(origin0, gauge0[1])),
                       float(np.dot(origin0, gauge0[0])))
            pole, _ = _nominal_pole(tt.jd1, tt.jd2)
            duration = float(Fraction(tt.jd1-2451545)+Fraction(tt.jd2))
            history = TimeSpan(seed, tt) if duration >= 0 else TimeSpan(tt, seed)
            def pole_function(offsets):
                p, _ = _nominal_pole(2451545., offsets)
                # Retain exact-split endpoint poles instead of rounded offsets.
                if offsets[0] == 0:
                    p[0] = pole0
                if offsets[-1] == duration:
                    p[-1] = pole
                return p
            transport = _transport_origin(pole_function, duration_days=duration,
                seed_locator=s0, history=history, settings=self.settings)
            c = _orientation_matrix(_orientation_r3(-transport.locator_rad) @ _pole_gauge(pole))
            rotation = self.rotation.evaluate(tt)
            era = float(erfa.era00(rotation.ut1_jd1, rotation.ut1_jd2))
            full = _orientation_matrix(_orientation_r3(era) @ c)
        except (InvalidQuery, OutsideCoverage, AccuracyUnavailable, InvalidProviderResult):
            raise
        except Exception as exc:
            raise ProviderEvaluationError('Nominal orientation backend/transport failed.', time=tt) from exc
        matrix_tuple = lambda a: tuple(tuple(float(x) for x in row) for row in a)
        event = lambda t: (t.jd1, t.jd2.hex(), t.scale)
        span = lambda s: (event(s.start), event(s.stop))
        binding = dict(policy=self.policy, tt=event(tt), coverage=span(self.coverage),
            path_coverage=span(self.path_coverage), versions=versions, backend_hashes=hashes,
            frames=[f.model.configuration_digest for f in frames],
            settings=(self.settings.max_step_days, self.settings.tolerance_rad,
                      self.settings.max_refinements, self.settings.max_samples),
            seed_pole=[float(x).hex() for x in pole0],
            seed_origin=[float(x).hex() for x in origin0],
            locator=transport.locator_rad.hex(),
            refinements=[x.hex() for x in transport.extrapolated_locators_rad],
            matrix=[[float(x).hex() for x in row] for row in full],
            terrestrial='xp=yp=s-prime=0;nominal-axes-not-ITRF')
        # ModelRef is represented structurally, not with a platform-specific repr.
        binding['rotation'] = (rotation.model.model_id, rotation.model.version,
            rotation.model.configuration_digest, span(rotation.coverage),
            rotation.ut1_jd1, rotation.ut1_jd2.hex(), rotation.delta_t_s.hex())
        model = ModelRef('wenu.astrometry:nominal-earth-orientation', '1', sha256(
            json.dumps(binding, sort_keys=True, separators=(',', ':'),
                       allow_nan=False).encode()).hexdigest(), ())
        return NominalOrientationResult(tt, self.coverage, self.path_coverage, rotation,
            *frames, versions, hashes, tuple(map(float, pole0)), tuple(map(float, origin0)),
            tuple(map(float, pole)), tuple(map(float, c[0])), transport, era,
            matrix_tuple(c), matrix_tuple(full), matrix_tuple(full.T), model,
            perf_counter()-started)
