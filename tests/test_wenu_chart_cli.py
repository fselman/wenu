"""Installed unified command over Wenu's ordinary chart facade."""

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from wenu.cli import chart
from wenu.configuration import ConfigurationError


EXPECTED_COMMANDS = {
    "all-sky", "planisphere", "regional", "circumpolar", "binocular",
    "defaults",
}


def test_project_installs_the_underscored_command():
    source = Path("pyproject.toml").read_text(encoding="utf-8")

    assert 'wenu_chart = "wenu.cli.chart:main"' in source
    assert "wenu-chart =" not in source


def test_parser_exposes_one_family_subcommand_set():
    subparsers = next(
        action for action in chart.parser()._actions
        if action.dest == "command"
    )

    assert set(subparsers.choices) == EXPECTED_COMMANDS


def test_regional_accepts_one_named_center():
    one = chart.parser().parse_args([
        "regional", "--center-on", "constellation:Cru",
    ])

    assert one.center_on == "constellation:Cru"


def test_center_content_and_mask_options_are_order_independent():
    first = chart.parser().parse_args([
        "regional", "--center-on", "Vir", "--planet", "venus,mars",
        "--constellation-mask", "Vir",
    ])
    second = chart.parser().parse_args([
        "regional", "--constellation-mask", "Vir",
        "--planet", "venus,mars", "--center-on", "Vir",
    ])

    assert vars(first) == vars(second)


@pytest.mark.parametrize(
    "legacy",
    (
        ("--constellations", "Vir"),
        ("--target", "Venus"),
        ("--center-ra", "10"),
        ("--mask",),
    ),
)
def test_removed_overloaded_options_are_rejected(legacy):
    with pytest.raises(SystemExit):
        chart.parser().parse_args(["regional", *legacy])


def test_long_options_do_not_accept_ambiguous_abbreviations():
    with pytest.raises(SystemExit):
        chart.parser().parse_args(["regional", "--center-i", "10deg"])


def test_constellation_system_is_an_explicit_parameter_not_content():
    arguments = chart.parser().parse_args([
        "regional", "--constellation-system", "western"
    ])

    assert arguments.constellation_system == "western"
    assert arguments.constellation_lines == []
    assert arguments.constellation_labels == []
    assert arguments.constellation_boundaries == []
    assert arguments.constellation_mask == []


def test_every_chart_family_exposes_solar_system_selectors():
    for family in EXPECTED_COMMANDS - {"defaults"}:
        arguments = chart.parser().parse_args(
            [family, "--planet", "venus", "--moon"]
        )
        assert arguments.planet == [("venus",)]
        assert arguments.moon is True


def test_every_chart_family_exposes_moving_object_data_policy():
    for family in EXPECTED_COMMANDS - {"defaults"}:
        arguments = chart.parser().parse_args([
            family, "--data-policy", "offline",
        ])
        assert arguments.data_policy == "offline"


def test_planisphere_accepts_one_comma_separated_planet_selection():
    arguments = chart.parser().parse_args([
        "planisphere",
        "--planet", "mercury,venus,mars,jupiter,saturn,uranus,neptune",
    ])

    assert arguments.planet == [(
        "mercury", "venus", "mars", "jupiter", "saturn", "uranus",
        "neptune",
    )]


def test_all_chart_families_accept_milky_way_contour():
    for family in EXPECTED_COMMANDS - {"defaults"}:
        arguments = chart.parser().parse_args([
            family, "--mw-contour", "OL2",
        ])
        assert arguments.mw_contour == [("ol2",)]


def test_regional_orientation_is_named_or_a_literal_angle():
    named = chart.parser().parse_args([
        "regional", "--orientation", "zenith-up",
    ])
    literal = chart.parser().parse_args([
        "regional", "--position-angle", "0",
    ])

    assert named.orientation == "zenith-up"
    assert named.position_angle is None
    assert literal.orientation is None
    assert literal.position_angle == pytest.approx(0.0)
    with pytest.raises(SystemExit):
        chart.parser().parse_args([
            "regional", "--orientation", "zenith-up",
            "--position-angle", "0",
        ])


def test_regional_accepts_a_fixed_horizontal_camera_center():
    arguments = chart.parser().parse_args([
        "regional",
        "--center-altitude", "20deg", "--center-azimuth", "270deg",
        "--field-width", "60", "--field-height", "50",
        "--orientation", "zenith-up",
    ])

    assert arguments.center_altitude == pytest.approx(20.0)
    assert arguments.center_azimuth == pytest.approx(270.0)


