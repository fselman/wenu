"""Public output-format vocabulary."""

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


@dataclass(frozen=True)
class ChartOutputPolicy:
    """One validated static chart output format."""

    output_format: OutputFormat = OutputFormat.PNG

    def __post_init__(self):
        try:
            output_format = OutputFormat(self.output_format)
        except ValueError as error:
            raise ValueError(
                f"Unsupported output format: {self.output_format!r}."
            ) from error
        object.__setattr__(self, "output_format", output_format)
