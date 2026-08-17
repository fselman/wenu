"""Single-A4 imposition and export of the folded polar pouch."""

import numpy as np
import pytest

from wenu import (
    PolarPouchSheetExportResult,
    PolarPouchSheetRequest,
    PolarPouchSheetRendering,
    draw_polar_pouch_sheet,
    export_polar_pouch_sheet,
)
from wenu.charts.regional import ExportOptions

from test_polar_pouch_rendering import pouches


def resolved_sheet():
    value = pouches()
    return value, PolarPouchSheetRequest().resolve(value)


def test_sheet_places_top_south_and_inverted_bottom_north_around_spine():
    _, sheet = resolved_sheet()

    assert sheet.page_size_mm == pytest.approx((210.0, 297.0))
    assert sheet.lower_fold_y_mm == pytest.approx(148.0)
    assert sheet.upper_fold_y_mm == pytest.approx(149.0)
    assert sheet.spine_width_mm == pytest.approx(1.0)
    assert sheet.panel_depth_mm == pytest.approx(148.0)
    assert sheet.disk_protrusion_mm == pytest.approx(47.0)
    assert sheet.south.rotation_deg == pytest.approx(0.0)
    assert sheet.south.translation_mm == pytest.approx((0.0, 52.0))
    assert sheet.south.face_disk_center_mm == pytest.approx((105.0, 194.5))
    assert sheet.north.rotation_deg == pytest.approx(180.0)
    assert sheet.north.translation_mm == pytest.approx((210.0, 245.0))
    assert sheet.north.face_disk_center_mm == pytest.approx((105.0, 194.5))
    assert sheet.south.clip_bounds_mm == pytest.approx((0, 149, 210, 297))
    assert sheet.north.clip_bounds_mm == pytest.approx((0, 0, 210, 148))


def test_sheet_renderer_preserves_vector_faces_and_distinct_fold_lines():
    pouches_value, sheet = resolved_sheet()
    result = draw_polar_pouch_sheet(sheet, pouches_value)
    try:
        assert isinstance(result, PolarPouchSheetRendering)
        assert result.page_axes.get_xlim() == pytest.approx((0.0, 210.0))
        assert result.page_axes.get_ylim() == pytest.approx((0.0, 297.0))
        fold_y = []
        for line in result.fold_lines:
            source = np.column_stack((line.get_xdata(), line.get_ydata()))
            display = line.get_transform().transform(source)
            imposed = result.page_axes.transData.inverted().transform(display)
            fold_y.append(float(np.mean(imposed[:, 1])))
        assert tuple(fold_y) == pytest.approx((149.0, 148.0))
        assert all(
            label.get_rotation() == pytest.approx(180.0)
            for label in result.north.labels
            if label.get_text() in {"W", "N", "E"}
        )
        assert all(
            90.0 <= label.get_rotation() <= 270.0
            for label in result.north.hour_labels
        )
        assert result.north.magnitude_scale.title.get_rotation() == (
            pytest.approx(180.0)
        )
        assert all(
            label.get_rotation() == pytest.approx(180.0)
            for label in result.north.magnitude_scale.labels
        )
    finally:
        import matplotlib.pyplot as plt

        plt.close(result.page_axes.figure)


def test_single_sheet_export_saves_one_exact_a4_product(monkeypatch, tmp_path):
    calls = []

    def fake_save(self, figure, path):
        calls.append((self, figure, path))
        return path

    monkeypatch.setattr(ExportOptions, "save", fake_save)
    pouches_value, sheet = resolved_sheet()
    output = tmp_path / "pouch.pdf"
    result = export_polar_pouch_sheet(
        sheet,
        pouches_value,
        output,
        source_revision="test",
    )

    assert isinstance(result, PolarPouchSheetExportResult)
    assert result.output == output
    assert len(calls) == 1
    assert calls[0][1].get_size_inches() == pytest.approx(
        (210.0 / 25.4, 297.0 / 25.4)
    )
    assert calls[0][0].bbox_inches is None


def test_sheet_request_and_public_contracts_are_validated():
    with pytest.raises(ValueError, match="spine_width_mm"):
        PolarPouchSheetRequest(spine_width_mm=0.0)
    with pytest.raises(TypeError, match="pouches"):
        PolarPouchSheetRequest().resolve(object())

    import wenu

    for name in (
        "PolarPouchPanelPlacement",
        "PolarPouchSheetFurniture",
        "PolarPouchSheetRequest",
        "PolarPouchSheetRendering",
        "draw_polar_pouch_sheet",
        "PolarPouchSheetExportResult",
        "export_polar_pouch_sheet",
        "compose_polar_pouch_sheet_preview",
    ):
        assert name in wenu.__all__
