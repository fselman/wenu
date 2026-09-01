"""Built-in moving-body catalog; external catalogs can extend this value."""

from wenu.sky.solar_system_bodies import SolarSystemBodyCatalog
from wenu.sky.mercury import MERCURY_BODY
from wenu.sky.venus import VENUS_POINT


SOLAR_SYSTEM_BODY_CATALOG = SolarSystemBodyCatalog((VENUS_POINT, MERCURY_BODY))
