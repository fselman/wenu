from types import SimpleNamespace

from wenu.charts.detail import ResolvedDetail
from wenu.charts.detail_application import apply_resolved_detail


class MilkyWayLayer:
    layer_name = "milky_way_isophotes"


def sky_with_milky_way():
    layer = MilkyWayLayer()
    return SimpleNamespace(
        layers=(layer,),
        stars=None,
        galaxies=None,
    ), layer


def resolved_detail(enabled_layers):
    return ResolvedDetail(
        star_magnitude_limit=3.0,
        enabled_layers=frozenset(enabled_layers),
    )


def test_semantic_content_name_enables_registered_milky_way_layer():
    sky, layer = sky_with_milky_way()
    application = apply_resolved_detail(
        sky,
        resolved_detail({"milky_way"}),
        reload_catalogues=False,
    )
    assert application.layer_options[layer]["enabled"] is True
    assert (
        application.layer_options["milky_way_isophotes"]["enabled"]
        is True
    )


def test_absent_semantic_content_name_disables_milky_way_layer():
    sky, layer = sky_with_milky_way()
    application = apply_resolved_detail(
        sky,
        resolved_detail({"stars"}),
        reload_catalogues=False,
    )
    assert application.layer_options[layer]["enabled"] is False

