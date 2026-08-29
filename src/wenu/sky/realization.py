"""Immutable scientific input for one sky-layer realization."""

from __future__ import annotations

from dataclasses import dataclass

from wenu.coordinates import CoordinateSpec, ObservationContext


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
    the compatibility adapter on SkyLayer until deliberately migrated.
    """

    product_coordinate_spec: CoordinateSpec
    observation: ObservationContext | None = None
    evaluation_instant: str | None = None
    evaluation_time_scale: str | None = None
    reference_equinox: str | None = None

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
