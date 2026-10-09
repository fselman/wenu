"""Observer-independent atlas geometry specimens and strict versioned JSON.

This is not a tiler or a complete atlas. Exact footprints are defined by the
existing stereographic inverse applied to each useful plane rectangle.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from numbers import Real
from pathlib import Path

import numpy as np

from wenu.geometry.frame import SphericalFrame
from wenu.geometry.viewport import Viewport
from wenu.projections.stereographic import StereographicProjection


SCHEMA_VERSION = 1
DOCUMENT_KIND = "wenu-atlas-geometry-specimen"


def _number(value, name):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite number.")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be a finite number.")
    return result


def _integer(value, name):
    if type(value) is not int or value < 1:
        raise ValueError(f"{name} must be a positive integer.")


def _identifier(value, name):
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{name} must be a nonempty trimmed string.")


def _keys(value, expected, name):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError(f"Invalid or unknown keys in {name}.")


def _record(cls, value):
    _keys(value, cls.__dataclass_fields__, cls.__name__)
    return cls(**value)


@dataclass(frozen=True)
class AtlasPageGeometry:
    """Right-hand page dimensions and margins, all in millimetres."""

    width_mm: float
    height_mm: float
    top_mm: float
    bottom_mm: float
    inner_mm: float
    outer_mm: float

    def __post_init__(self):
        for name in self.__dataclass_fields__:
            value = _number(getattr(self, name), name)
            if value < 0 or (name in {"width_mm", "height_mm"} and value == 0):
                raise ValueError(f"Invalid page dimension: {name}.")
            object.__setattr__(self, name, value)
        if self.useful_width_mm <= 0 or self.useful_height_mm <= 0:
            raise ValueError("Page margins leave no useful rectangle.")
        if not math.isfinite(self.aspect_ratio) or self.aspect_ratio <= 0:
            raise ValueError("Useful page aspect ratio must be finite and positive.")

    @property
    def useful_width_mm(self):
        return self.width_mm - self.inner_mm - self.outer_mm

    @property
    def useful_height_mm(self):
        return self.height_mm - self.top_mm - self.bottom_mm

    @property
    def aspect_ratio(self):
        return self.useful_width_mm / self.useful_height_mm


@dataclass(frozen=True)
class AtlasOverviewGeometry:
    """Celestial join geometry, independent of index layout on paper."""

    join_ra_deg: float
    shared_band_width_deg: float

    def __post_init__(self):
        for name in self.__dataclass_fields__:
            object.__setattr__(self, name, _number(getattr(self, name), name))
        if not 0 <= self.join_ra_deg < 360:
            raise ValueError("join_ra_deg must be in [0, 360).")
        if not 0 <= self.shared_band_width_deg < 180:
            raise ValueError("shared_band_width_deg must be in [0, 180).")

    @property
    def north_limit_dec_deg(self):
        return -self.shared_band_width_deg / 2

    @property
    def south_limit_dec_deg(self):
        return self.shared_band_width_deg / 2


@dataclass(frozen=True)
class AtlasSheetGeometry:
    """An ICRS-centred stereographic rectangle with explicit orientation.

    At a pole, centre RA is canonically zero and pole_meridian_ra_deg selects
    the tangent direction placed at +y when position_angle_deg is zero.
    Elsewhere, angle and east/west flip use SphericalFrame's existing policy.
    """

    sheet_id: str
    number: int
    center_ra_deg: float
    center_dec_deg: float
    field_width_deg: float
    position_angle_deg: float = 0.0
    flip_ew: bool = False
    pole_meridian_ra_deg: float | None = None
    projection_radius: float = 2.0

    def __post_init__(self):
        _identifier(self.sheet_id, "sheet_id")
        _integer(self.number, "number")
        for name in ("center_ra_deg", "center_dec_deg", "field_width_deg",
                     "position_angle_deg", "projection_radius"):
            object.__setattr__(self, name, _number(getattr(self, name), name))
        if not 0 <= self.center_ra_deg < 360:
            raise ValueError("center_ra_deg must be in [0, 360).")
        if not -90 <= self.center_dec_deg <= 90:
            raise ValueError("center_dec_deg must be in [-90, 90].")
        if not 0 < self.field_width_deg < 360:
            raise ValueError("field_width_deg must be in (0, 360).")
        if not -180 <= self.position_angle_deg < 180:
            raise ValueError("position_angle_deg must be in [-180, 180).")
        if self.projection_radius <= 0:
            raise ValueError("projection_radius must be positive.")
        if type(self.flip_ew) is not bool:
            raise ValueError("flip_ew must be boolean.")
        polar = abs(self.center_dec_deg) == 90
        if polar:
            anchor = _number(self.pole_meridian_ra_deg, "pole_meridian_ra_deg")
            if self.center_ra_deg != 0 or not 0 <= anchor < 360:
                raise ValueError("Polar sheets require RA=0 and a meridian in [0, 360).")
            object.__setattr__(self, "pole_meridian_ra_deg", anchor)
        elif self.pole_meridian_ra_deg is not None:
            raise ValueError("pole_meridian_ra_deg is only for polar sheets.")
        half_width = self.projection.projected_radius(self.field_width_deg / 2)
        if not math.isfinite(half_width) or half_width <= 0:
            raise ValueError("Sheet projected extent must be finite and positive.")

    @property
    def frame(self):
        angle = self.position_angle_deg
        if abs(self.center_dec_deg) == 90:
            angle += math.copysign(1, self.center_dec_deg) * self.pole_meridian_ra_deg
        return SphericalFrame(
            pole_lon_deg=self.center_ra_deg,
            pole_lat_deg=self.center_dec_deg,
            position_angle_deg=angle,
        )

    @property
    def projection(self):
        return StereographicProjection(
            radius=self.projection_radius, flip_ew=self.flip_ew, frame=self.frame
        )

    def viewport(self, page):
        if not isinstance(page, AtlasPageGeometry):
            raise TypeError("page must be AtlasPageGeometry.")
        half_width = self.projection.projected_radius(self.field_width_deg / 2)
        return Viewport.centered(
            width=2 * half_width, height=2 * half_width / page.aspect_ratio
        )

    def field_height_deg(self, page):
        return 2 * self.projection.angular_radius_for_projected_radius(
            self.viewport(page).height / 2
        )

    def boundary_samples(self, page, *, samples_per_edge=17):
        """Diagnostic samples of the exact footprint, not a coverage proof."""
        _integer(samples_per_edge, "samples_per_edge")
        if samples_per_edge < 2:
            raise ValueError("Each edge needs at least two samples.")
        v = self.viewport(page)
        corners = ((v.x_min, v.y_min), (v.x_max, v.y_min),
                   (v.x_max, v.y_max), (v.x_min, v.y_max))
        xy = np.concatenate([
            np.linspace(a, b, samples_per_edge, endpoint=False)
            for a, b in zip(corners, corners[1:] + corners[:1])
        ])
        coordinates = self.projection.unproject_spherical(xy[:, 0], xy[:, 1])
        return tuple(zip((coordinates.lon_deg % 360).tolist(),
                         coordinates.lat_deg.tolist()))

    def contains(self, page, ra_deg, dec_deg):
        """Test exact inverse-defined rectangle membership on the sphere."""
        ra, dec = np.broadcast_arrays(np.asarray(ra_deg, dtype=float),
                                     np.asarray(dec_deg, dtype=float))
        if not np.all(np.isfinite(ra)) or not np.all(np.isfinite(dec)):
            raise ValueError("Directions must be finite.")
        if np.any(np.abs(dec) > 90):
            raise ValueError("Declinations must be in [-90, 90].")
        aligned = self.frame.transform(ra, dec)
        x, y = self.projection.project_spherical(ra, dec)
        v = self.viewport(page)
        tolerance = 1e-12 * max(v.width, v.height)
        return ((aligned.lat_deg > -90) & np.isfinite(x) & np.isfinite(y)
                & (x >= v.x_min - tolerance) & (x <= v.x_max + tolerance)
                & (y >= v.y_min - tolerance) & (y <= v.y_max + tolerance))

    def resolved(self, page):
        """Exact parameters and redundant geometry verified on JSON loading."""
        return {
            "projection": "stereographic",
            "tangent_basis": self.frame.rotation_matrix.tolist(),
            "viewport": asdict(self.viewport(page)),
            "field_height_deg": self.field_height_deg(page),
        }


@dataclass(frozen=True)
class AtlasGeometrySpecimen:
    """Immutable explicit-centre specimen; whole-sphere coverage unverified."""

    design_id: str
    revision: int
    page: AtlasPageGeometry
    overview: AtlasOverviewGeometry
    sheets: tuple[AtlasSheetGeometry, ...]

    def __post_init__(self):
        _identifier(self.design_id, "design_id")
        _integer(self.revision, "revision")
        if not isinstance(self.page, AtlasPageGeometry):
            raise TypeError("page must be AtlasPageGeometry.")
        if not isinstance(self.overview, AtlasOverviewGeometry):
            raise TypeError("overview must be AtlasOverviewGeometry.")
        sheets = tuple(self.sheets)
        if not sheets or any(not isinstance(s, AtlasSheetGeometry) for s in sheets):
            raise ValueError("A specimen needs explicit sheet geometries.")
        for attribute in ("sheet_id", "number"):
            if len({getattr(s, attribute) for s in sheets}) != len(sheets):
                raise ValueError(f"Duplicate sheet {attribute}.")
        for sheet in sheets:
            sheet.viewport(self.page)
        object.__setattr__(self, "sheets", tuple(sorted(sheets, key=lambda s: s.number)))

    def to_dict(self):
        return {
            "schema_version": SCHEMA_VERSION,
            "document_kind": DOCUMENT_KIND,
            "coverage_status": "unverified",
            "coordinate_frame": "icrs",
            "angular_units": "degrees",
            "design_id": self.design_id,
            "revision": self.revision,
            "page": asdict(self.page),
            "overview": asdict(self.overview),
            "sheets": [{"geometry": asdict(s), "resolved": s.resolved(self.page)}
                       for s in self.sheets],
        }

    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True,
                          indent=2, allow_nan=False) + "\n"

    def write_json(self, path):
        """Write one specimen; output-directory creation belongs to the caller."""
        destination = Path(path)
        destination.write_text(self.to_json(), encoding="utf-8")
        return destination

    @classmethod
    def from_dict(cls, data):
        _keys(data, ("schema_version", "document_kind", "coverage_status",
                    "coordinate_frame", "angular_units", "design_id", "revision",
                    "page", "overview", "sheets"), "specimen")
        if type(data["schema_version"]) is not int or data["schema_version"] != SCHEMA_VERSION:
            raise ValueError("Unsupported atlas geometry schema version.")
        for key, value in (("document_kind", DOCUMENT_KIND),
                           ("coverage_status", "unverified"),
                           ("coordinate_frame", "icrs"), ("angular_units", "degrees")):
            if data[key] != value:
                raise ValueError(f"Unsupported {key}.")
        page = _record(AtlasPageGeometry, data["page"])
        overview = _record(AtlasOverviewGeometry, data["overview"])
        if not isinstance(data["sheets"], list):
            raise ValueError("sheets must be an array.")
        sheets = []
        for item in data["sheets"]:
            _keys(item, ("geometry", "resolved"), "sheet")
            sheet = _record(AtlasSheetGeometry, item["geometry"])
            expected = sheet.resolved(page)
            actual = item["resolved"]
            _keys(actual, expected, "resolved sheet")
            if actual["projection"] != "stereographic":
                raise ValueError("Unsupported projection.")
            for name in ("tangent_basis", "field_height_deg"):
                try:
                    leaves = actual[name]
                    if name == "tangent_basis":
                        leaves = [v for row in leaves for v in row]
                    else:
                        leaves = [leaves]
                    for leaf in leaves:
                        _number(leaf, name)
                    value = np.asarray(actual[name], dtype=float)
                    reference = np.asarray(expected[name], dtype=float)
                    valid = (value.shape == reference.shape and np.all(np.isfinite(value))
                             and np.allclose(value, reference,
                                             rtol=1e-12 if name == "field_height_deg" else 0,
                                             atol=0 if name == "field_height_deg" else 1e-12))
                except (TypeError, ValueError):
                    valid = False
                if not valid:
                    raise ValueError(f"Inconsistent resolved {name}.")
            _keys(actual["viewport"], expected["viewport"], "viewport")
            viewport = Viewport(**{
                n: _number(v, n) for n, v in actual["viewport"].items()
            })
            if any(not math.isclose(getattr(viewport, n), expected["viewport"][n],
                                    rel_tol=1e-12, abs_tol=0)
                   for n in expected["viewport"]):
                raise ValueError("Inconsistent resolved viewport.")
            sheets.append(sheet)
        return cls(data["design_id"], data["revision"], page, overview, tuple(sheets))

    @classmethod
    def from_json(cls, text):
        def object_pairs(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError(f"Duplicate JSON key: {key}.")
                result[key] = value
            return result

        def invalid_constant(value):
            raise ValueError(f"Non-finite JSON constant: {value}.")

        return cls.from_dict(json.loads(text, object_pairs_hook=object_pairs,
                                       parse_constant=invalid_constant))

    @classmethod
    def read_json(cls, path):
        return cls.from_json(Path(path).read_text(encoding="utf-8"))
