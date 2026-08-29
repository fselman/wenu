"""Validated public policy for coupled celestial references."""

from __future__ import annotations

from dataclasses import dataclass

from astropy.time import Time

from wenu.coordinates import CoordinateSpec, PositionStatus


@dataclass(frozen=True)
class CelestialReferencePolicy:
    """One coherent FK5/ecliptic equinox for chart references."""

    equinox: str = "J2000"

    def __post_init__(self):
        value = str(self.equinox).strip()
        if not value:
            raise ValueError("reference equinox cannot be empty.")
        if value.lower() != "of_date":
            try:
                Time(value)
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"Invalid reference equinox {value!r}."
                ) from error
        object.__setattr__(
            self,
            "equinox",
            "of_date" if value.lower() == "of_date" else value,
        )

    def resolved_equinox(self, observer) -> str | Time:
        """Resolve ``of_date`` from the declared chart observer instant."""
        if self.equinox == "of_date":
            instant = getattr(observer, "t_astropy", None)
            if instant is None:
                raise TypeError("of_date requires an observer with t_astropy.")
            return instant
        return self.equinox

    def equatorial_spec(self, observer) -> CoordinateSpec:
        return CoordinateSpec(
            frame="fk5",
            origin="solar-system-barycenter",
            position_status=PositionStatus.ASTROMETRIC,
            equinox=str(self.resolved_equinox(observer)),
            provider="wenu public reference policy",
        )

    def ecliptic_spec(self, observer) -> CoordinateSpec:
        return CoordinateSpec(
            frame="barycentric-true-ecliptic",
            origin="solar-system-barycenter",
            position_status=PositionStatus.GEOMETRIC,
            equinox=str(self.resolved_equinox(observer)),
            provider="wenu public reference policy",
        )
