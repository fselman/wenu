"""Fixed-equatorial atlas specimen geometry and strict persistence contracts."""

from dataclasses import replace
import json

import numpy as np
import pytest

from wenu.atlas_design import (
    AtlasGeometrySpecimen,
    AtlasOverviewGeometry,
    AtlasPageGeometry,
    AtlasSheetGeometry,
    ANGULAR_GUARD_DEG,
    AtlasBandTiling,
    design_band_atlas,
    design_five_band_atlas,
    RECTANGULAR_TILING_METHOD,
    _sector_linear_maximum,
)


@pytest.fixture
def five_band_atlas(page):
    return design_five_band_atlas(
        "five-band", 1, page, AtlasOverviewGeometry(82.5, 20),
        field_width_deg=50, overlap_deg=0.25, seed_ra_deg=82.5,
        equatorial_half_height_deg=17, middle_boundary_dec_deg=45,
    )


@pytest.mark.parametrize("ra0,ra1,lo,hi,target_ra,target_dec", [
    (350, 370, 10, 30, 0, 20),
    (-5, 355, 75, 90, 82.5, 83),
    (350, 710, -90, -70, 359.5, -81),
])
def test_sector_bound_includes_interior_extrema_and_wrapped_longitudes(
        ra0, ra1, lo, hi, target_ra, target_dec):
    ra, dec = np.radians((target_ra, target_dec))
    vector = np.array((np.cos(dec) * np.cos(ra), np.cos(dec) * np.sin(ra), np.sin(dec)))
    assert _sector_linear_maximum(vector, ra0, ra1, lo, hi) == pytest.approx(1, abs=1e-12)
    # Corners alone would miss these extrema, including a polar-cap interior.
    corner_values = [vector @ np.array((np.cos(d) * np.cos(r),
                                       np.cos(d) * np.sin(r), np.sin(d)))
                     for r in np.radians((ra0, ra1)) for d in np.radians((lo, hi))]
    assert max(corner_values) < 1 - 1e-5


def test_five_band_layout_reduces_ra_counts_without_changing_physical_scale(five_band_atlas, page):
    atlas = five_band_atlas
    assert [len(b.sheet_ids) for b in atlas.bands] == [1, 5, 7, 8, 7, 5, 1]
    assert len(atlas.geometry.sheets) == 34
    assert [b.sector_width_deg for b in atlas.bands[3:6]] == pytest.approx([45, 360 / 7, 72])
    assert sum(b.area_sr for b in atlas.bands) == pytest.approx(4 * np.pi)
    assert all(s.field_width_deg == 50 for s in atlas.geometry.sheets)
    assert all(s.viewport(page).aspect_ratio == pytest.approx(323 / 230)
               for s in atlas.geometry.sheets)
    result = atlas.validation()
    assert result["coverage_status"] == "validated_analytic_rectangle_bound"
    assert result["shared_boundary_overlap_lower_bound_deg"] >= 0.25
    assert result["shared_boundary_overlap_lower_bound_deg"] < 0.250001
    with pytest.raises(ValueError):
        replace(atlas, containment_method="latitude-bands-inscribed-cap-v1")


@pytest.mark.parametrize("seed", [0, 82.5, 359.5])
def test_five_band_rectangle_contains_primary_regions_and_boundary_neighbourhoods(page, seed):
    atlas = design_five_band_atlas(
        "five-band", 1, page, AtlasOverviewGeometry(82.5, 20),
        field_width_deg=50, overlap_deg=.25, seed_ra_deg=seed,
        equatorial_half_height_deg=17, middle_boundary_dec_deg=45,
    )
    by_id = {s.sheet_id: s for s in atlas.geometry.sheets}
    for band in atlas.bands:
        for i, identifier in enumerate(band.sheet_ids):
            ra0 = band.ra_origin_deg + i * band.sector_width_deg
            ra, dec = np.meshgrid(np.linspace(ra0, ra0 + band.sector_width_deg, 13),
                                  np.linspace(band.dec_min_deg, band.dec_max_deg, 13))
            sheet = by_id[identifier]
            assert np.all(sheet.contains(page, ra, dec))
            # An independent spherical perturbation tests the reserved overlap
            # ball at all grid points. Sampling is an oracle, not the proof.
            lon, lat = np.radians(ra.ravel()), np.radians(dec.ravel())
            vectors = np.column_stack((np.cos(lat) * np.cos(lon),
                                       np.cos(lat) * np.sin(lon), np.sin(lat)))
            east = np.column_stack((-np.sin(lon), np.cos(lon), np.zeros(len(lon))))
            north = np.cross(vectors, east)
            distance = np.radians(.125)
            for angle in np.linspace(0, 2 * np.pi, 8, endpoint=False):
                moved = vectors * np.cos(distance) + (
                    east * np.cos(angle) + north * np.sin(angle)) * np.sin(distance)
                moved_ra = np.degrees(np.arctan2(moved[:, 1], moved[:, 0]))
                moved_dec = np.degrees(np.arctan2(moved[:, 2], np.hypot(moved[:, 0], moved[:, 1])))
                assert np.all(sheet.contains(page, moved_ra, moved_dec))


