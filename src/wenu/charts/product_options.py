"""Shared selection and naming for user-facing chart products."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from wenu.output_policy import OutputFormat, SvgFontPolicy


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


def _packaged_product_defaults():
    from wenu.configuration import (
        packaged_furniture_product_export_defaults,
    )

    return packaged_furniture_product_export_defaults().product


@dataclass(frozen=True)
class ChartProductOptions:
    """Resolved request for one or all canonical chart products."""

    output: Path
    style: str = "atlas"
    mode: str = "print"
    all_products: bool = False
    output_format: OutputFormat | None = None
    svg_font_policy: SvgFontPolicy = SvgFontPolicy.PUBLICATION

    def __post_init__(self):
        product = ChartProduct(self.style, self.mode)
        object.__setattr__(self, "output", Path(self.output))
        object.__setattr__(self, "style", product.style)
        object.__setattr__(self, "mode", product.mode)
        object.__setattr__(self, "all_products", bool(self.all_products))
        if self.output_format is not None:
            try:
                output_format = OutputFormat(self.output_format)
            except ValueError as error:
                raise ValueError(
                    f"Unsupported output format: {self.output_format!r}."
                ) from error
            object.__setattr__(self, "output_format", output_format)
        try:
            font_policy = SvgFontPolicy(self.svg_font_policy)
        except ValueError as error:
            raise ValueError(
                f"Unsupported SVG font policy: {self.svg_font_policy!r}."
            ) from error
        if (
            font_policy is SvgFontPolicy.EDITABLE
            and self.output_format not in (None, OutputFormat.SVG)
        ):
            raise ValueError(
                "An editable SVG font policy requires SVG output."
            )
        object.__setattr__(self, "svg_font_policy", font_policy)

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
        extension: str | None = None,
    ) -> Path:
        """Return one deterministic path without creating directories."""
        if product not in self.products:
            raise ValueError("product is not selected by these options.")
        normalized_stem = str(stem).strip()
        if not normalized_stem:
            raise ValueError("stem cannot be empty.")
        configured_extension = (
            _packaged_product_defaults().extension
            if extension is None else extension
        )
        suffix = str(
            self.output_format.extension
            if self.output_format is not None
            else configured_extension
        ).strip()
        if not suffix.startswith("."):
            suffix = "." + suffix
        if not self.all_products and self.output.suffix:
            if (
                self.output_format is not None
                and self.output.suffix.lower() != self.output_format.extension
            ):
                raise ValueError(
                    "Output filename extension contradicts explicit format."
                )
            return self.output
        return self.output / f"{normalized_stem}-{product.suffix}{suffix}"

    def outputs(self, *, stem: str, extension: str | None = None):
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
    parser.allow_abbrev = False
    defaults = _packaged_product_defaults()
    parser.add_argument(
        "--style",
        choices=CHART_STYLES,
        default=None,
        help=(
            "chart visual style "
            f"(default: {defaults.product.style})"
        ),
    )
    parser.add_argument(
        "--mode",
        choices=CHART_MODES,
        default=None,
        help=(
            "output medium "
            f"(default: {defaults.product.mode})"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(default_output),
        help="output file, or output directory with --all-products",
    )
    parser.add_argument(
        "--format",
        choices=tuple(item.value for item in OutputFormat),
        dest="output_format",
        help="explicit output format: png, pdf, or svg",
    )
    parser.add_argument(
        "--svg-font-policy",
        choices=tuple(item.value for item in SvgFontPolicy),
        help=(
            "SVG text policy: publication paths or editable text "
            "(default: publication)"
        ),
    )
    parser.add_argument(
        "--all-products",
        action="store_true",
        dest="all_products",
        default=None,
        help="generate atlas/cartoon in print/presentation modes",
    )
    return parser


def chart_product_options(arguments, *, defaults=None) -> ChartProductOptions:
    """Resolve parsed common arguments into one immutable request."""
    defaults = _packaged_product_defaults() if defaults is None else defaults
    return ChartProductOptions(
        output=arguments.output,
        style=(
            defaults.product.style
            if arguments.style is None else arguments.style
        ),
        mode=(
            defaults.product.mode
            if arguments.mode is None else arguments.mode
        ),
        all_products=(
            defaults.all_products
            if arguments.all_products is None else arguments.all_products
        ),
        output_format=arguments.output_format,
        svg_font_policy=(
            SvgFontPolicy.PUBLICATION
            if arguments.svg_font_policy is None
            else arguments.svg_font_policy
        ),
    )
