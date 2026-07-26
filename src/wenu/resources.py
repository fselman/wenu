# resouces.py
from importlib.resources import files

_CONSTELLATION_LINE_FILES = {
    "western": (
        "wenu.data.constellations.western",
        "const_aug.fab",
    ),
    "mapuche": (
        "wenu.data.constellations.mapuche",
        "mapuche.fab",
    ),
}


def catalog_path(name):
    """
    Return the path to a built-in star catalogue.
    """
    name = name.lower()

    if name == "hipparcos":
        return files(
            "wenu.data.catalogs.hipparcos"
        ) / "hip_main.dat"

    raise ValueError(
        f"Unknown catalogue: {name}"
    )


def constellation_lines_path(system="western"):
    """
    Return the packaged .fab file for a constellation-line system.
    """

    try:
        package, filename = _CONSTELLATION_LINE_FILES[system]
    except KeyError as error:
        available = ", ".join(
            sorted(_CONSTELLATION_LINE_FILES)
        )

        raise ValueError(
            f"Unknown constellation-line system: {system!r}. "
            f"Available systems: {available}."
        ) from error

    resource = files(package) / filename

    if not resource.is_file():
        raise FileNotFoundError(
            f"Constellation-line resource not found: {resource}"
        )

    return resource


def boundary_path(name):
    """
    Return the path to a built-in boundary catalogue.
    """
    name = name.lower()

    if name == "iau":
        return files(
            "wenu.data.constellations.iau"
        ) / "bound_18.dat"

    raise ValueError(
        f"Unknown boundary set: {name}"
    )

def nonstellar_catalog_path(name):
    """Return a packaged non-stellar catalogue resource."""
    name = name.lower()
    if name != "messier":
        raise ValueError(f"Unknown non-stellar catalogue: {name}")

    package = files("wenu.data.catalogs.messier")
    preferred = (
        "messier_heasarc.ecsv",
        "heasarc_messier.ecsv",
        "messier.ecsv",
    )
    for filename in preferred:
        resource = package / filename
        if resource.is_file():
            return resource

    available = tuple(
        resource
        for resource in package.iterdir()
        if resource.name.lower().endswith(".ecsv")
    )
    if len(available) == 1:
        return available[0]
    raise FileNotFoundError(
        "Expected one Messier ECSV catalogue in "
        "wenu.data.catalogs.messier."
    )