def test_five_band_json_revalidates_without_replacing_the_legacy_method(five_band_atlas, monkeypatch, tmp_path):
    import wenu.atlas_design as module
    path = five_band_atlas.write_json(tmp_path / "five_band_v1.json")
    def forbidden(*args, **kwargs):
        raise AssertionError("Reading must not regenerate placement")
    monkeypatch.setattr(module, "design_five_band_atlas", forbidden)
    assert AtlasBandTiling.read_json(path) == five_band_atlas
    data = five_band_atlas.to_dict()
    assert data["generator"] == RECTANGULAR_TILING_METHOD
    data["validation"]["minimum_primary_clearance_deg"] += .01
    with pytest.raises(ValueError):
        AtlasBandTiling.from_dict(data)
    with pytest.raises(ValueError):
        replace(five_band_atlas, containment_method="unknown")
    bands = list(five_band_atlas.bands)
    bands[1] = replace(bands[1], dec_min_deg=bands[1].dec_min_deg + 1e-12)
    with pytest.raises(ValueError):
        replace(five_band_atlas, bands=tuple(bands))


def test_five_band_infeasible_primary_profile_and_small_budget_fail(page):
    options = dict(field_width_deg=50, overlap_deg=.25, seed_ra_deg=82.5,
                   equatorial_half_height_deg=17, middle_boundary_dec_deg=45)
    args = ("five-band", 1, page, AtlasOverviewGeometry(82.5, 20))
    with pytest.raises(ValueError):
        design_five_band_atlas(*args, **options, max_sheets=33)
    with pytest.raises(ValueError):
        design_five_band_atlas(*args, **{**options, "equatorial_half_height_deg": 30}, max_sheets=64)
    with pytest.raises(ValueError):
        design_five_band_atlas(*args, **{**options, "middle_boundary_dec_deg": 85})


def test_five_band_overview_preserves_all_numbers_and_exports(five_band_atlas, overview_example, tmp_path, monkeypatch):
    draw = overview_example._draw_face
    numbers = set()
    def inspected(ax, atlas, face, **kwargs):
        draw(ax, atlas, face, **kwargs)
        numbers.update(text.get_text() for text in ax.texts)
    monkeypatch.setattr(overview_example, "_draw_face", inspected)
    path = five_band_atlas.write_json(tmp_path / "five_band_v1.json")
    overview_example.plot_overview(path, tmp_path / "five_band_overview_v1", footprints=True)
    assert numbers == {str(i) for i in range(1, 35)}


@pytest.fixture
def overview_example():
    from wenu.charts import atlas_index
    return atlas_index


@pytest.mark.parametrize("join,width", [(0, 0), (82.5, 20), (359.5, 40)])
def test_composed_index_registers_equator_and_preserves_own_hemispheres(overview_example, join, width):
    import matplotlib.pyplot as plt
    overview = AtlasOverviewGeometry(join, width)
    figure = plt.figure(figsize=(14, 8))
    try:
        axes = overview_example.composed_axes(figure, overview)
        locations = []
        for ax, pole in zip(axes, ("north", "south")):
            face = overview_example.overview_face(overview, pole)
            ax.set_xlim(-face.boundary_radius, face.boundary_radius)
            ax.set_ylim(-face.boundary_radius, face.boundary_radius)
            ax.set_aspect("equal")
            x,y = face.projection.project_spherical(join, 0)
            locations.append(ax.transData.transform((x,y)))
            ra,dec = np.meshgrid(np.linspace(0,360,73), np.linspace(0,90 if pole == "north" else -90,19))
            x,y = face.projection.project_spherical(ra.ravel(), dec.ravel())
            physical = figure.transFigure.inverted().transform(ax.transData.transform(np.column_stack((x,y))))
            assert np.all(physical[:,0] <= .5 + 1e-12) if pole == "north" else np.all(physical[:,0] >= .5 - 1e-12)
        np.testing.assert_allclose(locations[0], locations[1], atol=1e-10)
        a,b = (ax.get_position() for ax in axes)
        assert a.x1 >= b.x0 - 1e-12
        assert a.x1 > b.x0 if width else a.x1 == pytest.approx(b.x0)
    finally:
        plt.close(figure)


