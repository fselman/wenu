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
    assign_furniture_semantics,
)
from wenu.charts.footer_furniture import ChartFooterRendering
from wenu.charts.regional import ExportOptions
from wenu.rendering import MatplotlibRenderer
from wenu.geometry.projected import ProjectedCurve, ProjectedCurves
from wenu.sky.semantic_identity import SemanticLayerIdentity
from wenu.output_policy import SvgProvenance
from svg_inspection import inspect_svg


POINTS_PER_INCH = 72.0
MM_PER_INCH = 25.4


def _star_area_analyzer():
    import importlib.util
    from pathlib import Path
    filename = Path(__file__).parents[1] / "tools/analyze_atlas_star_areas.py"
    spec = importlib.util.spec_from_file_location("atlas_star_area_analysis", filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_svg_star_area_analysis_measures_references_transforms_and_clipping(tmp_path):
    import math
    analyzer = _star_area_analyzer()
    source = tmp_path / "chart-01.svg"
    source.write_text('''<svg xmlns="http://www.w3.org/2000/svg"
        xmlns:xlink="http://www.w3.org/1999/xlink"
        width="100mm" height="100mm" viewBox="0 0 100 100">
      <defs><path id="triangle" d="M0 0 L1 0 L0 1 Z"/>
        <clipPath id="window"><rect width="60" height="60"/></clipPath></defs>
      <g data-wenu-semantic-path="sky/stars/symbols" clip-path="url(#window)">
        <g transform="translate(10 20) scale(2 3)"><use xlink:href="#triangle"/></g>
        <circle cx="30" cy="30" r="2"/>
        <circle cx="59" cy="30" r="2"/>
        <circle cx="70" cy="30" r="2"/>
        <circle cx="20" cy="20" r="0"/>
        <g display="none"><circle r="10"/></g>
        <g data-wenu-paint-role="variable_stars"><circle cx="30" cy="30" r="4"/></g>
      </g>
      <g data-wenu-semantic-path="furniture/legends/stars"><circle r="8"/></g>
    </svg>''')
    records = analyzer.read_star_markers(source)
    assert len(records) == 3
    assert [row['area_mm2'] for row in records] == pytest.approx([3, 4*math.pi, 4*math.pi])
    assert records[0]['x_mm'] == pytest.approx(11)
    assert records[0]['y_mm'] == pytest.approx(21.5)
    # Unsupported editor geometry must not silently produce wrong areas.
    source.write_text(source.read_text().replace('M0 0 L1 0 L0 1 Z', 'M0 0 A1 1 0 0 0 1 1 Z'))
    with pytest.raises(ValueError, match='Unsupported SVG path command'):
        analyzer.read_star_markers(source)


def test_svg_star_area_analysis_matches_actual_matplotlib_marker_scaling(tmp_path):
    import math
    analyzer = _star_area_analyzer()
    areas = []
    for diameter_scale in (1, 2):
        figure, ax = plt.subplots(figsize=(3, 2))
        try:
            artist = ax.scatter([0, 0.5, 0.75], [0, 0.5, 0.75],
                                s=[16*diameter_scale**2, 64*diameter_scale**2, 0])
            artist.set_gid('measured-stars')
            from wenu.svg_document import attach_semantic_svg_metadata
            attach_semantic_svg_metadata(artist, layer='stars', zorder=5,
                paint_role=None, edit_policy=EditPolicy.STYLE,
                semantic_path=('sky', 'stars', 'symbols'),
                lock_owner_path=('sky', 'stars'), display_name='Stars',
                presentation_order=40, style_role='stars')
            filename = ExportOptions(bbox_inches=None).save(figure,
                tmp_path / f'chart-{diameter_scale:02d}.svg')
        finally:
            plt.close(figure)
        records = analyzer.read_star_markers(filename)
        assert len(records) == 2
        areas.append([row['area_mm2'] for row in records])
    assert areas[0] == pytest.approx([math.pi*4*(25.4/72)**2,
                                    math.pi*16*(25.4/72)**2], rel=0.001)
    assert areas[1] == pytest.approx([value*4 for value in areas[0]], rel=1e-5)
    # Directory selection ignores reports; repeated explicit inputs are not counted twice.
    (tmp_path / 'chart-01_report.svg').write_text('<invalid-report/>')
    summary = analyzer.analyze([tmp_path, tmp_path/'chart-01.svg'], tmp_path/'areas_v1', bins=8)
    assert summary['star_appearances'] == 4
    import csv
    with (tmp_path/'areas_v1_bins.csv').open() as output:
        bins = list(csv.DictReader(output))
    assert sum(int(row['count']) for row in bins) == 4
    assert any(row['log10_count'] == '' for row in bins)
    assert all((tmp_path/f'areas_v1.{extension}').exists() for extension in ('png', 'pdf', 'svg'))
    with pytest.raises(ValueError, match='filenames must be new'):
        analyzer.analyze([tmp_path/'chart-01.svg'], tmp_path/'areas_v1')


@pytest.mark.parametrize('algorithm', ['legacy', 'asinh', 'quadratic'])
def test_svg_star_area_magnitude_guides_follow_manifest_scale_and_faint_plateau(tmp_path, algorithm):
    import hashlib
    import json
    import numpy as np
    from wenu.charts.presets import AtlasChartStyle
    from wenu.charts.style_components import StellarMagnitudeSizing
    from wenu.charts.style_overrides import ChartStyleOverrides
    from wenu.charts import stellar_sizing_report
    from dataclasses import replace
    from wenu.rendering.preparation import configured_magnitude_sizes
    from wenu.svg_document import attach_semantic_svg_metadata
    analyzer = _star_area_analyzer()
    stars = AtlasChartStyle().stars
    if algorithm != 'legacy':
        stars = ChartStyleOverrides(stellar_magnitude_sizing=StellarMagnitudeSizing(algorithm=algorithm)).apply(AtlasChartStyle()).stars
    reference_areas = []
    for scale in (1, 2):
        directory = tmp_path / str(scale)
        directory.mkdir()
        figure, ax = plt.subplots(figsize=(3, 2))
        try:
            sizes = configured_magnitude_sizes(np.array([2., 6., 8.]), stars.magnitude_sizing,
                                               limiting_magnitude=8) * stars.area_scale * scale**2
            artist = ax.scatter([0, .5, 1], [0, .5, 1], s=sizes)
            artist.set_gid('magnitude-reference-stars')
            attach_semantic_svg_metadata(artist, layer='stars', zorder=5,
                paint_role=None, edit_policy=EditPolicy.STYLE,
                semantic_path=('sky', 'stars', 'symbols'),
                lock_owner_path=('sky', 'stars'), display_name='Stars',
                presentation_order=40, style_role='stars')
            filename = ExportOptions(bbox_inches=None).save(figure, directory / 'chart-10.svg')
        finally:
            plt.close(figure)
        presentation = {'style': 'atlas', 'star_magnitude_limit': 8}
        if scale != 1:  # Older atlas manifests lack the multiplier: default is 1.
            presentation['star_size_scale'] = scale
        manifest = {'document_kind': 'wenu-atlas-chart-batch', 'presentation': presentation,
                    'products': {filename.name: hashlib.sha256(filename.read_bytes()).hexdigest()}}
        if algorithm != 'legacy':
            manifest['stellar_sizing'] = stellar_sizing_report.resolved_sizing_record(
                replace(stars, area_scale=stars.area_scale*scale**2), 8)
        if algorithm != 'legacy':
            budget = stellar_sizing_report.magnitude_area_budget([2., 6., 8.], manifest['stellar_sizing'], 1000.)
            report_path = directory / 'chart-10_report_data.json'
            report_path.write_text(json.dumps(dict(stellar_sizing=manifest['stellar_sizing'], stellar_area_budget=budget)))
            manifest['products'][report_path.name] = hashlib.sha256(report_path.read_bytes()).hexdigest()
        (directory / 'manifest.json').write_text(json.dumps(manifest))
        measured = [row['area_mm2'] for row in analyzer.read_star_markers(filename)]
        guides, status = analyzer.magnitude_guides({filename}, measured)
        assert 'verified' in status
        assert guides[0]['magnitude'] == 2
        assert guides[0]['area_mm2'] == pytest.approx(measured[0], rel=1e-5)
        assert guides[-1]['area_mm2'] == pytest.approx(measured[2], rel=1e-5)
        if algorithm == 'legacy':
            assert measured[1] == pytest.approx(measured[2], rel=1e-5)
            assert guides[-1]['label'] == '5.50–8'
            assert guides[-1]['magnitude_max'] == 8
        else:
            assert measured[1] > measured[2]
            assert guides[-1]['label'] == '8'
        reference_areas.append(guides[0]['area_mm2'])
        summary = analyzer.analyze([directory], directory / 'guides_v1', bins=8)
        assert summary['magnitude_guides'] == guides
        if algorithm != 'legacy':
            budget = summary['magnitude_area_budget']
            assert [row['count'] for row in budget['bins']] == [1, 1, 1]
            assert budget['total_area_mm2'] == pytest.approx(sum(measured), rel=1e-6)
            assert sum(row['symbol_area_fraction'] for row in budget['bins']) == pytest.approx(1)
            assert (directory/'guides_v1_area-budget.pdf').is_file()
        plot = ET.parse(directory / 'guides_v1.svg').getroot()
        if algorithm == 'legacy':
            assert any(element.text == '5.50–8' for element in plot.iter())
        report = json.loads((directory/'guides_v1-report_data.json').read_text())
        assert report['policy']['sizing']['algorithm'] == algorithm
        assert sum(report['histogram']['counts']) == 3
        assert all((directory/f'guides_v1-report.{suffix}').is_file() for suffix in ('png', 'pdf', 'svg'))
        if algorithm != 'legacy':
            # Recorded policy survives a later change of the packaged preset.
            saved = stellar_sizing_report.resolved_sizing_record
            stellar_sizing_report.resolved_sizing_record = lambda *a: (_ for _ in ()).throw(AssertionError('No preset reconstruction'))
            try:
                assert analyzer.magnitude_guides({filename}, measured)[0] == guides
            finally:
                stellar_sizing_report.resolved_sizing_record = saved
        filename.write_text(filename.read_text() + '\n')
        assert analyzer.magnitude_guides({filename}, measured)[0] == []
        assert 'differs' in analyzer.magnitude_guides({filename}, measured)[1]
    assert reference_areas[1] == pytest.approx(4 * reference_areas[0])
    guides, status = analyzer.magnitude_guides({tmp_path/'no-manifest.svg'}, [1])
    assert guides == [] and 'No atlas batch manifest' in status


def test_ordered_semantic_fragments_preserve_interleaved_artists(tmp_path):
    from wenu.svg_document import attach_semantic_svg_metadata
    figure, ax = plt.subplots()
    try:
        artists = [ax.plot([0, 1], [i / 5, i / 5], zorder=i)[0]
                   for i in range(5)]
        paths = ["chart/atlas_index/north/atlas_charts/chart_14/boundary",
                 "chart/atlas_index/north/veil", None,
                 "chart/atlas_index/north/atlas_charts/chart_14/number",
                 "chart/atlas_index/north/veil"]
        for i, (artist, path) in enumerate(zip(artists, paths, strict=True)):
            artist.set_gid(f"ordered-{i}")
            if path is not None:
                parts = tuple(path.split("/"))
                attach_semantic_svg_metadata(artist, layer="test", zorder=i,
                    paint_role=None, edit_policy=EditPolicy.STYLE,
                    semantic_path=parts, lock_owner_path=parts[:-1],
                    display_name=parts[-1].capitalize(), presentation_order=100-i,
                    style_role="test", preserve_paint_order=True)
        destination = ExportOptions().save(figure, tmp_path / "ordered.svg")
    finally:
        plt.close(figure)
    root = ET.parse(destination).getroot()
    ids = [e.get("id") for e in root.iter() if e.get("id")]
    assert [identifier for identifier in ids if identifier.startswith("ordered-")] == [
        f"ordered-{i}" for i in range(5)]
    assert len(ids) == len(set(ids))
    fragments = [e for e in root.iter() if e.get("data-wenu-semantic-path") ==
                 "chart/atlas_index/north/atlas_charts/chart_14"
                 and "wenu-semantic-group" in e.get("class", "")]
    assert len(fragments) == 2


def test_declared_svg_containers_expose_compact_artist_leaves(tmp_path):
    from wenu.svg_document import attach_semantic_svg_metadata
    figure, ax = plt.subplots()
    try:
        figure.set_gid("compact-document")
        ax.set_gid("compact-disk")
        for artist, path, name in ((figure, ("chart", "example"), "Example"),
                (ax, ("chart", "example", "north"), "North Disk")):
            attach_semantic_svg_metadata(artist, layer="test", zorder=0,
                paint_role=None, edit_policy=EditPolicy.LAYOUT, semantic_path=path,
                lock_owner_path=path, display_name=name, presentation_order=None,
                style_role="container", hierarchy_container=True)
        line = ax.plot((0, 1), (0.2, 0.8), zorder=2)[0]
        line.set_clip_path(Circle((0.5, 0.5), 0.4, transform=ax.transAxes))
        line.set_gid("compact-boundary")
        path = ("chart", "example", "north", "charts", "chart_21", "boundary")
        attach_semantic_svg_metadata(line, layer="test", zorder=2,
            paint_role=None, edit_policy=EditPolicy.STYLE, semantic_path=path,
            lock_owner_path=path[:-1], display_name="Boundary", presentation_order=2,
            style_role="boundary", compact_hierarchy=True,
            svg_clip_box=(0, 0, figure.get_figwidth() * 36, figure.get_figheight() * 72))
        raw = tmp_path / "raw.svg"
        figure.savefig(raw)
        raw_root = ET.parse(raw).getroot()
        original = next(e for e in raw_root.iter() if e.get("id") == "compact-boundary")
        expected = next(e.get("d") for e in original.iter() if e.tag.endswith("}path"))
        destination = ExportOptions(bbox_inches=None).save(figure, tmp_path / "compact.svg")
    finally:
        plt.close(figure)
    root = ET.parse(destination).getroot()
    by_id = {e.get("id"): e for e in root.iter()}
    parents = {child: parent for parent in root.iter() for child in parent}
    boundary = by_id["compact-boundary"]
    assert boundary.tag.endswith("}path") and boundary.get("d") == expected
    clip = by_id[boundary.get("clip-path")[5:-1]]
    rectangle = next(iter(clip))
    assert rectangle.tag.endswith("}rect") and float(rectangle.get("width")) == 230.4
    path_clip = by_id[rectangle.get("clip-path")[5:-1]]
    assert any(e.tag.endswith("}path") for e in path_clip)
    chart = parents[boundary]
    assert chart.get("data-wenu-display-name") == "Chart 21"
    charts = parents[chart]
    assert charts.get("data-wenu-display-name") == "Charts"
    assert parents[charts] is by_id["compact-disk"]
    assert parents[by_id["compact-disk"]] is by_id["compact-document"]


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


def test_svg_skips_semantic_artist_omitted_by_matplotlib(tmp_path):
    destination = tmp_path / "omitted-artist.svg"
    figure, ax = plt.subplots()
    artist = ax.plot((0.0, 1.0), (0.0, 1.0))[0]
    artist.set_visible(False)
    MatplotlibRenderer.assign_semantic_identity(
        (artist,),
        SemanticLayerIdentity(
            name="celestial_points",
            svg_id="omitted-point",
            semantic_path=("sky", "grids", "reference_points"),
            display_name="Celestial reference points",
            presentation_order=74,
            style_role="celestial_points",
        ),
    )
    try:
        ExportOptions().save(figure, destination)
    finally:
        plt.close(figure)

    root = ET.parse(destination).getroot()
    assert not any(
        element.get("id") == "omitted-point"
        for element in root.iter()
    )


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
    artists = renderer.draw(
        curves,
        style={"color": "#123456", "linewidth": 2.5},
    )
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
    lines_style = dict(
        item.split(": ", 1)
        for item in lines.get("style", "").split("; ")
        if ":" in item
    )
    assert lines_style["stroke"] == "#123456"
    assert lines_style["stroke-width"] == "2.5"
    descendant_paths = [
        element
        for element in lines.iter()
        if element.tag.rsplit("}", 1)[-1] == "path"
    ]
    assert descendant_paths
    assert all(
        "stroke" not in dict(
            item.split(":", 1)
            for item in element.get("style", "").split("; ")
            if ":" in item
        )
        for element in descendant_paths
    )
    assert all(
        "stroke-width" not in dict(
            item.split(":", 1)
            for item in element.get("style", "").split("; ")
            if ":" in item
        )
        for element in descendant_paths
    )
    insensitive = (
        "{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}"
        "insensitive"
    )
    assert lines.get(insensitive) == "true"
    assert lines.get("data-wenu-locked") == "true"
    assert cru.get(insensitive) is None
    assert mus.get(insensitive) is None
    assert all(
        child.get("data-wenu-lock-owner-path")
        == "sky/constellations/lines_western"
        for entity in (cru, mus)
        for child in entity
    )
    assert all(
        child.get(insensitive) is None
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
    ].get(insensitive) is None
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
        "chart_boundary"
    ]
    assert len(list(frame)) == 4
    assert {
        child.get("id") for child in frame
    } == {
        "chart-boundary--0001",
        "chart-boundary--0002",
        "chart-boundary--0003",
        "chart-boundary--0004",
    }