def test_regional_accepts_named_and_explicit_icrs_centers():
    named = chart.parser().parse_args([
        "regional", "--center-on", "target:Centaurus A",
    ])
    coordinate = chart.parser().parse_args([
        "regional", "--center-icrs-ra", "201.365deg",
        "--center-icrs-dec=-43.019deg", "--center-name", "My field",
    ])

    assert named.center_on == "target:Centaurus A"
    assert coordinate.center_icrs_ra == pytest.approx(201.365)
    assert coordinate.center_icrs_dec == pytest.approx(-43.019)
    assert coordinate.center_name == "My field"


def test_icrs_center_supplies_an_informative_default_title():
    arguments = chart.parser().parse_args([
        "regional", "--center-icrs-ra", "201.365deg",
        "--center-icrs-dec=-43.019deg", "--center-name", "My field",
    ])

    assert chart._title(arguments) == (
        "My field — ICRS RA 13:25:27.6, Dec −43:01:08.4"
    )
    arguments.title = "Explicit title"
    assert chart._title(arguments) == "Explicit title"


def test_center_forms_are_complete_and_mutually_exclusive():
    half = chart.parser().parse_args([
        "regional", "--center-icrs-ra", "10deg"
    ])
    competing = chart.parser().parse_args([
        "regional", "--center-on", "Vir",
        "--center-altitude", "20deg", "--center-azimuth", "270deg",
    ])

    with pytest.raises(ValueError, match="must be used together"):
        chart._coordinate_center(half)
    with pytest.raises(ValueError, match="exactly one"):
        chart._coordinate_center(competing)


def test_named_planet_supplies_an_explicit_regional_center(
    monkeypatch,
):
    arguments = chart.parser().parse_args([
        "regional", "--center-on", "planet:venus", "--planet", "venus",
    ])
    center = SimpleNamespace(altitude_deg=12.5, azimuth_deg=234.0)
    monkeypatch.setattr(
        chart, "get_object_center", lambda *args, **kwargs: center
    )
    configuration = SimpleNamespace(
        reference_policy=SimpleNamespace(
            resolved_equinox=lambda observer: "J2000"
        )
    )

    assert chart._center_arguments(
        arguments, {"centers": {}}, configuration, object()
    ) == {
        "center_altitude_deg": 12.5,
        "center_azimuth_deg": 234.0,
    }


def test_planet_center_and_constellation_mask_are_independent(monkeypatch):
    arguments = chart.parser().parse_args([
        "regional", "--center-on", "planet:venus", "--planet", "venus",
        "--constellation-mask", "Vir",
        "--field-width", "20", "--field-height", "15",
    ])
    center = SimpleNamespace(altitude_deg=12.5, azimuth_deg=234.0)
    monkeypatch.setattr(
        chart, "get_object_center", lambda *args, **kwargs: center
    )
    configuration = SimpleNamespace(
        reference_policy=SimpleNamespace(
            resolved_equinox=lambda observer: "J2000"
        )
    )

    view_arguments = chart._view_arguments(arguments)
    center_arguments = chart._center_arguments(
        arguments, {"centers": {}}, configuration, object()
    )

    assert view_arguments["constellation_mask"] == ("Vir",)
    assert center_arguments == {
        "center_altitude_deg": 12.5,
        "center_azimuth_deg": 234.0,
    }
    assert set(center_arguments).isdisjoint(view_arguments)


def test_several_selected_objects_do_not_change_the_configured_center():
    arguments = chart.parser().parse_args([
        "regional", "--planet", "venus,mars",
    ])

    values = {"centers": {"regional_single": {
        "kind": "constellations", "constellations": ["Cru"]
    }}}
    configuration = SimpleNamespace(minor_body_resource_directory=None)
    assert chart._center_arguments(
        arguments, values, configuration, object()
    ) == {"constellations": ("Cru",)}


def test_binocular_omits_the_shared_grid_default_but_keeps_opt_in():
    omitted = chart.parser().parse_args(["binocular"])
    selected = chart.parser().parse_args([
        "binocular", "--equatorial-grid", "--equatorial-grid-labels",
    ])

    assert omitted.equatorial_grid is False
    assert omitted.equatorial_grid_labels is False
    assert selected.equatorial_grid is True
    assert selected.equatorial_grid_labels is True


def test_circumpolar_accepts_independent_declination_spacing():
    arguments = chart.parser().parse_args([
        "circumpolar",
        "--pole", "south",
        "--limiting-declination", "-60",
        "--declination-step", "10",
    ])

    assert arguments.declination_step == pytest.approx(10.0)


def test_defaults_prints_packaged_authority_without_generation(
    monkeypatch, capsys
):
    monkeypatch.setattr(
        chart,
        "generate_celestial_sphere",
        lambda: pytest.fail("defaults must not load catalogues"),
    )

    assert chart.main(["defaults"]) == 0
    output = capsys.readouterr().out
    assert output.startswith("# Wenu authoritative public defaults")
    assert "schema_version = 2" in output


