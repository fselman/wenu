"""Immutable scientific input for one sky-layer realization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wenu.astrometric_observation import ReceptionContext

from wenu.coordinates import CoordinateSpec, ObservationContext, PositionStatus


NATIVE_ICRS_SPEC = CoordinateSpec(
    frame="icrs", origin="solar-system-barycenter",
    position_status=PositionStatus.ASTROMETRIC,
    provider="native catalogues", model="unpropagated catalogue directions",
)


def _optional_text(value, *, name):
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string or None.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{name} must be non-empty when supplied.")
    return normalized


@dataclass(frozen=True)
class LayerRealizationContext:
    """Request-adjacent scientific input supplied before projection.

    The context contains no projection, viewport, renderer, appearance,
    furniture, output, or cache policy. Existing layers may ignore it through
    the compatibility adapter on SkyLayer until deliberately migrated. An explicit
    reception receipt requires deliberate support and cannot use that fallback.
    """

    product_coordinate_spec: CoordinateSpec
    observation: ObservationContext | None = None
    evaluation_instant: str | None = None
    evaluation_time_scale: str | None = None
    reference_equinox: str | None = None
    reception: ReceptionContext | None = None

    @property
    def is_native_icrs(self):
        """Native ICRS axes; an explicit epoch may be consumed by admitted layers."""
        return (
            self.product_coordinate_spec == NATIVE_ICRS_SPEC
            and self.observation is None
            and self.reference_equinox is None
            and self.reception is None
        )

    @staticmethod
    def _reception_fields(reception):
        from wenu.astrometric_observation import ReceptionContext
        if type(reception) is not ReceptionContext or not reception.utc_isot:
            raise TypeError("reception must be a prepared ReceptionContext.")
        spec = CoordinateSpec(frame="altaz", origin="observer",
            position_status=PositionStatus.OBSERVED, instant=reception.utc_isot,
            time_scale="utc", corrections=frozenset(("parallax", "solar-deflection",
                "aberration", "earth-orientation", "vacuum")))
        observation = ObservationContext(*reception.site_wgs84, reception.utc_isot,
            earth_orientation_policy="iers-final-b")
        return spec, observation

    @classmethod
    def from_reception(cls, reception):
        """Request vacuum AltAz from an explicit offline reception receipt.

        The receipt's caller-qualified WGS84 height is never inferred from a
        legacy Observer. Source model selection remains a per-layer option.
        """
        spec, observation = cls._reception_fields(reception)
        return cls(spec, observation, reception.utc_isot, "utc", reception=reception)

    def __post_init__(self):
        if not isinstance(self.product_coordinate_spec, CoordinateSpec):
            raise TypeError(
                "product_coordinate_spec must be a CoordinateSpec."
            )
        if (
            self.observation is not None
            and not isinstance(self.observation, ObservationContext)
        ):
            raise TypeError(
                "observation must be an ObservationContext or None."
            )
        instant = _optional_text(
            self.evaluation_instant,
            name="evaluation_instant",
        )
        time_scale = _optional_text(
            self.evaluation_time_scale,
            name="evaluation_time_scale",
        )
        if (instant is None) != (time_scale is None):
            raise ValueError(
                "evaluation_instant and evaluation_time_scale must be "
                "supplied together."
            )
        object.__setattr__(self, "evaluation_instant", instant)
        object.__setattr__(
            self,
            "evaluation_time_scale",
            None if time_scale is None else time_scale.lower(),
        )
        object.__setattr__(
            self,
            "reference_equinox",
            _optional_text(
                self.reference_equinox,
                name="reference_equinox",
            ),
        )

        if self.reception is not None:
            spec, observation = self._reception_fields(self.reception)
            if (self.product_coordinate_spec != spec or self.observation != observation
                    or self.evaluation_instant != self.reception.utc_isot
                    or self.evaluation_time_scale != "utc" or self.reference_equinox is not None):
                raise ValueError("Reception context, product, site and evaluation event must agree.")