@pytest.mark.parametrize("initial_dpi", [100, 200])
def test_join_clip_tracks_export_dpi_and_retains_both_contours(five_band_atlas, overview_example, initial_dpi):
    import matplotlib.pyplot as plt
    figure = plt.figure(figsize=(14,8), dpi=initial_dpi)
    try:
        axes = overview_example.composed_axes(figure, five_band_atlas.geometry.overview)
        for ax,pole in zip(axes, ("north", "south")):
            overview_example._draw_face(ax, five_band_atlas,
                overview_example.overview_face(five_band_atlas.geometry.overview,pole), footprints=True)
        overview_example._join_faces(figure, axes, five_band_atlas)
        for ax, pole in zip(axes, ("north", "south")):
            contours = [a for a in ax.lines if a.get_gid() == f"atlas-index-{pole}-complete-rim"]
            assert len(contours) == 1 and not contours[0].get_clip_on()
        clips = [ax.lines[0].get_clip_box() for ax in axes]
        before = [clip.extents.copy() for clip in clips]
        # GUI canvases may already have scaled the requested DPI for Retina.
        scale = 160 / figure.dpi
        figure.set_dpi(160)
        for old,clip in zip(before,clips):
            np.testing.assert_allclose(clip.extents, old * scale)
    finally:
        plt.close(figure)


@pytest.mark.parametrize("with_clouds", [False, True])
def test_astronomical_index_uses_json_and_native_canonical_pipeline(
        five_band_atlas, overview_example, tmp_path, monkeypatch, with_clouds):
    from wenu.sky.celestial_sphere import CelestialSphere
    from wenu.coordinate_service import CoordinateService
    import wenu.observer
    def forbidden(*args, **kwargs):
        raise AssertionError("Index requested placement, observer or observed geometry")
    path = five_band_atlas.write_json(tmp_path / "atlas_v1.json")
    before = path.read_bytes()
    monkeypatch.setattr("wenu.atlas_design.design_five_band_atlas", forbidden)
    monkeypatch.setattr(wenu.observer.Observer, "__init__", forbidden)
    monkeypatch.setattr(CoordinateService, "transform_observer_geometry", forbidden)
    draw = CelestialSphere.draw_chart
    results = []
    def recording(self, **options):
        result = draw(self, **options)
        results.append(result)
        return result
    monkeypatch.setattr(CelestialSphere, "draw_chart", recording)
    join = overview_example._join_faces
    numbers = set()
    def inspect_join(figure, axes, atlas, presentation=None):
        join(figure, axes, atlas, presentation)
        for ax in axes:
            for artist in ax.texts:
                if artist.get_text().isdigit():
                    x,y = artist.get_transform().transform(artist.get_position())
                    if artist.get_clip_box().contains(x,y):
                        numbers.add(int(artist.get_text()))
    monkeypatch.setattr(overview_example, "_join_faces", inspect_join)
    magnitude = 4.5 if with_clouds else 5
    outputs = overview_example.plot_overview(path, tmp_path / "joined_sky_v1",
        joined=True, astronomy=True, footprints=True, star_magnitude_limit=magnitude,
        include_lowest_mw_isophote=with_clouds, magellanic_clouds=with_clouds)
    assert len(results) == 2
    assert numbers == set(range(1,35))
    assert [len(r.layers) for r in results] == ([6, 6] if with_clouds else [4, 4])
    for result in results:
        assert {r.layer.layer_name for r in result.layers} == {
            "stars", "constellation_lines", "constellation_labels", "milky_way_isophotes"} | (
                {"magellanic_cloud_isophotes"} if with_clouds else set())
        assert all(r.spherical.coordinate_spec.frame == "icrs" for r in result.layers)
        stars = next(r.spherical for r in result.layers if r.layer.layer_name == "stars")
        assert np.max(stars.metadata["magnitude"]) <= magnitude
        mw = next(r.spherical for r in result.layers if r.layer.layer_name == "milky_way_isophotes")
        assert set(mw.metadata["level"]) == ({"ol1", "ol2", "ol3", "ol4", "ol5"} if with_clouds else {"ol2", "ol3", "ol4", "ol5"})
        if with_clouds:
            clouds = [r for r in result.layers if r.layer.layer_name == "magellanic_cloud_isophotes"]
            assert {r.layer.cloud for r in clouds} == {"lmc", "smc"}
            for r in clouds:
                assert set(r.spherical.metadata["level"]) == {1, 2, 3, 4}
                assert not r.layer._observed_polygon_cache
        lines = next(r.spherical for r in result.layers if r.layer.layer_name == "constellation_lines")
        assert not lines.metadata["unresolved_star_ids"]
    assert all(p.exists() and p.stat().st_size > 1000 for p in outputs)
    assert path.read_bytes() == before
    if with_clouds:
        import xml.etree.ElementTree as ET
        svg = next(p for p in outputs if p.suffix == ".svg")
        identifiers = [element.get("id", "") for element in ET.parse(svg).getroot().iter()]
        for required in ("isophote-ol1", "lmc-isophotes-isophote-1", "smc-isophotes-isophote-1"):
            assert any(required in value for value in identifiers)


