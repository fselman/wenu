from types import SimpleNamespace

import pytest

from wenu import (
    ResolvedStellarLegendInputs,
    resolve_stellar_legend_inputs,
)


class ComposedStyle:
    stars = SimpleNamespace(area_scale=0.75, color="#123456")

    def as_publication_style(self):
        return SimpleNamespace(
            star_area_scale=self.stars.area_scale,
            star_color=self.stars.color,
        )


def test_inputs_resolve_from_detail_and_composed_style():
    detail = SimpleNamespace(star_magnitude_limit=6.25)
    inputs = resolve_stellar_legend_inputs(detail, ComposedStyle())
    assert inputs == ResolvedStellarLegendInputs(
        effective_limit=6.25,
        area_scale=0.75,
        color="#123456",
        alpha=1.0,
    )


def test_publication_style_is_supported_directly():
    style = SimpleNamespace(
        star_area_scale=1.4,
        star_color="white",
        star_alpha=0.8,
    )
    inputs = resolve_stellar_legend_inputs(
        SimpleNamespace(star_magnitude_limit=4.0),
        style,
    )
    assert inputs.area_scale == pytest.approx(1.4)
    assert inputs.color == "white"
    assert inputs.alpha == pytest.approx(0.8)


def test_explicit_values_override_resolved_sources():
    inputs = resolve_stellar_legend_inputs(
        SimpleNamespace(star_magnitude_limit=6.0),
        ComposedStyle(),
        effective_limit=5.0,
        area_scale=2.0,
        color="red",
        alpha=0.5,
    )
    assert inputs == ResolvedStellarLegendInputs(
        effective_limit=5.0,
        area_scale=2.0,
        color="red",
        alpha=0.5,
    )


def test_missing_resolved_limit_is_rejected():
    with pytest.raises(ValueError, match="no stellar magnitude limit"):
        resolve_stellar_legend_inputs(
            SimpleNamespace(star_magnitude_limit=None),
            ComposedStyle(),
        )


def test_explicit_limit_preserves_legacy_call_pattern():
    inputs = resolve_stellar_legend_inputs(
        None,
        ComposedStyle(),
        effective_limit=3.0,
    )
    assert inputs.effective_limit == pytest.approx(3.0)


def test_invalid_area_scale_is_rejected():
    with pytest.raises(ValueError, match="positive"):
        resolve_stellar_legend_inputs(
            SimpleNamespace(star_magnitude_limit=5.0),
            ComposedStyle(),
            area_scale=0.0,
        )
