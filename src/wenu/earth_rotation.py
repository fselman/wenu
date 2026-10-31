"""Named nominal Earth spin timing, independent of axis/site/ephemeris models.

NASA Espenak--Meeus (2006) coefficients, reviewed 2026-10-31:
https://eclipse.gsfc.nasa.gov/SEcat5/deltatpoly.html
No Canon-specific lunar correction, fitted residual, observed EOP or acquisition.
"""
from dataclasses import dataclass, field
from fractions import Fraction
from hashlib import sha256
import json
from math import floor, isfinite
from types import MappingProxyType
from typing import Callable

from wenu_kernel.errors import InvalidQuery, OutsideCoverage, TimeConversionUnavailable
from wenu_kernel.records import ModelRef, TimePoint, TimeSpan


DEFAULT_ROTATION_MODEL = 'espenak-meeus-2006/1'
_PROVENANCE = (
    'https://eclipse.gsfc.nasa.gov/SEcat5/deltatpoly.html',
    'Espenak--Meeus 2006; published coefficients; no Canon lunar correction',
    'Continuous proleptic Gregorian decimal TT year; astronomical year zero',
    'Outer parabola extended outside published -1999 through +3000 interval',
    'Nominal spin timing only; numerical/physical errors unknown; no ancient accuracy certificate',
)
# Upper year (exclusive), origin, divisor, ascending powers.
# 2050--2150 has the additional published linear join term.
_PIECES = (
    (-500, 1820, 100, (-20., 0., 32.)),
    (500, 0, 100, (10583.6, -1014.41, 33.78311, -5.952053,
                   -.1798452, .022174192, .0090316521)),
    (1600, 1000, 100, (1574.2, -556.01, 71.23472, .319781,
                       -.8503463, -.005050998, .0083572073)),
    (1700, 1600, 1, (120., -.9808, -.01532, 1/7129)),
    (1800, 1700, 1, (8.83, .1603, -.0059285, .00013336, -1/1174000)),
    (1860, 1800, 1, (13.72, -.332447, .0068612, .0041116,
                     -.00037436, .0000121272, -.0000001699, .000000000875)),
    (1900, 1860, 1, (7.62, .5737, -.251754, .01680668, -.0004473624, 1/233174)),
    (1920, 1900, 1, (-2.79, 1.494119, -.0598939, .0061966, -.000197)),
    (1941, 1920, 1, (21.20, .84493, -.076100, .0020936)),
    (1961, 1950, 1, (29.07, .407, -1/233, 1/2547)),
    (1986, 1975, 1, (45.45, 1.067, -1/260, -1/718)),
    (2005, 2000, 1, (63.86, .3345, -.060374, .0017275, .000651814, .00002373599)),
    (2050, 2000, 1, (62.92, .32217, .005589)),
    (2150, 1820, 100, (-20., 0., 32.)),
    (None, 1820, 100, (-20., 0., 32.)),
)
_MODEL_DIGEST = sha256(json.dumps(dict(
    name=DEFAULT_ROTATION_MODEL, pieces=_PIECES,
    join_2050_2150=-.5628,
    year='continuous-proleptic-gregorian-TT-fraction-of-calendar-year/1',
    extrapolation='same-outer-parabola;published-year-minus1999-through3000',
    lunar_correction=False, evaluator='Horner-binary64/1',
), sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _espenak_meeus(year):
    for upper, origin, divisor, coefficients in _PIECES:
        if upper is None or year < upper:
            u = float((year-origin)/divisor)
            value = 0.
            for c in reversed(coefficients):
                value = value*u+c
            if upper == 2150:
                value -= .5628*(2150-year)
            return value


def _jan1_jdn(year):
    # Proleptic Gregorian arithmetic works for negative years with floor division.
    y = year+4799
    return 1+(153*10+2)//5+365*y+y//4-y//100+y//400-32045


def _decimal_tt_year(tt):
    day = Fraction(tt.jd1)+Fraction(tt.jd2)
    jdn = floor(day+Fraction(1, 2))
    a = jdn+32044
    b = (4*a+3)//146097
    c = a-(146097*b)//4
    d = (4*c+3)//1461
    e = c-(1461*d)//4
    m = (5*e+2)//153
    year = 100*b+d-4800+m//10
    start = Fraction(_jan1_jdn(year))-Fraction(1, 2)
    length = _jan1_jdn(year+1)-_jan1_jdn(year)
    return year+(day-start)/length


def _split(day):
    whole = floor(day+Fraction(1, 2))
    small = float(day-whole)
    if small == .5:
        whole, small = whole+1, -.5
    if abs(whole) > 2**53:
        raise InvalidQuery('Rotation date exceeds exact binary64 integer-day range.')
    return whole, small


def _evaluate_espenak_meeus(tt):
    year = _decimal_tt_year(tt)
    delta = _espenak_meeus(year)
    outside = year < -1999 or year >= 3001
    # The published interval includes complete calendar years -1999..3000.
    regime = ('extended-parabola' if outside else
              'secular-parabola' if year < -500 or year >= 2150 else
              'prediction-polynomial' if year >= 2005 else 'historical-polynomial')
    return float(year), delta, regime, outside, regime != 'historical-polynomial'


# Future named implementations add a descriptor here, sharing the same
# receipt, domain guards and Skyfield seam. No runtime registration/global setter.
_MODEL_SPECS = MappingProxyType({
    DEFAULT_ROTATION_MODEL: (_evaluate_espenak_meeus, ModelRef(
        'wenu.earth-rotation:espenak-meeus-2006', '1', _MODEL_DIGEST, ()), _PROVENANCE),
})
ROTATION_MODELS = tuple(_MODEL_SPECS)


@dataclass(frozen=True, slots=True)
class RotationResult:
    """Data-only receipt. UT1 fields are not a relabelled SDK TimePoint.

    The SDK deliberately admits only continuous TAI/TT/TDB/TCB scales.
    This separate spin receipt neither extends that contract nor qualifies
    observer orientation. Negative Delta-T is permitted by the published fit.
    """
    tt: TimePoint
    decimal_year_tt: float
    delta_t_s: float
    ut1_jd1: int
    ut1_jd2: float
    model: ModelRef
    coverage: TimeSpan
    regime: str
    extrapolated: bool
    outside_published_interval: bool
    provenance: tuple[str, ...] = _PROVENANCE
    physical_error_s: None = None
    numerical_error_s: None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class EarthRotationModel:
    """One explicitly named model over caller-declared finite TT coverage.

    The default belongs only to this new boundary. Existing Observer, IERS,
    Astropy, charts and CLI defaults are unchanged. Future implementations
    extend the explicit allowlist; no global model setter or import-by-name.
    """
    coverage: TimeSpan
    name: str = DEFAULT_ROTATION_MODEL
    model: ModelRef = field(init=False)
    _evaluator: Callable = field(init=False, repr=False, compare=False)
    _provenance: tuple[str, ...] = field(init=False, repr=False)

    def __post_init__(self):
        if type(self.name) is not str or self.name not in ROTATION_MODELS:
            raise InvalidQuery('Unknown Earth rotation model name.')
        if type(self.coverage) is not TimeSpan:
            raise InvalidQuery('Explicit finite TT rotation coverage is required.')
        if self.coverage.start.scale != 'tt':
            raise TimeConversionUnavailable('Rotation coverage requires TT.')
        if any(abs(t.jd1) > 2**53 for t in (self.coverage.start, self.coverage.stop)):
            raise InvalidQuery('Rotation coverage exceeds exact binary64 integer-day range.')
        evaluator, identity, provenance = _MODEL_SPECS[self.name]
        object.__setattr__(self, 'model', identity)
        object.__setattr__(self, '_evaluator', evaluator)
        object.__setattr__(self, '_provenance', provenance)

    def evaluate(self, tt):
        if type(tt) is not TimePoint:
            raise InvalidQuery('Explicit split TT TimePoint required.')
        if tt.scale != 'tt':
            raise TimeConversionUnavailable('Rotation evaluation requires TT, not relabelling.')
        if not self.coverage.contains(tt):
            raise OutsideCoverage('Outside admitted rotation model coverage.', time=tt)
        year, delta, regime, outside, extrapolated = self._evaluator(tt)
        if not isfinite(delta):
            raise InvalidQuery('Delta-T overflows binary64.')
        whole, small = _split(Fraction(tt.jd1)+Fraction(tt.jd2)-Fraction(delta)/86400)
        return RotationResult(tt, year, delta, whole, small, self.model,
                              self.coverage, regime, extrapolated, outside, self._provenance)

    def __call__(self, tt_jd):
        """Skyfield delta_t_function: summed TT JD scalar/array -> seconds.

        Skyfield supplies a binary64 summed JD at this interface. Any precision
        already lost there cannot be restored; evaluate() retains split input.
        An out-of-coverage member refuses the entire array, including warm use.
        No implicit UTC, downloads or mutation of a global timescale.
        """
        import numpy as np
        raw = np.asarray(tt_jd)
        if raw.dtype.kind not in 'iuf' or not np.all(np.isfinite(raw)):
            raise InvalidQuery('Finite real TT Julian dates required.')
        values = np.asarray(raw, dtype=float)
        result = np.empty(values.shape, dtype=float)
        for index in np.ndindex(values.shape):
            value = float(values[index])
            whole = floor(value+.5)
            result[index] = self.evaluate(TimePoint(whole, value-whole, 'tt')).delta_t_s
        return float(result) if result.ndim == 0 else result

    def skyfield_timescale(self, *, leap_dates, leap_offsets):
        """Build a fresh Skyfield Timescale from explicitly supplied leap arrays.

        No source timescale is modified. Leap arrays are copied, not acquired.
        This establishes the Delta-T seam only: no polar motion, precession or
        ancient UTC policy is selected. Use TT input for ancient evaluations.
        """
        import numpy as np
        from skyfield.timelib import Timescale
        dates = np.array(leap_dates, dtype=float, copy=True)
        offsets = np.array(leap_offsets, dtype=float, copy=True)
        if (dates.ndim != 1 or dates.size < 2 or offsets.shape != dates.shape
                or not np.all(np.isfinite(dates)) or not np.all(np.isfinite(offsets))
                or not np.all(np.diff(dates) > 0)):
            raise InvalidQuery('Finite ordered equal-length leap arrays required.')
        return Timescale(self, dates, offsets)
