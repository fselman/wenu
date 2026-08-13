"""Contracts for the packaged authoritative configuration document."""

from importlib.resources import files

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
        "exponent": 0.20,
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
