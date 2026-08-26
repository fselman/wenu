"""Focused structural audit of Matplotlib SVG output."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import pytest

from wenu.charts.regional import ExportOptions
from wenu.rendering import MatplotlibRenderer
from wenu.sky.semantic_identity import SemanticLayerIdentity
from svg_inspection import inspect_svg


POINTS_PER_INCH = 72.0
MM_PER_INCH = 25.4


def _representative_figure(*, figsize=(4.0, 3.0)):
    figure, ax = plt.subplots(figsize=figsize)
    boundary = Circle((0.5, 0.5), 0.42, transform=ax.transAxes)
    line = ax.plot((0.0, 1.0), (0.2, 0.8), label="reference")[0]
    line.set_clip_path(boundary)
    ax.add_patch(
        Circle(
            (0.5, 0.5),
            0.42,
            transform=ax.transAxes,
            fill=False,
        )
    )
    ax.text(0.5, 0.55, "Cielo austral", ha="center")
    ax.legend()
    return figure


@pytest.mark.parametrize(
    ("fonttype", "expected_text"),
    (("none", True), ("path", False)),
)
def test_existing_export_path_produces_parseable_vector_svg(
    tmp_path,
    fonttype,
    expected_text,
):
    destination = tmp_path / f"representative-{fonttype}.svg"
    figure = _representative_figure()
    try:
        with matplotlib.rc_context({"svg.fonttype": fonttype}):
            ExportOptions(
                transparent=True,
                metadata={
                    "Title": "Wenu SVG structural audit",
                    "Creator": "Wenu",
                },
            ).save(figure, destination)
    finally:
        plt.close(figure)

    inspection = inspect_svg(destination)

    assert inspection.has_svg_root
    assert inspection.width.unit == "pt"
    assert inspection.height.unit == "pt"
    assert inspection.view_box[2:] == pytest.approx(
        (inspection.width.value, inspection.height.value)
    )
    assert inspection.count("clipPath") >= 1
    assert (inspection.count("text") > 0) is expected_text
    assert inspection.count("path") > 0
    assert inspection.count("metadata") == 1
    assert not inspection.has_raster_images



def test_svg_translates_pdf_subject_to_description(tmp_path):
    destination = tmp_path / "metadata.svg"
    figure = _representative_figure()
    try:
        ExportOptions(
            metadata={
                "Title": "Physical polar page",
                "Creator": "Wenu",
                "Subject": "Source revision 918b4bd",
            },
        ).save(figure, destination)
    finally:
        plt.close(figure)

    serialized = destination.read_text(encoding="utf-8")

    assert "<dc:description>Source revision 918b4bd</dc:description>" in (
        serialized
    )


def test_non_svg_export_preserves_subject_metadata(tmp_path):
    class RecordingFigure:
        def __init__(self):
            self.path = None
            self.kwargs = None

        def savefig(self, path, **kwargs):
            self.path = path
            self.kwargs = kwargs

    figure = RecordingFigure()
    destination = tmp_path / "physical-page.pdf"

    ExportOptions(
        metadata={"Subject": "Source revision 918b4bd"},
    ).save(figure, destination)

    assert figure.path == destination
    assert figure.kwargs["metadata"] == {
        "Subject": "Source revision 918b4bd"
    }

def test_non_tight_export_preserves_requested_physical_page(tmp_path):
    destination = tmp_path / "a4-page.svg"
    page_mm = (210.0, 297.0)
    figsize = tuple(value / MM_PER_INCH for value in page_mm)
    figure = _representative_figure(figsize=figsize)
    try:
        ExportOptions(
            bbox_inches=None,
            transparent=False,
            facecolor="white",
        ).save(figure, destination)
    finally:
        plt.close(figure)

    inspection = inspect_svg(destination)
    expected_points = tuple(
        value * POINTS_PER_INCH / MM_PER_INCH for value in page_mm
    )

    assert inspection.width.unit == "pt"
    assert inspection.height.unit == "pt"
    assert inspection.width.value == pytest.approx(
        expected_points[0], abs=0.01
    )
    assert inspection.height.value == pytest.approx(
        expected_points[1], abs=0.01
    )
    assert inspection.view_box == pytest.approx(
        (0.0, 0.0, *expected_points), abs=0.01
    )


def test_inspection_reports_embedded_raster_payload(tmp_path):
    destination = tmp_path / "raster.svg"
    destination.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg"
        width="10pt" height="20pt" viewBox="0 0 10 20">
        <image href="data:image/png;base64,AA==" />
        </svg>""",
        encoding="utf-8",
    )

    inspection = inspect_svg(destination)

    assert inspection.count("image") == 1
    assert inspection.has_raster_images
    assert inspection.raster_image_references == (
        "data:image/png;base64,AA==",
    )


@pytest.mark.parametrize(
    ("attribute", "value", "message"),
    (
        ("width", "", "width"),
        ("height", "wrong", "height"),
        ("viewBox", "0 0 10", "viewBox"),
    ),
)
def test_inspection_rejects_missing_structural_dimensions(
    tmp_path,
    attribute,
    value,
    message,
):
    attributes = {
        "width": "10pt",
        "height": "20pt",
        "viewBox": "0 0 10 20",
    }
    attributes[attribute] = value
    destination = tmp_path / "invalid.svg"
    destination.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" '
        + " ".join(
            f'{name}="{item}"'
            for name, item in attributes.items()
            if item
        )
        + " />",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=message):
        inspect_svg(destination)


def test_matplotlib_semantic_anchors_survive_svg_serialization(tmp_path):
    destination = tmp_path / "semantic-anchors.svg"
    figure, ax = plt.subplots()
    artists = ax.plot(
        (0.0, 1.0),
        (0.25, 0.75),
        color="black",
    ) + ax.plot(
        (0.0, 1.0),
        (0.75, 0.25),
        color="gray",
    )
    semantic_artists = MatplotlibRenderer.assign_semantic_identity(
        artists,
        SemanticLayerIdentity(
            name="constellation_lines",
            svg_id="wenu-layer-constellation-lines",
        ),
    )
    try:
        ExportOptions().save(figure, destination)
    finally:
        plt.close(figure)

    serialized = destination.read_text(encoding="utf-8")

    assert 'id="wenu-layer-constellation-lines--artist-0001"' in serialized
    assert 'id="wenu-layer-constellation-lines--artist-0002"' in serialized
    assert [item.svg_id for item in semantic_artists] == [
        "wenu-layer-constellation-lines--artist-0001",
        "wenu-layer-constellation-lines--artist-0002",
    ]
    assert all(item.zorder == 2.0 for item in semantic_artists)
    assert all(item.paint_role.name == "boundaries" for item in semantic_artists)
    assert all(
        item.paint_role.band.name == "structure"
        for item in semantic_artists
    )
    assert (
        'class="wenu-semantic-artist '
        'wenu-layer-constellation-lines '
        'wenu-paint-boundaries wenu-band-structure"'
        in serialized
    )
    assert 'data-wenu-layer="constellation_lines"' in serialized
    assert 'data-wenu-zorder="2"' in serialized
    assert 'data-wenu-paint-role="boundaries"' in serialized
    assert 'data-wenu-paint-band="structure"' in serialized


def test_svg_annotation_is_noop_without_wenu_semantics(tmp_path):
    destination = tmp_path / "plain.svg"
    figure = _representative_figure()
    try:
        ExportOptions().save(figure, destination)
    finally:
        plt.close(figure)

    serialized = destination.read_text(encoding="utf-8")

    assert "data-wenu-" not in serialized
    assert "wenu-semantic-artist" not in serialized