@pytest.mark.parametrize("join", [0, 82.5, 359.5])
def test_overview_join_meridian_points_inward(overview_example, join):
    overview = AtlasOverviewGeometry(join, 20)
    for pole, sign in (("north", 1), ("south", -1)):
        face = overview_example.overview_face(overview, pole)
        x, y = face.projection.project_spherical(join, 0)
        assert x == pytest.approx(sign * 2)
        assert y == pytest.approx(0, abs=1e-12)
        assert face.projection.angular_radius_for_projected_radius(face.boundary_radius) == pytest.approx(100)


@pytest.mark.parametrize("width", [30, 40, 50])
def test_overview_sector_intersections_preserve_cap_area_and_sheet_identity(page, overview_example, width):
    atlas = design_band_atlas("visual", 1, page, AtlasOverviewGeometry(359.5, 20),
                             field_width_deg=width, overlap_deg=2, seed_ra_deg=82.5)
    ids = set()
    shared_ids = []
    for pole in ("north", "south"):
        face = overview_example.overview_face(atlas.geometry.overview, pole)
        regions = list(overview_example.visible_regions(atlas, face))
        area = sum(np.radians(ra1 - ra0) *
                   (np.sin(np.radians(upper)) - np.sin(np.radians(lower)))
                   for _, ra0, ra1, lower, upper in regions)
        assert area == pytest.approx(2 * np.pi * (1 + np.sin(np.radians(10))))
        labelled = {sheet.sheet_id for sheet, _, _, lower, upper in regions
                    if lower <= sheet.center_dec_deg <= upper}
        ids.update(labelled)
        shared_ids.append(labelled)
    assert ids == {sheet.sheet_id for sheet in atlas.geometry.sheets}
    assert shared_ids[0] & shared_ids[1] == {
        sheet.sheet_id for sheet in atlas.geometry.sheets if abs(sheet.center_dec_deg) <= 10
    }


@pytest.mark.parametrize("pole", ["north", "south"])
def test_overview_polar_primary_cap_has_no_false_radial_border(overview_example, pole):
    face = overview_example.overview_face(AtlasOverviewGeometry(82.5, 20), pole)
    lower, upper = (80, 90) if pole == "north" else (-90, -80)
    polygon = overview_example.primary_outline(face, 350, 710, lower, upper)
    radius = face.projection.projected_radius(10)
    np.testing.assert_allclose(np.hypot(polygon.x, polygon.y), radius, atol=1e-12)


def test_overview_reads_json_without_placement_and_exports_all_formats(page, overview_example, tmp_path, monkeypatch):
    import matplotlib.pyplot as plt
    import wenu.atlas_design as design_module
    from xml.etree import ElementTree

    atlas = design_band_atlas("visual", 1, page, AtlasOverviewGeometry(82.5, 20),
                             field_width_deg=40, overlap_deg=2, seed_ra_deg=82.5)
    design_path = atlas.write_json(tmp_path / "design_v1.json")
    original = design_path.read_bytes()
    def forbidden_placement(*args, **kwargs):
        raise AssertionError("Plotting must not regenerate placement")
    monkeypatch.setattr(design_module, "design_band_atlas", forbidden_placement)
    original_draw = overview_example._draw_face
    seen = {}
    def inspected_draw(ax, atlas, face, **kwargs):
        original_draw(ax, atlas, face, **kwargs)
        seen[face.pole] = {text.get_text() for text in ax.texts}
        assert all(text.get_clip_on() for text in ax.texts)
    monkeypatch.setattr(overview_example, "_draw_face", inspected_draw)
    before = set(plt.get_fignums())
    paths = overview_example.plot_overview(design_path, tmp_path / "index_v1", footprints=True)
    assert {path.suffix for path in paths} == {".png", ".pdf", ".svg"}
    assert all(path.stat().st_size > 1000 for path in paths)
    assert ElementTree.parse(paths[2]).getroot().tag.endswith("svg")
    assert seen["north"] | seen["south"] == {str(sheet.number) for sheet in atlas.geometry.sheets}
    assert design_path.read_bytes() == original
    assert set(plt.get_fignums()) == before
    saved = paths[0].read_bytes()
    with pytest.raises(FileExistsError):
        overview_example.plot_overview(design_path, tmp_path / "index_v1")
    assert paths[0].read_bytes() == saved


