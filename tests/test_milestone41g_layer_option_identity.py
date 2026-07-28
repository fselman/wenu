from types import SimpleNamespace

from wenu.charts.detail import ResolvedDetail
from wenu.charts.detail_application import apply_resolved_detail


class Layer:
    def __init__(self, name):
        self.layer_name = name


def test_named_disabled_option_overrides_object_keyed_style():
    milky_way = Layer("milky_way")
    sky = SimpleNamespace(
        layers=(milky_way,),
        stars=None,
        galaxies=None,
    )
    detail = ResolvedDetail(
        enabled_layers=frozenset({"stars"}),
    )
    applied = apply_resolved_detail(
        sky,
        detail,
        base_layer_options={
            milky_way: {
                "prepare": object(),
                "render": {"style": {"color": "blue"}},
            }
        },
        reload_catalogues=False,
    )
    by_object = applied.layer_options[milky_way]
    by_name = applied.layer_options["milky_way"]
    assert by_object is by_name
    assert by_object["enabled"] is False
    assert by_object["render"]["style"]["color"] == "blue"


def test_explicit_named_option_has_final_precedence_for_object_key():
    layer = Layer("milky_way")
    sky = SimpleNamespace(
        layers=(layer,),
        stars=None,
        galaxies=None,
    )
    applied = apply_resolved_detail(
        sky,
        ResolvedDetail(enabled_layers=frozenset({"stars"})),
        base_layer_options={layer: {"enabled": True}},
        explicit_layer_options={"milky_way": {"enabled": True}},
        reload_catalogues=False,
    )
    assert applied.layer_options[layer]["enabled"] is True


def test_object_key_is_more_specific_within_one_source():
    layer = Layer("milky_way")
    sky = SimpleNamespace(
        layers=(layer,),
        stars=None,
        galaxies=None,
    )
    applied = apply_resolved_detail(
        sky,
        ResolvedDetail(enabled_layers=None),
        explicit_layer_options={
            "milky_way": {"render": {"style": {"alpha": 0.2}}},
            layer: {"render": {"style": {"alpha": 0.7}}},
        },
        reload_catalogues=False,
    )
    assert (
        applied.layer_options[layer]["render"]["style"]["alpha"]
        == 0.7
    )