def test_defaults_write_is_an_exact_deterministic_editable_copy(
    monkeypatch, tmp_path, capsys
):
    monkeypatch.setattr(
        chart,
        "generate_celestial_sphere",
        lambda: pytest.fail("defaults must not load catalogues"),
    )
    destination = tmp_path / "profiles" / "publication.toml"
    destination.parent.mkdir()

    assert chart.main(["defaults", "--write", str(destination)]) == 0

    expected = chart.packaged_defaults_text().encode("utf-8")
    assert destination.read_bytes() == expected
    assert capsys.readouterr().out.strip() == str(destination)

    destination.write_text("changed", encoding="utf-8")
    assert chart.write_defaults_template(destination) == destination
    assert destination.read_bytes() == expected


def test_defaults_write_requires_an_existing_parent(tmp_path):
    destination = tmp_path / "missing" / "observing.toml"

    with pytest.raises(FileNotFoundError):
        chart.write_defaults_template(destination)

    assert not destination.exists()


def test_invalid_configuration_fails_before_observer_or_sphere(
    monkeypatch, tmp_path
):
    path = tmp_path / "invalid.toml"
    path.write_text("schema_version = 2\nunknown = true\n", encoding="utf-8")
    calls = []
    monkeypatch.setattr(
        chart, "Observer", lambda **kwargs: calls.append("observer")
    )
    monkeypatch.setattr(
        chart,
        "generate_celestial_sphere",
        lambda: calls.append("sphere"),
    )
    monkeypatch.setattr(
        chart,
        "get_chart_view",
        lambda *args, **kwargs: calls.append("view"),
    )
    monkeypatch.setattr(
        chart,
        "draw_chart_view_from_arguments",
        lambda *args, **kwargs: calls.append("draw"),
    )

    with pytest.raises(ConfigurationError):
        chart.generate(chart.parser().parse_args([
            "planisphere", "--config", str(path),
        ]))

    assert calls == []


def test_command_delegates_to_three_stage_library_interface(monkeypatch):
    calls = []
    observer = SimpleNamespace(close=lambda: calls.append(("close",)))
    sky = object()
    view = SimpleNamespace(
        family="regional",
        constellations=SimpleNamespace(key="cyg-lyr-aql"),
        target=None,
    )
    result = SimpleNamespace(output=Path("map.png"))
    monkeypatch.setattr(
        chart, "Observer",
        lambda **kwargs: calls.append(("observer", kwargs)) or observer,
    )
    monkeypatch.setattr(
        chart, "generate_celestial_sphere",
        lambda: calls.append(("sphere",)) or sky,
    )
    monkeypatch.setattr(
        chart, "get_chart_view",
        lambda *args, **kwargs: calls.append(("view", args, kwargs)) or view,
    )
    monkeypatch.setattr(
        chart, "draw_chart_view_from_arguments",
        lambda *args, **kwargs: (
            calls.append(("draw", args, kwargs)) or (result,)
        ),
    )

    outputs = chart.generate(chart.parser().parse_args([
        "regional", "--center-on", "group:summer-triangle",
        "--observer-location", "Papudo",
        "--observer-time", "2026-08-15 22:00",
        "--style", "cartoon", "--mode", "presentation",
    ]))

    assert outputs == (Path("map.png"),)
    assert [call[0] for call in calls] == [
        "observer", "sphere", "view", "draw", "close",
    ]
    assert calls[0][1]["location"] == "Papudo"
    assert calls[2][2]["group"] == "summer-triangle"
    assert calls[2][2]["family"] == "regional"
    assert calls[3][2]["stem"] == "regional-cyg-lyr-aql"


def test_observer_and_subject_omissions_use_effective_toml(monkeypatch):
    captured = []
    observer = SimpleNamespace(close=lambda: None)
    view = SimpleNamespace(
        family="binocular",
        constellations=None,
        target=SimpleNamespace(key="centaurus-a"),
    )
    monkeypatch.setattr(
        chart, "Observer",
        lambda **kwargs: captured.append(("observer", kwargs)) or observer,
    )
    monkeypatch.setattr(chart, "generate_celestial_sphere", lambda: object())
    monkeypatch.setattr(
        chart, "get_chart_view",
        lambda *args, **kwargs: captured.append(("view", kwargs)) or view,
    )
    monkeypatch.setattr(
        chart, "draw_chart_view_from_arguments",
        lambda *args, **kwargs: (),
    )

    chart.generate(chart.parser().parse_args(["binocular"]))

    assert captured[0][1]["location"] == "La Ligua"
    assert captured[0][1]["time"] == "2026-08-15 21:00"
    assert captured[1][1]["target"] == "centaurus-a"


