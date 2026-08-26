"""Public output-format and SVG font-policy contracts."""

from __future__ import annotations

import pytest

from wenu.output_policy import (
    ChartOutputPolicy,
    OutputFormat,
    SvgFontPolicy,
)


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
    policy = ChartOutputPolicy(
        output_format="svg",
        svg_font_policy="editable",
    )

    assert policy.output_format is OutputFormat.SVG
    assert policy.svg_font_policy is SvgFontPolicy.EDITABLE


def test_output_policy_defaults_to_portable_png_publication():
    policy = ChartOutputPolicy()

    assert policy.output_format is OutputFormat.PNG
    assert policy.svg_font_policy is SvgFontPolicy.PUBLICATION


@pytest.mark.parametrize("value", ("jpeg", "", "SVG"))
def test_output_policy_rejects_unknown_or_noncanonical_format(value):
    with pytest.raises(ValueError, match="Unsupported output format"):
        ChartOutputPolicy(output_format=value)


@pytest.mark.parametrize("value", ("path", "none", "", "working"))
def test_output_policy_rejects_backend_or_unknown_font_vocabulary(value):
    with pytest.raises(ValueError, match="Unsupported SVG font policy"):
        ChartOutputPolicy(
            output_format=OutputFormat.SVG,
            svg_font_policy=value,
        )


@pytest.mark.parametrize("output_format", (OutputFormat.PNG, OutputFormat.PDF))
def test_editable_font_policy_requires_svg(output_format):
    with pytest.raises(
        ValueError,
        match="editable SVG font policy requires SVG output",
    ):
        ChartOutputPolicy(
            output_format=output_format,
            svg_font_policy=SvgFontPolicy.EDITABLE,
        )
