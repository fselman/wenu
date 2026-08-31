"""Diagnose 49I.2D.2 tick labels before renderer handoff."""
from pathlib import Path
from wenu.coordinates import PositionStatus, observer_altaz_spec
from wenu.observer import DEFAULT_DATA_DIRECTORY, DEFAULT_EPHEMERIS, Observer
from wenu.sky.realization import LayerRealizationContext
from wenu.sky.solar_system_tracks import SolarSystemTrackRealizer, SolarSystemTrackRequest
from wenu.sky.solar_system_track_layer import prepare_projected_track
from wenu.sky.venus import VENUS_POINT
from wenu.charts.regional import RegionalChart
from wenu.rendering.matplotlib import MatplotlibRenderer
from wenu.sky.solar_system_track_layer import start_label_anchor

START = "2026-08-30T00:00:00Z"

def main():
    path = Path(DEFAULT_DATA_DIRECTORY) / DEFAULT_EPHEMERIS
    if not path.is_file():
        raise SystemExit(f"Installed kernel required: {path}")
    with Observer(
        location="La Ligua", time=START,
        ephemeris_name=DEFAULT_EPHEMERIS,
        data_directory=DEFAULT_DATA_DIRECTORY,
    ) as observer:
        context = LayerRealizationContext(
            product_coordinate_spec=observer_altaz_spec(
                observer,
                position_status=PositionStatus.APPARENT,
                provider="49I.2D.2 fixed chart frame",
                model="vacuum apparent Solar-System track",
            ),
            observation=observer.observation_context,
        )
        request = SolarSystemTrackRequest(
            descriptor=VENUS_POINT,
            start_instant=START,
            start_time_scale="utc",
            sample_step_days=1.0 / 24.0,
            tick_step_days=7.0,
            tick_count=4,
        )
        result = SolarSystemTrackRealizer().curve(
            request, context=context, observer=observer
        )
        chart = RegionalChart(
            center_alt_deg=22.5,
            center_az_deg=271.0,
            field_width_deg=35.0,
            field_height_deg=50.0,
            position_angle_deg=0.0,
        )
        projected = chart.projection.project_geometry(result.geometry)
        prepared = prepare_projected_track(
            result.geometry,
            projected,
            tick_length=0.018 * min(chart.viewport.width, chart.viewport.height),
            label_ticks=True,
        )
        instants = tuple(result.geometry.metadata["sample_instants"])
        print(f"samples: {len(result.sample_instants)}")
        print(f"geometry metadata sample instants: {len(instants)}")
        print(f"tick sample indices: {result.tick_sample_indices}")
        print(f"prepared ticks: {len(prepared['ticks'])}")
        for ordinal, (index, tick) in enumerate(
            zip(result.tick_sample_indices[1:], prepared["ticks"]), start=1
        ):
            print(
                f"  {ordinal}: index {index}, instant {instants[index]}, "
                f"label {tick.name!r}, "
                f"x {tick.x.mean():.12f}, y {tick.y.mean():.12f}"
            )
        label = prepared["labels"][0]
        print(
            f"start label: {label.name!r}, "
            f"x {label.x.mean():.12f}, y {label.y.mean():.12f}"
        )
        import matplotlib.pyplot as plt
        figure, axes = plt.subplots()
        renderer = MatplotlibRenderer(axes)
        renderer.apply_viewport(chart.viewport)
        renderer.draw(
            prepared,
            component_styles={
                "path": {"color": "#C44E52"},
                "ticks": {"color": "#C44E52"},
                "labels": {"alpha": 0.0, "linewidth": 0.0},
            },
            draw_labels=True,
            label_anchor=start_label_anchor,
            label_style={"color": "#C44E52"},
        )
        rendered_text = tuple(artist.get_text() for artist in axes.texts)
        print(f"renderer text artists: {rendered_text!r}")
        plt.close(figure)
        assert rendered_text == (
            "2026-09-06", "2026-09-13", "2026-09-20", "2026-09-27",
            "♀ 2026-08-30",
        )
        assert len(instants) == len(result.sample_instants) == 673
        assert tuple(tick.name for tick in prepared["ticks"]) == (
            "2026-09-06", "2026-09-13", "2026-09-20", "2026-09-27"
        )

if __name__ == "__main__":
    main()
