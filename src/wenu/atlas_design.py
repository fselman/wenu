"""Observer-independent atlas geometry specimens and strict versioned JSON.

Exact footprints are defined by the existing stereographic inverse applied to
each useful plane rectangle. Band tilings are conservative comparison products,
not the final atlas command or publication contract.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import json
import hashlib
import math
import re
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


# Keep the accepted specimen protocol unchanged. This separate comparison
# protocol adds an analytic containment certificate and primary partition.
TILING_KIND = "wenu-atlas-band-tiling"
TILING_METHOD = "latitude-bands-inscribed-cap-v1"
RECTANGULAR_TILING_METHOD = "latitude-bands-rectangle-halfspaces-v1"
ANGULAR_GUARD_DEG = 1e-8
MAX_TILING_SHEETS = 4096


@dataclass(frozen=True)
class AtlasPrimaryBand:
    """Latitude band partitioned into equal, half-open RA sectors.

    sheet_ids are in increasing RA order starting at ra_origin_deg.
    The end latitude is excluded except at +90. A one-sheet polar band
    owns all RAs, including the pole independently of its arbitrary RA.
    """

    dec_min_deg: float
    dec_max_deg: float
    ra_origin_deg: float
    sheet_ids: tuple[str, ...]

    def __post_init__(self):
        for name in ("dec_min_deg", "dec_max_deg", "ra_origin_deg"):
            object.__setattr__(self, name, _number(getattr(self, name), name))
        if not -90 <= self.dec_min_deg < self.dec_max_deg <= 90:
            raise ValueError("Invalid primary-band latitude interval.")
        if not 0 <= self.ra_origin_deg < 360:
            raise ValueError("Primary-band RA origin must be in [0, 360).")
        if not isinstance(self.sheet_ids, (tuple, list)) or not self.sheet_ids:
            raise ValueError("Primary band requires sheet IDs.")
        for identifier in self.sheet_ids:
            _identifier(identifier, "primary sheet_id")
        if len(set(self.sheet_ids)) != len(self.sheet_ids):
            raise ValueError("Duplicate primary sheet IDs.")
        object.__setattr__(self, "sheet_ids", tuple(self.sheet_ids))

    @property
    def sector_width_deg(self):
        return 360 / len(self.sheet_ids)

    @property
    def area_sr(self):
        return 2 * math.pi * (
            math.sin(math.radians(self.dec_max_deg))
            - math.sin(math.radians(self.dec_min_deg))
        )


def _inscribed_radius_deg(sheet, page):
    viewport = sheet.viewport(page)
    return sheet.projection.angular_radius_for_projected_radius(
        min(viewport.width, viewport.height) / 2
    )


def _sector_radius_deg(center_dec, dec_min, dec_max, half_ra):
    """Maximum centre separation of an aligned sector (half_RA <= 60).

    cos(distance) = sin(dc)*sin(d) + cos(dc)*cos(d)*cos(delta_RA).
    Its minimum in RA is at either longitudinal edge. There cos(delta_RA)
    is positive, so the only interior latitude stationary point is a maximum
    of cos(distance); the minimum is at a latitude endpoint. This bounds the
    entire closed sector, not just samples.
    """
    dc = math.radians(center_dec)
    longitude = math.cos(math.radians(half_ra))
    dots = [
        math.sin(dc) * math.sin(math.radians(d))
        + math.cos(dc) * math.cos(math.radians(d)) * longitude
        for d in (dec_min, dec_max)
    ]
    return math.degrees(math.acos(max(-1.0, min(1.0, min(dots)))))


def _longitude_intersection(a, b):
    """Positive length of the intersection of two closed circular sectors."""
    start_a, width_a = a
    start_b, width_b = b
    return sum(max(0.0, min(start_a + width_a, start_b + width_b + shift)
                   - max(start_a, start_b + shift))
               for shift in (-360, 0, 360))


def _sector_linear_maximum(vector, ra_min, ra_max, dec_min, dec_max):
    """Maximum of vector dot unit direction over a closed RA/Dec sector.

    cos(dec) is nonnegative, so maximize the horizontal sinusoid in RA first.
    Its endpoints and any contained maximum give one horizontal coefficient.
    Then check latitude endpoints and all contained stationary points. This
    also handles unwrapped RA sectors and full-RA polar caps without sampling.
    """
    cx, cy, cz = vector
    phase = math.degrees(math.atan2(cy, cx))
    longitudes = [ra_min, ra_max]
    first = math.ceil((ra_min - phase) / 360)
    last = math.floor((ra_max - phase) / 360)
    longitudes.extend(phase + 360 * k for k in range(first, last + 1))
    horizontal = max(cx * math.cos(math.radians(ra))
                     + cy * math.sin(math.radians(ra)) for ra in longitudes)
    latitudes = [dec_min, dec_max]
    phase = math.degrees(math.atan2(cz, horizontal))
    for k in range(-2, 3):
        latitude = phase + 180 * k
        if dec_min <= latitude <= dec_max:
            latitudes.append(latitude)
    return max(horizontal * math.cos(math.radians(dec))
               + cz * math.sin(math.radians(dec)) for dec in latitudes)


def _rectangle_clearance_deg(sheet, page, ra_min, ra_max, dec_min, dec_max):
    """Continuous minimum distance to the four stereographic edge circles.

    With canonical tangent-frame coordinates u, plane x=r*u_y/(1+u_z)
    and y=r*u_x/(1+u_z). Each rectangle edge is a spherical halfspace
    (+/-u_axis - t*u_z) <= t, where t is its half-side divided by r.
    For unit edge normal n and threshold b, the interior angular clearance
    is asin(b)-asin(n dot direction). Its minimum uses the analytic sector
    maximum above. Restrict the primary region to the tangent hemisphere to
    exclude the stereographic antipode and keep the denominator positive.
    """
    matrix = sheet.frame.rotation_matrix
    if _sector_linear_maximum(-matrix[2], ra_min, ra_max, dec_min, dec_max) >= 0:
        raise ValueError("Rectangular primary region leaves the tangent hemisphere.")
    viewport = sheet.viewport(page)
    margins = []
    for axis, half_side in ((matrix[1], viewport.width / 2),
                            (matrix[0], viewport.height / 2)):
        t = half_side / sheet.projection_radius
        for sign in (-1, 1):
            normal = sign * axis - t * matrix[2]
            maximum = _sector_linear_maximum(
                normal, ra_min, ra_max, dec_min, dec_max,
            ) / float(np.linalg.norm(normal))
            margins.append(math.degrees(math.atan(t) - math.asin(
                max(-1.0, min(1.0, maximum))
            )))
    return min(margins)


@dataclass(frozen=True)
class AtlasBandTiling:
    """Validated conservative whole-sphere partition and rectangle coverage.

    Only aligned equal-sector latitude bands with one sheet at each pole are
    admitted. Validation uses analytic cap or rectangle bounds with a numerical guard,
    not formal interval arithmetic or an optimized sheet-count claim.
    """

    geometry: AtlasGeometrySpecimen
    bands: tuple[AtlasPrimaryBand, ...]
    overlap_deg: float
    seed_ra_deg: float
    containment_method: str = TILING_METHOD
    request_json: str | None = None

    def __post_init__(self):
        if not isinstance(self.geometry, AtlasGeometrySpecimen):
            raise TypeError("geometry must be AtlasGeometrySpecimen.")
        if not isinstance(self.bands, (tuple, list)) or not self.bands:
            raise ValueError("A tiling requires primary bands.")
        if not all(isinstance(b, AtlasPrimaryBand) for b in self.bands):
            raise TypeError("bands must contain AtlasPrimaryBand records.")
        object.__setattr__(self, "bands", tuple(self.bands))
        for name in ("overlap_deg", "seed_ra_deg"):
            object.__setattr__(self, name, _number(getattr(self, name), name))
        if self.overlap_deg < 0 or not 0 <= self.seed_ra_deg < 360:
            raise ValueError("Invalid overlap or seed RA.")
        self.validation()
        if self.request_json is not None:
            request = AtlasDesignRequest.from_dict(json.loads(self.request_json))
            if (request.page != self.geometry.page
                    or request.overview != self.geometry.overview
                    or request.design_id != self.geometry.design_id
                    or request.revision != self.geometry.revision
                    or request.overlap_deg != self.overlap_deg
                    or request.seed_ra_deg != self.seed_ra_deg
                    or any(sheet.field_width_deg != (
                        _polar_field_width_deg(request.page, request.polar_primary_diameter_deg,
                                               request.overlap_deg)
                        if abs(sheet.center_dec_deg) == 90 and request.polar_primary_diameter_deg is not None
                        else request.field_width_deg) for sheet in self.geometry.sheets)
                    or (request.polar_primary_diameter_deg is not None and
                        not math.isclose(2 * (self.bands[0].dec_max_deg + 90),
                                         request.polar_primary_diameter_deg, abs_tol=1e-10))):
                raise ValueError("Design request does not match resolved geometry.")

    def validation(self):
        """Recompute partition completeness and conservative angular margins."""
        if not isinstance(self.containment_method, str) or self.containment_method not in (
                TILING_METHOD, RECTANGULAR_TILING_METHOD):
            raise ValueError("Unsupported band-tiling containment method.")
        sheets = {s.sheet_id: s for s in self.geometry.sheets}
        if len(sheets) > MAX_TILING_SHEETS:
            raise ValueError("Tiling exceeds the sheet-count budget.")
        assigned = [s for b in self.bands for s in b.sheet_ids]
        if len(assigned) != len(set(assigned)) or set(assigned) != set(sheets):
            raise ValueError("Primary bands must assign every sheet exactly once.")
        if len(self.bands) < 3:
            raise ValueError("Tiling requires two polar bands and an interior.")
        if self.bands[0].dec_min_deg != -90 or self.bands[-1].dec_max_deg != 90:
            raise ValueError("Primary bands must reach both poles.")
        # Exact shared persisted endpoints avoid accepting small hidden holes.
        if any(a.dec_max_deg != b.dec_min_deg
               for a, b in zip(self.bands, self.bands[1:])):
            raise ValueError("Primary latitude bands have gaps or overlap.")
        margins = []
        for index, band in enumerate(self.bands):
            polar = index in (0, len(self.bands) - 1)
            if polar and len(band.sheet_ids) != 1:
                raise ValueError("Each polar band requires exactly one sheet.")
            if not polar and len(band.sheet_ids) < 3:
                raise ValueError("Interior bands require at least three sectors.")
            for sector, identifier in enumerate(band.sheet_ids):
                sheet = sheets[identifier]
                if not 5 <= sheet.field_width_deg <= 120:
                    raise ValueError("Band prototype requires fields in [5, 120] degrees.")
                if polar:
                    dec = -90 if index == 0 else 90
                    if sheet.center_dec_deg != dec:
                        raise ValueError("Polar band requires its polar sheet.")
                    if sheet.pole_meridian_ra_deg != self.seed_ra_deg:
                        raise ValueError("Polar meridian must match the tiling seed.")
                    radius = (band.dec_max_deg + 90 if index == 0
                              else 90 - band.dec_min_deg)
                else:
                    first_ra = (band.ra_origin_deg + band.sector_width_deg / 2) % 360
                    seed_offset = (first_ra - self.seed_ra_deg + 180) % 360 - 180
                    if abs(seed_offset) > 1e-10:
                        raise ValueError("Primary-band phase must match the tiling seed.")
                    expected_ra = (band.ra_origin_deg
                                   + (sector + 0.5) * band.sector_width_deg) % 360
                    offset = (sheet.center_ra_deg - expected_ra + 180) % 360 - 180
                    if abs(offset) > 1e-10 or sheet.center_dec_deg != (
                            band.dec_min_deg + band.dec_max_deg) / 2:
                        raise ValueError("Interior centres must align with primary sectors.")
                    radius = _sector_radius_deg(
                        sheet.center_dec_deg, band.dec_min_deg,
                        band.dec_max_deg, band.sector_width_deg / 2,
                    )
                clearance = _inscribed_radius_deg(sheet, self.geometry.page) - radius
                if self.containment_method == RECTANGULAR_TILING_METHOD:
                    ra_min = band.ra_origin_deg + sector * band.sector_width_deg
                    clearance = _rectangle_clearance_deg(
                        sheet, self.geometry.page, ra_min,
                        ra_min + band.sector_width_deg,
                        band.dec_min_deg, band.dec_max_deg,
                    )
                if clearance < self.overlap_deg / 2 + ANGULAR_GUARD_DEG:
                    boundary = "sheet cap" if self.containment_method == TILING_METHOD else "sheet rectangle"
                    raise ValueError(f"Primary area or overlap is outside the {boundary}.")
                margins.append(clearance - ANGULAR_GUARD_DEG)
        return {
            "method": self.containment_method,
            "coverage_status": ("validated_analytic_cap_bound"
                                if self.containment_method == TILING_METHOD
                                else "validated_analytic_rectangle_bound"),
            "angular_guard_deg": ANGULAR_GUARD_DEG,
            "primary_area_sr": sum(b.area_sr for b in self.bands),
            "minimum_primary_clearance_deg": min(margins),
            "shared_boundary_overlap_lower_bound_deg": 2 * min(margins),
            "sheet_count": len(sheets),
        }

    def primary_sheet_id(self, ra_deg, dec_deg):
        """Unique scalar ownership: upper latitude/RA sector wins a shared edge."""
        ra = _number(ra_deg, "ra_deg")
        dec = _number(dec_deg, "dec_deg")
        if not -90 <= dec <= 90:
            raise ValueError("Declination outside [-90, 90].")
        for band in self.bands:
            if band.dec_min_deg <= dec < band.dec_max_deg or (
                    dec == 90 and band.dec_max_deg == 90):
                offset = (ra - band.ra_origin_deg) % 360
                sector = min(int(offset / band.sector_width_deg),
                             len(band.sheet_ids) - 1)
                return band.sheet_ids[sector]
        raise ValueError("Direction has no primary owner.")

    def neighbours(self):
        """Reciprocal shared-primary-edge graph; corner-only contacts excluded.

        This is navigation topology, not a list of every rectangle intersection.
        Each edge inherits the validated shared-boundary overlap lower bound.
        """
        graph = {s.sheet_id: set() for s in self.geometry.sheets}

        def connect(a, b):
            graph[a].add(b)
            graph[b].add(a)

        for band in self.bands:
            if len(band.sheet_ids) > 1:
                for a, b in zip(band.sheet_ids,
                                band.sheet_ids[1:] + band.sheet_ids[:1]):
                    connect(a, b)
        for lower, upper in zip(self.bands, self.bands[1:]):
            for i, a in enumerate(lower.sheet_ids):
                interval_a = ((lower.ra_origin_deg
                               + i * lower.sector_width_deg) % 360,
                              lower.sector_width_deg)
                for j, b in enumerate(upper.sheet_ids):
                    interval_b = ((upper.ra_origin_deg
                                   + j * upper.sector_width_deg) % 360,
                                  upper.sector_width_deg)
                    if _longitude_intersection(interval_a, interval_b) > 1e-10:
                        connect(a, b)
        return {s: tuple(sorted(v)) for s, v in sorted(graph.items())}

    def to_dict(self):
        result = {
            "schema_version": 1,
            "document_kind": TILING_KIND,
            "generator": self.containment_method,
            "geometry": self.geometry.to_dict(),
            "bands": [asdict(b) for b in self.bands],
            "overlap_deg": self.overlap_deg,
            "seed_ra_deg": self.seed_ra_deg,
            "validation": self.validation(),
            "neighbours": self.neighbours(),
        }
        if self.request_json is not None:
            request = json.loads(self.request_json)
            result["design_request"] = request
            page = self.geometry.page
            result["layout"] = {
                "interior_band_count": len(self.bands) - 2,
                "charts_per_band": [len(b.sheet_ids) for b in self.bands],
                "orientation": "portrait" if page.height_mm > page.width_mm else "landscape",
                "field_width_deg": self.geometry.sheets[1].field_width_deg,
                "field_height_deg": self.geometry.sheets[1].field_height_deg(page),
                "polar_primary_diameter_deg": 2 * (self.bands[0].dec_max_deg + 90),
                "placement": ("polar-first-grid-bands-v1" if request["schema_version"] == 2
                              or request["tiling"].get("algorithm") == "polar_first"
                              else request["tiling"]["algorithm"]),
                "objective": "minimum charts, then fewer bands on symmetric one-degree declination boundary grid"
                             if request["schema_version"] == 2 or request["tiling"].get("algorithm") == "polar_first"
                             else "explicit version-1 algorithm",
            }
        return result

    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True,
                          indent=2, allow_nan=False) + "\n"

    def write_json(self, path):
        destination = Path(path)
        destination.write_text(self.to_json(), encoding="utf-8")
        return destination

    @classmethod
    def from_dict(cls, data):
        _keys(data, ("schema_version", "document_kind", "generator", "geometry",
                    "bands", "overlap_deg", "seed_ra_deg", "validation",
                    "neighbours", *(key for key in ("design_request", "layout")
                                    if key in data)), "band tiling")
        if ("design_request" in data) != ("layout" in data):
            raise ValueError("Design request and layout must occur together.")
        if type(data["schema_version"]) is not int or data["schema_version"] != 1:
            raise ValueError("Unsupported band-tiling schema.")
        if data["document_kind"] != TILING_KIND or data["generator"] not in (
                TILING_METHOD, RECTANGULAR_TILING_METHOD):
            raise ValueError("Unsupported band-tiling method or kind.")
        if not isinstance(data["bands"], list):
            raise ValueError("bands must be an array.")
        result = cls(
            AtlasGeometrySpecimen.from_dict(data["geometry"]),
            tuple(_record(AtlasPrimaryBand, b) for b in data["bands"]),
            data["overlap_deg"], data["seed_ra_deg"], data["generator"],
            json.dumps(data["design_request"], sort_keys=True, allow_nan=False)
            if "design_request" in data else None,
        )
        # JSON comparison also rejects booleans masquerading as numbers.
        for key in ("validation", "neighbours", *(k for k in ("layout",) if k in data)):
            expected = result.to_dict()[key]
            actual = data[key]
            if key == "validation" and isinstance(actual, dict) and actual.keys() == expected.keys():
                actual = dict(actual)
                # Derived evidence may differ in the last bits across NumPy/libm
                # builds. Recompute coverage above; only its redundant floating
                # summary receives tolerances, below the angular guard.
                for name, tolerance in (("primary_area_sr", 1e-12),
                        ("minimum_primary_clearance_deg", 1e-10),
                        ("shared_boundary_overlap_lower_bound_deg", 1e-10)):
                    value = _number(actual[name], name)
                    if not math.isclose(value, expected[name], rel_tol=0, abs_tol=tolerance):
                        raise ValueError("Inconsistent tiling validation.")
                    actual[name] = expected[name]
            if json.dumps(actual, sort_keys=True, allow_nan=False) != json.dumps(
                    expected, sort_keys=True, allow_nan=False):
                raise ValueError(f"Inconsistent tiling {key}.")
        return result

    @classmethod
    def from_json(cls, text):
        def pairs(values):
            result = {}
            for key, value in values:
                if key in result:
                    raise ValueError(f"Duplicate JSON key: {key}.")
                result[key] = value
            return result

        def constant(value):
            raise ValueError(f"Non-finite JSON constant: {value}.")

        return cls.from_dict(json.loads(text, object_pairs_hook=pairs,
                                       parse_constant=constant))

    @classmethod
    def read_json(cls, path):
        return cls.from_json(Path(path).read_text(encoding="utf-8"))


def design_band_atlas(design_id, revision, page, overview, *,
                      field_width_deg, overlap_deg, seed_ra_deg,
                      max_sheets=MAX_TILING_SHEETS):
    """Build a conservative stereographic comparison tiling without catalogues.

    Fields in [5,120] degrees, north-up interior sheets, an equatorial row,
    increasing-RA sectors and south-to-north numbering. The seed specifies
    one centre per row independently of the overview join. overlap_deg is
    a minimum angular width at shared primary boundaries, not a percentage.
    """
    _identifier(design_id, "design_id")
    _integer(revision, "revision")
    _integer(max_sheets, "max_sheets")
    if max_sheets > MAX_TILING_SHEETS:
        raise ValueError("max_sheets exceeds the prototype budget.")
    if not isinstance(page, AtlasPageGeometry) or not isinstance(
            overview, AtlasOverviewGeometry):
        raise TypeError("page and overview require atlas geometry records.")
    width = _number(field_width_deg, "field_width_deg")
    overlap = _number(overlap_deg, "overlap_deg")
    seed = _number(seed_ra_deg, "seed_ra_deg")
    if not 5 <= width <= 120 or overlap < 0 or not 0 <= seed < 360:
        raise ValueError("Invalid field, overlap or seed RA.")
    trial = AtlasSheetGeometry("trial", 1, seed, 0, width)
    # Additional guard keeps construction off the validation threshold.
    radius = _inscribed_radius_deg(trial, page) - overlap / 2 - 2 * ANGULAR_GUARD_DEG
    if radius < 1:
        raise ValueError("Field/aspect/overlap leaves less than a 1-degree design cap.")
    extent = 90 - radius
    rows = max(1, math.ceil(2 * extent / (math.sqrt(2) * radius)))
    if rows % 2 == 0:
        rows += 1
    if rows * 3 + 2 > max_sheets:
        raise ValueError("Tiling exceeds the sheet-count budget.")
    # Namespace changes on retiling, independent of overview presentation.
    recipe = [TILING_METHOD, design_id, revision, asdict(page), width, overlap, seed]
    digest = hashlib.sha256(json.dumps(recipe, sort_keys=True).encode()).hexdigest()
    namespace = f"{design_id}:r{revision}:{digest}"
    sheets, bands = [], []

    def append_sheet(key, ra, dec):
        identifier = f"{namespace}:{key}"
        sheets.append(AtlasSheetGeometry(
            identifier, len(sheets) + 1, ra, dec, width,
            pole_meridian_ra_deg=seed if abs(dec) == 90 else None,
        ))
        return identifier

    south = append_sheet("south", 0, -90)
    bands.append(AtlasPrimaryBand(-90, -extent, 0, (south,)))
    edges = [extent * (2 * i - rows) / rows for i in range(rows + 1)]
    edges[0], edges[-1] = -extent, extent
    for row in range(rows):
        lo, hi = edges[row:row + 2]
        dc = (lo + hi) / 2

        def fits(count):
            return _sector_radius_deg(dc, lo, hi, 180 / count) <= radius

        count = 3
        while not fits(count):
            count *= 2
            if count > max_sheets:
                raise ValueError("Tiling exceeds the sheet-count budget.")
        low, high = 3, count
        while low < high:
            mid = (low + high) // 2
            if fits(mid):
                high = mid
            else:
                low = mid + 1
        count = low
        if len(sheets) + count + 1 > max_sheets:
            raise ValueError("Tiling exceeds the sheet-count budget.")
        step = 360 / count
        origin = (seed - step / 2) % 360
        identifiers = tuple(append_sheet(f"band-{row + 1}-sector-{i + 1}",
                                         (origin + (i + 0.5) * step) % 360, dc)
                            for i in range(count))
        bands.append(AtlasPrimaryBand(lo, hi, origin, identifiers))
    north = append_sheet("north", 0, 90)
    bands.append(AtlasPrimaryBand(extent, 90, 0, (north,)))
    specimen = AtlasGeometrySpecimen(design_id, revision, page, overview, tuple(sheets))
    return AtlasBandTiling(specimen, tuple(bands), overlap, seed)


def design_five_band_atlas(design_id, revision, page, overview, *,
                           field_width_deg, overlap_deg, seed_ra_deg,
                           equatorial_half_height_deg,
                           middle_boundary_dec_deg,
                           max_sheets=MAX_TILING_SHEETS):
    """Five interior latitude bands and exactly two polar sheets.

    Equatorial/middle primary boundaries are explicit symmetric declinations.
    The polar boundary is resolved from the polar rectangle's shorter side,
    reserving half the requested angular overlap and a numerical guard.
    Every row uses the smallest integer number of equal RA sectors admitted
    by continuous four-edge rectangle containment. This exploits converging
    meridians without substituting a cos(dec) approximation for projection.
    All sheets retain one horizontal field and the B4/page physical scale.
    This is a comparison layout, not a global minimum-sheet optimizer.
    """
    _identifier(design_id, "design_id")
    _integer(revision, "revision")
    _integer(max_sheets, "max_sheets")
    if not 17 <= max_sheets <= MAX_TILING_SHEETS:
        raise ValueError("Five-band sheet budget must be in [17, 4096].")
    if not isinstance(page, AtlasPageGeometry) or not isinstance(overview, AtlasOverviewGeometry):
        raise TypeError("page and overview require atlas geometry records.")
    width = _number(field_width_deg, "field_width_deg")
    overlap = _number(overlap_deg, "overlap_deg")
    seed = _number(seed_ra_deg, "seed_ra_deg")
    a = _number(equatorial_half_height_deg, "equatorial_half_height_deg")
    b = _number(middle_boundary_dec_deg, "middle_boundary_dec_deg")
    if not 5 <= width <= 120 or overlap < 0 or not 0 <= seed < 360:
        raise ValueError("Invalid field, overlap or seed RA.")
    margin = overlap / 2 + 2 * ANGULAR_GUARD_DEG
    trial = AtlasSheetGeometry("trial", 1, seed, 0, width)
    polar_radius = _inscribed_radius_deg(trial, page) - margin
    c = 90 - polar_radius
    if polar_radius < 1 or not 0 < a < b < c < 90:
        raise ValueError("Invalid five-band primary boundaries or polar extent.")
    edges = (-90, -c, -b, -a, a, b, c, 90)
    return _design_rectangular_bands(design_id, revision, page, overview,
                                     width, overlap, seed, edges, max_sheets)


def _design_rectangular_bands(design_id, revision, page, overview,
                              width, overlap, seed, edges, max_sheets,
                              polar_width=None):
    """Common analytic rectangular admission and deterministic assembly."""
    margin = overlap / 2 + 2 * ANGULAR_GUARD_DEG
    c = edges[-2]
    counts = [_band_sector_count(page, width, seed, overlap, lo, hi, max_sheets)
              for lo, hi in zip(edges[1:-2], edges[2:-1])]
    if any(count is None for count in counts):
        raise ValueError("Requested band geometry cannot fit the sheet budget.")
    if sum(counts) + 2 > max_sheets:
        raise ValueError("Tiling exceeds the sheet-count budget.")
    recipe = [RECTANGULAR_TILING_METHOD, design_id, revision, asdict(page),
              width, overlap, seed, edges, counts]
    if polar_width is not None:
        recipe.append(polar_width)
    digest = hashlib.sha256(json.dumps(recipe, sort_keys=True).encode()).hexdigest()
    namespace = f"{design_id}:r{revision}:{digest}"
    sheets, bands = [], []

    def append_sheet(key, ra, dec):
        identifier = f"{namespace}:{key}"
        sheets.append(AtlasSheetGeometry(
            identifier, len(sheets) + 1, ra, dec,
            polar_width if abs(dec) == 90 and polar_width is not None else width,
            pole_meridian_ra_deg=seed if abs(dec) == 90 else None,
        ))
        return identifier

    south = append_sheet("south", 0, -90)
    bands.append(AtlasPrimaryBand(-90, -c, 0, (south,)))
    for row, (lo, hi, count) in enumerate(zip(edges[1:-2], edges[2:-1], counts)):
        step = 360 / count
        origin = (seed - step / 2) % 360
        identifiers = tuple(append_sheet(
            f"band-{row + 1}-sector-{sector + 1}",
            (origin + (sector + 0.5) * step) % 360, (lo + hi) / 2,
        ) for sector in range(count))
        bands.append(AtlasPrimaryBand(lo, hi, origin, identifiers))
    north = append_sheet("north", 0, 90)
    bands.append(AtlasPrimaryBand(c, 90, 0, (north,)))
    geometry = AtlasGeometrySpecimen(design_id, revision, page, overview, tuple(sheets))
    return AtlasBandTiling(geometry, tuple(bands), overlap, seed, RECTANGULAR_TILING_METHOD)


def _band_sector_count(page, width, seed, overlap, lo, hi, budget):
    """Smallest integer RA count certified by the shared rectangle bound."""
    trial = AtlasSheetGeometry("trial", 1, seed, (lo + hi) / 2, width)
    margin = overlap / 2 + 2 * ANGULAR_GUARD_DEG

    def fits(count):
        try:
            return _rectangle_clearance_deg(
                trial, page, seed - 180 / count, seed + 180 / count, lo, hi
            ) >= margin
        except ValueError:
            return False

    if budget < 3 or not fits(budget):
        return None
    lower, upper = 3, budget
    while lower < upper:
        middle = (lower + upper) // 2
        if fits(middle):
            upper = middle
        else:
            lower = middle + 1
    return lower


def design_polar_first_atlas(design_id, revision, page, overview, *,
                             field_width_deg, overlap_deg, seed_ra_deg,
                             max_sheets=MAX_TILING_SHEETS,
                             polar_primary_diameter_deg=None):
    """Minimum chart count on a symmetric one-degree boundary grid.

    Fix the largest safe polar caps; choose one equatorial band and paired
    unequal-height bands by dynamic programming. RA sectors are equal within
    each band. Grid points are integer declinations plus the exact cap edge.
    Coverage is continuous and analytic; only placement optimality is grid
    restricted. Ties prefer fewer bands, then deterministic boundary order.
    """
    _identifier(design_id, "design_id")
    _integer(revision, "revision")
    _integer(max_sheets, "max_sheets")
    if max_sheets > MAX_TILING_SHEETS:
        raise ValueError("max_sheets exceeds the 4096-sheet budget.")
    if not isinstance(page, AtlasPageGeometry) or not isinstance(overview, AtlasOverviewGeometry):
        raise TypeError("page and overview require atlas geometry records.")
    width = _number(field_width_deg, "field_width_deg")
    overlap = _number(overlap_deg, "overlap_deg")
    seed = _number(seed_ra_deg, "seed_ra_deg")
    if not 5 <= width <= 120 or overlap < 0 or not 0 <= seed < 360:
        raise ValueError("Invalid field, overlap or seed RA.")
    trial = AtlasSheetGeometry("trial", 1, seed, 0, width)
    radius = _inscribed_radius_deg(trial, page) - overlap / 2 - 2 * ANGULAR_GUARD_DEG
    polar_width = None
    if polar_primary_diameter_deg is not None:
        diameter = _number(polar_primary_diameter_deg, "polar_primary_diameter_deg")
        if not 2 <= diameter <= 120:
            raise ValueError("polar_primary_diameter_deg must be between 2 and 120.")
        radius = diameter / 2
        polar_width = _polar_field_width_deg(page, diameter, overlap)
        if not 5 <= polar_width <= 120:
            raise ValueError("Polar field width must be between 5 and 120 degrees.")
    if radius < 1:
        raise ValueError("Field/aspect/overlap leaves less than a 1-degree polar cap.")
    extent = 90 - radius
    nodes = [float(i) for i in range(1, math.ceil(extent))] + [extent]
    # dp[i] holds the best northern partition from nodes[i] to the cap.
    # Costs are per hemisphere; boundaries are retained for deterministic ties.
    dp = {len(nodes) - 1: (0, 0, (extent,))}
    for i in range(len(nodes) - 2, -1, -1):
        choices = []
        for j in range(i + 1, len(nodes)):
            if j not in dp:
                continue
            count = _band_sector_count(page, width, seed, overlap,
                                       nodes[i], nodes[j], max_sheets)
            if count is not None:
                cost, bands, boundaries = dp[j]
                choices.append((cost + count, bands + 1, (nodes[i], *boundaries)))
        if choices:
            dp[i] = min(choices)
    choices = []
    for i, (cost, bands, boundaries) in dp.items():
        count = _band_sector_count(page, width, seed, overlap,
                                   -nodes[i], nodes[i], max_sheets)
        if count is not None and 2 + count + 2 * cost <= max_sheets:
            choices.append((2 + count + 2 * cost, 1 + 2 * bands, boundaries))
    if not choices:
        raise ValueError("No polar-first layout fits the sheet-count budget.")
    _, _, north = min(choices)
    edges = (-90, *(-v for v in reversed(north)), *north, 90)
    return _design_rectangular_bands(design_id, revision, page, overview,
                                     width, overlap, seed, edges, max_sheets, polar_width)


def _polar_field_width_deg(page, diameter, overlap):
    """Size the polar short side to include the primary cap and overlap."""
    short_field = diameter + overlap + 4 * ANGULAR_GUARD_DEG
    return math.degrees(4 * math.atan(
        max(1.0, page.aspect_ratio) * math.tan(math.radians(short_field / 4))))


def select_atlas_sheets(atlas, selector):
    """Resolve a bounded union of numbers, inclusive ranges and S/N/E groups.

    Selection retains persisted numbering and uses centre declination, never
    footprint intersection. It neither loads catalogues nor reruns placement.
    """
    if not isinstance(atlas, AtlasBandTiling):
        raise TypeError("atlas must be an AtlasBandTiling.")
    if not isinstance(selector, str) or not selector.strip():
        raise ValueError("Chart selector must be a nonempty string.")
    sheets = atlas.geometry.sheets
    available = {sheet.number for sheet in sheets}
    selected = set()
    max_number = max(available)

    def number(token):
        # Reject huge numeric endpoints before int conversion/range allocation.
        digits = token.lstrip("0") or "0"
        if len(digits) > len(str(max_number)):
            raise ValueError("Chart number is absent from the design.")
        value = int(digits)
        if value not in available:
            raise ValueError(f"Chart {value} is absent from the design.")
        return value

    for raw in selector.split(","):
        token = raw.strip()
        group = token.upper()
        if group == "ALL":
            selected.update(available)
        elif group in ("S", "N", "E"):
            selected.update(sheet.number for sheet in sheets if (
                (group == "S" and sheet.center_dec_deg < 0)
                or (group == "N" and sheet.center_dec_deg > 0)
                or (group == "E" and sheet.center_dec_deg == 0)))
        elif re.fullmatch(r"[0-9]+", token):
            selected.add(number(token))
        elif re.fullmatch(r"[0-9]+\.\.[0-9]+", token):
            start, stop = (number(part) for part in token.split(".."))
            if start > stop:
                raise ValueError("Chart ranges must be ascending.")
            members = {value for value in available if start <= value <= stop}
            if len(members) != stop - start + 1:
                raise ValueError("Chart range contains numbers absent from the design.")
            selected.update(members)
        else:
            raise ValueError(f"Invalid chart selector token: {token!r}.")
    if not selected:
        raise ValueError("Chart selector selects no sheets.")
    return tuple(sheet for sheet in sheets if sheet.number in selected)


@dataclass(frozen=True)
class AtlasDesignRequest:
    """Versioned geometry request for the supported stereographic designers.

    This is independent of schema-v2 chart configuration. Astronomical
    selection and index presentation are not geometry-request inputs.
    """

    design_id: str
    revision: int
    page: AtlasPageGeometry
    overview: AtlasOverviewGeometry
    algorithm: str
    field_width_deg: float
    overlap_deg: float
    seed_ra_deg: float
    max_sheets: int = MAX_TILING_SHEETS
    equatorial_half_height_deg: float | None = None
    middle_boundary_dec_deg: float | None = None
    request_json: str | None = None
    polar_primary_diameter_deg: float | None = None

    def __post_init__(self):
        _identifier(self.design_id, "design_id")
        _integer(self.revision, "revision")
        _integer(self.max_sheets, "max_sheets")
        if self.max_sheets > MAX_TILING_SHEETS:
            raise ValueError("max_sheets exceeds the 4096-sheet budget.")
        if not isinstance(self.page, AtlasPageGeometry) or not isinstance(
                self.overview, AtlasOverviewGeometry):
            raise ValueError("page and overview require atlas geometry records.")
        if self.algorithm not in ("five_band", "cap_bands", "polar_first"):
            raise ValueError("algorithm must be five_band, cap_bands or polar_first.")
        for name in ("field_width_deg", "overlap_deg", "seed_ra_deg"):
            object.__setattr__(self, name, _number(getattr(self, name), name))
        if not 5 <= self.field_width_deg <= 120 or self.overlap_deg < 0:
            raise ValueError("Invalid field width or minimum overlap.")
        if not 0 <= self.seed_ra_deg < 360:
            raise ValueError("seed_ra_deg must be in [0, 360).")
        profile = ("equatorial_half_height_deg", "middle_boundary_dec_deg")
        if self.algorithm == "five_band":
            for name in profile:
                object.__setattr__(self, name, _number(getattr(self, name), name))
            if not 0 < self.equatorial_half_height_deg < self.middle_boundary_dec_deg < 90:
                raise ValueError("Invalid five-band latitude boundaries.")
        elif any(getattr(self, name) is not None for name in profile):
            raise ValueError("Latitude profile is only supported by five_band.")
        if self.polar_primary_diameter_deg is not None:
            diameter = _number(self.polar_primary_diameter_deg, "polar_primary_diameter_deg")
            if self.algorithm != "polar_first" or not 2 <= diameter <= 120:
                raise ValueError("Independent polar diameter requires polar_first and 2..120 degrees.")
            object.__setattr__(self, "polar_primary_diameter_deg", diameter)

    @classmethod
    def from_dict(cls, data):
        """Parse a closed request, with explicit degrees or hours for each RA."""
        _keys(data, ("schema_version", "document_kind", "design_id", "revision",
                     "coordinate_frame", "projection", "page", "overview",
                     "tiling"), "atlas design request")
        if type(data["schema_version"]) is not int or data["schema_version"] not in (1, 2):
            raise ValueError("Unsupported atlas design request schema.")
        if data["document_kind"] != "wenu-atlas-design-request":
            raise ValueError("Unsupported atlas design request kind.")
        if data["coordinate_frame"] != "icrs" or data["projection"] != "stereographic":
            raise ValueError("Only icrs stereographic atlas designs are supported.")

        def ra_record(record, prefix, required, optional=()):
            if not isinstance(record, dict):
                raise ValueError(f"{prefix} input must be a table.")
            degrees, hours = prefix + "_deg", prefix + "_hours"
            present = set(record) & {degrees, hours}
            if len(present) != 1:
                raise ValueError(f"Supply exactly one of {degrees} or {hours}.")
            key = present.pop()
            _keys(record, set(required) | {key} | (set(optional) & set(record)), prefix)
            value = _number(record[key], key)
            limit = 24 if key == hours else 360
            if not 0 <= value < limit:
                raise ValueError(f"{key} must be in [0, {limit}).")
            return value * 15 if key == hours else value

        overview = data["overview"]
        join = ra_record(overview, "join_ra", ("shared_band_width_deg",))
        tiling = data["tiling"]
        if not isinstance(tiling, dict):
            raise ValueError("tiling must be a table.")
        version = data["schema_version"]
        required = {"field_width_deg", "overlap_deg"}
        if version == 2:
            fields = set(tiling) & {"field_width_deg", "field_height_deg"}
            if len(fields) != 1:
                raise ValueError("Supply exactly one of field_width_deg or field_height_deg.")
            required = fields | {"overlap_deg"}
        if version == 1:
            required.add("algorithm")
        page_data = data["page"]
        if version == 2:
            _keys(page_data, ("paper_size", "orientation", "top_mm", "bottom_mm",
                              "inner_mm", "outer_mm"), "page")
            if page_data["paper_size"] != "B4":
                raise ValueError("Version-2 paper_size currently supports ISO B4.")
            if page_data["orientation"] not in ("portrait", "landscape"):
                raise ValueError("orientation must be portrait or landscape.")
            width_mm, height_mm = ((250, 353) if page_data["orientation"] == "portrait"
                                   else (353, 250))
            page_data = {k: page_data[k] for k in
                         ("top_mm", "bottom_mm", "inner_mm", "outer_mm")}
            page_data.update(width_mm=width_mm, height_mm=height_mm)
        if version == 1 and tiling.get("algorithm") == "five_band":
            required |= {"equatorial_half_height_deg", "middle_boundary_dec_deg"}
        seed = ra_record(tiling, "seed_ra", required,
                         ("max_sheets", "polar_primary_diameter_deg") if version == 2 else ("max_sheets",))
        page = _record(AtlasPageGeometry, page_data)
        width = tiling.get("field_width_deg")
        if width is None:
            height = _number(tiling["field_height_deg"], "field_height_deg")
            if not 5 <= height <= 120:
                raise ValueError("field_height_deg must be between 5 and 120.")
            width = math.degrees(4 * math.atan(page.aspect_ratio * math.tan(math.radians(height / 4))))
        canonical = json.loads(json.dumps(data, allow_nan=False))
        canonical["overview"].pop("join_ra_hours", None)
        canonical["overview"]["join_ra_deg"] = join
        canonical["tiling"].pop("seed_ra_hours", None)
        canonical["tiling"]["seed_ra_deg"] = seed
        canonical["tiling"].setdefault("max_sheets", MAX_TILING_SHEETS)
        return cls(
            data["design_id"], data["revision"],
            page,
            AtlasOverviewGeometry(join, overview["shared_band_width_deg"]),
            tiling["algorithm"] if version == 1 else "polar_first", width, tiling["overlap_deg"],
            seed, tiling.get("max_sheets", MAX_TILING_SHEETS),
            tiling.get("equatorial_half_height_deg"),
            tiling.get("middle_boundary_dec_deg"),
            json.dumps(canonical, sort_keys=True, allow_nan=False),
            tiling.get("polar_primary_diameter_deg"),
        )

    def resolve(self):
        """Construct a complete validated layout through the existing owner."""
        options = dict(field_width_deg=self.field_width_deg,
                       overlap_deg=self.overlap_deg, seed_ra_deg=self.seed_ra_deg,
                       max_sheets=self.max_sheets)
        designer = (design_polar_first_atlas if self.algorithm == "polar_first"
                    else design_band_atlas)
        if self.algorithm == "five_band":
            designer = design_five_band_atlas
            options.update(equatorial_half_height_deg=self.equatorial_half_height_deg,
                           middle_boundary_dec_deg=self.middle_boundary_dec_deg)
        if self.polar_primary_diameter_deg is not None:
            options["polar_primary_diameter_deg"] = self.polar_primary_diameter_deg
        result = designer(self.design_id, self.revision, self.page, self.overview, **options)
        return replace(result, request_json=self.request_json)

