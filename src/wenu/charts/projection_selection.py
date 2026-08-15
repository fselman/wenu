"""Immutable chart projection selection and construction boundary."""

from __future__ import annotations

from dataclasses import dataclass


_PROJECTION_FRAMES = {
    "stereographic": frozenset({"horizontal", "equatorial"}),
    "mollweide": frozenset({"galactic"}),
    "polar_azimuthal_equidistant": frozenset({"equatorial"}),
}


@dataclass(frozen=True)
class ProjectionSelection:
    """A projection identity paired with its spherical coordinate frame."""

    name: str
    coordinate_frame: str

    def __post_init__(self):
        name = str(self.name).strip().lower()
        coordinate_frame = str(self.coordinate_frame).strip().lower()
        try:
            accepted_frames = _PROJECTION_FRAMES[name]
        except KeyError as error:
            raise ValueError(f"Unsupported projection: {name!r}.") from error
        if coordinate_frame not in accepted_frames:
            expected = " or ".join(
                repr(value) for value in sorted(accepted_frames)
            )
            raise ValueError(
                f"projection={name!r} requires "
                f"coordinate_frame={expected}."
            )
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "coordinate_frame", coordinate_frame)

    @classmethod
    def from_request(cls, request):
        """Return the immutable selection declared by a chart request."""
        return cls(request.projection, request.coordinate_frame)

    def build(self, **geometry):
        """Construct the selected backend-neutral projection lazily."""
        if self.name == "stereographic":
            from wenu.projections import StereographicProjection

            return StereographicProjection(**geometry)
        if self.name == "mollweide":
            from wenu.projections import MollweideProjection

            return MollweideProjection(**geometry)

        from wenu.projections import PolarAzimuthalEquidistantProjection

        return PolarAzimuthalEquidistantProjection(**geometry)
