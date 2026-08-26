"""Public output-format and SVG font-policy vocabulary."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class OutputFormat(str, Enum):
    """Supported static chart output formats."""

    PNG = "png"
    PDF = "pdf"
    SVG = "svg"

    @property
    def extension(self) -> str:
        """Return the canonical filename extension."""
        return f".{self.value}"


class SvgFontPolicy(str, Enum):
    """Public SVG text portability and editability choices."""

    PUBLICATION = "publication"
    EDITABLE = "editable"


@dataclass(frozen=True)
class ChartOutputPolicy:
    """One validated output format and SVG font policy."""

    output_format: OutputFormat = OutputFormat.PNG
    svg_font_policy: SvgFontPolicy = SvgFontPolicy.PUBLICATION

    def __post_init__(self):
        try:
            output_format = OutputFormat(self.output_format)
        except ValueError as error:
            raise ValueError(
                f"Unsupported output format: {self.output_format!r}."
            ) from error
        try:
            svg_font_policy = SvgFontPolicy(self.svg_font_policy)
        except ValueError as error:
            raise ValueError(
                f"Unsupported SVG font policy: {self.svg_font_policy!r}."
            ) from error
        if (
            output_format is not OutputFormat.SVG
            and svg_font_policy is not SvgFontPolicy.PUBLICATION
        ):
            raise ValueError(
                "An editable SVG font policy requires SVG output."
            )
        object.__setattr__(self, "output_format", output_format)
        object.__setattr__(self, "svg_font_policy", svg_font_policy)
