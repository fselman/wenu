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
