"""Resource-free TT(TAI)/TAI coordinate conversion with explicit coverage.

TT(TAI) = TAI + 32.184 seconds. This is not TT(BIPM), UTC, UT1,
an ancient atomic-clock realization or a relativistic barycentric model.
Authority: https://aa.usno.navy.mil/faq/TT (reviewed 2026-10-18).
No SOFA code is copied or required by this implementation.
"""

from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from math import inf, nextafter

from .errors import InvalidQuery, OutsideCoverage, TimeConversionUnavailable
from .records import ModelRef, TimePoint, TimeSpan, exact
from .time import TimeConversion, TimeConversionAdmission


TAI_TT_MODEL = ModelRef(
    "wenu.time:tt-tai", "1",
    sha256(b'{"offset_seconds":"32.184","realization":"TT(TAI)","version":1}').hexdigest(), (),
)
TAI_TT_PROVENANCE = (
    "https://aa.usno.navy.mil/faq/TT",
    "TT(TAI) = TAI + 32.184 s exactly; rational offset and bounded binary64 rounding",
    "Numerical bound excludes physical clock/realization and input-time uncertainty",
)


@dataclass(frozen=True, slots=True, init=False)
class TaiTtAdapter:
    """One directed conversion with a caller-admitted finite source interval.

    Callers explicitly choose the domain: an algebraic mapping alone does not
    establish a historical TAI realization. No default/unbounded domain is used.
    """

    _admission: TimeConversionAdmission

    def __init__(self, validity: TimeSpan):
        exact(validity, TimeSpan)
        source = validity.start.scale
        if source not in ("tai", "tt"):
            raise InvalidQuery("TT/TAI adapter requires TT or TAI source coverage")
        target = "tt" if source == "tai" else "tai"
        object.__setattr__(self, "_admission", TimeConversionAdmission(
            source, target, validity, TAI_TT_MODEL, 2**-36, TAI_TT_PROVENANCE,
        ))

    def describe(self) -> TimeConversionAdmission:
        return self._admission

    def convert(self, time: TimePoint, target_scale: str) -> TimeConversion:
        exact(time, TimePoint)
        admission = self._admission
        if (time.scale, target_scale) != (admission.source_scale, admission.target_scale):
            raise TimeConversionUnavailable("TT/TAI adapter pair mismatch", time=time)
        if not admission.validity.contains(time):
            raise OutsideCoverage("time outside admitted TT/TAI interval", time=time)
        # Work only on the small part; never round a large summed Julian date.
        delta = Fraction(32184, 1000 * 86400)
        if time.scale == "tt":
            delta = -delta
        fraction = Fraction(time.jd2) + delta
        carry = (fraction + Fraction(1, 2)).__floor__()
        small = float(fraction - carry)
        # Rounding itself can put the small part on the excluded upper edge.
        if small == .5:
            small = -.5
            carry += 1
        target = TimePoint(time.jd1 + carry, small, target_scale)
        error = abs(Fraction(carry) + Fraction(target.jd2) - fraction) * 86400
        bound = float(error)
        if Fraction(bound) < error:
            bound = nextafter(bound, inf)
        return TimeConversion(time, target, admission.model, bound, admission.provenance)
