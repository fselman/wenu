"""Backend-independent metadata for informational chart legends."""

from __future__ import annotations

from dataclasses import dataclass
import re

from astropy import units as u
from astropy.coordinates import FK5, SkyCoord
from astropy.time import Time


@dataclass(frozen=True)
class LegendMetadata:
    """Resolved textual metadata shown above a chart symbol key."""

    center_text: str
    grid_text: str
    coordinate_system: str
    frame: str | None = None
    epoch: str | None = None

    @property
    def title(self) -> str:
        """Return the conventional two-line legend title."""
        return f"{self.center_text}\n{self.grid_text}"


def active_coordinate_grid(sky, explicit=None):
    """Return an explicit grid or the last registered coordinate grid."""
    if explicit is not None:
        return explicit
    for layer in reversed(tuple(getattr(sky, "layers", ()))):
        if hasattr(layer, "coordinate_system"):
            return layer
    return None


def _normalized_epoch(value) -> str | None:
    if value is None:
        return None
    text = str(value)
    if text.lower() == "of_date":
        return "of date"
    match = re.fullmatch(
        r"\s*([JBjb])\s*(\d+(?:\.\d*)?)\s*",
        text,
    )
    if match:
        return f"{match.group(1).upper()}{float(match.group(2)):.1f}"
    try:
        time = value if isinstance(value, Time) else Time(value)
    except (TypeError, ValueError):
        return text
    return str(time)


def _grid_description(grid) -> tuple[str, str | None, str | None, str]:
    if grid is None:
        return "equatorial", "fk5", "J2000.0", (
            "Equatorial grid: FK5, J2000.0"
        )

    system = str(
        getattr(grid, "coordinate_system", "spherical")
    ).lower()
    frame = getattr(grid, "frame", None)
    frame = None if frame is None else str(frame).lower()
    epoch = _normalized_epoch(getattr(grid, "equinox", None))

    if system == "equatorial":
        resolved_frame = (frame or "icrs").upper()
        if resolved_frame == "ICRS":
            return system, frame or "icrs", None, "Equatorial grid: ICRS"
        suffix = "" if epoch is None else f", {epoch}"
        return system, frame, epoch, (
            f"Equatorial grid: {resolved_frame}{suffix}"
        )
    if system == "ecliptic":
        suffix = "" if epoch is None else f", {epoch}"
        return system, frame, epoch, f"Ecliptic grid{suffix}"
    if system == "galactic":
        return system, frame, None, "Galactic grid: IAU Galactic"
    if system in {"horizontal", "altaz"}:
        return system, frame, "of date", "Horizontal grid: AltAz, of date"
    return system, frame, epoch, f"Coordinate grid: {system}"


def _center_text(chart, sky) -> str:
    context = getattr(chart, "chart_context", None)
    altitude = getattr(
        chart,
        "center_alt_deg",
        getattr(context, "tangent_latitude_deg", 90.0),
    )
    azimuth = getattr(
        chart,
        "center_az_deg",
        getattr(context, "tangent_longitude_deg", 0.0),
    )
    horizontal = SkyCoord(
        az=float(azimuth) * u.deg,
        alt=float(altitude) * u.deg,
        frame=sky.observer.altaz_frame,
    )
    center = horizontal.transform_to(FK5(equinox=Time("J2000")))
    ra = center.ra.to_string(unit=u.hour, sep="hms", precision=0)
    dec = center.dec.to_string(
        unit=u.deg,
        sep="°′″",
        precision=0,
        alwayssign=True,
    )
    return f"Center: RA {ra}, Dec {dec}"


def resolve_legend_metadata(chart, sky, *, grid=None) -> LegendMetadata:
    """Resolve center and active-grid descriptions for a chart legend."""
    active = active_coordinate_grid(sky, explicit=grid)
    system, frame, epoch, description = _grid_description(active)
    return LegendMetadata(
        center_text=_center_text(chart, sky),
        grid_text=description,
        coordinate_system=system,
        frame=frame,
        epoch=epoch,
    )
