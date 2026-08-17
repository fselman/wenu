"""Physical A4 information geometry for paired classroom disks."""

from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from wenu import (
    PolarPageFurnitureRequest,
    PolarPagePairFurniture,
    PolarPlanispherePairRequest,
)


SOURCE_REVISION = "28c37ba"


def page_furniture(**options):
    request = PolarPageFurnitureRequest(
        source_revision=SOURCE_REVISION,
        **options,
    )
    return request.resolve(PolarPlanispherePairRequest().resolve())


def test_default_request_resolves_matched_actual_size_a4_faces():
    furniture = page_furniture()

    assert isinstance(furniture, PolarPagePairFurniture)
    assert furniture.faces == (furniture.south, furniture.north)
    assert tuple(face.face for face in furniture.faces) == (
        "south",
        "north",
    )
    for face in furniture.faces:
        assert face.page_size_mm == pytest.approx((210.0, 297.0))
        assert face.disk_center_mm == pytest.approx((105.0, 148.5))
        assert face.disk_diameter_mm == pytest.approx(195.0)
        assert face.center_punch_radius_mm == pytest.approx(1.0)
        assert face.product_identifier.startswith("Wenu polar planisphere")
        assert face.source_revision == SOURCE_REVISION
        assert face.safe_margin_mm == pytest.approx(5.0)
        assert face.disk_center_mm[0] - face.disk_radius_mm >= 5.0
        assert face.disk_center_mm[0] + face.disk_radius_mm <= 205.0


def test_information_blocks_cover_the_print_and_classroom_contract():
    furniture = page_furniture()
    south = furniture.south
    north = furniture.north
    roles = {
        "face_identity",
        "rights_notice",
        "edition_site",
        "geometry",
        "print_instruction",
        "time_instruction",
        "assembly_instruction",
        "face_use",
        "provenance",
        "ruler_caption",
    }

    assert {block.role for block in south.text_blocks} == roles
    assert {block.role for block in north.text_blocks} == roles
    south_text = "\n".join(
        line for block in south.text_blocks for line in block.lines
    )
    north_text = "\n".join(
        line for block in north.text_blocks for line in block.lines
    )
    assert "SOUTH / SUR" in south_text
    assert "NORTH / NORTE" in north_text
    for text in (south_text, north_text):
        assert "La Ligua/Papudo" in text
        assert "32.443342° S" in text
        assert "71.230289° O" in text
        assert "UTC-4" in text
        assert "horario de verano no incorporado" in text
        assert "magnitud límite 5" in text
        assert "195 mm" in text
        assert "100% / ACTUAL SIZE" in text
        assert "NO AJUSTAR A PÁGINA" in text
        assert "ALL RIGHTS RESERVED" in text
        assert "TODOS LOS DERECHOS RESERVADOS" in text
        assert "perfore el centro" in text
        assert "reverso con reverso" in text
        assert SOURCE_REVISION in text
    assert "Declinación -90° a +20°" in south_text
    assert "Declinación -20° a +90°" in north_text


def test_top_information_group_is_lowered_inside_the_safe_page():
    furniture = page_furniture()

    for face in furniture.faces:
        blocks = {block.role: block for block in face.text_blocks}
        assert blocks["face_identity"].position_mm == pytest.approx(
            (105.0, 285.0)
        )
        assert blocks["rights_notice"].position_mm == pytest.approx(
            (105.0, 279.5)
        )
        assert blocks["edition_site"].position_mm == pytest.approx(
            (105.0, 273.5)
        )
        assert blocks["geometry"].position_mm == pytest.approx(
            (105.0, 265.0)
        )


def test_all_text_anchors_remain_outside_the_disk_and_inside_safe_page():
    furniture = page_furniture()

    for face in furniture.faces:
        center = np.asarray(face.disk_center_mm)
        for block in face.text_blocks:
            position = np.asarray(block.position_mm)
            assert face.safe_margin_mm <= position[0] <= (
                face.page_width_mm - face.safe_margin_mm
            )
            assert face.safe_margin_mm <= position[1] <= (
                face.page_height_mm - face.safe_margin_mm
            )
            assert np.linalg.norm(position - center) > face.disk_radius_mm


