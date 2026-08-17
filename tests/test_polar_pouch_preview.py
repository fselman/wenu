"""Diagnostic canonical-disk composition behind pouch markings."""

import numpy as np
import pytest

from wenu import (
    PolarPageFurnitureRequest,
    PolarPlanispherePairRequest,
    PolarPouchSheetRequest,
    compose_polar_pouch_preview,
    compose_polar_pouch_sheet_preview,
)

from test_polar_pouch_rendering import pouches


def pages():
    return PolarPageFurnitureRequest(source_revision="test").resolve(
        PolarPlanispherePairRequest().resolve()
    )


def test_preview_registers_faded_disk_and_preserves_black_pouch_marks():
    disk = np.ones((594, 420, 3), dtype=float)
    pouch = np.ones_like(disk)
    disk[296:299, 209:212] = 0.0
    pouch[20, 20] = 0.0

    result = compose_polar_pouch_preview(
        disk,
        pouch,
        page_face=pages().south,
        pouch_face=pouches().south,
        disk_opacity=0.2,
    )

    assert result.shape == disk.shape
    assert result[204:207, 209:212].min() == pytest.approx(0.8)
    assert result[20, 20].max() == pytest.approx(0.0)
    assert result[297, 210].min() == pytest.approx(1.0)


def test_preview_validates_faces_images_and_opacity():
    image = np.ones((20, 20, 3), dtype=float)
    page = pages().south
    pouch = pouches().south

    with pytest.raises(ValueError, match="faces must match"):
        compose_polar_pouch_preview(
            image,
            image,
            page_face=pages().north,
            pouch_face=pouch,
        )
    with pytest.raises(ValueError, match="must match"):
        compose_polar_pouch_preview(
            image,
            image[:10],
            page_face=page,
            pouch_face=pouch,
        )
    with pytest.raises(ValueError, match="disk_opacity"):
        compose_polar_pouch_preview(
            image,
            image,
            page_face=page,
            pouch_face=pouch,
            disk_opacity=1.1,
        )


def test_preview_service_is_public():
    import wenu

    assert "compose_polar_pouch_preview" in wenu.__all__


def test_sheet_preview_places_south_above_and_inverted_north_below():
    disk_south = np.ones((594, 420, 3), dtype=float)
    disk_north = np.ones_like(disk_south)
    pouch = np.ones_like(disk_south)
    disk_south[296:299, 209:212] = 0.0
    disk_north[296:299, 209:212] = 0.0
    sheet = PolarPouchSheetRequest().resolve(pouches())

    result = compose_polar_pouch_sheet_preview(
        (disk_south, disk_north),
        pouch,
        pages=pages(),
        sheet=sheet,
        disk_opacity=0.2,
    )

    assert result[100:103, 209:212].min() == pytest.approx(0.8)
    assert result[492:495, 209:212].min() == pytest.approx(0.8)


def test_sheet_preview_applies_date_hour_rotation_about_disk_center():
    disk_south = np.ones((594, 420, 3), dtype=float)
    disk_north = np.ones_like(disk_south)
    pouch = np.ones_like(disk_south)
    disk_south[296:299, 229:232] = 0.0
    sheet = PolarPouchSheetRequest().resolve(pouches())

    result = compose_polar_pouch_sheet_preview(
        (disk_south, disk_north),
        pouch,
        pages=pages(),
        sheet=sheet,
        disk_opacity=0.2,
        disk_rotation_deg=(90.0, 0.0),
    )

    assert result[80:83, 209:212].min() == pytest.approx(0.8)
