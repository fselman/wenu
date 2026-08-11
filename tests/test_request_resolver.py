"""Declarative request resolution and profile-validation contracts."""

from pathlib import Path

import pytest

from wenu import (
    CANONICAL_MAXIMAL_SPHERE_PROFILE,
    ChartContentExclusions,
    ChartObserverRequest,
    ChartProductOptions,
    ChartRequest,
    ChartSubjectRequest,
    DetailOverrides,
    SkyContentSelection,
    resolve_chart_request,
)


def request(
    *, family="binocular", subject=None, detail=None, content=None,
    exclusions=None,
):
    return ChartRequest(
        observer=ChartObserverRequest(
            location="La Ligua", time="2026-08-15 22:00"
        ),
        family=family,
        subject=subject or ChartSubjectRequest(target="M57"),
        detail=detail or DetailOverrides(),
        content=content or SkyContentSelection(),
        exclusions=exclusions or ChartContentExclusions(),
        product=ChartProductOptions(output=Path("output/chart.png")),
    )


def test_target_component_is_retained_independently_of_general_thresholds():
    resolved = resolve_chart_request(
        request(
            detail=DetailOverrides(star_magnitude_limit=6.0),
            content=SkyContentSelection(
                planetary_nebulae={"another nebula"}
            ),
        ),
        CANONICAL_MAXIMAL_SPHERE_PROFILE,
    )

    assert resolved.target.key == "m57"
    assert resolved.request.content.planetary_nebulae == {
        "another nebula", "PN G063.1+13.9"
    }


def test_constellation_resolution_populates_internal_identities_and_content():
    resolved = resolve_chart_request(
        request(
            family="regional",
            subject=ChartSubjectRequest(group="galactic-center"),
        ),
        CANONICAL_MAXIMAL_SPHERE_PROFILE,
    )

    assert resolved.constellations.line_constellations[-2:] == (
        "Ser1", "Ser2"
    )
    assert resolved.request.content.constellation_boundaries == {
        "Sgr", "Sco", "Oph", "Ser"
    }
    assert "NGC 6475" in resolved.request.content.open_clusters


def test_group_content_can_be_explicitly_excluded():
    resolved = resolve_chart_request(
        request(
            family="regional",
            subject=ChartSubjectRequest(group="galactic-center"),
            exclusions=ChartContentExclusions(
                open_clusters={"NGC 6475"}
            ),
        ),
        CANONICAL_MAXIMAL_SPHERE_PROFILE,
    )

    assert "NGC 6475" not in resolved.request.content.open_clusters


def test_conflicting_explicit_content_is_rejected():
    with pytest.raises(ValueError, match="both include and exclude"):
        resolve_chart_request(
            request(
                content=SkyContentSelection(open_clusters={"NGC 6475"}),
                exclusions=ChartContentExclusions(
                    open_clusters={"NGC 6475"}
                ),
            ),
            CANONICAL_MAXIMAL_SPHERE_PROFILE,
        )


def test_central_target_cannot_be_excluded():
    with pytest.raises(ValueError, match="central target cannot be excluded"):
        resolve_chart_request(
            request(
                exclusions=ChartContentExclusions(
                    planetary_nebulae={"PN G063.1+13.9"}
                )
            ),
            CANONICAL_MAXIMAL_SPHERE_PROFILE,
        )


@pytest.mark.parametrize(
    ("detail", "field"),
    [
        (DetailOverrides(star_magnitude_limit=12.0), "star_magnitude_limit"),
        (DetailOverrides(galaxy_magnitude_limit=13.0), "galaxy_magnitude_limit"),
        (DetailOverrides(extended_object_samples=121), "extended_object_samples"),
    ],
)
def test_request_cannot_exceed_the_selected_load_profile(detail, field):
    with pytest.raises(ValueError, match=field):
        resolve_chart_request(
            request(detail=detail), CANONICAL_MAXIMAL_SPHERE_PROFILE
        )


def test_resolution_does_not_mutate_the_immutable_input_request():
    original = request()
    resolved = resolve_chart_request(
        original, CANONICAL_MAXIMAL_SPHERE_PROFILE
    )

    assert original.content.planetary_nebulae is None
    assert resolved.request is not original


def test_binocular_family_supplies_a_sensible_default_field():
    resolved = resolve_chart_request(
        request(), CANONICAL_MAXIMAL_SPHERE_PROFILE
    )

    assert resolved.frame.field_diameter_deg == pytest.approx(6.5)
    assert resolved.frame.source == "family-default"


def test_packaged_group_supplies_framing_but_request_overrides_it():
    grouped = resolve_chart_request(
        request(
            family="regional",
            subject=ChartSubjectRequest(group="summer-triangle"),
        ),
        CANONICAL_MAXIMAL_SPHERE_PROFILE,
    )

    assert grouped.frame.field_width_deg == pytest.approx(143.52)
    assert grouped.frame.field_height_deg == pytest.approx(104.0)
    assert grouped.frame.source == "packaged-group"


def test_arbitrary_constellation_set_defers_automatic_field_to_geometry():
    resolved = resolve_chart_request(
        request(
            family="regional",
            subject=ChartSubjectRequest(constellations=("Cru", "Cen")),
        ),
        CANONICAL_MAXIMAL_SPHERE_PROFILE,
    )

    assert resolved.frame.automatic_from_geometry is True
    assert resolved.frame.field_width_deg is None


def test_resolver_rejects_untyped_inputs():
    with pytest.raises(TypeError, match="request must be"):
        resolve_chart_request(object(), CANONICAL_MAXIMAL_SPHERE_PROFILE)
    with pytest.raises(TypeError, match="profile must be"):
        resolve_chart_request(request(), object())
