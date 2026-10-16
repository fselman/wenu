"""Installed atlas adapters for geometry, index and chart-page production."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import tempfile

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10, supported by the package.
    import tomli as tomllib

from wenu.atlas_design import AtlasDesignRequest, AtlasBandTiling
from wenu.resources import configuration_input_path, configuration_preset_names


def _layout_arguments(parser):
    geometry = parser.add_mutually_exclusive_group()
    geometry.add_argument('--design', type=Path, help='Resolved JSON path or installed atlas layout name.')
    geometry.add_argument('--layout', choices=configuration_preset_names('atlas-layout'),
        help='Installed atlas layout (default b4-portrait).')


def _layout_path(args):
    return configuration_input_path(args.design or args.layout or 'b4-portrait', kind='atlas-layout')


def _publish_json(destination, text):
    """Publish complete UTF-8 bytes atomically without replacing any file."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", newline="\n",
                prefix=".wenu-atlas-", suffix=".tmp",
                dir=destination.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        # A same-directory hard link gives an atomic no-clobber publication.
        os.link(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def design_main(argv=None):
    parser = argparse.ArgumentParser(
        prog="wenu_design_atlas",
        description="Resolve an atlas geometry TOML into validated JSON.",
        allow_abbrev=False,
    )
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument('--config', type=Path, help='Explicit atlas design request TOML or installed layout name.')
    choice.add_argument('--layout', choices=configuration_preset_names('atlas-layout'),
                        help='Installed resolved layout (default b4-portrait).')
    parser.add_argument("--output", required=True, type=Path,
                        help="New resolved JSON path; parent directory must exist.")
    args = parser.parse_args(argv)
    try:
        if args.output.suffix.lower() != ".json":
            raise ValueError("--output must have a .json extension.")
        if args.output.exists() or args.output.is_symlink():
            raise ValueError(f"Output already exists: {args.output}")
        if not args.output.parent.is_dir():
            raise ValueError("Output parent directory must exist.")
        source = configuration_input_path(args.config or args.layout or 'b4-portrait', kind='atlas-layout')
        if source.suffix == '.json':
            text = source.read_text()
            atlas = AtlasBandTiling.from_json(text)
        else:
            with source.open('rb') as stream:
                request = AtlasDesignRequest.from_dict(tomllib.load(stream))
            atlas = request.resolve()
            text = atlas.to_json()
        _publish_json(args.output, text)
    except (ValueError, OSError, UnicodeError) as exc:
        parser.error(str(exc))
    except KeyboardInterrupt:
        print("Atlas design interrupted.", file=sys.stderr)
        return 130
    print(f"Resolved {len(atlas.geometry.sheets)} sheets: {args.output}", file=sys.stderr)
    return 0


def plot_main(argv=None):
    parser = argparse.ArgumentParser(prog="wenu_plot_atlas",
        description="Render a resolved atlas JSON using independent presentation TOML.",
        allow_abbrev=False)
    _layout_arguments(parser)
    parser.add_argument('--config', type=Path, help='Atlas index TOML path or installed index preset name.')
    parser.add_argument("--output-prefix", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        from wenu.charts.atlas_index import AtlasIndexPresentation, plot_overview
        design = _layout_path(args)
        atlas = AtlasBandTiling.from_json(design.read_text())
        page = atlas.geometry.page
        default_index = 'b4-landscape' if page.width_mm > page.height_mm else 'b4-portrait'
        with configuration_input_path(args.config or default_index, kind='atlas-index').open('rb') as stream:
            presentation = AtlasIndexPresentation.from_dict(tomllib.load(stream))
        outputs = plot_overview(design, args.output_prefix, presentation=presentation)
    except (ValueError, OSError, UnicodeError) as exc:
        parser.error(str(exc))
    except KeyboardInterrupt:
        print("Atlas index interrupted.", file=sys.stderr)
        return 130
    for output in outputs:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(design_main())


def create_main(argv=None):
    parser = argparse.ArgumentParser(prog="wenu_create_atlas",
        description="Produce selected fixed ICRS atlas chart pages from resolved geometry.",
        allow_abbrev=False)
    _layout_arguments(parser)
    parser.add_argument('--config', type=Path, default=Path('atlas-v6'),
                        help='Full atlas presentation TOML path or installed style name (default atlas-v6).')
    parser.add_argument("--charts", default="all")
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--magnitude-limit", type=float,
        help="Override the presentation's stellar magnitude limit (-2 through 11).")
    from wenu.charts.style_overrides import add_magnitude_sizing_arguments
    add_magnitude_sizing_arguments(parser)
    parser.add_argument("--style", choices=("atlas", "cartoon"))
    parser.add_argument("--mode", choices=("print", "presentation"))
    parser.add_argument("--star-size-scale", type=float, help="Explicit diameter multiplier.")
    parser.add_argument("--legend", dest="chart_legend_visible",
        action=argparse.BooleanOptionalAction, default=None,
        help="Show or hide the stellar magnitude legend inside chart pages; reports are unchanged.")
    parser.add_argument("--planetary-nebulae", action=argparse.BooleanOptionalAction, default=None,
        help="Show or hide the planetary-nebula layer; overrides the presentation layer selection.")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--index", type=Path,
        help="One-page index PDF; enables even report pages facing odd chart pages.")
    parser.add_argument("--open-cluster-catalogue", type=Path,
        help="Versioned ECSV or active open_star_clusters.ecsv symlink; changes only open clusters. Requires a new sky.")
    parser.add_argument("--planetary-nebula-catalogue", type=Path,
        help="Versioned ECSV or active planetary_nebulae.ecsv symlink; changes only planetary nebulae. Requires a new sky.")
    parser.add_argument("--selection-criteria", type=Path, action="append", default=[],
        help="Catalogue-bound criteria JSON stored alongside its curated ECSV; repeat for each catalogue. Append verified PDF pages.")
    parser.add_argument("--open-cluster-size", choices=("angular", "fixed"),
        help="Open-cluster diameter at the central chart scale, with current symbol as minimum (default angular); fixed restores previous symbols.")
    sky = parser.add_mutually_exclusive_group()
    sky.add_argument("--save-sky", type=Path)
    sky.add_argument("--from-sky", type=Path)
    args = parser.parse_args(argv)
    try:
        from wenu.charts.atlas_publication import AtlasChartPresentation, create_atlas
        with configuration_input_path(args.config, kind='atlas-style').open('rb') as stream:
            presentation = AtlasChartPresentation.from_dict(tomllib.load(stream))
        from dataclasses import replace
        from wenu.charts.style_overrides import magnitude_sizing_from_arguments
        presentation = replace(presentation,
            stellar_magnitude_sizing=magnitude_sizing_from_arguments(args, presentation.stellar_magnitude_sizing),
            **{name: getattr(args, name) for name in ("style", "mode", "star_size_scale", "chart_legend_visible")
               if getattr(args, name) is not None})
        if args.planetary_nebulae is not None:
            layers = tuple(layer for layer in presentation.layers if layer != "planetary_nebulae")
            if args.planetary_nebulae:
                layers = presentation.layers if "planetary_nebulae" in presentation.layers else (*layers, "planetary_nebulae")
            presentation = replace(presentation, layers=layers)
        if args.open_cluster_size is not None:
            presentation = replace(presentation, open_cluster_angular_sizes=args.open_cluster_size == "angular")
        if args.magnitude_limit is not None:
            from dataclasses import replace
            presentation = replace(presentation, star_magnitude_limit=args.magnitude_limit)
        from wenu.cli.chart import main as chart_command
        output = create_atlas(_layout_path(args), args.output_dir, presentation=presentation,
            charts=args.charts, jobs=args.jobs, save_sky=args.save_sky, from_sky=args.from_sky,
            index=args.index, chart_command=chart_command,
            open_cluster_catalogue=args.open_cluster_catalogue,
            planetary_nebula_catalogue=args.planetary_nebula_catalogue,
            selection_criteria=args.selection_criteria)
    except (ValueError, TypeError, OSError, UnicodeError, RuntimeError) as exc:
        parser.error(str(exc))
    except KeyboardInterrupt:
        print("Atlas generation interrupted.", file=sys.stderr)
        return 130
    print(output)
    return 0
