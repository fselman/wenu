"""Copy the example Wenu notebooks into a user-selected directory."""

from __future__ import annotations

import argparse
import shutil
from importlib.resources import as_file, files
from pathlib import Path


def copy_notebooks(destination: Path, *, force: bool = False) -> list[Path]:
    """Copy the packaged Wenu notebooks to ``destination``.

    Parameters
    ----------
    destination
        Directory into which the notebooks will be copied.
    force
        If True, overwrite existing notebook files.

    Returns
    -------
    list[pathlib.Path]
        Paths of the notebooks copied.
    """
    destination = destination.expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)

    notebook_resource = files("wenu.notebooks")
    copied: list[Path] = []

    with as_file(notebook_resource) as source_directory:
        for source in sorted(source_directory.rglob("*.ipynb")):
            relative = source.relative_to(source_directory)
            target = destination / relative

            target.parent.mkdir(parents=True, exist_ok=True)

            if target.exists() and not force:
                print(f"Skipping existing file: {relative}")
                continue

            shutil.copy2(source, target)
            copied.append(target)
            print(f"Copied: {relative}")

    return copied


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="wenu_notebooks",
        description="Copy the Wenu example notebooks into a directory.",
    )

    parser.add_argument(
        "destination",
        nargs="?",
        default=".",
        help="Destination directory. Defaults to the current directory.",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite notebooks that already exist.",
    )

    return parser


def main() -> int:
    """Run the wenu_notebooks command."""
    parser = build_parser()
    args = parser.parse_args()

    destination = Path(args.destination)

    copied = copy_notebooks(
        destination,
        force=args.force,
    )

    if copied:
        print(f"\nCopied {len(copied)} notebook(s) to {destination.resolve()}")
    else:
        print("\nNo notebooks were copied.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
