"""Diagnostic composition of canonical disks behind polar-pouch marks."""

from __future__ import annotations

import numpy as np

from wenu.charts.polar_page_furniture import (
    PolarFacePageFurniture,
    PolarPagePairFurniture,
)
from wenu.charts.polar_pouch_furniture import PolarPouchFaceFurniture
from wenu.charts.polar_pouch_sheet import PolarPouchSheetFurniture


def compose_polar_pouch_preview(
    disk_image,
    pouch_image,
    *,
    page_face,
    pouch_face,
    disk_opacity=0.18,
):
    """Return one faded, registered disk beneath opaque pouch markings."""
    if not isinstance(page_face, PolarFacePageFurniture):
        raise TypeError("page_face must be a PolarFacePageFurniture value.")
    if not isinstance(pouch_face, PolarPouchFaceFurniture):
        raise TypeError("pouch_face must be a PolarPouchFaceFurniture value.")
    if page_face.face != pouch_face.face:
        raise ValueError("Disk page and pouch faces must match.")
    opacity = float(disk_opacity)
    if not 0.0 <= opacity <= 1.0:
        raise ValueError("disk_opacity must lie between zero and one.")
    disk = _rgb_image(disk_image, name="disk_image")
    pouch = _rgb_image(pouch_image, name="pouch_image")
    if disk.shape != pouch.shape:
        raise ValueError("Disk and pouch diagnostic images must match.")

    height_px, width_px, _ = disk.shape
    page_width, page_height = pouch_face.page_size_mm
    x_per_mm = width_px / page_width
    y_per_mm = height_px / page_height
    source_center = _pixel_center(
        page_face.disk_center_mm,
        page_height,
        x_per_mm,
        y_per_mm,
    )
    target_center = _pixel_center(
        pouch_face.disk_center_mm,
        page_height,
        x_per_mm,
        y_per_mm,
    )
    shift_x = int(round(target_center[0] - source_center[0]))
    shift_y = int(round(target_center[1] - source_center[1]))

    rows, columns = np.indices((height_px, width_px))
    radius_x = pouch_face.disk_radius_mm * x_per_mm
    radius_y = pouch_face.disk_radius_mm * y_per_mm
    disk_mask = (
        ((columns - target_center[0]) / radius_x) ** 2
        + ((rows - target_center[1]) / radius_y) ** 2
        <= 1.0
    )
    source_rows = rows - shift_y
    source_columns = columns - shift_x
    valid = (
        disk_mask
        & (source_rows >= 0)
        & (source_rows < height_px)
        & (source_columns >= 0)
        & (source_columns < width_px)
    )
    registered = np.ones_like(disk)
    registered[valid] = disk[source_rows[valid], source_columns[valid]]
    background = np.ones_like(disk)
    background[disk_mask] = (
        (1.0 - opacity) + opacity * registered[disk_mask]
    )
    return np.clip(background * pouch, 0.0, 1.0)


def compose_polar_pouch_sheet_preview(
    disk_images,
    pouch_image,
    *,
    pages,
    sheet,
    disk_opacity=0.18,
    disk_rotation_deg=(0.0, 0.0),
):
    """Return both canonical disks faded behind one imposed pouch sheet."""
    if not isinstance(pages, PolarPagePairFurniture):
        raise TypeError("pages must be a PolarPagePairFurniture value.")
    if not isinstance(sheet, PolarPouchSheetFurniture):
        raise TypeError("sheet must be a PolarPouchSheetFurniture value.")
    opacity = float(disk_opacity)
    if not 0.0 <= opacity <= 1.0:
        raise ValueError("disk_opacity must lie between zero and one.")
    disks = tuple(_rgb_image(value, name="disk_image") for value in disk_images)
    if len(disks) != 2:
        raise ValueError("disk_images must contain south and north images.")
    pouch = _rgb_image(pouch_image, name="pouch_image")
    if any(disk.shape != pouch.shape for disk in disks):
        raise ValueError("Disk and pouch diagnostic images must match.")
    rotations = tuple(float(value) for value in disk_rotation_deg)
    if len(rotations) != 2 or not np.all(np.isfinite(rotations)):
        raise ValueError("disk_rotation_deg must contain two finite values.")
    height_px, width_px, _ = pouch.shape
    page_width, page_height = sheet.page_size_mm
    x_per_mm = width_px / page_width
    y_per_mm = height_px / page_height
    rows, columns = np.indices((height_px, width_px))
    target_x = columns / x_per_mm
    target_y = page_height - rows / y_per_mm
    background = np.ones_like(pouch)
    for disk, page, placement, disk_rotation in zip(
        disks, pages.faces, sheet.placements, rotations, strict=True
    ):
        if placement.rotation_deg == 0.0:
            source_x = target_x - placement.translation_mm[0]
            source_y = target_y - placement.translation_mm[1]
        elif placement.rotation_deg == 180.0:
            source_x = placement.translation_mm[0] - target_x
            source_y = placement.translation_mm[1] - target_y
        else:
            raise ValueError("Only zero- and 180-degree placements are valid.")
        angle = np.deg2rad(disk_rotation)
        delta_x = source_x - placement.face_disk_center_mm[0]
        delta_y = source_y - placement.face_disk_center_mm[1]
        rotated_source_x = (
            page.disk_center_mm[0]
            + np.cos(angle) * delta_x
            + np.sin(angle) * delta_y
        )
        rotated_source_y = (
            page.disk_center_mm[1]
            - np.sin(angle) * delta_x
            + np.cos(angle) * delta_y
        )
        source_columns = np.rint(rotated_source_x * x_per_mm).astype(int)
        source_rows = np.rint(
            (page_height - rotated_source_y) * y_per_mm
        ).astype(int)
        radius = page.disk_radius_mm
        disk_mask = (
            delta_x**2
            + delta_y**2
            <= radius**2
        )
        left, bottom, right, top = placement.clip_bounds_mm
        panel_mask = (
            (target_x >= left)
            & (target_x <= right)
            & (target_y >= bottom)
            & (target_y <= top)
        )
        valid = (
            disk_mask
            & panel_mask
            & (source_rows >= 0)
            & (source_rows < height_px)
            & (source_columns >= 0)
            & (source_columns < width_px)
        )
        sampled = np.ones_like(disk)
        sampled[valid] = disk[source_rows[valid], source_columns[valid]]
        background[valid] = (
            (1.0 - opacity) + opacity * sampled[valid]
        )
    return np.clip(background * pouch, 0.0, 1.0)


def _rgb_image(value, *, name):
    image = np.asarray(value, dtype=float)
    if image.ndim != 3 or image.shape[2] not in (3, 4):
        raise ValueError(f"{name} must be one RGB or RGBA image.")
    if image.shape[2] == 4:
        alpha = image[..., 3:4]
        image = image[..., :3] * alpha + (1.0 - alpha)
    if image.size and np.nanmax(image) > 1.0:
        image = image / 255.0
    if not np.all(np.isfinite(image)):
        raise ValueError(f"{name} must contain only finite values.")
    return np.clip(image, 0.0, 1.0)


def _pixel_center(position_mm, page_height_mm, x_per_mm, y_per_mm):
    return (
        float(position_mm[0]) * x_per_mm,
        (float(page_height_mm) - float(position_mm[1])) * y_per_mm,
    )
