"""Contracts for the packaged authoritative configuration document."""

from importlib.resources import files

import pytest

from wenu.configuration import (
    ConfigurationError,
    load_packaged_defaults,
    parse_configuration,
    validate_configuration,
)

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10
    import tomli as tomllib


TOP_LEVEL_ORDER = (
    "schema_version",
    "observer",
    "subjects",
    "families",
    "detail",
    "styles",
    "modes",
    "grids_references",
    "furniture",
    "products",
    "export",
)
LINE_STYLES = {"solid", "dashed", "dotted", "dash_dot", "none"}


def _resource():
    return files("wenu.configuration").joinpath("defaults.toml")


def _load():
    return tomllib.loads(_resource().read_text(encoding="utf-8"))


def _tables(value, path=()):
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from _tables(child, (*path, key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _tables(child, (*path, str(index)))


def test_packaged_defaults_are_resource_loadable_and_ordered():
    resource = _resource()
    assert resource.is_file()
    text = resource.read_text(encoding="utf-8")
    assert text.startswith("# Wenu authoritative public defaults")
    assert "# Atlas print is the semantic appearance baseline." in text

    defaults = tomllib.loads(text)
    assert tuple(defaults) == TOP_LEVEL_ORDER
    assert defaults["schema_version"] == 1


def test_packaged_defaults_cover_schema_responsibilities():
    defaults = _load()
    assert tuple(defaults["subjects"]) == (
        "all_sky",
        "planisphere",
        "regional_single",
        "regional_group",
        "circumpolar",
        "binocular",
    )
    assert tuple(defaults["families"]) == tuple(defaults["subjects"])
    assert len(defaults["detail"]["adaptive"]["levels"]) == 7
    assert defaults["detail"]["polar_planisphere"] == {
        "star_magnitude_limit": 5.5,
        "label_density": 1.0,
        "enabled_layers": [
            "stars",
            "constellation_lines",
            "constellation_labels",
                "milky_way",
                "magellanic_clouds",
                "nonstellar_objects",
                "galaxies",
                "globular_clusters",
                "open_clusters",
                "planetary_nebulae",
            ],
        "constellation_star_mode": "none",
    }

    components = (
        "canvas",
        "stars",
        "milky_way",
        "lmc",
        "smc",
        "nonstellar",
        "galaxy",
        "supernova_remnant",
        "globular_cluster",
        "planetary_nebula",
        "open_cluster",
        "constellation_boundaries",
        "constellation_figures",
        "constellation_labels",
        "equatorial_grid",
        "ecliptic_grid",
        "galactic_grid",
        "altaz_grid",
        "coordinate_labels",
        "horizon",
        "mask",
        "chart_boundary",
        "legend",
    )
    for style_name in ("atlas", "cartoon"):
        style = defaults["styles"][style_name]
        for name in components:
            assert name in style
    polar = defaults["styles"]["polar_planisphere"]
    assert polar["paper_color"] == "#FFFFFF"
    assert polar["star_color"] == "#003F66"
    assert polar["star_minimum_area"] == pytest.approx(1.25)
    assert polar["star_magnitude_scale"] == pytest.approx(2.2727272727272725)
    assert polar["star_magnitude_exponent"] == pytest.approx(0.30488598388546717)
    assert polar["bright_star_magnitude_limit"] == pytest.approx(0.18)
    assert polar["bright_star_magnitude_scale"] == pytest.approx(1.0 / 1.62)
    assert polar["bright_star_magnitude_offset"] == pytest.approx(-1.0 / 9.0)
    assert polar["bright_star_symbol_area_scale"] == pytest.approx(
        1.0 / 0.38**2
    )
    assert polar["ordinary_star_magnitude_scale"] == pytest.approx(4.0 / 5.32)
    assert polar["ordinary_star_magnitude_offset"] == pytest.approx(
        -0.18 * 4.0 / 5.32
    )
    assert polar["milky_way_opacity"] == pytest.approx(0.45)
    assert polar["lmc_opacity"] == pytest.approx(0.32)
    assert polar["smc_opacity"] == pytest.approx(0.28)
    assert polar["constellation_line_width"] == pytest.approx(0.675)
    assert polar["reference_line_width"] == pytest.approx(0.75)
    assert polar["reference_opacity"] == pytest.approx(0.65)
    assert polar["calendar_day_label_font_size"] == pytest.approx(6.45)
    assert polar["calendar_month_label_font_size"] == pytest.approx(11.5)
    assert defaults["grids_references"][
        "polar_planisphere_label_anchors"
    ] == {
        "north": {
            "equatorial_right_ascension_deg": 225.0,
            "ecliptic_longitude_deg": 45.0,
        },
        "south": {
            "equatorial_right_ascension_deg": 45.0,
            "ecliptic_longitude_deg": 225.0,
        },
    }


def test_every_packaged_line_has_independent_public_fields():
    defaults = _load()
    lines = {
        path: table
        for path, table in _tables(defaults["styles"])
        if "line_style" in table
    }
    assert lines
    for path, line in lines.items():
        assert "color" in line, ".".join(path)
        assert "line_width" in line, ".".join(path)
        assert line["line_style"] in LINE_STYLES, ".".join(path)


def test_packaged_defaults_preserve_audited_baseline_values():
    defaults = _load()
    assert defaults["subjects"]["regional_group"]["constellations"] == [
        "Sgr",
        "Sco",
        "Oph",
        "Ser",
    ]
    assert defaults["families"]["circumpolar"][
        "limiting_declination"
    ] == -69.75
    assert defaults["detail"]["binocular_stellar_sizing"] == {
        "reference": "limiting_magnitude",
        "scale": 1.0,
        "exponent": 0.35,
        "minimum_area": 1.0,
        "maximum_area": 40.0,
    }
    horizon = defaults["styles"]["atlas"]["horizon"]
    assert horizon["color"] == "#707070"
    assert horizon["line_width"] == 0.55
    assert horizon["line_style"] == "dashed"
    boundary = defaults["styles"]["atlas"]["chart_boundary"]
    assert boundary == {
        "background": "inherit_canvas",
        "color": "#777777",
        "line_width": 0.35,
        "line_style": "dotted",
        "opacity": 0.65,
        "z_order": 8.0,
    }
    assert defaults["modes"]["presentation"]["dpi"] == 160
    cartoon = defaults["styles"]["cartoon"]
    assert cartoon["canvas"]["label_font_size"] == 13.0
    assert cartoon["constellation_figures"]["line_width"] == 1.15
    assert cartoon["horizon"]["line_style"] == "dashed"
    assert defaults["products"]["default"]["extension"] == ".png"


def test_packaged_defaults_pass_strict_validation_without_shared_state():
    first = load_packaged_defaults()
    second = load_packaged_defaults()
    assert first == second == _load()
    assert first is not second
    first["observer"]["location"] = "Changed"
    assert second["observer"]["location"] == "La Ligua"


@pytest.mark.parametrize(
    ("mutation", "diagnostic"),
    (
        (
            lambda value: value.update(schema_version=2),
            "schema_version: unsupported value 2",
        ),
        (
            lambda value: value["styles"]["atlas"]["horizon"].update(
                line_style="dashdot"
            ),
            "styles.atlas.horizon.line_style: unsupported value",
        ),
        (
            lambda value: value["styles"]["atlas"]["horizon"].update(
                color="definitely-not-a-color"
            ),
            "styles.atlas.horizon.color: invalid color",
        ),
        (
            lambda value: value["styles"]["atlas"]["mask"].update(
                opacity=1.5
            ),
            "styles.atlas.mask.opacity: must be in the interval [0, 1]",
        ),
        (
            lambda value: value["modes"]["print"].update(dpi=True),
            "modes.print.dpi: expected an integer",
        ),
        (
            lambda value: value["families"]["regional_single"].update(
                width=12.0
            ),
            "families.regional_single.height: width and height must both",
        ),
        (
            lambda value: value["families"]["circumpolar"].update(
                limiting_declination=69.75
            ),
            "families.circumpolar.limiting_declination: must be negative",
        ),
        (
            lambda value: value["detail"]["binocular_stellar_sizing"].update(
                maximum_area=0.5
            ),
            "detail.binocular_stellar_sizing.maximum_area: must be at least",
        ),
    ),
)
def test_strict_validation_reports_complete_paths(mutation, diagnostic):
    value = _load()
    mutation(value)
    with pytest.raises(ConfigurationError, match=None) as error:
        validate_configuration(value)
    assert diagnostic in str(error.value)


def test_strict_validation_rejects_unknown_and_missing_keys():
    unknown = _load()
    unknown["styles"]["atlas"]["horizon"]["renderer_operation"] = "plot"
    with pytest.raises(ConfigurationError) as error:
        validate_configuration(unknown)
    assert (
        "styles.atlas.horizon.renderer_operation: unknown configuration key"
        in str(error.value)
    )

    missing = _load()
    del missing["products"]["default"]["style"]
    with pytest.raises(ConfigurationError) as error:
        validate_configuration(missing)
    assert "products.default.style: missing required key" in str(error.value)


def test_toml_syntax_diagnostic_names_its_source():
    with pytest.raises(ConfigurationError) as error:
        parse_configuration("schema_version = [", source="broken.toml")
    assert "broken.toml: invalid TOML" in str(error.value)