def test_overview_rejects_corrupt_design_before_creating_output(page, overview_example, tmp_path):
    atlas = design_band_atlas("visual", 1, page, AtlasOverviewGeometry(82.5, 20),
                             field_width_deg=40, overlap_deg=2, seed_ra_deg=82.5)
    data = atlas.to_dict()
    data["validation"]["sheet_count"] += 1
    path = tmp_path / "corrupt_v1.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        overview_example.plot_overview(path, tmp_path / "rejected_v1")
    assert not list(tmp_path.glob("rejected_v1.*"))


@pytest.fixture
def page():
    return AtlasPageGeometry(353, 250, 10, 10, 20, 10)


@pytest.fixture
def specimen(page):
    return AtlasGeometrySpecimen(
        "orion-trial", 1, page, AtlasOverviewGeometry(82.5, 20),
        (AtlasSheetGeometry("orion", 2, 82.5, 0, 40),
         AtlasSheetGeometry("north", 1, 0, 90, 40, pole_meridian_ra_deg=82.5),
         AtlasSheetGeometry("south", 3, 0, -90, 40, pole_meridian_ra_deg=82.5)),
    )


def test_field_height_uses_projected_page_aspect(page):
    sheet = AtlasSheetGeometry("test", 1, 0, 0, 70)
    v = sheet.viewport(page)
    expected_height = np.degrees(4 * np.arctan(
        np.tan(np.radians(70) / 4) * 230 / 323
    ))
    assert v.aspect_ratio == pytest.approx(323 / 230)
    assert sheet.field_height_deg(page) == pytest.approx(expected_height)
    assert sheet.field_height_deg(page) != pytest.approx(70 * 230 / 323)
    assert v.width == pytest.approx(4 * np.tan(np.radians(70) / 4))


@pytest.mark.parametrize("ra,dec,anchor", [(359.5, 20, None), (0, 90, 82.5),
                                             (0, -90, 82.5)])
@pytest.mark.parametrize("angle,flip", [(0, False), (37, False), (-25, True)])
def test_footprint_round_trip_at_wrap_and_poles(page, ra, dec, anchor, angle, flip):
    sheet = AtlasSheetGeometry("test", 1, ra, dec, 40, angle, flip, anchor)
    v = sheet.viewport(page)
    xy = np.array([[v.x_min, v.y_min], [v.x_max, v.y_min],
                   [v.x_max, v.y_max], [v.x_min, v.y_max],
                   [0, v.y_min], [v.x_max, 0], [0, 0]])
    points = sheet.projection.unproject_spherical(xy[:, 0], xy[:, 1])
    x, y = sheet.projection.project_spherical(points.lon_deg, points.lat_deg)
    np.testing.assert_allclose(np.column_stack([x, y]), xy, atol=3e-8)
    assert np.all(sheet.contains(page, points.lon_deg, points.lat_deg))
    assert len(sheet.boundary_samples(page, samples_per_edge=4)) == 16


@pytest.mark.parametrize("dec", [90, -90])
@pytest.mark.parametrize("anchor", [0, 82.5, 270])
def test_polar_meridian_sets_positive_y(page, dec, anchor):
    sheet = AtlasSheetGeometry("pole", 1, 0, dec, 40, pole_meridian_ra_deg=anchor)
    x, y = sheet.projection.project_spherical(anchor, np.sign(dec) * 80)
    assert x == pytest.approx(0, abs=1e-12)
    assert y > 0
    np.testing.assert_allclose(sheet.frame.rotation_matrix @ sheet.frame.rotation_matrix.T,
                               np.eye(3), atol=1e-12)


def test_north_up_and_ra_left_convention(page):
    sheet = AtlasSheetGeometry("test", 1, 0, 0, 40)
    x, y = sheet.projection.project_spherical([10, 0], [0, 10])
    assert x[0] < 0 and y[1] > 0
    rotated = replace(sheet, position_angle_deg=90)
    x, y = rotated.projection.project_spherical(0, 10)
    assert x < 0 and y == pytest.approx(0, abs=1e-12)
    assert sheet.contains(page, 0, 0)
    assert not sheet.contains(page, 180, 0)
    assert not sheet.contains(page, 50, 0)


