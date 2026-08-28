"""Astronomical position-provider boundary."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from wenu.geometry import SphericalPoints


@runtime_checkable
class PositionProvider(Protocol):
    """Generate native astronomical positions without transforming them."""

    def position(self, instant: str | None = None) -> SphericalPoints:
        """Return native positions for the requested physical instant."""
        ...
