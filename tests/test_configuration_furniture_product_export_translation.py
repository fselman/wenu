"""Parity contracts for the final packaged-default translation slice."""

from dataclasses import FrozenInstanceError
from types import MappingProxyType

import pytest

from wenu.charts.furniture import (
    ChartContextOptions,
    FooterOptions,
    PoleAnnotations,
    ReferenceAnnotations,
)
from wenu.charts.legend_plan import (
    LegendOptions,
    default_chart_legend_plan,
)
from wenu.charts.magnitude_legend_style import StellarMagnitudeLegendStyle
from wenu.charts.product_options import ChartProduct
from wenu.charts.regional import ExportOptions
from wenu.configuration import (
    ConfigurationError,
    FooterLayoutDefaults,
    ProductDefaults,
    load_packaged_defaults,
    translate_furniture_product_export_defaults,
    validate_configuration,
)


FAMILIES = (
    "regional", "planisphere", "all_sky", "circumpolar", "binocular"
)


def test_packaged_furniture_translates_to_existing_immutable_contracts():
    defaults = translate_furniture_product_export_defaults()
    assert isinstance(defaults.furniture_by_family, MappingProxyType)
    assert defaults.legend_options == LegendOptions()
    for family in FAMILIES:
        furniture = defaults.furniture_by_family[family]
        assert furniture.references == ReferenceAnnotations()
        assert furniture.poles == PoleAnnotations()
        assert furniture.footer == FooterOptions()
        assert furniture.context == ChartContextOptions()
        assert furniture.legends.plan == default_chart_legend_plan(family)
        assert furniture.legends.resolve(family).plan == (
            default_chart_legend_plan(family)
        )

    with pytest.raises(TypeError):
        defaults.furniture_by_family["regional"] = defaults.furniture_by_family[
            "regional"
        ]


def test_packaged_footer_and_magnitude_legend_values_have_parity():
    defaults = translate_furniture_product_export_defaults()
    assert defaults.footer_layout == FooterLayoutDefaults(
        font_size=7.0,
        y=0.018,
        left_x=0.01,
        right_x=0.99,
    )
    assert defaults.magnitude_legend == StellarMagnitudeLegendStyle()
    with pytest.raises(FrozenInstanceError):
        defaults.footer_layout.font_size = 8.0


def test_packaged_product_and_export_values_have_parity():
    defaults = translate_furniture_product_export_defaults()
    assert defaults.product == ProductDefaults(
        product=ChartProduct("atlas", "print"),
        all_products=False,
        language="en",
        title=None,
        extension=".png",
    )
    assert defaults.export_options == ExportOptions()
    assert defaults.export_padding == 0.0


def test_disabled_footer_cannot_silently_translate_visible_copyright():
    values = load_packaged_defaults()
    values["furniture"]["footer"]["copyright"] = "Copyright"
    with pytest.raises(ConfigurationError) as error:
        translate_furniture_product_export_defaults(values)
    assert "furniture.footer.copyright" in str(error.value)


def test_unknown_family_legend_location_reports_complete_path():
    values = load_packaged_defaults()
    values["furniture"]["legends"]["regional"][
        "objects_location"
    ] = "somewhere"
    with pytest.raises(ConfigurationError) as error:
        validate_configuration(values)
    assert (
        "furniture.legends.regional.objects_location: unsupported value"
        in str(error.value)
    )


def test_reference_repeat_length_factor_translates_and_survives_cli_selection(tmp_path):
    from wenu.configuration import load_configuration_defaults
    from wenu.charts.command_line import chart_cli_furniture
    from wenu.cli.chart import parser

    path = tmp_path / 'reference-v10.toml'
    path.write_text('schema_version = 2\n[grids_references.references]\nlabel_repeat_length_factor = 7.5\n')
    config = load_configuration_defaults(path)
    args = parser().parse_args(['regional', '--grid-references', 'all'])
    furniture = chart_cli_furniture(args, configuration=config, family='regional')
    for name in ('celestial_equator', 'ecliptic', 'galactic_plane'):
        assert getattr(furniture.references, name).label_repeat_length_factor == 7.5


@pytest.mark.parametrize('factor', [0.0, -1.0, float('nan'), float('inf')])
def test_reference_repeat_length_factor_rejects_invalid_values(factor):
    from wenu.charts.furniture import ReferencePlaneAnnotation
    config = load_packaged_defaults()
    config['grids_references']['references']['label_repeat_length_factor'] = factor
    with pytest.raises(ConfigurationError):
        validate_configuration(config)
    with pytest.raises(ValueError, match='label_repeat_length_factor'):
        ReferencePlaneAnnotation(label_repeat_length_factor=factor)
