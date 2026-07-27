"""Milestone 27 tests for the bundled OpenNGC bright-galaxy catalogue."""

from importlib.resources import as_file, files
import json

import numpy as np
from astropy.table import Table
import pytest

from wenu.resources import nonstellar_catalog_path


EXPECTED_ROWS = 1058
EXPECTED_COLUMNS = {
    "name",
    "object_type",
    "ra_deg",
    "dec_deg",
    "major_axis_arcmin",
    "minor_axis_arcmin",
    "position_angle_deg",
    "b_magnitude",
    "v_magnitude",
    "selection_magnitude",
    "selection_band",
    "surface_brightness_b_mag_arcsec2",
    "morphology",
    "rendering_class",
}


@pytest.fixture(scope="module")
def catalogue():
    resource = nonstellar_catalog_path("galaxies")
    with as_file(resource) as path:
        return Table.read(path)


def test_galaxy_catalogue_is_a_packaged_resource(catalogue):
    assert len(catalogue) == EXPECTED_ROWS
    assert EXPECTED_COLUMNS <= set(catalogue.colnames)


def test_catalogue_has_unique_names_and_finite_coordinates(catalogue):
    names = np.asarray(catalogue["name"], dtype=str)
    assert len(set(names)) == len(names)
    assert np.all(np.char.str_len(names) > 0)
    assert np.all(np.isfinite(catalogue["ra_deg"]))
    assert np.all(np.isfinite(catalogue["dec_deg"]))


def test_every_selected_galaxy_has_complete_ellipse_geometry(catalogue):
    for name in (
        "major_axis_arcmin",
        "minor_axis_arcmin",
        "position_angle_deg",
    ):
        assert np.all(np.isfinite(catalogue[name]))
    assert np.all(catalogue["major_axis_arcmin"] > 0.0)
    assert np.all(catalogue["minor_axis_arcmin"] > 0.0)
    assert np.all(
        catalogue["major_axis_arcmin"]
        >= catalogue["minor_axis_arcmin"]
    )


def test_selection_magnitude_and_band_are_explicit(catalogue):
    magnitude = np.asarray(
        catalogue["selection_magnitude"],
        dtype=float,
    )
    band = np.asarray(catalogue["selection_band"], dtype=str)
    assert np.all(np.isfinite(magnitude))
    assert np.all(magnitude <= 12.0)
    assert np.count_nonzero(band == "V") == 1052
    assert np.count_nonzero(band == "B") == 6


def test_magellanic_clouds_are_reserved_for_isophotes(catalogue):
    names = np.asarray(catalogue["name"], dtype=str)
    classes = np.asarray(catalogue["rendering_class"], dtype=str)
    by_name = dict(zip(names, classes))
    assert by_name["NGC0292"] == "isophote"
    assert by_name["ESO056-115"] == "isophote"
    assert np.count_nonzero(classes == "isophote") == 2
    assert np.count_nonzero(classes == "ellipse") == 1056


def test_surface_brightness_is_present_except_for_ngc5786(catalogue):
    names = np.asarray(catalogue["name"], dtype=str)
    brightness = np.asarray(
        catalogue["surface_brightness_b_mag_arcsec2"],
        dtype=float,
    )
    missing = names[~np.isfinite(brightness)]
    assert missing.tolist() == ["NGC5786"]


def test_provenance_records_pinned_source_and_selection():
    provenance_resource = files(
        "wenu.data.catalogs.galaxies"
    ).joinpath(
        "galaxies_openngc.provenance.json",
    )
    with as_file(provenance_resource) as path:
        provenance = json.loads(path.read_text(encoding="utf-8"))

    assert provenance["source"] == "OpenNGC"
    assert provenance["release"] == "v20260501"
    assert provenance["license"] == "CC-BY-SA-4.0"
    assert provenance["selection"]["object_type"] == "G"
    assert provenance["selection"]["magnitude_limit"] == 12.0
    assert provenance["statistics"]["selected_rows"] == EXPECTED_ROWS
    assert set(provenance["source_files"]) == {
        "NGC.csv",
        "addendum.csv",
    }


def test_unknown_nonstellar_catalogue_reports_available_names():
    with pytest.raises(ValueError, match="galaxies, globular_clusters, messier"):
        nonstellar_catalog_path("unknown")
