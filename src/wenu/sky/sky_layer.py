"""Common contract for chartable celestial-sphere layers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar


class SkyLayer(ABC):
    """A source of spherical geometry for a celestial chart.

    Sky layers belong to the domain side of Wenu's rendering pipeline. They
    may carry semantic metadata and a default identity, but they do not
    project, clip, or render their geometry.
    """

    layer_name: ClassVar[str | None] = None

    def realize(
        self,
        context: Any,
        observer: Any,
        **geometry_options: Any,
    ) -> Any:
        """Adapt an explicit realization context to the legacy layer call."""
        del context
        return self.spherical_geometry(observer, **geometry_options)

    @abstractmethod
    def spherical_geometry(self, observer: Any) -> Any:
        """Return this layer's spherical geometry for ``observer``."""
        raise NotImplementedError
