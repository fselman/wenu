"""Install Wenu's canonical example scripts in the current directory."""

from __future__ import annotations

import argparse
import shutil
from importlib.resources import files
from pathlib import Path


DEFAULT_DIRECTORY = "wenu_examples"


def copy_examples(destination: Path, *, force: bool = False) -> list[Path]:
    """Copy the packaged example scripts into ``destination``."""
    destination = destination.expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)

    copied: list[Path] = []
    resources = files("wenu.example_scripts")
    sources = sorted(
        resource
        for resource in resources.iterdir()
        if resource.name.endswith(".py")
        and resource.name != "__init__.py"
    )

    for source in sources:
        target = destination / source.name
        if target.exists() and not force:
            print(f"Skipping existing file: {source.name}")
            continue

        with source.open("rb") as source_file, target.open("wb") as target_file:
            shutil.copyfileobj(source_file, target_file)
        copied.append(target)

    return copied


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="wenu_examples",
        description="Install Wenu's canonical example scripts.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite example scripts that already exist.",
    )
    return parser


def main() -> int:
    """Run the ``wenu_examples`` command."""
    arguments = build_parser().parse_args()
    destination = Path.cwd() / DEFAULT_DIRECTORY
    copied = copy_examples(destination, force=arguments.force)

    if copied:
        print(f"Installed {len(copied)} Wenu example script(s) in {destination}:")
        for path in copied:
            print(f"  {path.name}")
    else:
        print(f"No example scripts installed in {destination}.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