def test_named_observer_accepts_public_elevation_and_timezone_overrides():
    latitude, longitude, elevation, timezone, name = (
        chart.Observer._resolve_location(
            location="La Ligua",
            lat_deg=None,
            lon_deg=None,
            elevation_m=75.0,
            timezone_name="UTC",
        )
    )

    assert latitude == pytest.approx(-32.443342)
    assert longitude == pytest.approx(-71.230289)
    assert elevation == pytest.approx(75.0)
    assert timezone == "UTC"
    assert name == "La Ligua"


def test_cli_source_does_not_import_or_execute_examples():
    source = Path("src/wenu/cli/chart.py").read_text(encoding="utf-8")

    assert "wenu.example_scripts" not in source
    assert "runpy" not in source


def test_family_help_exposes_public_output_formats_only():
    root = chart.parser()
    subparsers = next(
        action for action in root._actions
        if action.dest == "command"
    )
    regional = subparsers.choices["regional"]
    format_action = next(
        action for action in regional._actions
        if "--format" in action.option_strings
    )

    assert tuple(format_action.choices) == ("png", "pdf", "svg")
    assert format_action.help == "explicit output format: png, pdf, or svg"
    assert all(
        "--svg-font-policy" not in action.option_strings
        for action in regional._actions
    )


def test_family_help_exposes_temporal_sequence_controls():
    regional = chart.parser().parse_args([
        "regional",
        "--observer-time", "2026-08-21T21:00:00-04:00",
        "--sequence-stop", "2026-08-22T03:00:00-04:00",
        "--sequence-frames", "25",
        "--display-timezone", "America/Santiago",
        "--playback-duration", "2",
        "--frames-per-second", "12.5",
        "--restart-policy", "resume",
    ])

    assert regional.sequence_stop == "2026-08-22T03:00:00-04:00"
    assert regional.sequence_frames == 25
    assert regional.display_timezone == "America/Santiago"
    assert regional.playback_duration == pytest.approx(2.0)
    assert regional.frames_per_second == pytest.approx(12.5)
    assert regional.restart_policy == "resume"


def test_sequence_cli_delegates_to_canonical_sequence_api(
    monkeypatch,
    tmp_path,
):
    calls = []
    observer = SimpleNamespace(
        utc_datetime=datetime(2026, 8, 22, 1, tzinfo=timezone.utc),
        timezone_name="America/Santiago",
        close=lambda: calls.append(("close",)),
    )
    view = SimpleNamespace(
        family="circumpolar",
        constellations=None,
        target=None,
    )
    chart_request = object()
    sequence_request = object()
    monkeypatch.setattr(chart, "Observer", lambda **kwargs: observer)
    monkeypatch.setattr(chart, "generate_celestial_sphere", lambda: object())
    monkeypatch.setattr(chart, "get_chart_view", lambda *args, **kwargs: view)
    monkeypatch.setattr(
        chart,
        "draw_chart_view_from_arguments",
        lambda *args, **kwargs: pytest.fail("sequence used static draw"),
    )
    monkeypatch.setattr(
        chart,
        "chart_view_requests_from_arguments",
        lambda *args, **kwargs: (
            calls.append(("requests", kwargs)) or (chart_request,)
        ),
    )
    monkeypatch.setattr(
        chart,
        "ObserverTimeChartSequenceRequest",
        lambda **kwargs: (
            calls.append(("sequence", kwargs)) or sequence_request
        ),
    )
    monkeypatch.setattr(
        chart,
        "generate_observer_time_chart_sequence",
        lambda request, **kwargs: (
            calls.append(("generate", request, kwargs))
            or SimpleNamespace(
                outputs=(
                    tmp_path / "frames" / "frame-0000.png",
                    tmp_path / "frames" / "frame-0001.png",
                )
            )
        ),
    )

    outputs = chart.generate(chart.parser().parse_args([
        "circumpolar",
        "--observer-time", "2026-08-21T21:00:00-04:00",
        "--sequence-stop", "2026-08-22T03:00:00-04:00",
        "--sequence-frames", "2",
        "--format", "png",
        "--output", str(tmp_path / "frames"),
        "--restart-policy", "resume",
    ]))

    assert outputs == (
        tmp_path / "frames" / "frame-0000.png",
        tmp_path / "frames" / "frame-0001.png",
    )
    assert calls[0][0] == "requests"
    assert calls[0][1]["sequence"] is True
    assert calls[1][0] == "sequence"
    assert calls[1][1]["chart"] is chart_request
    assert calls[1][1]["timeline"].frame_count == 2
    assert calls[1][1]["configuration"] is not None
    assert calls[2] == (
        "generate",
        sequence_request,
        {"restart_policy": "resume"},
    )
    assert calls[3] == ("close",)
