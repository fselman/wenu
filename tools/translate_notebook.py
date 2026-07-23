#!/usr/bin/env python3
"""
Translate Markdown cells in Wenu notebooks from English to Spanish.

This is a repository tool, not part of the installed ``wenu`` package.

Expected repository layout:

    wenu/
    ├── pyproject.toml
    ├── tools/
    │   ├── translate_notebook.py
    │   └── glossaries/
    │       └── en_es.json        # optional
    └── notebooks/
        ├── 01_introduction.ipynb
        ├── 02_planisphere.ipynb
        └── es/
            ├── 01_introduccion.ipynb
            └── 02_planisferio.ipynb

The tool:

- detects the Wenu repository root automatically;
- accepts either a notebook filename or a path;
- searches ``notebooks/`` recursively for a filename;
- writes Spanish notebooks under ``notebooks/es/`` by default;
- preserves code cells, raw cells, outputs, execution counts, and metadata;
- translates only Markdown cells;
- batches Markdown cells to reduce API overhead;
- uses a Wenu terminology glossary;
- writes a checkpoint after every completed API request;
- can skip translation when the output is newer than the source;
- supports explicit source and output paths when needed.

Requirements:

    python -m pip install --upgrade openai nbformat

Environment:

    export OPENAI_API_KEY="..."
    export OPENAI_MODEL="gpt-5.6-luna"   # optional

Examples:

    python tools/translate_notebook.py 01_introduction.ipynb

    python tools/translate_notebook.py \
        notebooks/02_planisphere.ipynb \
        --output notebooks/es/02_planisferio.ipynb

    python tools/translate_notebook.py 01_introduction.ipynb --force

    python tools/translate_notebook.py 01_introduction.ipynb --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import nbformat
from openai import APIConnectionError, APIStatusError, OpenAI, RateLimitError


DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.6-luna")
DEFAULT_BATCH_CHARS = 14_000

DEFAULT_GLOSSARY: dict[str, str] = {
    "altitude": "altura",
    "azimuth": "acimut",
    "celestial equator": "ecuador celeste",
    "celestial sphere": "esfera celeste",
    "chart": "carta celeste",
    "constellation boundary": "límite de constelación",
    "constellation lines": "líneas de constelación",
    "coordinate frame": "sistema de referencia",
    "ecliptic": "eclíptica",
    "galactic plane": "plano galáctico",
    "horizon": "horizonte",
    "layer": "capa",
    "Milky Way": "Vía Láctea",
    "observer": "observador",
    "planisphere": "planisferio",
    "projection": "proyección",
    "renderer": "renderizador",
    "sky chart": "carta celeste",
    "stereographic projection": "proyección estereográfica",
    "viewport": "ventana gráfica",
    "zenith": "cenit",
}

PROTECTED_PATTERNS = (
    "fenced code blocks",
    "inline code",
    "LaTeX and MathJax expressions",
    "URLs",
    "file paths",
    "Python identifiers",
    "class, method, function, module, package, and variable names",
    "command-line commands and options",
    "HTML tags",
    "Markdown structure",
)


def find_repository_root(start: Path | None = None) -> Path:
    """Find the nearest parent containing pyproject.toml and src/wenu."""
    current = (start or Path.cwd()).resolve()

    for candidate in (current, *current.parents):
        if (
            (candidate / "pyproject.toml").is_file()
            and (candidate / "src" / "wenu").is_dir()
        ):
            return candidate

    script_path = Path(__file__).resolve()
    for candidate in (script_path.parent, *script_path.parents):
        if (
            (candidate / "pyproject.toml").is_file()
            and (candidate / "src" / "wenu").is_dir()
        ):
            return candidate

    raise SystemExit(
        "Could not locate the Wenu repository root. Expected a parent directory "
        "containing pyproject.toml and src/wenu/."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Translate Markdown cells in a Wenu notebook."
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Notebook path or filename to locate under notebooks/",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output path; default is notebooks/es/<source filename>",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"OpenAI model ID (default: {DEFAULT_MODEL!r})",
    )
    parser.add_argument("--source-language", default="English")
    parser.add_argument("--target-language", default="Spanish")
    parser.add_argument(
        "--batch-chars",
        type=int,
        default=DEFAULT_BATCH_CHARS,
        help="Approximate maximum source characters per API request",
    )
    parser.add_argument(
        "--glossary",
        type=Path,
        help=(
            "Optional JSON glossary. By default, the tool also loads "
            "tools/glossaries/en_es.json when present."
        ),
    )
    parser.add_argument(
        "--start-cell",
        type=int,
        default=0,
        help="Skip Markdown cells before this notebook cell index",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=4,
        help="Maximum attempts for each API request",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Seconds to wait after each successful API request",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing output, even when it is newer than the source",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show paths and planned batches without calling the API",
    )
    return parser.parse_args()


def resolve_input(root: Path, requested: Path) -> Path:
    """Resolve a supplied path or locate a notebook filename under notebooks/."""
    candidates = [
        requested,
        root / requested,
        root / "notebooks" / requested,
    ]

    for candidate in candidates:
        candidate = candidate.expanduser().resolve()
        if candidate.is_file():
            return candidate

    if requested.parent == Path("."):
        search_roots = (
            root / "src" / "wenu" / "notebooks" / "en",
            root / "notebooks" / "en",
            root / "notebooks",
        )

        matches = sorted(
            path
            for search_root in search_roots
            if search_root.is_dir()
            for path in search_root.rglob(requested.name)
        )

        if len(matches) == 1:
            return matches[0].resolve()

        if len(matches) > 1:
            formatted = "\n".join(f"  - {path}" for path in matches)
            raise SystemExit(
                f"Notebook name is ambiguous: {requested.name}\n{formatted}"
            )

    raise SystemExit(f"Could not find notebook: {requested}")


def default_output_path(root: Path, source: Path) -> Path:
    """Map a notebook under an English directory to its Spanish counterpart."""

    notebook_roots = (
        root / "src" / "wenu" / "notebooks",
        root / "notebooks",
    )

    for notebooks_dir in notebook_roots:
        notebooks_dir = notebooks_dir.resolve()

        try:
            relative = source.resolve().relative_to(notebooks_dir)
        except ValueError:
            continue

        if relative.parts and relative.parts[0] == "en":
            return notebooks_dir / "es" / Path(*relative.parts[1:])

        if relative.parts and relative.parts[0] == "es":
            raise SystemExit(
                "The source notebook is already inside a Spanish notebook directory."
            )

        return notebooks_dir / "es" / relative

    return source.parent / "es" / source.name

def resolve_output(root: Path, source: Path, requested: Path | None) -> Path:
    if requested is None:
        return default_output_path(root, source)

    if requested.is_absolute():
        return requested.expanduser().resolve()

    return (root / requested).resolve()


def load_glossary(root: Path, explicit_path: Path | None) -> dict[str, str]:
    glossary = dict(DEFAULT_GLOSSARY)

    paths: list[Path] = []
    default_path = root / "tools" / "glossaries" / "en_es.json"
    if default_path.is_file():
        paths.append(default_path)

    if explicit_path is not None:
        path = explicit_path
        if not path.is_absolute():
            path = root / path
        paths.append(path.resolve())

    for path in paths:
        try:
            user_glossary = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SystemExit(f"Could not read glossary {path}: {exc}") from exc

        if not isinstance(user_glossary, dict):
            raise SystemExit(f"Glossary {path} must contain a JSON object.")

        for source, target in user_glossary.items():
            if not isinstance(source, str) or not isinstance(target, str):
                raise SystemExit(
                    f"Every glossary key and value in {path} must be a string."
                )
            glossary[source] = target

    return glossary


def markdown_cells(
    notebook: nbformat.NotebookNode,
    start_cell: int,
) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []

    for index, cell in enumerate(notebook.cells):
        if index < start_cell or cell.cell_type != "markdown":
            continue

        source = str(cell.source)
        if not source.strip():
            continue

        cells.append(
            {
                "id": f"cell-{index}",
                "index": index,
                "source": source,
            }
        )

    return cells


def make_batches(
    cells: list[dict[str, Any]],
    max_chars: int,
) -> list[list[dict[str, Any]]]:
    if max_chars <= 0:
        raise SystemExit("--batch-chars must be greater than zero.")

    batches: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_chars = 0

    for cell in cells:
        size = len(cell["source"])

        if current and current_chars + size > max_chars:
            batches.append(current)
            current = []
            current_chars = 0

        current.append(cell)
        current_chars += size

    if current:
        batches.append(current)

    return batches


def glossary_text(glossary: dict[str, str]) -> str:
    entries = sorted(glossary.items(), key=lambda item: item[0].casefold())
    return "\n".join(f"- {source} → {target}" for source, target in entries)


def build_instructions(
    source_language: str,
    target_language: str,
    glossary: dict[str, str],
) -> str:
    protected = "\n".join(f"- {item}" for item in PROTECTED_PATTERNS)

    return f"""You translate technical Jupyter-notebook documentation from
{source_language} into {target_language}.

