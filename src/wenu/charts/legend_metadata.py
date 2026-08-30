"""Backend-independent metadata for informational chart legends."""

from __future__ import annotations

from dataclasses import dataclass
import re
from zoneinfo import ZoneInfo

from astropy import units as u
from astropy.coordinates import Angle
from astropy.time import Time

from wenu.coordinate_service import CoordinateService
from wenu.coordinates import (
    CoordinateSpec,
    PositionStatus,
    observation_context,
    observer_altaz_spec,
)
from wenu.geometry.spherical import SphericalPoints


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


def _center_coordinates(chart, sky, observer=None) -> tuple[str, str]:
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
    resolved_observer = getattr(sky, "observer", None) if observer is None else observer
    if resolved_observer is None:
        raise TypeError("chart metadata requires an observer.")
    horizontal = SphericalPoints(
        lon_deg=[float(azimuth)],
        lat_deg=[float(altitude)],
        coordinate_spec=observer_altaz_spec(
            resolved_observer,
            position_status=PositionStatus.GEOMETRIC,
            provider="wenu chart center",
        ),
    )
    center = CoordinateService().transform(
        horizontal,
        CoordinateSpec(
            frame="fk5",
            origin="solar-system-barycenter",
            position_status=PositionStatus.ASTROMETRIC,
            equinox="J2000.0",
            provider="astropy coordinate service",
        ),
        observation_context(resolved_observer),
    )
    ra = Angle(center.lon_deg[0] * u.deg).to_string(
        unit=u.hour, sep="hms", precision=0
    )
    dec = Angle(center.lat_deg[0] * u.deg).to_string(
        unit=u.deg,
        sep="°′″",
        precision=0,
        alwayssign=True,
    )
    return ra, dec


def _center_text(chart, sky, observer=None) -> str:
    ra, dec = _center_coordinates(chart, sky, observer)
    return f"Center: RA {ra}, Dec {dec}"


def resolve_legend_metadata(
    chart, sky, *, observer=None, grid=None
) -> LegendMetadata:
    """Resolve center and active-grid descriptions for a chart legend."""
    active = active_coordinate_grid(sky, explicit=grid)
    system, frame, epoch, description = _grid_description(active)
    return LegendMetadata(
        center_text=_center_text(chart, sky, observer),
        grid_text=description,
        coordinate_system=system,
        frame=frame,
        epoch=epoch,
    )


def chart_context_lines(
    chart,
    sky,
    *,
    observer=None,
    center: bool = True,
    grid: bool = True,
) -> tuple[str, ...]:
    """Return compact, independently selectable chart context lines."""
    lines = []
    if center:
        ra, dec = _center_coordinates(chart, sky, observer)
        lines.extend((f"RA {ra}", f"Dec {dec}"))
    if grid:
        description = resolve_legend_metadata(
            chart, sky, observer=observer
        ).grid_text
        lines.append(
            description.split(": ", 1)[-1]
            if ": " in description
            else description
        )
    return tuple(lines)


def observer_context_lines(
    observer,
    *,
    location: bool = True,
    date: bool = True,
    local_time: bool = True,
    labels: bool = True,
) -> tuple[str, ...]:
    """Return publication-ready observer location and local-time lines."""
    local = observer.utc_datetime.astimezone(
        ZoneInfo(observer.timezone_name)
    )
    offset = local.utcoffset()
    total_minutes = int(offset.total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "−"
    hours, minutes = divmod(abs(total_minutes), 60)
    location_value = (
        f"{observer.location_name} — "
        f"{abs(observer.lat_deg):.4f}° S, "
        f"{abs(observer.lon_deg):.4f}° W, "
        f"{observer.elevation_m:.0f} m"
    )
    date_value = f"{local:%Y-%m-%d}"
    time_value = (
        f"{local:%H:%M} (UTC{sign}{hours:02d}:{minutes:02d})"
    )
    candidates = (
        (location, "Location", location_value),
        (date, "Date", date_value),
        (local_time, "Local time", time_value),
    )
    return tuple(
        f"{label}: {value}" if labels else value
        for enabled, label, value in candidates
        if enabled
    )
