"""Public output-format vocabulary."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


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


@dataclass(frozen=True)
class SvgProvenance:
    """Portable provenance recorded in one SVG metadata element."""

    product_name: str
    parameters: Mapping[str, Any]
    title: str | None = None
    creator: str = "Wenu"
    credit: str = "Generated with Wenu"
    copyright: str | None = None
    license: str | None = None
    source_revision: str | None = None
    created_utc: str | None = None

    def __post_init__(self):
        product_name = str(self.product_name).strip()
        if not product_name:
            raise ValueError("product_name cannot be empty.")
        if not isinstance(self.parameters, Mapping):
            raise TypeError("parameters must be a mapping.")
        object.__setattr__(self, "product_name", product_name)
        object.__setattr__(self, "parameters", dict(self.parameters))
        for name in (
            "title", "creator", "credit", "copyright", "license",
            "source_revision", "created_utc",
        ):
            value = getattr(self, name)
            if value is not None:
                normalized = str(value).strip()
                object.__setattr__(self, name, normalized or None)
