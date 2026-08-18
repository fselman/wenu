"""Shared generated-label translation dictionary."""

import pytest

from wenu.translations import translate_label, translation_dictionary


def test_packaged_spanish_reference_labels_are_canonical():
    labels = translation_dictionary()["es"]

    assert labels["Celestial equator"] == "Ecuador celeste"
    assert labels["Ecliptic"] == "Eclíptica"
    assert labels["Galactic plane"] == "Plano galáctico"
    assert labels["Taurus"] == "Tauro"
    assert labels["Scorpius"] == "Escorpio"


def test_translation_retains_unknown_generated_text():
    assert translate_label("Aries", "es") == "Aries"


def test_translation_rejects_unsupported_language():
    with pytest.raises(ValueError, match="unsupported language"):
        translate_label("Ecliptic", "xx")