def test_separate_identity_assignments_share_one_figure_id_sequence(tmp_path):
    destination = tmp_path / "separate-semantic-layers.svg"
    figure, ax = plt.subplots()
    first = ax.plot((0.0, 1.0), (0.2, 0.3))[0]
    second = ax.plot((0.0, 1.0), (0.7, 0.8))[0]
    identity = SemanticLayerIdentity(
        name="magellanic_cloud_isophotes",
        svg_id="wenu-layer-magellanic-cloud-isophotes",
        semantic_path=(
            "sky",
            "milky_way_and_magellanic_clouds",
            "magellanic_clouds",
        ),
        display_name="Magellanic Clouds",
        presentation_order=21,
        style_role="magellanic_clouds",
    )

    MatplotlibRenderer.assign_semantic_identity((first,), identity)
    MatplotlibRenderer.assign_semantic_identity((second,), identity)
    try:
        ExportOptions().save(figure, destination)
    finally:
        plt.close(figure)

    root = ET.parse(destination).getroot()
    semantic_ids = [
        element.get("id")
        for element in root.iter()
        if "wenu-semantic-artist" in element.get("class", "").split()
    ]

    assert semantic_ids == [
        "wenu-layer-magellanic-cloud-isophotes--0001",
        "wenu-layer-magellanic-cloud-isophotes--0002",
    ]


