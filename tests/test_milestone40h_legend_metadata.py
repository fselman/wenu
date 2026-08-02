from types import SimpleNamespace
from dataclasses import replace

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from wenu import (
    AtlasChartStyle,
    LegendMetadata,
    draw_chart_legend,
    resolve_legend_metadata,
    observer_context_lines,
)


class FakeHorizontal:
    def transform_to(self, frame):
        from astropy import units as u
        from astropy.coordinates import SkyCoord

        return SkyCoord(ra=15.0 * u.deg, dec=-30.0 * u.deg, frame=frame)


class FakeObserver:
    altaz_frame = object()


class FakeSkyCoord:
    def __init__(self, **kwargs):
        pass

    def transform_to(self, frame):
        return FakeHorizontal().transform_to(frame)


def fake_chart():
    return SimpleNamespace(center_alt_deg=45.0, center_az_deg=180.0)


def fake_sky(*layers):
    return SimpleNamespace(
        observer=FakeObserver(),
        layers=layers,
        open_clusters=None,
        globular_clusters=None,
        planetary_nebulae=None,
        supernova_remnants=None,
        galaxies=None,
        milky_way_isophotes=None,
    )


def test_metadata_uses_last_registered_coordinate_grid(monkeypatch):
    import wenu.charts.legend_metadata as module

    monkeypatch.setattr(module, "SkyCoord", FakeSkyCoord)
    first = SimpleNamespace(
        coordinate_system="galactic",
    )
    active = SimpleNamespace(
        coordinate_system="equatorial",
        frame="fk5",
        equinox="J2050",
    )
    metadata = resolve_legend_metadata(
        fake_chart(),
        fake_sky(first, object(), active),
    )
    assert isinstance(metadata, LegendMetadata)
    assert metadata.coordinate_system == "equatorial"
    assert metadata.frame == "fk5"
    assert metadata.epoch == "J2050.0"
    assert metadata.grid_text == "Equatorial grid: FK5, J2050.0"
    assert "RA 1h00m00s" in metadata.center_text


def test_explicit_grid_overrides_registered_grid(monkeypatch):
    import wenu.charts.legend_metadata as module

    monkeypatch.setattr(module, "SkyCoord", FakeSkyCoord)
    registered = SimpleNamespace(
        coordinate_system="equatorial",
        frame="fk5",
        equinox="J2000",
    )
    explicit = SimpleNamespace(coordinate_system="galactic")
    metadata = resolve_legend_metadata(
        fake_chart(),
        fake_sky(registered),
        grid=explicit,
    )
    assert metadata.coordinate_system == "galactic"
    assert metadata.grid_text == "Galactic grid: IAU Galactic"


def test_icrs_has_no_fictitious_epoch(monkeypatch):
    import wenu.charts.legend_metadata as module

    monkeypatch.setattr(module, "SkyCoord", FakeSkyCoord)
    grid = SimpleNamespace(
        coordinate_system="equatorial",
        frame="icrs",
        equinox="J2000",
    )
    metadata = resolve_legend_metadata(
        fake_chart(),
        fake_sky(grid),
    )
    assert metadata.grid_text == "Equatorial grid: ICRS"
    assert metadata.epoch is None


def test_legend_visibility_and_location_remain_style_controlled():
    style = AtlasChartStyle()
    hidden = replace(
        style,
        legend=replace(style.legend, visible=False),
    )
    figure, ax = plt.subplots()
    assert draw_chart_legend(
        ax,
        fake_chart(),
        fake_sky(),
        hidden,
    ) is None
    plt.close(figure)


def test_legend_accepts_explicit_title_without_resolving_coordinates():
    figure, ax = plt.subplots()
    legend = draw_chart_legend(
        ax,
        fake_chart(),
        fake_sky(),
        AtlasChartStyle(),
        title="Custom metadata",
    )
    assert legend.get_title().get_text() == "Custom metadata"
    assert legend._loc == 1
    plt.close(figure)


def test_metadata_module_has_no_render_backend_dependency():
    from pathlib import Path
    import wenu.charts.legend_metadata as module

    source = Path(module.__file__).read_text().lower()
    assert "matplotlib" not in source


def test_observer_context_lines_include_location_and_local_time():
    from datetime import datetime, timezone

    observer = SimpleNamespace(
        utc_datetime=datetime(2026, 8, 16, 1, 0, tzinfo=timezone.utc),
        timezone_name="America/Santiago",
        location_name="La Ligua",
        lat_deg=-32.4524,
        lon_deg=-71.2311,
        elevation_m=52.0,
    )

    assert observer_context_lines(observer) == (
        "Location: La Ligua — 32.4524° S, 71.2311° W, 52 m",
        "Date: 2026-08-15",
        "Local time: 21:00 (UTC−04:00)",
    )
