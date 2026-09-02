"""Built-in moving-body catalog; external catalogs can extend this value."""

from wenu.sky.solar_system_bodies import SolarSystemBodyCatalog
from wenu.sky.earth import EARTH_BODY
from wenu.sky.mercury import MERCURY_BODY
from wenu.sky.major_planets import APPARENT_MAJOR_PLANETS
from wenu.sky.moon import MOON_BODY
from wenu.sky.venus import VENUS_POINT


SOLAR_SYSTEM_BODY_CATALOG = SolarSystemBodyCatalog((
    EARTH_BODY,
    MOON_BODY,
    VENUS_POINT,
    MERCURY_BODY,
    *APPARENT_MAJOR_PLANETS,
))
