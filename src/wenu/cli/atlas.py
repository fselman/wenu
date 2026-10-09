"""Installed atlas adapters for geometry design and index presentation."""

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

from wenu.atlas_design import AtlasDesignRequest


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
        description="Resolve a version-1 atlas geometry TOML into validated JSON.",
        allow_abbrev=False,
    )
    parser.add_argument("--config", required=True, type=Path,
                        help="Explicit version-1 atlas design request TOML.")
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
        with args.config.open("rb") as stream:
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
    parser.add_argument("--design", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-prefix", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        from wenu.charts.atlas_index import AtlasIndexPresentation, plot_overview
        with args.config.open("rb") as stream:
            presentation = AtlasIndexPresentation.from_dict(tomllib.load(stream))
        outputs = plot_overview(args.design, args.output_prefix, presentation=presentation)
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
