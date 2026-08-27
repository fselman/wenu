"""Focused structural audit of Matplotlib SVG output."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
from matplotlib.patches import Circle
import pytest

from wenu.chart_document import (
    EditPolicy,
    SemanticArtistIdentity,
    assign_canvas_semantics,
)
from wenu.charts.regional import ExportOptions
from wenu.rendering import MatplotlibRenderer
from wenu.geometry.projected import ProjectedCurve, ProjectedCurves
from wenu.sky.semantic_identity import SemanticLayerIdentity
from wenu.output_policy import SvgProvenance
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


def test_existing_export_path_produces_parseable_editable_vector_svg(
    tmp_path,
):
    destination = tmp_path / "representative-editable.svg"
    figure = _representative_figure()
    try:
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
    assert inspection.count("text") > 0
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


def test_svg_records_standard_and_wenu_provenance(tmp_path, monkeypatch):
    destination = tmp_path / "provenance.svg"
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "0")
    monkeypatch.setenv("WENU_SOURCE_REVISION", "abc1234")
    figure = _representative_figure()
    try:
        ExportOptions(
            metadata={"Title": "Existing title", "Creator": "Wenu"},
            svg_provenance=SvgProvenance(
                product_name="regional",
                title="Regional chart",
                parameters={"z": 2, "a": {"values": frozenset({"b", "a"})}},
                copyright="© Fernando Selman",
            ),
        ).save(figure, destination)
    finally:
        plt.close(figure)

    root = ET.parse(destination).getroot()
    metadata = [
        element for element in root
        if element.tag.rsplit("}", 1)[-1] == "metadata"
    ]
    assert len(metadata) == 1
    serialized = ET.tostring(metadata[0], encoding="unicode")
    assert "Existing title" in serialized
    assert "1970-01-01T00:00:00Z" in serialized
    assert "image/svg+xml" in serialized
    assert "© Fernando Selman" in serialized
    assert "abc1234" in serialized
    parameters = next(
        element for element in metadata[0].iter()
        if element.tag.rsplit("}", 1)[-1] == "parameters"
    )
    assert parameters.text == '{"a":{"values":["a","b"]},"z":2}'


def test_svg_provenance_does_not_require_semantic_artists(tmp_path):
    destination = tmp_path / "plain-provenance.svg"
    figure = _representative_figure()
    try:
        ExportOptions(
            svg_provenance=SvgProvenance(
                product_name="regional",
                parameters={"family": "regional"},
                created_utc="2026-08-27T12:00:00Z",
            ),
        ).save(figure, destination)
    finally:
        plt.close(figure)

    assert "wenu:provenance" in destination.read_text(encoding="utf-8")


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
            semantic_path=("sky", "constellations", "lines"),
            display_name="Constellation lines",
            presentation_order=50,
            style_role="constellation_lines",
        ),
    )
    try:
        ExportOptions().save(figure, destination)
    finally:
        plt.close(figure)

    serialized = destination.read_text(encoding="utf-8")

    assert 'id="wenu-layer-constellation-lines--0001"' in serialized
    assert 'id="wenu-layer-constellation-lines--0002"' in serialized
    assert [item.svg_id for item in semantic_artists] == [
        "wenu-layer-constellation-lines--0001",
        "wenu-layer-constellation-lines--0002",
    ]
    assert all(item.zorder == 2.0 for item in semantic_artists)
    assert all(
        item.edit_policy is EditPolicy.STYLE
        for item in semantic_artists
    )
    assert all(item.paint_role.name == "boundaries" for item in semantic_artists)
    assert (
        'class="wenu-semantic-artist '
        'wenu-layer-constellation-lines wenu-edit-style '
        'wenu-style-constellation-lines wenu-paint-boundaries"'
        in serialized
    )
    assert 'data-wenu-layer="constellation_lines"' in serialized
    assert 'data-wenu-edit="style"' in serialized
    assert 'data-wenu-semantic-path="sky/constellations/lines"' in serialized
    assert 'data-wenu-parent-path="sky/constellations"' in serialized
    assert 'data-wenu-display-name="Constellation lines"' in serialized
    assert 'data-wenu-presentation-order="50"' in serialized
    assert 'data-wenu-style-role="constellation_lines"' in serialized
    assert 'data-wenu-zorder="2"' in serialized
    assert 'data-wenu-paint-role="boundaries"' in serialized
    assert "data-wenu-paint-band" not in serialized
    assert "wenu-band-" not in serialized

    root = ET.parse(destination).getroot()
    by_id = {
        element.get("id"): element
        for element in root.iter()
        if element.get("id")
    }
    sky = by_id["wenu-group-sky"]
    constellations = by_id["wenu-group-sky-constellations"]
    lines = by_id["wenu-group-sky-constellations-lines"]

    assert constellations in list(sky)
    assert lines in list(constellations)
    assert [
        child.get("id") for child in lines
    ] == [
        "wenu-layer-constellation-lines--0001",
        "wenu-layer-constellation-lines--0002",
    ]
    assert sky.get(
        "{http://www.inkscape.org/namespaces/inkscape}groupmode"
    ) == "layer"
    assert lines.get(
        "{http://www.inkscape.org/namespaces/inkscape}label"
    ) == "Constellation lines"


def test_sky_groups_follow_supplied_presentation_order(tmp_path):
    destination = tmp_path / "semantic-order.svg"
    figure, ax = plt.subplots()
    galaxy = ax.plot((0.0, 1.0), (0.2, 0.2), zorder=7.0)[0]
    star = ax.plot((0.0, 1.0), (0.8, 0.8), zorder=1.0)[0]

    MatplotlibRenderer.assign_semantic_identity(
        (galaxy,),
        SemanticLayerIdentity(
            name="galaxies",
            svg_id="wenu-layer-galaxies",
            semantic_path=("sky", "galaxies"),
            display_name="Galaxies",
            presentation_order=10,
            style_role="galaxies",
        ),
    )
    MatplotlibRenderer.assign_semantic_identity(
        (star,),
        SemanticLayerIdentity(
            name="stars",
            svg_id="wenu-layer-stars",
            semantic_path=("sky", "stars", "symbols"),
            display_name="Star symbols",
            presentation_order=40,
            style_role="stars",
        ),
    )
    try:
        ExportOptions().save(figure, destination)
    finally:
        plt.close(figure)

    root = ET.parse(destination).getroot()
    sky = next(
        element
        for element in root.iter()
        if element.get("id") == "wenu-group-sky"
    )

    assert [
        child.get("data-wenu-semantic-path") for child in sky
    ] == [
        "sky/galaxies",
        "sky/stars",
    ]
    assert [
        child.get("data-wenu-presentation-order") for child in sky
    ] == ["10", "40"]


def test_constellation_entities_form_a_shallow_system_specific_group(tmp_path):
    destination = tmp_path / "constellation-entities.svg"
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)
    curves = ProjectedCurves(
        items=[
            ProjectedCurve([0.0, 1.0], [0.2, 0.3], name="Cru"),
            ProjectedCurve([0.2, 0.8], [0.4, 0.7], name="Cru"),
            ProjectedCurve([0.1, 0.9], [0.8, 0.6], name="Mus"),
        ],
        metadata={
            "semantic_entity_keys": ("cru", "cru", "mus"),
            "semantic_entity_display_names": ("Cru", "Cru", "Mus"),
        },
    )
    artists = renderer.draw(curves)
    MatplotlibRenderer.assign_semantic_identity(
        artists,
        SemanticLayerIdentity(
            name="constellation_lines",
            svg_id="western-lines",
            semantic_path=(
                "sky", "constellations", "lines_western"
            ),
            display_name="Lines-Western",
            presentation_order=50,
            style_role="constellation_lines_western",
        ),
    )
    try:
        ExportOptions().save(figure, destination)
    finally:
        plt.close(figure)

    root = ET.parse(destination).getroot()
    by_path = {
        element.get("data-wenu-semantic-path"): element
        for element in root.iter()
        if (
            element.get("data-wenu-semantic-path")
            and "wenu-semantic-group"
            in element.get("class", "").split()
        )
    }
    lines = by_path["sky/constellations/lines_western"]
    cru = by_path["sky/constellations/lines_western/cru"]
    mus = by_path["sky/constellations/lines_western/mus"]

    assert lines.get(
        "{http://www.inkscape.org/namespaces/inkscape}label"
    ) == "Lines-Western"
    assert cru.get(
        "{http://www.inkscape.org/namespaces/inkscape}label"
    ) == "Cru"
    assert mus.get(
        "{http://www.inkscape.org/namespaces/inkscape}label"
    ) == "Mus"
    assert [child.get("id") for child in cru] == [
        "western-lines-cru--0001",
        "western-lines-cru--0002",
    ]
    assert [child.get("id") for child in mus] == [
        "western-lines-mus",
    ]
    assert "sky/constellations/lines_western/western" not in by_path
    insensitive = (
        "{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}"
        "insensitive"
    )
    assert lines.get(insensitive) == "true"
    assert lines.get("data-wenu-locked") == "true"
    assert cru.get(insensitive) == "true"
    assert mus.get(insensitive) == "true"
    assert all(
        child.get("data-wenu-lock-owner-path")
        == "sky/constellations/lines_western"
        for entity in (cru, mus)
        for child in entity
    )
    assert all(
        child.get(insensitive) == "true"
        for entity in (cru, mus)
        for child in entity
    )


def test_semantic_sibling_labels_must_be_unique(tmp_path):
    destination = tmp_path / "duplicate-labels.svg"
    figure, ax = plt.subplots()
    first = ax.plot((0.0, 1.0), (0.2, 0.2))[0]
    second = ax.plot((0.0, 1.0), (0.8, 0.8))[0]
    for artist, child in ((first, "first"), (second, "second")):
        MatplotlibRenderer.assign_semantic_identity(
            (artist,),
            SemanticLayerIdentity(
                name=child,
                svg_id=f"wenu-layer-{child}",
                semantic_path=("sky", "test", child),
                display_name="Repeated",
                presentation_order=1,
            ),
        )
    try:
        with pytest.raises(ValueError, match="unique within sky/test"):
            ExportOptions().save(figure, destination)
    finally:
        plt.close(figure)


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



def test_semantic_label_group_inherits_common_font_style(tmp_path):
    destination = tmp_path / "inherited-label-font.svg"
    figure, ax = plt.subplots()
    labels = (
        ax.text(0.2, 0.4, "10:00", fontsize=7.0),
        ax.text(0.8, 0.6, "20:00", fontsize=7.0),
    )
    MatplotlibRenderer.assign_semantic_identity(
        labels,
        SemanticLayerIdentity(
            name="equatorial_grid_labels",
            svg_id="wenu-layer-equatorial-grid-labels",
            edit_policy=EditPolicy.LAYOUT,
            semantic_path=("sky", "grids", "equatorial", "labels"),
            display_name="Equatorial grid labels",
            presentation_order=70,
            style_role="equatorial_grid_labels",
        ),
    )
    try:
        ExportOptions().save(figure, destination)
    finally:
        plt.close(figure)

    root = ET.parse(destination).getroot()
    group = next(
        element
        for element in root.iter()
        if element.get("id")
        == "wenu-group-sky-grids-equatorial-labels"
    )
    text_elements = [
        element
        for element in group.iter()
        if element.tag.rsplit("}", 1)[-1] == "text"
    ]

    assert "font:" in group.get("style", "")
    assert "7px" in group.get("style", "")
    assert len(text_elements) == 2
    assert list(group) == text_elements
    assert all(
        "wenu-semantic-artist"
        in element.get("class", "").split()
        for element in text_elements
    )
    assert all(
        element.get("data-wenu-semantic-path")
        == "sky/grids/equatorial/labels"
        for element in text_elements
    )
    assert all(
        "font:" not in element.get("style", "")
        for element in text_elements
    )



def test_chart_semantics_form_a_parallel_hierarchy(tmp_path):
    destination = tmp_path / "chart-semantic-group.svg"
    figure, ax = plt.subplots()
    sky_artist = ax.plot((0.0, 1.0), (0.5, 0.5), zorder=1.0)[0]
    mask_artist = Circle(
        (0.5, 0.5),
        0.3,
        transform=ax.transAxes,
        zorder=20.0,
    )
    ax.add_patch(mask_artist)
    title_artist = ax.text(0.5, 0.9, "Chart title")
    MatplotlibRenderer.assign_semantic_identity(
        (sky_artist,),
        SemanticLayerIdentity(
            name="stars",
            svg_id="wenu-layer-stars",
            semantic_path=("sky", "stars", "symbols"),
            display_name="Star symbols",
            presentation_order=40,
            style_role="stars",
        ),
    )
    MatplotlibRenderer.assign_semantic_identity(
        (mask_artist,),
        SemanticArtistIdentity(
            name="outside_constellation_group_mask",
            svg_id="wenu-chart-outside-constellation-group-mask",
            edit_policy=EditPolicy.STYLE,
            semantic_path=(
                "chart",
                "masks_and_boundary",
                "outside_constellation_group_mask",
            ),
            display_name="Outside constellation-group mask",
            presentation_order=80,
            style_role="outside_mask",
        ),
    )
    MatplotlibRenderer.assign_semantic_identity(
        (title_artist,),
        SemanticArtistIdentity(
            name="title",
            svg_id="wenu-furniture-title",
            edit_policy=EditPolicy.LAYOUT,
            semantic_path=("furniture", "title"),
            display_name="Title",
            presentation_order=90,
            style_role="title",
        ),
    )
    try:
        ExportOptions().save(figure, destination)
    finally:
        plt.close(figure)

    root = ET.parse(destination).getroot()
    by_id = {
        element.get("id"): element
        for element in root.iter()
        if element.get("id")
    }

    assert "wenu-group-sky" in by_id
    assert "wenu-group-chart" in by_id
    assert "wenu-group-furniture" in by_id
    assert "wenu-group-furniture-title" in by_id
    assert by_id["wenu-furniture-title"].tag.endswith(
        "}text"
    )
    masks = by_id["wenu-group-chart-masks_and_boundary"]
    mask = by_id[
        "wenu-group-chart-masks_and_boundary-"
        "outside_constellation_group_mask"
    ]
    assert mask in list(masks)
    assert mask.get(
        "{http://www.inkscape.org/namespaces/inkscape}label"
    ) == "Outside constellation-group mask"
    insensitive = (
        "{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}"
        "insensitive"
    )
    assert by_id["wenu-group-chart"].get(insensitive) is None
    assert masks.get(insensitive) is None
    assert mask.get(insensitive) == "true"
    assert by_id[
        "wenu-chart-outside-constellation-group-mask"
    ].get(insensitive) == "true"
    assert by_id["wenu-group-furniture"].get(insensitive) is None



def test_canvas_semantics_group_independent_svg_parents(tmp_path):
    destination = tmp_path / "canvas-semantics.svg"
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)
    assign_canvas_semantics(renderer)
    try:
        ExportOptions().save(figure, destination)
    finally:
        plt.close(figure)

    root = ET.parse(destination).getroot()
    by_id = {
        element.get("id"): element
        for element in root.iter()
        if element.get("id")
    }

    assert "wenu-group-page" in by_id
    assert "wenu-group-page-background" in by_id
    assert "page-background" in by_id
    assert "wenu-group-sky-background" in by_id
    assert "sky-background" in by_id
    frame = by_id[
        "wenu-group-chart-masks_and_boundary-"
        "rectangular_viewport_frame"
    ]
    assert len(list(frame)) == 4
    assert {
        child.get("id") for child in frame
    } == {
        "viewport-frame--0001",
        "viewport-frame--0002",
        "viewport-frame--0003",
        "viewport-frame--0004",
    }
