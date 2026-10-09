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
)


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
def test_nonstandard_or_duplicate_json_is_rejected(text):
    with pytest.raises(ValueError):
        AtlasGeometrySpecimen.from_json(text)


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
