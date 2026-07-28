from types import SimpleNamespace

from wenu.charts.detail_application import merge_sky_layer_options


class Layer:
    layer_name = "milky_way_isophotes"


def test_semantic_milky_way_alias_controls_registered_isophote_layer():
    layer = Layer()
    sky = SimpleNamespace(layers=(layer,))
    merged = merge_sky_layer_options(
        sky,
        {layer: {"enabled": True, "render": {"alpha": 0.2}}},
        {"milky_way": {"enabled": False}},
    )
    assert merged[layer]["enabled"] is False
    assert merged["milky_way"]["enabled"] is False
    assert merged["milky_way_isophotes"]["enabled"] is False
    assert merged[layer]["render"]["alpha"] == 0.2


def test_presentation_alias_can_enable_registered_isophote_layer():
    layer = Layer()
    sky = SimpleNamespace(layers=(layer,))
    merged = merge_sky_layer_options(
        sky,
        {layer: {"enabled": False}},
        {"milky_way": {"enabled": True}},
    )
    assert merged[layer]["enabled"] is True


def test_unhashable_synthetic_layer_is_supported():
    layer = SimpleNamespace(layer_name="constellation_lines")
    sky = SimpleNamespace(layers=(layer,))
    merged = merge_sky_layer_options(
        sky,
        {"constellation_lines": {"enabled": True}},
    )
    assert merged["constellation_lines"]["enabled"] is True