def test_specimen_round_trip_and_deterministic_order(specimen, tmp_path):
    text = specimen.to_json()
    path = specimen.write_json(tmp_path / "atlas_geometry_specimen_v1.json")
    assert AtlasGeometrySpecimen.read_json(path) == specimen
    assert AtlasGeometrySpecimen.from_json(text).to_json() == text
    assert replace(specimen, sheets=tuple(reversed(specimen.sheets))).to_json() == text
    data = json.loads(text)
    assert data["coverage_status"] == "unverified"
    assert data["document_kind"] == "wenu-atlas-geometry-specimen"
    assert data["overview"]["shared_band_width_deg"] == 20
    assert specimen.overview.north_limit_dec_deg == -10
    assert specimen.overview.south_limit_dec_deg == 10
    assert data["coordinate_frame"] == "icrs"


@pytest.mark.parametrize("changes", [
    {"center_ra_deg": -1}, {"center_dec_deg": 91}, {"field_width_deg": 360},
    {"field_width_deg": 0}, {"field_width_deg": float("nan")},
    {"position_angle_deg": 180}, {"projection_radius": 0}, {"number": True},
    {"flip_ew": 1}, {"center_ra_deg": "82.5"}, {"sheet_id": " bad"},
    {"pole_meridian_ra_deg": 82.5}, {"center_dec_deg": 90},
])
def test_invalid_sheet_parameters_fail(changes):
    values = dict(sheet_id="test", number=1, center_ra_deg=0,
                  center_dec_deg=0, field_width_deg=40)
    values.update(changes)
    with pytest.raises(ValueError):
        AtlasSheetGeometry(**values)


def test_page_overview_and_duplicate_identity_validation(specimen):
    with pytest.raises(ValueError):
        AtlasPageGeometry(353, 250, 125, 125, 10, 10)
    with pytest.raises(ValueError):
        AtlasPageGeometry(True, 250, 0, 0, 0, 0)
    with pytest.raises(ValueError):
        AtlasOverviewGeometry(360, 20)
    with pytest.raises(ValueError):
        AtlasOverviewGeometry(0, 180)
    assert AtlasOverviewGeometry(0, 0).north_limit_dec_deg == 0
    with pytest.raises(ValueError, match="Duplicate"):
        replace(specimen, sheets=(specimen.sheets[0], specimen.sheets[0]))
    with pytest.raises(ValueError, match="Duplicate"):
        replace(specimen, sheets=(specimen.sheets[0],
                replace(specimen.sheets[1], number=specimen.sheets[0].number)))


@pytest.mark.parametrize("mutation", [
    lambda d: d.update(schema_version=2), lambda d: d.update(schema_version=True),
    lambda d: d.update(coverage_status="complete"),
    lambda d: d.update(coordinate_frame="fk5"), lambda d: d.update(extra=1),
    lambda d: d["page"].update(extra=1),
    lambda d: d["sheets"][0]["geometry"].pop("flip_ew"),
    lambda d: d["sheets"][0]["resolved"].update(projection="gnomonic"),
    lambda d: d["sheets"][0]["resolved"].update(tangent_basis=[[1, 0, 0]]),
    lambda d: d["sheets"][0]["resolved"]["tangent_basis"][0].__setitem__(0, True),
    lambda d: d["sheets"][0]["resolved"].update(field_height_deg="40"),
    lambda d: d["sheets"][0]["resolved"]["viewport"].update(x_max=100),
    lambda d: d["sheets"][0]["resolved"]["viewport"].update(x_min="-1"),
])
def test_json_rejects_unknown_or_inconsistent_records(specimen, mutation):
    data = specimen.to_dict()
    original = specimen.to_dict()
    mutation(data)
    assert json.dumps(data, sort_keys=True) != json.dumps(original, sort_keys=True)
    with pytest.raises(ValueError):
        AtlasGeometrySpecimen.from_dict(data)


@pytest.mark.parametrize("text", [
    '{"schema_version":1,"schema_version":1}',
    '{"value":NaN}', '{"value":Infinity}',
])
@pytest.mark.parametrize("reader", [AtlasGeometrySpecimen, AtlasBandTiling])
def test_nonstandard_or_duplicate_json_is_rejected(text, reader):
    with pytest.raises(ValueError):
        reader.from_json(text)