def test_arbitrary_canvas_background_and_boundary_are_semantic(tmp_path):
    destination = tmp_path / "arbitrary-canvas.svg"
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)
    boundary = ProjectedCurve(
        (-1.0, 1.0, 1.0, -1.0),
        (-0.5, -0.5, 0.5, 0.5),
        closed=True,
    )
    renderer.set_boundary_background(boundary, color="#123456")
    renderer.set_clip_boundary(
        boundary,
        style={"fill": False, "edgecolor": "#707070"},
    )
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

    assert "wenu-chart" in by_id
    assert "plot-area" in by_id
    assert "figure_1" not in by_id
    assert "axes_1" not in by_id
    assert "page-background" in by_id
    assert "sky-background" in by_id
    assert "chart-boundary" in by_id
    assert not any(
        object_id.startswith("patch_") for object_id in by_id
    )
    assert (
        by_id["sky-background"].get("data-wenu-semantic-path")
        == "sky/background"
    )
    assert (
        by_id["chart-boundary"].get("data-wenu-semantic-path")
        == "chart/masks_and_boundary/chart_boundary"
    )


def test_figure_margin_credits_and_version_belong_to_footer_furniture(
    tmp_path,
):
    destination = tmp_path / "footer.svg"
    figure, ax = plt.subplots()
    ax.set_title("Designer audit")
    renderer = MatplotlibRenderer(ax)
    credits = figure.text(0.05, 0.02, "© Chart author", ha="left")
    version = figure.text(0.95, 0.02, "Wenu 1.2.3", ha="right")
    assign_furniture_semantics(
        renderer,
        object(),
        footer_rendering=ChartFooterRendering(
            copyright_text="© Chart author",
            application_text="Wenu 1.2.3",
            artists=(credits, version),
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
        if element.get("data-wenu-semantic-path")
    }

    by_id = {
        element.get("id"): element
        for element in root.iter()
        if element.get("id")
    }
    parent_of = {
        child: parent
        for parent in root.iter()
        for child in parent
    }
    furniture_groups = [
        element
        for element in root.iter()
        if element.get("data-wenu-semantic-path") == "furniture"
    ]

    assert "wenu-chart" in by_id
    assert (
        by_id["wenu-chart"].get(
            "{http://www.inkscape.org/namespaces/inkscape}label"
        )
        == "Wenu chart - Designer audit"
    )
    assert "plot-area" in by_id
    assert len(furniture_groups) == 1
    assert parent_of[furniture_groups[0]] is by_id["wenu-chart"]
    assert parent_of[by_id["plot-area"]] is by_id["wenu-chart"]
    assert "furniture/footer" in by_path
    assert "furniture/footer/credits" in by_path
    assert "furniture/footer/application" in by_path
    assert (
        by_path["furniture/footer/credits"].get(
            "data-wenu-display-name"
        )
        == "Credits"
    )
    assert (
        by_path["furniture/footer/application"].get(
            "data-wenu-display-name"
        )
        == "Wenu version"
    )
    assert not any(
        element.get("id", "").startswith("text_")
        and any(
            value in "".join(element.itertext())
            for value in ("© Chart author", "Wenu 1.2.3")
        )
        for element in root.iter()
    )


@pytest.mark.parametrize('style,mode,family', [('atlas', 'print', 'regional'), ('cartoon', 'presentation', 'binocular')])
def test_stellar_sizing_preview_reuses_composition_without_sky(tmp_path, monkeypatch, style, mode, family):
    import json
    from pathlib import Path
    import numpy as np
    from wenu.charts.stellar_sizing_report import preview_main
    from wenu.sky import native_snapshot
    def forbidden(*args, **kwargs):
        raise AssertionError('An appearance preview must not prepare a sky.')
    monkeypatch.setattr(native_snapshot, 'prepare_native_sky_snapshot', forbidden)
    records = []
    for scale in (1, 3):
        prefix = tmp_path / f'preview-{scale}'
        assert preview_main(['--mag-algorithm', 'asinh', '--mag-dmin', '.3',
            '--mag-a', '.5', '--mag-b', '3', '--mag-size-reference', '8',
            '--star-size-scale', str(scale), '--style', style, '--mode', mode,
            '--family', family, '--dpi', '90', '--output-prefix', str(prefix)]) == 0
        records.append(json.loads(Path(str(prefix)+'_data.json').read_text()))
        for suffix in ('.png', '.pdf', '.svg', '.csv'):
            assert Path(str(prefix)+suffix).stat().st_size > 0
    np.testing.assert_allclose(records[1]['diameters_mm'], np.asarray(records[0]['diameters_mm'])*3)
    np.testing.assert_allclose(records[1]['areas_mm2'], np.asarray(records[0]['areas_mm2'])*9)
    # Presentation multiplies symbol area by 1.25, hence diameter by its square root.
    mode_area_scale = 1.25 if mode == 'presentation' else 1.0
    assert records[0]['diameters_mm'][-1] == pytest.approx(.3 * np.sqrt(mode_area_scale))
    assert records[1]['diameters_mm'][-1] == pytest.approx(.9 * np.sqrt(mode_area_scale))
    assert records[1]['mode'] == mode
    with pytest.raises(SystemExit):
        preview_main(['--output-prefix', str(prefix)])  # no overwrite
