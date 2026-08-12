"""Immutable declarative chart-request contracts."""

from dataclasses import FrozenInstanceError
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from wenu import (
    ChartContentExclusions,
    ChartFrameRequest,
    ChartObserverRequest,
    ChartProduct,
    ChartProductCompositionOptions,
    ChartProductOptions,
    ChartRequest,
    ChartSubjectRequest,
    DetailOverrides,
    FixedDetailPolicy,
    ResolvedDetail,
    SkyContentSelection,
)
from wenu.observer import Observer


def observer():
    return ChartObserverRequest(
        location="La Ligua",
        time="2026-08-15 22:00",
    )


def product():
    return ChartProductOptions(
        output=Path("output/chart.png"),
        style="atlas",
        mode="presentation",
    )


def test_named_observer_is_independent_of_display_furniture():
    request = observer()

    assert request.observer_kwargs() == {
        "time": "2026-08-15 22:00",
        "location": "La Ligua",
        "lat_deg": None,
        "lon_deg": None,
        "elevation_m": None,
        "timezone_name": None,
    }


def test_observer_request_matches_its_normalized_scientific_observer():
    request = observer()
    actual = SimpleNamespace(
        lat_deg=-32.443342,
        lon_deg=-71.230289,
        elevation_m=52.0,
        utc_datetime=datetime.fromisoformat("2026-08-16T02:00:00+00:00"),
    )

    assert request.matches(actual) is True
    actual.lon_deg = -71.0
    assert request.matches(actual) is False


def test_observer_identity_resolution_does_not_construct_an_ephemeris(
    monkeypatch,
):
    monkeypatch.setattr(
        Observer,
        "__init__",
        lambda self, **kwargs: pytest.fail("must not construct Observer"),
    )

    identity = observer().scientific_identity()

    assert identity[:3] == (-32.443342, -71.230289, 52.0)


def test_explicit_observer_coordinates_are_normalized():
    request = ChartObserverRequest(
        time=datetime.fromisoformat("2026-08-15T22:00:00-04:00"),
        lat_deg=-33,
        lon_deg=-71.5,
    )

    assert request.elevation_m == 0.0
    with pytest.raises(ValueError, match="either a named location"):
        ChartObserverRequest(
            location="Papudo",
            time="2026-08-15 22:00",
            lat_deg=-32.5,
            lon_deg=-71.4,
        )


def test_target_and_coordinate_subjects_are_unambiguous():
    named = ChartSubjectRequest(target=" M57 ")
    coordinate = ChartSubjectRequest(
        ra_deg=-10.0,
        dec_deg=-20.0,
        display_name="Custom target",
    )

    assert named.target == "M57"
    assert coordinate.ra_deg == 350.0
    with pytest.raises(ValueError, match="only one subject form"):
        ChartSubjectRequest(target="M57", ra_deg=1.0, dec_deg=2.0)


def test_constellation_subjects_are_normalized_and_unique():
    subject = ChartSubjectRequest(constellations=("cen", "Cru", "mus"))

    assert subject.constellations == ("CEN", "CRU", "MUS")
    with pytest.raises(ValueError, match="unique"):
        ChartSubjectRequest(constellations=("Cru", "cru"))


def test_binocular_request_expresses_recent_m57_use_case():
    request = ChartRequest(
        observer=observer(),
        family="BINOCULAR",
        subject=ChartSubjectRequest(target="M57"),
        frame=ChartFrameRequest(field_diameter_deg=6.5),
        detail=DetailOverrides(star_magnitude_limit=11.0),
        product=product(),
        title="M57",
    )

    assert request.family == "binocular"
    assert request.projection == "stereographic"
    assert request.coordinate_frame == "horizontal"
    assert request.subject.target == "M57"
    assert request.frame.field_diameter_deg == 6.5
    assert request.detail.star_magnitude_limit == 11.0


def test_request_normalizes_implemented_projection_geometry():
    request = ChartRequest(
        observer=observer(),
        family="planisphere",
        product=product(),
        projection=" STEREOGRAPHIC ",
        coordinate_frame=" HORIZONTAL ",
    )

    assert request.projection == "stereographic"
    assert request.coordinate_frame == "horizontal"
    with pytest.raises(ValueError, match="requires projection"):
        ChartRequest(
            observer=observer(), family="planisphere", product=product(),
            projection="mollweide",
        )
    with pytest.raises(ValueError, match="requires projection"):
        ChartRequest(
            observer=observer(), family="planisphere", product=product(),
            coordinate_frame="galactic",
        )


