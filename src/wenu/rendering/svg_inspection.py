"""Backend-tolerant inspection of generated SVG documents.

This module observes serialized SVG structure.  It does not define Wenu's
future semantic SVG contract and deliberately ignores backend-generated IDs
and element ordering.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import re
import xml.etree.ElementTree as ET


SVG_NAMESPACE = "http://www.w3.org/2000/svg"
_DIMENSION = re.compile(
    r"^\s*"
    r"(?P<value>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)"
    r"(?P<unit>[A-Za-z%]*)"
    r"\s*$"
)


@dataclass(frozen=True)
class SvgDimension:
    """One numeric SVG dimension and its serialized unit."""

    value: float
    unit: str


@dataclass(frozen=True)
class SvgInspection:
    """Structural facts that are stable across ordinary SVG serializers."""

    width: SvgDimension
    height: SvgDimension
    view_box: tuple[float, float, float, float]
    element_counts: dict[str, int]
    raster_image_references: tuple[str, ...]
    root_namespace: str

    @property
    def has_svg_root(self):
        return self.root_namespace == SVG_NAMESPACE

    @property
    def has_raster_images(self):
        return bool(self.raster_image_references)

    def count(self, local_name):
        return self.element_counts.get(str(local_name), 0)


def _local_name(tag):
    return tag.rsplit("}", 1)[-1]


def _namespace(tag):
    if tag.startswith("{") and "}" in tag:
        return tag[1:].split("}", 1)[0]
    return ""


def _dimension(value, *, name):
    match = _DIMENSION.fullmatch(value or "")
    if match is None:
        raise ValueError(f"SVG {name} is missing or invalid: {value!r}.")
    return SvgDimension(
        value=float(match.group("value")),
        unit=match.group("unit"),
    )


def _view_box(value):
    fields = (value or "").replace(",", " ").split()
    if len(fields) != 4:
        raise ValueError(f"SVG viewBox must contain four numbers: {value!r}.")
    result = tuple(float(field) for field in fields)
    if result[2] <= 0.0 or result[3] <= 0.0:
        raise ValueError("SVG viewBox width and height must be positive.")
    return result


def inspect_svg(path):
    """Parse one SVG and return backend-tolerant structural facts."""
    root = ET.parse(Path(path)).getroot()
    if _local_name(root.tag) != "svg":
        raise ValueError("The document root is not an SVG element.")

    counts = Counter(_local_name(element.tag) for element in root.iter())
    raster_references = []
    for element in root.iter():
        if _local_name(element.tag) != "image":
            continue
        href = next(
            (
                value
                for key, value in element.attrib.items()
                if _local_name(key) == "href"
            ),
            "",
        )
        raster_references.append(href)

    return SvgInspection(
        width=_dimension(root.get("width"), name="width"),
        height=_dimension(root.get("height"), name="height"),
        view_box=_view_box(root.get("viewBox")),
        element_counts=dict(counts),
        raster_image_references=tuple(raster_references),
        root_namespace=_namespace(root.tag),
    )
