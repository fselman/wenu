"""Product-specific composition choices for declarative chart requests."""

from __future__ import annotations

from dataclasses import dataclass

from .detail import DetailPolicy
from .product_options import ChartProduct
from .style_overrides import ChartStyleOverrides


@dataclass(frozen=True)
class ChartProductCompositionOptions:
    """Detail and appearance choices for one exact chart product.

    Chart geometry deliberately remains outside this value.  It belongs to
    the chart family and frame request, independently of style and mode.
    """

    product: ChartProduct
    detail: DetailPolicy | None = None
    style_overrides: ChartStyleOverrides | None = None

    def __post_init__(self):
        if not isinstance(self.product, ChartProduct):
            raise TypeError("product must be a ChartProduct value.")
        if self.detail is not None and not isinstance(
            self.detail, DetailPolicy
        ):
            raise TypeError("detail must implement DetailPolicy.")
        if (
            self.style_overrides is not None
            and not isinstance(self.style_overrides, ChartStyleOverrides)
        ):
            raise TypeError(
                "style_overrides must be a ChartStyleOverrides value."
            )
