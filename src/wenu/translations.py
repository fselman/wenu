"""Package-wide translation of generated visual labels."""

from __future__ import annotations

import json
from functools import lru_cache
from importlib.resources import files
from types import MappingProxyType


@lru_cache(maxsize=1)
def translation_dictionary():
    """Return the immutable packaged English-to-language dictionary."""
    resource = files("wenu.data").joinpath("translations.json")
    values = json.loads(resource.read_text(encoding="utf-8"))
    return MappingProxyType({
        language: MappingProxyType(labels)
        for language, labels in values.items()
    })


def translate_label(label: str, language: str = "en") -> str:
    """Translate one generated label, retaining unknown text unchanged."""
    language = str(language).strip().lower()
    dictionary = translation_dictionary()
    if language not in dictionary:
        raise ValueError(f"unsupported language: {language}")
    return dictionary[language].get(str(label), str(label))
