"""Milestone 45F example-local Spanish planisphere text."""

from pathlib import Path

from wenu import LegendOptions
from wenu.charts.legend_symbols import legend_symbol_descriptors
from wenu.charts.presets import AtlasChartStyle
from wenu.translations import translate_label


PLANISPHERE = Path("examples/planisphere.py")


def test_planisphere_requests_spanish_annotations_and_titles():
    source = PLANISPHERE.read_text(encoding="utf-8")

    for text in (
        "Planisferio de La Ligua",
        "Cúmulo abierto",
        "Cúmulo globular",
        "Nebulosa planetaria",
        "Remanente de supernova",
        "Galaxia",
        "Vía Láctea",
        'stellar_title="Estrellas"',
    ):
        assert text in source
    assert 'language="es"' in source

    assert translate_label("Celestial equator", "es") == (
        "Ecuador celeste"
    )
    assert translate_label("Ecliptic", "es") == "Eclíptica"
    assert translate_label("Galactic plane", "es") == "Plano galáctico"


def test_legend_text_overrides_are_resolved_without_global_translation():
    resolved = LegendOptions(
        symbol_labels=(("galaxy", "Galaxia"),),
        stellar_title="Estrellas",
    ).resolve("planisphere")

    assert resolved.symbol_labels == (("galaxy", "Galaxia"),)
    assert resolved.stellar_title == "Estrellas"
    defaults = LegendOptions().resolve("regional")
    assert defaults.symbol_labels == ()
    assert defaults.stellar_title == "Stars"


def test_symbol_descriptor_accepts_example_local_label_overrides():
    class Sky:
        open_clusters = None
        globular_clusters = None
        planetary_nebulae = None
        supernova_remnants = None
        galaxies = object()
        milky_way_isophotes = None

    descriptors = legend_symbol_descriptors(
        Sky(),
        AtlasChartStyle(),
        labels=(("galaxy", "Galaxia"),),
    )

    assert [descriptor.label for descriptor in descriptors] == ["Galaxia"]
