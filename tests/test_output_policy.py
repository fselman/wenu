"""Public output-format contracts."""

from __future__ import annotations

import pytest

from wenu.output_policy import ChartOutputPolicy, OutputFormat, SvgProvenance


@pytest.mark.parametrize(
    ("output_format", "extension"),
    (
        (OutputFormat.PNG, ".png"),
        (OutputFormat.PDF, ".pdf"),
        (OutputFormat.SVG, ".svg"),
    ),
)
def test_output_formats_have_canonical_extensions(output_format, extension):
    assert output_format.extension == extension


def test_output_policy_accepts_public_string_vocabulary():
    policy = ChartOutputPolicy(output_format="svg")

    assert policy.output_format is OutputFormat.SVG


def test_output_policy_defaults_to_png():
    assert ChartOutputPolicy().output_format is OutputFormat.PNG


@pytest.mark.parametrize("value", ("jpeg", "", "SVG"))
def test_output_policy_rejects_unknown_or_noncanonical_format(value):
    with pytest.raises(ValueError, match="Unsupported output format"):
        ChartOutputPolicy(output_format=value)


def test_svg_provenance_requires_a_product_name_and_mapping():
    with pytest.raises(ValueError, match="product_name"):
        SvgProvenance(product_name=" ", parameters={})
    with pytest.raises(TypeError, match="parameters"):
        SvgProvenance(product_name="regional", parameters=())


def test_svg_provenance_copies_mutable_parameter_mapping():
    parameters = {"family": "regional"}
    provenance = SvgProvenance("regional", parameters)
    parameters["family"] = "changed"

    assert provenance.parameters == {"family": "regional"}
