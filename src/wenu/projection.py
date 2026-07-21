# src/wenu/projection.py

import numpy as np

# -----------------------
# Proyección estereográfica (cenit)
# -----------------------
class StereographicProjection:

    def __init__(self, radius=2.0, flip_ew=True):
        self.radius = radius
        self.flip_ew = flip_ew

    def draw_point(
        self,
        ax,
        alt_deg,
        az_deg,
        *,
        marker="+",
        size=100,
        label=None,
        label_offset=(0.03, 0.03),
        fontsize=9,
        **kwargs,
    ):
        """
            Project and draw one point given in altitude and azimuth.
    
        Parameters
        ----------
        ax : matplotlib.axes.Axes
            Axis on which the point is drawn.
        alt_deg, az_deg : float
            Horizontal coordinates in degrees.
        marker : str, optional
            Matplotlib marker.
        size : float, optional
            Marker area passed to ``ax.scatter``.
        label : str or None, optional
            Optional label.
        label_offset : tuple, optional
            Label offset in projected coordinates.
        fontsize : float, optional
            Label font size.
        **kwargs
            Additional keyword arguments passed to ``ax.scatter``.

        Returns
        -------
        tuple
            Projected ``(x, y)`` coordinates, or ``(None, None)`` when
            the point is below the horizon.
        """

        alt_deg = float(np.asarray(alt_deg))
        az_deg = float(np.asarray(az_deg))

        if alt_deg < 0.0:
            return None, None

        x, y = self.project(alt_deg, az_deg)

        x = float(np.asarray(x))
        y = float(np.asarray(y))

        ax.scatter(
            x,
            y,
            marker=marker,
            s=size,
            **kwargs,
        )

        if label is not None:
            dx, dy = label_offset

            ax.text(
                x + dx,
                y + dy,
                label,
                fontsize=fontsize,
                color=kwargs.get("color"),
                ha="left",
                va="bottom",
                zorder=kwargs.get("zorder"),
            )

        return x, y

    def project_spherical(
        self,
        lon_deg,
        lat_deg,
    ):
        """
        Project generic spherical longitude and latitude coordinates.

        Parameters
        ----------
        lon_deg
            Spherical longitude in degrees.

        lat_deg
            Spherical latitude in degrees.

        Returns
        -------
        tuple
            Projected ``(x, y)`` coordinates.

        Notes
        -----
        Latitude +90 degrees is the tangent point and maps to the
        projection origin.
        """

        lon = np.radians(lon_deg)
        lat = np.radians(lat_deg)

        r = self.radius * np.tan(
            (np.pi / 2.0 - lat) / 2.0
        )

        x = r * np.sin(lon)
        y = r * np.cos(lon)

        if self.flip_ew:
            x = -x

        return x, y

    def project(
        self,
        alt_deg,
        az_deg,
    ):
        """
        Project horizontal Alt/Az coordinates.

        This is the backward-compatible interface used by the existing
        Wenu code. Altitude is interpreted as spherical latitude and
        azimuth as spherical longitude.
        """

        return self.project_spherical(
            lon_deg=az_deg,
            lat_deg=alt_deg,
        )

    def visible(self, alt_deg, az_deg=None):
        """
        Return the visibility mask for the planisphere.
        """

        return np.asarray(alt_deg) > 0.0

    def draw_curve(
        self,
        ax,
        alt_deg,
        az_deg,
        *,
        min_altitude=0.0,
        **plot_kwargs,
    ):
        """
        Project and draw visible contiguous segments of a curve.
        """

        alt_deg = np.asarray(alt_deg)
        az_deg = np.asarray(az_deg)

        if alt_deg.shape != az_deg.shape:
            raise ValueError(
                "alt_deg and az_deg must have the same shape."
            )

        x, y = self.project(alt_deg, az_deg)

        visible = alt_deg > min_altitude

        indices = np.flatnonzero(visible)

        if len(indices) == 0:
            return []

        breaks = np.where(np.diff(indices) > 1)[0] + 1
        segments = np.split(indices, breaks)

        artists = []

        for segment in segments:
            if len(segment) < 2:
                continue

            artist, = ax.plot(
                x[segment],
                y[segment],
                **plot_kwargs,
            )

            artists.append(artist)

        return artists