def test_all_sky_request_requires_galactic_mollweide_geometry():
    request = ChartRequest(
        observer=observer(),
        family="all_sky",
        product=product(),
        projection="mollweide",
        coordinate_frame="galactic",
    )

    assert request.projection == "mollweide"
    assert request.coordinate_frame == "galactic"
    with pytest.raises(ValueError, match="mollweide"):
        ChartRequest(
            observer=observer(), family="all_sky", product=product()
        )


def test_regional_request_expresses_constellation_group_without_scripts():
    request = ChartRequest(
        observer=observer(),
        family="regional",
        subject=ChartSubjectRequest(
            constellations=("Cen", "Cru", "Mus")
        ),
        frame=ChartFrameRequest(position_angle_deg=12.0),
        mask=True,
        content=SkyContentSelection(
            constellation_lines={"Cen", "Cru", "Mus"}
        ),
        product=product(),
        language="es",
    )

    assert request.subject.constellations == ("CEN", "CRU", "MUS")
    assert request.mask is True
    assert request.language == "es"


def test_catalogue_exclusions_are_normalized_and_immutable():
    exclusions = ChartContentExclusions(
        open_clusters={" NGC 6475 ", "M 7"},
        galaxies={"NGC 5128"},
    )

    assert exclusions.open_clusters == {"NGC 6475", "M 7"}
    assert exclusions.galaxies == {"NGC 5128"}
    with pytest.raises(ValueError, match="empty identifier"):
        ChartContentExclusions(open_clusters={""})


def test_planisphere_mask_and_circumpolar_limit_are_explicit():
    masked = ChartRequest(
        observer=observer(),
        family="planisphere",
        subject=ChartSubjectRequest(constellations=("Cru", "Cen")),
        mask=True,
        product=product(),
    )
    polar = ChartRequest(
        observer=observer(),
        family="circumpolar",
        frame=ChartFrameRequest(
            pole="south", limiting_declination_deg=-30.0
        ),
        product=product(),
    )

    assert masked.mask is True
    assert polar.frame.limiting_declination_deg == -30.0


def test_family_specific_missing_inputs_are_rejected():
    with pytest.raises(ValueError, match="binocular request requires"):
        ChartRequest(
            observer=observer(), family="binocular", product=product()
        )
    with pytest.raises(ValueError, match="regional request requires"):
        ChartRequest(
            observer=observer(), family="regional", product=product()
        )
    with pytest.raises(ValueError, match="circumpolar request requires"):
        ChartRequest(
            observer=observer(), family="circumpolar", product=product()
        )


def test_request_graph_is_immutable():
    request = ChartRequest(
        observer=observer(),
        family="binocular",
        subject=ChartSubjectRequest(target="M13"),
        product=product(),
    )

    with pytest.raises(FrozenInstanceError):
        request.language = "es"


def test_product_compositions_are_immutable_unique_and_selected():
    atlas = ChartProduct("atlas", "presentation")
    options = ChartProductCompositionOptions(
        product=atlas,
        detail=FixedDetailPolicy(
            ResolvedDetail(star_magnitude_limit=11.0)
        ),
    )
    request = ChartRequest(
        observer=observer(),
        family="binocular",
        subject=ChartSubjectRequest(target="M13"),
        product=product(),
        product_compositions=[options],
    )

    assert request.product_compositions == (options,)
    assert request.composition_for(atlas) is options
    assert request.composition_for(ChartProduct("atlas", "print")) is None
    with pytest.raises(ValueError, match="configure a product twice"):
        ChartRequest(
            observer=observer(),
            family="binocular",
            subject=ChartSubjectRequest(target="M13"),
            product=product(),
            product_compositions=(options, options),
        )
    with pytest.raises(ValueError, match="only selected products"):
        ChartRequest(
            observer=observer(),
            family="binocular",
            subject=ChartSubjectRequest(target="M13"),
            product=product(),
            product_compositions=(ChartProductCompositionOptions(
                product=ChartProduct("cartoon", "print")
            ),),
        )
