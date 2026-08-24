"""Resolved-view parity between canonical examples and ``wenu_chart``."""

from dataclasses import asdict
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

from wenu.charts.view_defaults import chart_view_defaults
from wenu.cli import chart


ROOT = Path(__file__).resolve().parents[1]


CASES = (
    ("all_sky.py", (), ("all-sky", "--observer-location", "La Ligua",
     "--observer-time", "2026-08-15 21:00")),
    ("planisphere.py", (), ("planisphere", "--observer-location", "La Ligua",
     "--observer-time", "2026-08-15 21:00")),
    ("regional_constellation.py", (),
     ("regional", "--constellations", "Cru", "--observer-location",
      "La Ligua", "--observer-time", "2026-08-15 21:00")),
    ("regional_constellation_group.py", (),
     ("regional", "--constellations", "Sgr,Sco,Oph,Ser",
      "--observer-location", "La Ligua", "--observer-time",
      "2026-08-15 21:00")),
    ("circumpolar.py", (),
     ("circumpolar", "--observer-location", "La Ligua",
      "--observer-time", "2026-08-15 21:00")),
    ("binocular_object.py", (),
     ("binocular", "--target", "centaurus-a", "--observer-location",
      "La Ligua", "--observer-time", "2026-05-15 22:00")),
)


def _load_example(filename):
    path = ROOT / "examples" / filename
    spec = importlib.util.spec_from_file_location(f"parity_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Observer:
    def __init__(self, **values):
        self.values = values

    def close(self):
        pass


def _effective_view(call):
    family = call["family"]
    constellations = call.get("constellations")
    defaults = chart_view_defaults(
        family,
        group=constellations is not None and len(constellations) > 1,
        configuration=call["configuration"],
    )
    values = asdict(defaults)
    values.update({
        "family": family,
        "target": call.get("target"),
        "ra_deg": call.get("ra_deg"),
        "dec_deg": call.get("dec_deg"),
        "constellations": constellations,
        "group": call.get("group"),
        "display_name": call.get("display_name"),
    })
    for name in (
        "field_diameter_deg", "field_width_deg", "field_height_deg",
        "orientation", "position_angle_deg", "pole",
        "limiting_declination_deg",
        "projection", "coordinate_frame", "mask",
    ):
        if call.get(name) is not None:
            values[name] = call[name]
    if call.get("position_angle_deg") is not None:
        values["orientation"] = None
    values.pop("framing")
    return values


@pytest.mark.parametrize("filename,example_argv,command_argv", CASES)
def test_canonical_example_and_installed_command_resolve_the_same_view(
    monkeypatch, filename, example_argv, command_argv
):
    configuration_values = chart.load_configuration()
    configuration = chart.translate_configuration_defaults(
        configuration_values
    )
    sky = SimpleNamespace(load_profile=object())
    example = _load_example(filename)
    example_calls = []
    command_calls = []

    def record(calls):
        def get_view(_sky, observer, **values):
            calls.append((observer, values))
            constellations = values.get("constellations")
            target = values.get("target")
            return SimpleNamespace(
                family=values["family"], observer=observer,
                constellations=(None if constellations is None
                                else SimpleNamespace(key="constellations")),
                target=(None if target is None
                        else SimpleNamespace(key="target")),
            )
        return get_view

    monkeypatch.setattr(example, "chart_configuration", lambda arguments: configuration)
    monkeypatch.setattr(example, "generate_celestial_sphere", lambda: sky)
    monkeypatch.setattr(example, "Observer", _Observer)
    monkeypatch.setattr(example, "get_chart_view", record(example_calls))

    monkeypatch.setattr(
        chart, "load_configuration", lambda path=None: configuration_values
    )
    monkeypatch.setattr(chart, "translate_configuration_defaults",
                        lambda values: configuration)
    monkeypatch.setattr(chart, "generate_celestial_sphere", lambda: sky)
    monkeypatch.setattr(chart, "Observer", _Observer)
    monkeypatch.setattr(chart, "get_chart_view", record(command_calls))
    monkeypatch.setattr(chart, "draw_chart_view_from_arguments",
                        lambda *args, **kwargs: ())

    example.chart_view(example.parser().parse_args(example_argv))
    chart.generate(chart.parser().parse_args(command_argv))

    assert example_calls[0][0].values == command_calls[0][0].values
    assert _effective_view(example_calls[0][1]) == _effective_view(
        command_calls[0][1]
    )