def test_specimen_construction_does_not_request_catalogues_or_observers(page, monkeypatch):
    import wenu.observer
    import wenu.sky.maximal_sphere

    def forbidden(*args, **kwargs):
        raise AssertionError("Atlas geometry requested observational state")

    monkeypatch.setattr(wenu.observer.Observer, "__init__", forbidden)
    monkeypatch.setattr(wenu.sky.maximal_sphere, "build_maximal_sphere", forbidden)
    result = AtlasGeometrySpecimen("offline", 1, page, AtlasOverviewGeometry(0, 0),
                                   (AtlasSheetGeometry("one", 1, 0, 0, 40),))
    assert AtlasGeometrySpecimen.from_json(result.to_json()) == result


# Band tiling tests own the new partition/certificate/persistence seam. Existing
# specimen tests above retain the projection and tangent-frame oracles.
@pytest.fixture
def tiling(page):
    return design_band_atlas(
        "trial", 1, page, AtlasOverviewGeometry(82.5, 20),
        field_width_deg=40, overlap_deg=2, seed_ra_deg=359.5,
    )


@pytest.mark.parametrize("width,aspect", [(30, 353 / 250), (40, 353 / 250),
                                          (50, 353 / 250), (50, 250 / 353)])
def test_band_partition_and_independent_point_membership(width, aspect):
    p = AtlasPageGeometry(250 * aspect, 250, 0, 0, 0, 0)
    a = design_band_atlas("geometry", 1, p, AtlasOverviewGeometry(82.5, 20),
                          field_width_deg=width, overlap_deg=2, seed_ra_deg=359.5)
    evidence = a.validation()
    assert evidence["primary_area_sr"] == pytest.approx(4 * np.pi)
    assert evidence["shared_boundary_overlap_lower_bound_deg"] >= 2
    assert a.bands[0].dec_min_deg == -90 and a.bands[-1].dec_max_deg == 90
    assert sum(s.center_dec_deg == 0 and abs(
        (s.center_ra_deg - 359.5 + 180) % 360 - 180
    ) < 1e-10 for s in a.geometry.sheets) == 1
    sheets = {s.sheet_id: s for s in a.geometry.sheets}
    # Diagnostic grid is independent corroboration, never the certificate.
    for dec in np.linspace(-90, 90, 11):
        for ra in np.linspace(0, 360, 13):
            owner = a.primary_sheet_id(ra, dec)
            assert sheets[owner].contains(p, ra, dec)
    for band in a.bands[1:-1]:
        for i, identity in enumerate(band.sheet_ids):
            # Independent Cartesian-dot bound corroborates both corner edges.
            s = sheets[identity]
            dc, rc = np.radians([s.center_dec_deg, s.center_ra_deg])
            c = np.array([np.cos(dc)*np.cos(rc), np.cos(dc)*np.sin(rc), np.sin(dc)])
            for d in (band.dec_min_deg, band.dec_max_deg):
                for r in (band.ra_origin_deg + i * band.sector_width_deg,
                          band.ra_origin_deg + (i + 1) * band.sector_width_deg):
                    dr, rr = np.radians([d, r])
                    v = np.array([np.cos(dr)*np.cos(rr), np.cos(dr)*np.sin(rr), np.sin(dr)])
                    separation = np.degrees(np.arctan2(np.linalg.norm(np.cross(c, v)),
                                                        np.dot(c, v)))
                    vp = s.viewport(p)
                    radius = np.degrees(2 * np.arctan(min(vp.width, vp.height) / 4))
                    assert separation + 1 + ANGULAR_GUARD_DEG <= radius


def test_band_round_trip_is_deterministic_and_strict(tiling, tmp_path):
    text = tiling.to_json()
    assert AtlasBandTiling.from_json(text) == tiling
    path = tiling.write_json(tmp_path / "atlas_band_trial_v1.json")
    assert AtlasBandTiling.read_json(path).to_json() == text
    assert tiling.geometry.to_dict()["coverage_status"] == "unverified"
    assert json.loads(text)["document_kind"] == "wenu-atlas-band-tiling"


def test_geometry_identity_is_independent_of_index_join(tiling):
    geometry = replace(tiling.geometry, overview=AtlasOverviewGeometry(120, 40))
    changed = replace(tiling, geometry=geometry)
    assert changed.validation() == tiling.validation()
    assert changed.bands == tiling.bands
    assert changed.geometry.sheets == tiling.geometry.sheets
    regenerated = design_band_atlas(
        geometry.design_id, geometry.revision, geometry.page, geometry.overview,
        field_width_deg=40, overlap_deg=2, seed_ra_deg=359.5,
    )
    assert regenerated == changed
    redesign = design_band_atlas(
        geometry.design_id, 2, geometry.page, geometry.overview,
        field_width_deg=40, overlap_deg=2, seed_ra_deg=359.5,
    )
    assert set(s.sheet_id for s in redesign.geometry.sheets).isdisjoint(
        s.sheet_id for s in tiling.geometry.sheets)


