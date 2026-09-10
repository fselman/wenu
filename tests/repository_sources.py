"""Immutable session-local inventory of repository Python sources."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from functools import cached_property, lru_cache
from pathlib import Path


ROOT = Path(__file__).parents[1]
SOURCE_ROOT_NAMES = ("src", "tests", "examples", "tools", "example_scripts")


@dataclass(frozen=True)
class RepositorySource:
    """One source file read and parsed once for architectural assertions."""

    path: Path

    @cached_property
    def text(self) -> str:
        """Read the source only when an assertion needs its contents."""

        return self.path.read_text(encoding="utf-8")

    @cached_property
    def tree(self) -> ast.Module:
        """Parse the source only when a syntax-aware assertion needs it."""

        return ast.parse(self.text, filename=str(self.path))


@lru_cache(maxsize=1)
def repository_sources() -> tuple[RepositorySource, ...]:
    """Return the complete, stable Python-source inventory for this test run."""

    paths = (
        path
        for name in SOURCE_ROOT_NAMES
        if (root := ROOT / name).is_dir()
        for path in root.rglob("*.py")
    )
    return tuple(
        RepositorySource(path=path)
        for path in sorted(paths)
    )


@lru_cache(maxsize=None)
def sources_below(path: Path) -> tuple[RepositorySource, ...]:
    """Select indexed sources below an absolute repository directory."""

    return tuple(
        source for source in repository_sources()
        if source.path.is_relative_to(path)
    )