def test_scale_ruler_has_exact_physical_length_and_safe_position():
    furniture = page_furniture()

    for face in furniture.faces:
        ruler = face.scale_ruler
        delta = np.asarray(ruler.end_mm) - np.asarray(ruler.start_mm)
        assert np.linalg.norm(delta) == pytest.approx(50.0)
        assert ruler.length_mm == pytest.approx(50.0)
        assert ruler.major_interval_mm == pytest.approx(10.0)
        assert ruler.label == "50 mm scale check / escala"
        for point in (ruler.start_mm, ruler.end_mm):
            assert face.safe_margin_mm <= point[0] <= (
                face.page_width_mm - face.safe_margin_mm
            )
            assert face.safe_margin_mm <= point[1] <= (
                face.page_height_mm - face.safe_margin_mm
            )


def test_both_pages_share_one_resolved_polar_magnitude_scale():
    furniture = page_furniture()

    assert furniture.south.magnitude_scale is furniture.north.magnitude_scale
    assert len(furniture.south.magnitude_scale.bright_entries) == 4
    assert len(furniture.south.magnitude_scale.ordinary_entries) == 5
    for face in furniture.faces:
        assert face.magnitude_scale.limiting_magnitude == pytest.approx(5.0)
        assert face.magnitude_scale_placement.title_position_mm[1] > (
            face.disk_center_mm[1] + face.disk_radius_mm
        )


def test_registration_marks_coincide_after_upright_back_to_back_assembly():
    pair = PolarPlanispherePairRequest().resolve()
    furniture = PolarPageFurnitureRequest(
        source_revision=SOURCE_REVISION
    ).resolve(pair)
    south = furniture.south
    north = furniture.north

    assert len(south.registration_marks) == len(
        pair.south_registration.marks
    )
    assert tuple(mark.identifier for mark in south.registration_marks) == (
        tuple(mark.identifier for mark in north.registration_marks)
    )
    assert tuple(mark.glyph for mark in south.registration_marks) == (
        "triangle",
        "circle",
        "square",
    )
    assert south.orientation_mark_identifier == "registration_1"
    assert north.orientation_mark_identifier == "registration_1"
    for south_mark, north_mark in zip(
        south.registration_marks,
        north.registration_marks,
        strict=True,
    ):
        assert north_mark.position_mm[0] == pytest.approx(
            north.page_width_mm - south_mark.position_mm[0]
        )
        assert north_mark.position_mm[1] == pytest.approx(
            south_mark.position_mm[1]
        )
        assert north_mark.angle_deg == pytest.approx(
            (180.0 - south_mark.angle_deg) % 360.0
        )


def test_request_requires_provenance_and_rejects_pages_that_do_not_fit():
    pair = PolarPlanispherePairRequest().resolve()

    with pytest.raises(ValueError, match="source_revision"):
        PolarPageFurnitureRequest().resolve(pair)
    with pytest.raises(ValueError, match="does not fit"):
        PolarPageFurnitureRequest(
            page_width_mm=200.0,
            source_revision=SOURCE_REVISION,
        ).resolve(pair)
    with pytest.raises(ValueError, match="scale ruler"):
        PolarPageFurnitureRequest(
            scale_ruler_length_mm=205.0,
            source_revision=SOURCE_REVISION,
        ).resolve(pair)
    with pytest.raises(TypeError, match="pair"):
        PolarPageFurnitureRequest(
            source_revision=SOURCE_REVISION
        ).resolve(object())


def test_request_is_immutable_configurable_and_public():
    request = PolarPageFurnitureRequest(
        site_edition="Papudo",
        site_name="Papudo",
        site_latitude_deg=-32.507,
        site_longitude_deg=-71.448,
        source_revision="abcdef0",
    )
    pair = request.resolve(PolarPlanispherePairRequest().resolve())
    text = "\n".join(
        line for block in pair.south.text_blocks for line in block.lines
    )

    assert "Edición Papudo" in text
    assert "32.507000° S" in text
    assert "71.448000° O" in text
    with pytest.raises(FrozenInstanceError):
        request.site_name = "La Ligua"

    import wenu

    for name in (
        "PolarFacePageFurniture",
        "PolarPageFurnitureRequest",
        "PolarPagePairFurniture",
        "PolarPageRegistrationMark",
        "PolarPageScaleRuler",
        "PolarPageTextBlock",
    ):
        assert name in wenu.__all__
