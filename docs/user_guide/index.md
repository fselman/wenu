# Wenu v0.8 user guide

Wenu produces reproducible static sky charts through six canonical example
families. Each example uses the same chart composition and export pipeline and
supports atlas and cartoon styles in print and presentation modes.

## Install and run

From a checkout of Wenu:

```bash
pip install -e .
python examples/planisphere.py --style atlas --mode print
```

The canonical examples are:

| Chart family | Example | Guide |
|---|---|---|
| Galactic Mollweide all-sky map | `examples/all_sky.py` | [All-sky map](all_sky.md) |
| Visible-sky planisphere | `examples/planisphere.py` | [Planisphere](planisphere.md) |
| Constellation group | `examples/regional_constellation_group.py` | [Regional charts](regional_charts.md) |
| Single constellation | `examples/regional_constellation.py` | [Regional charts](regional_charts.md) |
| Circumpolar field | `examples/circumpolar.py` | [Circumpolar charts](circumpolar_charts.md) |
| Selected binocular object | `examples/binocular_object.py` | [Binocular charts](binocular_charts.md) |

## Common request model

Every example accepts:

```text
--style atlas|cartoon
--mode print|presentation
--output PATH
--all-products
```

A normal invocation writes one product. `--all-products` writes the four style/mode
products to a directory with deterministic names. See
[Styles, modes, detail, and furniture](styles_modes_detail.md) for shared
content, appearance, legend, reference, and credit options.

Use [`wenu_chart` and editable TOML profiles](configuration.md) to generate
any family through one installed command and keep publication, presentation,
outreach, location, or observing choices outside Wenu source.

Generated gallery products belong below `output/` and are not committed. The
one exception is the approved README image; its exact provenance is recorded
in [the planisphere guide](planisphere.md#readme-image-provenance).
