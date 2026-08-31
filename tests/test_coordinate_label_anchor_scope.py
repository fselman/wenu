"""Scope coordinate-boundary label anchoring to coordinate grids."""
from types import SimpleNamespace
from wenu.charts.boundaries import apply_coordinate_label_anchor

def test_coordinate_anchor_replaces_grid_anchor_only():
    old_grid_anchor = object()
    track_anchor = object()
    boundary_anchor = object()
    grid = SimpleNamespace(
        layer_name="coordinates_grid",
        coordinate_system="equatorial",
    )
    track = SimpleNamespace(
        layer_name="solar_system_track",
        coordinate_system=None,
    )
    options = {
        "equatorial_grid": {
            "render": {"label_anchor": old_grid_anchor}
        },
        "solar_system_track": {
            "render": {"label_anchor": track_anchor}
        },
        grid: {"render": {"label_anchor": old_grid_anchor}},
        track: {"render": {"label_anchor": track_anchor}},
    }
    resolved = apply_coordinate_label_anchor(options, boundary_anchor)
    assert resolved["equatorial_grid"]["render"]["label_anchor"] is boundary_anchor
    assert resolved[grid]["render"]["label_anchor"] is boundary_anchor
    assert resolved["solar_system_track"]["render"]["label_anchor"] is track_anchor
    assert resolved[track]["render"]["label_anchor"] is track_anchor
