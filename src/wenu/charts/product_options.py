"""Shared selection and naming for user-facing chart products."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


CHART_STYLES = ("atlas", "cartoon")
CHART_MODES = ("print", "presentation")


@dataclass(frozen=True, order=True)
class ChartProduct:
    """One canonical style and output-mode combination."""

    style: str
    mode: str

    def __post_init__(self):
        style = str(self.style).strip().lower()
        mode = str(self.mode).strip().lower()
        if style not in CHART_STYLES:
            raise ValueError(
                "style must be 'atlas' or 'cartoon'."
            )
        if mode not in CHART_MODES:
            raise ValueError(
                "mode must be 'print' or 'presentation'."
            )
        object.__setattr__(self, "style", style)
        object.__setattr__(self, "mode", mode)

    @property
    def suffix(self) -> str:
        return f"{self.style}-{self.mode}"


CANONICAL_CHART_PRODUCTS = tuple(
    ChartProduct(style, mode)
    for style in CHART_STYLES
    for mode in CHART_MODES
)


@dataclass(frozen=True)
class ChartProductOptions:
    """Resolved request for one or all canonical chart products."""

    output: Path
    style: str = "atlas"
    mode: str = "print"
    all_products: bool = False

    def __post_init__(self):
        product = ChartProduct(self.style, self.mode)
        object.__setattr__(self, "output", Path(self.output))
        object.__setattr__(self, "style", product.style)
        object.__setattr__(self, "mode", product.mode)
        object.__setattr__(self, "all_products", bool(self.all_products))

    @property
    def products(self) -> tuple[ChartProduct, ...]:
        if self.all_products:
            return CANONICAL_CHART_PRODUCTS
        return (ChartProduct(self.style, self.mode),)

    def output_path(
        self,
        product: ChartProduct,
        *,
        stem: str,
        extension: str = ".png",
    ) -> Path:
        """Return one deterministic path without creating directories."""
        if product not in self.products:
            raise ValueError("product is not selected by these options.")
        normalized_stem = str(stem).strip()
        if not normalized_stem:
            raise ValueError("stem cannot be empty.")
        suffix = str(extension).strip()
        if not suffix.startswith("."):
            suffix = "." + suffix
        if not self.all_products and self.output.suffix:
            return self.output
        return self.output / f"{normalized_stem}-{product.suffix}{suffix}"

    def outputs(self, *, stem: str, extension: str = ".png"):
        """Return products paired with their deterministic output paths."""
        return tuple(
            (
                product,
                self.output_path(
                    product,
                    stem=stem,
                    extension=extension,
                ),
            )
            for product in self.products
        )


def add_chart_product_arguments(parser, *, default_output):
    """Add the four common chart-product arguments to an ArgumentParser."""
    parser.add_argument(
        "--style",
        choices=CHART_STYLES,
        default="atlas",
        help="chart visual style (default: atlas)",
    )
    parser.add_argument(
        "--mode",
        choices=CHART_MODES,
        default="print",
        help="output medium (default: print)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(default_output),
        help="output file, or output directory with --all",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="all_products",
        help="generate atlas/cartoon in print/presentation modes",
    )
    return parser


def chart_product_options(arguments) -> ChartProductOptions:
    """Resolve parsed common arguments into one immutable request."""
    return ChartProductOptions(
        output=arguments.output,
        style=arguments.style,
        mode=arguments.mode,
        all_products=arguments.all_products,
    )