def test_shared_edges_have_unique_ownership_and_reciprocal_neighbours(tiling):
    for lower, upper in zip(tiling.bands, tiling.bands[1:]):
        assert tiling.primary_sheet_id(upper.ra_origin_deg, upper.dec_min_deg) == (
            upper.sheet_ids[0])
    for b in tiling.bands[1:-1]:
        d = (b.dec_min_deg + b.dec_max_deg) / 2
        assert tiling.primary_sheet_id(b.ra_origin_deg, d) == b.sheet_ids[0]
        assert tiling.primary_sheet_id(b.ra_origin_deg + 360, d) == b.sheet_ids[0]
    for d, b in ((-90, tiling.bands[0]), (90, tiling.bands[-1])):
        assert {tiling.primary_sheet_id(r, d) for r in (0, 45, 359)} == set(b.sheet_ids)
    graph = tiling.neighbours()
    assert set(graph) == {s.sheet_id for s in tiling.geometry.sheets}
    for a, values in graph.items():
        assert a not in values and values
        for b in values:
            assert a in graph[b]
    assert set(graph[tiling.bands[0].sheet_ids[0]]) == set(tiling.bands[1].sheet_ids)
    assert set(graph[tiling.bands[-1].sheet_ids[0]]) == set(tiling.bands[-2].sheet_ids)


@pytest.mark.parametrize("fault", ["gap", "extra_owner", "missing_owner", "small_sheet",
                                    "seed", "false_certificate", "neighbour", "bool"])
def test_corrupted_tiling_is_rejected(tiling, fault):
    data = json.loads(tiling.to_json())
    baseline = json.dumps(data, sort_keys=True)
    if fault == "gap":
        data["bands"][1]["dec_min_deg"] += 1e-12
    elif fault == "extra_owner":
        data["bands"][1]["sheet_ids"][0] = data["bands"][0]["sheet_ids"][0]
    elif fault == "missing_owner":
        data["bands"][1]["sheet_ids"].pop()
    elif fault == "small_sheet":
        sheet = tiling.geometry.sheets[0]
        geometry = replace(tiling.geometry, sheets=(replace(sheet, field_width_deg=5),
                           *tiling.geometry.sheets[1:]))
        data["geometry"] = geometry.to_dict()
    elif fault == "seed":
        data["seed_ra_deg"] = 0
    elif fault == "false_certificate":
        data["validation"]["shared_boundary_overlap_lower_bound_deg"] = 100
    elif fault == "neighbour":
        data["neighbours"][next(iter(data["neighbours"]))] = []
    elif fault == "bool":
        data["schema_version"] = True
    assert json.dumps(data, sort_keys=True) != baseline
    with pytest.raises(ValueError):
        AtlasBandTiling.from_dict(data)


@pytest.mark.parametrize("arguments", [
    {"field_width_deg": 0}, {"field_width_deg": 121},
    {"overlap_deg": -1}, {"overlap_deg": 40}, {"overlap_deg": True},
    {"seed_ra_deg": 360}, {"max_sheets": 10}, {"max_sheets": 4097},
])
def test_band_design_rejects_invalid_or_exhausted_requests(page, arguments):
    values = dict(field_width_deg=40, overlap_deg=2, seed_ra_deg=82.5)
    values.update(arguments)
    with pytest.raises(ValueError):
        design_band_atlas("trial", 1, page, AtlasOverviewGeometry(0, 0), **values)


def test_band_design_does_not_construct_observational_state(page, monkeypatch):
    import wenu.observer
    import wenu.sky.maximal_sphere

    def forbidden(*args, **kwargs):
        raise AssertionError("Tiling requested observer/catalogue state")

    monkeypatch.setattr(wenu.observer.Observer, "__init__", forbidden)
    monkeypatch.setattr(wenu.sky.maximal_sphere, "build_maximal_sphere", forbidden)
    a = design_band_atlas("offline", 1, page, AtlasOverviewGeometry(82.5, 20),
                          field_width_deg=50, overlap_deg=2, seed_ra_deg=0)
    assert AtlasBandTiling.from_json(a.to_json()) == a


@pytest.mark.parametrize("option", ["include_lowest_mw_isophote", "magellanic_clouds"])
def test_extra_index_layers_require_astronomical_rendering(overview_example, tmp_path, option):
    with pytest.raises(ValueError, match="require astronomy"):
        overview_example.plot_overview(tmp_path / "unused.json", tmp_path / "unused", **{option: True})