Return only one valid JSON object. It must map each supplied cell ID to its
translated Markdown string. Include every supplied ID exactly once. Do not add
commentary or Markdown fences around the JSON.

Translate prose accurately and naturally. Preserve meaning, technical precision,
paragraph boundaries, headings, lists, tables, block quotes, emphasis, links,
and footnotes.

Do not translate or modify:
{protected}

Never translate the proper names "Wenu", "Python", "NumPy", "Astropy",
"Skyfield", "Matplotlib", "Jupyter", or "OpenAI".

Use this glossary consistently. When context requires a grammatical change,
preserve the intended terminology rather than translating mechanically:
{glossary_text(glossary)}
"""


def build_input(batch: list[dict[str, Any]]) -> str:
    payload = [
        {"id": cell["id"], "markdown": cell["source"]}
        for cell in batch
    ]
    return json.dumps(payload, ensure_ascii=False)


def strip_json_fence(text: str) -> str:
    match = re.fullmatch(
        r"\s*```(?:json)?\s*(.*?)\s*```\s*",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    return match.group(1) if match else text.strip()


def parse_translation(
    text: str,
    expected_ids: set[str],
) -> dict[str, str]:
    try:
        result = json.loads(strip_json_fence(text))
    except json.JSONDecodeError as exc:
        raise ValueError(f"The model did not return valid JSON: {exc}") from exc

    if not isinstance(result, dict):
        raise ValueError("The model response must be a JSON object.")

    returned_ids = set(result)
    missing = expected_ids - returned_ids
    extra = returned_ids - expected_ids

    if missing or extra:
        details = []
        if missing:
            details.append(f"missing IDs: {sorted(missing)}")
        if extra:
            details.append(f"unexpected IDs: {sorted(extra)}")
        raise ValueError("; ".join(details))

    for cell_id, translation in result.items():
        if not isinstance(translation, str):
            raise ValueError(f"{cell_id!r} does not map to a string.")

    return result


def translate_batch(
    client: OpenAI,
    model: str,
    instructions: str,
    batch: list[dict[str, Any]],
    retries: int,
) -> dict[str, str]:
    expected_ids = {cell["id"] for cell in batch}
    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            response = client.responses.create(
                model=model,
                instructions=instructions,
                input=build_input(batch),
            )
            return parse_translation(response.output_text, expected_ids)

        except (RateLimitError, APIConnectionError, APIStatusError, ValueError) as exc:
            last_error = exc
            if attempt == retries:
                break

            wait = min(2 ** (attempt - 1), 20)
            print(
                f"  Attempt {attempt}/{retries} failed: {exc}\n"
                f"  Retrying in {wait} seconds...",
                file=sys.stderr,
            )
            time.sleep(wait)

    assert last_error is not None
    raise RuntimeError(
        f"Translation failed after {retries} attempts: {last_error}"
    ) from last_error


def write_notebook(notebook: nbformat.NotebookNode, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, path)


def output_is_current(source: Path, output: Path) -> bool:
    return output.is_file() and output.stat().st_mtime >= source.stat().st_mtime


def main() -> int:
    args = parse_args()
    root = find_repository_root()
    source = resolve_input(root, args.input)
    output = resolve_output(root, source, args.output)

    if source.suffix.lower() != ".ipynb":
        raise SystemExit("The input file must have the .ipynb extension.")
    if output.suffix.lower() != ".ipynb":
        raise SystemExit("The output file must have the .ipynb extension.")
    if source == output:
        raise SystemExit("Input and output paths must be different.")

    if output.exists() and not args.force:
        if output_is_current(source, output):
            print(f"Skipping: translation is already current.\n{output}")
            return 0
        raise SystemExit(
            f"Output exists but is older than the source:\n{output}\n"
            "Use --force to regenerate it."
        )

    glossary = load_glossary(root, args.glossary)
    notebook = nbformat.read(source, as_version=4)
    cells = markdown_cells(notebook, args.start_cell)
    batches = make_batches(cells, args.batch_chars)

    print(f"Repository:     {root}")
    print(f"Input:          {source}")
    print(f"Output:         {output}")
    print(f"Model:          {args.model}")
    print(f"Markdown cells: {len(cells)}")
    print(f"API requests:   {len(batches)}")

    if args.dry_run:
        for number, batch in enumerate(batches, start=1):
            indices = [cell["index"] for cell in batch]
            chars = sum(len(cell["source"]) for cell in batch)
            print(
                f"Batch {number}: cells {indices}, "
                f"{len(batch)} Markdown cells, {chars} characters"
            )
        return 0

    if not cells:
        print("No non-empty Markdown cells found. Writing an unchanged copy.")
        write_notebook(notebook, output)
        return 0

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not defined.")

    client = OpenAI()
    instructions = build_instructions(
        args.source_language,
        args.target_language,
        glossary,
    )

    partial_path = output.with_suffix(".partial.ipynb")

    for number, batch in enumerate(batches, start=1):
        indices = [cell["index"] for cell in batch]
        print(f"Translating batch {number}/{len(batches)}: cells {indices}")

        translations = translate_batch(
            client=client,
            model=args.model,
            instructions=instructions,
            batch=batch,
            retries=args.retries,
        )

        for cell in batch:
            notebook.cells[cell["index"]].source = translations[cell["id"]]

        write_notebook(notebook, partial_path)

        if args.delay > 0:
            time.sleep(args.delay)

    write_notebook(notebook, output)

    if partial_path.exists():
        partial_path.unlink()

    print(f"Finished: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
