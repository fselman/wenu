"""Renderer-neutral A4 page furniture for paired polar planispheres."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from wenu.charts.polar_planisphere_pair import PolarPlanispherePair


_FACE_TITLES = {
    "south": "SOUTH / SUR",
    "north": "NORTH / NORTE",
}
_REGISTRATION_GLYPHS = ("triangle", "circle", "square")


@dataclass(frozen=True)
class PolarPageTextBlock:
    """One already-positioned semantic block in physical page coordinates."""

    role: str
    lines: tuple[str, ...]
    position_mm: tuple[float, float]
    horizontal_alignment: str = "center"


@dataclass(frozen=True)
class PolarPageRegistrationMark:
    """One asymmetric assembly mark positioned on one physical page."""

    identifier: str
    glyph: str
    position_mm: tuple[float, float]
    angle_deg: float
    radius_mm: float


@dataclass(frozen=True)
class PolarPageScaleRuler:
    """A measurable physical ruler with an explicit semantic label."""

    start_mm: tuple[float, float]
    end_mm: tuple[float, float]
    length_mm: float
    major_interval_mm: float
    label: str


@dataclass(frozen=True)
class PolarFacePageFurniture:
    """Resolved paper geometry and semantic information for one face."""

    face: str
    page_size_mm: tuple[float, float]
    safe_margin_mm: float
    disk_center_mm: tuple[float, float]
    disk_diameter_mm: float
    center_punch_radius_mm: float
    registration_marks: tuple[PolarPageRegistrationMark, ...]
    orientation_mark_identifier: str
    scale_ruler: PolarPageScaleRuler
    text_blocks: tuple[PolarPageTextBlock, ...]
    product_identifier: str
    source_revision: str

    @property
    def page_width_mm(self):
        return self.page_size_mm[0]

    @property
    def page_height_mm(self):
        return self.page_size_mm[1]

    @property
    def disk_radius_mm(self):
        return self.disk_diameter_mm / 2.0


@dataclass(frozen=True)
class PolarPagePairFurniture:
    """Matched north/south A4 page furniture from one resolved disk pair."""

    south: PolarFacePageFurniture
    north: PolarFacePageFurniture

    @property
    def faces(self):
        return self.south, self.north


@dataclass(frozen=True)
class PolarPageFurnitureRequest:
    """Resolve paired semantic furniture in physical A4 page coordinates."""

    page_width_mm: float = 210.0
    page_height_mm: float = 297.0
    safe_margin_mm: float = 5.0
    center_punch_radius_mm: float = 1.0
    scale_ruler_length_mm: float = 50.0
    scale_ruler_major_interval_mm: float = 10.0
    site_edition: str = "La Ligua/Papudo"
    site_name: str = "La Ligua"
    site_latitude_deg: float = -32.443342
    site_longitude_deg: float = -71.230289
    standard_utc_offset_hours: float = -4.0
    magnitude_limit: float = 5.5
    product_identifier: str = (
        "Wenu polar planisphere — classroom edition 2026-08"
    )
    source_revision: str = ""

    def __post_init__(self):
        numeric = np.asarray(
            (
                self.page_width_mm,
                self.page_height_mm,
                self.safe_margin_mm,
                self.center_punch_radius_mm,
                self.scale_ruler_length_mm,
                self.scale_ruler_major_interval_mm,
                self.site_latitude_deg,
                self.site_longitude_deg,
                self.standard_utc_offset_hours,
                self.magnitude_limit,
            ),
            dtype=float,
        )
        if not np.all(np.isfinite(numeric)):
            raise ValueError("Polar page-furniture values must be finite.")
        width, height, margin, punch, ruler, interval = numeric[:6]
        if width <= 0.0 or height <= 0.0:
            raise ValueError("Page dimensions must be positive.")
        if margin <= 0.0 or 2.0 * margin >= min(width, height):
            raise ValueError("safe_margin_mm does not fit on the page.")
        if punch <= 0.0:
            raise ValueError("center_punch_radius_mm must be positive.")
        if ruler <= 0.0 or interval <= 0.0 or interval > ruler:
            raise ValueError("Scale-ruler lengths must be positive and ordered.")
        if not -90.0 <= self.site_latitude_deg <= 90.0:
            raise ValueError("site_latitude_deg must lie between -90 and 90.")
        if not -180.0 <= self.site_longitude_deg <= 180.0:
            raise ValueError("site_longitude_deg must lie between -180 and 180.")
        if not -24.0 < self.standard_utc_offset_hours < 24.0:
            raise ValueError("standard_utc_offset_hours is invalid.")
        if self.magnitude_limit <= 0.0:
            raise ValueError("magnitude_limit must be positive.")
        for name in (
            "site_edition",
            "site_name",
            "product_identifier",
            "source_revision",
        ):
            value = str(getattr(self, name)).strip()
            if name != "source_revision" and not value:
                raise ValueError(f"{name} must not be empty.")
            object.__setattr__(self, name, value)
        object.__setattr__(self, "page_width_mm", float(width))
        object.__setattr__(self, "page_height_mm", float(height))
        object.__setattr__(self, "safe_margin_mm", float(margin))
        object.__setattr__(self, "center_punch_radius_mm", float(punch))
        object.__setattr__(self, "scale_ruler_length_mm", float(ruler))
        object.__setattr__(
            self, "scale_ruler_major_interval_mm", float(interval)
        )
        object.__setattr__(
            self, "site_latitude_deg", float(self.site_latitude_deg)
        )
        object.__setattr__(
            self, "site_longitude_deg", float(self.site_longitude_deg)
        )
        object.__setattr__(
            self,
            "standard_utc_offset_hours",
            float(self.standard_utc_offset_hours),
        )
        object.__setattr__(self, "magnitude_limit", float(self.magnitude_limit))

    def resolve(self, pair):
        """Return matched page furniture for one resolved disk pair."""
        if not isinstance(pair, PolarPlanispherePair):
            raise TypeError("pair must be a PolarPlanispherePair value.")
        if not self.source_revision:
            raise ValueError("source_revision is required for printable pages.")
        page_size = self.page_width_mm, self.page_height_mm
        center = self.page_width_mm / 2.0, self.page_height_mm / 2.0
        disk_radius = pair.south_registration.outer_radius_mm
        if not np.isclose(
            disk_radius,
            pair.north_registration.outer_radius_mm,
            atol=1.0e-12,
        ):
            raise ValueError("Paired page furniture requires equal disk radii.")
        if (
            center[0] - disk_radius < self.safe_margin_mm
            or center[0] + disk_radius
            > self.page_width_mm - self.safe_margin_mm
            or center[1] - disk_radius < self.safe_margin_mm
            or center[1] + disk_radius
            > self.page_height_mm - self.safe_margin_mm
        ):
            raise ValueError("The physical disk does not fit the safe page area.")
        if self.scale_ruler_length_mm > (
            self.page_width_mm - 2.0 * self.safe_margin_mm
        ):
            raise ValueError("The scale ruler does not fit the safe page area.")
        south = self._resolve_face(
            "south", pair.south, pair.south_registration, page_size, center
        )
        north = self._resolve_face(
            "north", pair.north, pair.north_registration, page_size, center
        )
        return PolarPagePairFurniture(south=south, north=north)

    def _resolve_face(self, face, chart, registration, page_size, center):
        marks = tuple(
            PolarPageRegistrationMark(
                identifier=identifier,
                glyph=_REGISTRATION_GLYPHS[
                    index % len(_REGISTRATION_GLYPHS)
                ],
                position_mm=_page_radial_point(
                    center,
                    angle_deg,
                    registration.outer_radius_mm * radius_fraction,
                ),
                angle_deg=angle_deg,
                radius_mm=(
                    registration.outer_radius_mm * radius_fraction
                ),
            )
            for index, (
                identifier,
                radius_fraction,
                angle_deg,
            ) in enumerate(registration.marks)
        )
        ruler_y = self.safe_margin_mm + 3.0
        ruler_start = self.safe_margin_mm + 2.0, ruler_y
        ruler = PolarPageScaleRuler(
            start_mm=ruler_start,
            end_mm=(ruler_start[0] + self.scale_ruler_length_mm, ruler_y),
            length_mm=self.scale_ruler_length_mm,
            major_interval_mm=self.scale_ruler_major_interval_mm,
            label=f"{self.scale_ruler_length_mm:g} mm scale check / escala",
        )
        return PolarFacePageFurniture(
            face=face,
            page_size_mm=page_size,
            safe_margin_mm=self.safe_margin_mm,
            disk_center_mm=center,
            disk_diameter_mm=2.0 * registration.outer_radius_mm,
            center_punch_radius_mm=self.center_punch_radius_mm,
            registration_marks=marks,
            orientation_mark_identifier=marks[0].identifier,
            scale_ruler=ruler,
            text_blocks=self._text_blocks(face, chart, center),
            product_identifier=self.product_identifier,
            source_revision=self.source_revision,
        )

    def _text_blocks(self, face, chart, center):
        page_top = self.page_height_mm - self.safe_margin_mm
        left = self.safe_margin_mm + 2.0
        right = self.page_width_mm - self.safe_margin_mm - 2.0
        offset = self.standard_utc_offset_hours
        offset_text = f"UTC{offset:+g}"
        latitude = _signed_coordinate(self.site_latitude_deg, "N", "S")
        longitude = _signed_coordinate(self.site_longitude_deg, "E", "O")
        lower, upper = sorted(
            (chart.limiting_declination_deg, chart.pole_declination_deg)
        )
        coverage = f"Declinación {lower:+g}° a {upper:+g}°"
        projection = {
            "polar_azimuthal_equidistant": (
                "Proyección azimutal equidistante polar"
            ),
            "stereographic": "Proyección estereográfica polar",
        }[chart.projection_name]
        top = (
            PolarPageTextBlock(
                role="face_identity",
                lines=(_FACE_TITLES[face],),
                position_mm=(center[0], page_top - 7.0),
            ),
            PolarPageTextBlock(
                role="rights_notice",
                lines=(
                    "ALL RIGHTS RESERVED / TODOS LOS DERECHOS RESERVADOS",
                ),
                position_mm=(center[0], page_top - 12.5),
            ),
            PolarPageTextBlock(
                role="edition_site",
                lines=(
                    f"Edición {self.site_edition} — sitio: {self.site_name}",
                    f"{latitude}, {longitude} — hora estándar {offset_text}",
                ),
                position_mm=(center[0], page_top - 18.5),
            ),
            PolarPageTextBlock(
                role="geometry",
                lines=(
                    f"{projection} — {coverage}",
                    (
                        f"Diámetro {chart.physical_diameter_mm:g} mm — "
                        f"magnitud límite {self.magnitude_limit:g}"
                    ),
                ),
                position_mm=(center[0], page_top - 27.0),
            ),
        )
        bottom = (
            PolarPageTextBlock(
                role="print_instruction",
                lines=(
                    "PRINT AT 100% / ACTUAL SIZE — DO NOT FIT TO PAGE",
                    "IMPRIMIR AL 100% / TAMAÑO REAL — NO AJUSTAR A PÁGINA",
                ),
                position_mm=(center[0], 43.0),
            ),
            PolarPageTextBlock(
                role="time_instruction",
                lines=(
                    (
                        f"Escala en hora estándar {offset_text}; horario "
                        "de verano no incorporado."
                    ),
                    (
                        "Con reloj civil UTC−3, aplique la corrección de "
                        "una hora indicada en la plantilla."
                    ),
                ),
                position_mm=(center[0], 34.0),
            ),
            PolarPageTextBlock(
                role="assembly_instruction",
                lines=(
                    "Recorte el borde; perfore el centro; pegue reverso con reverso.",
                    (
                        "Mantenga ambos títulos derechos; alinee las marcas "
                        "a contraluz."
                    ),
                ),
                position_mm=(center[0], 25.0),
            ),
            PolarPageTextBlock(
                role="face_use",
                lines=(f"Usar con la plantilla {_FACE_TITLES[face]}.",),
                position_mm=(right, 17.0),
                horizontal_alignment="right",
            ),
            PolarPageTextBlock(
                role="provenance",
                lines=(
                    self.product_identifier,
                    f"Source revision / revisión: {self.source_revision}",
                ),
                position_mm=(right, 10.0),
                horizontal_alignment="right",
            ),
            PolarPageTextBlock(
                role="ruler_caption",
                lines=("Verifique esta regla después de imprimir.",),
                position_mm=(left, 17.0),
                horizontal_alignment="left",
            ),
        )
        return top + bottom


def _page_radial_point(center, angle_deg, radius_mm):
    angle = np.deg2rad(float(angle_deg))
    return (
        float(center[0]) + float(radius_mm) * np.cos(angle),
        float(center[1]) + float(radius_mm) * np.sin(angle),
    )


def _signed_coordinate(value, positive, negative):
    direction = positive if value >= 0.0 else negative
    return f"{abs(float(value)):.6f}° {direction}"
