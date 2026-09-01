"""Generic preparation between projection and rendering."""

from __future__ import annotations

import numpy as np

from wenu.geometry.projected import (
    ProjectedCurve,
    ProjectedCurves,
    ProjectedGrid,
    ProjectedPolygon,
    ProjectedPolygons,
    ProjectedPoints,
)
from wenu.geometry.spherical import (
    SphericalCurves,
    SphericalGrid,
    SphericalPoints,
    SphericalPolygons,
)


def magnitude_sizes(
    magnitudes,
    *,
    scale=1.5,
    reference_magnitude=5.0,
    exponent=0.35,
    minimum=1.0,
    maximum=None,
):
    """Convert magnitudes to Matplotlib scatter areas."""
    values = scale * 10.0 ** (
        exponent
        * (reference_magnitude - np.asarray(magnitudes, dtype=float))
    )
    values = np.maximum(values, minimum)
    return values if maximum is None else np.minimum(values, maximum)


def configured_magnitude_sizes(
    magnitudes,
    sizing,
    *,
    limiting_magnitude=None,
):
    """Apply an immutable stellar sizing configuration."""
    reference = float(sizing.reference_magnitude)
    if sizing.reference == "limiting_magnitude":
        if limiting_magnitude is None:
            raise ValueError(
                "limiting_magnitude is required by the sizing configuration."
            )
        reference = float(limiting_magnitude)
    return magnitude_sizes(
        magnitudes,
        scale=sizing.scale,
        reference_magnitude=reference,
        exponent=sizing.exponent,
        minimum=sizing.minimum_area,
        maximum=sizing.maximum_area,
    )


def cull_points_to_viewport(
    projected,
    viewport,
    *,
    margin_fraction=0.02,
):
    """Mark points well outside a projected viewport as non-renderable.

    The small margin preserves marker fragments at the axes edge.  Point
    arrays and metadata retain their original length so renderer masks and
    per-object style arrays remain aligned.
    """
    from wenu.geometry.viewport import Viewport

    if not isinstance(projected, ProjectedPoints):
        raise TypeError("projected must be ProjectedPoints.")
    if not isinstance(viewport, Viewport):
        raise TypeError("viewport must be a Viewport.")
    margin_fraction = float(margin_fraction)
    if (
        not np.isfinite(margin_fraction)
        or margin_fraction < 0.0
    ):
        raise ValueError(
            "margin_fraction must be finite and non-negative."
        )
    margin_x = margin_fraction * viewport.width
    margin_y = margin_fraction * viewport.height
    x = np.asarray(projected.x, dtype=float).copy()
    y = np.asarray(projected.y, dtype=float).copy()
    retained = (
        np.isfinite(x)
        & np.isfinite(y)
        & (x >= viewport.x_min - margin_x)
        & (x <= viewport.x_max + margin_x)
        & (y >= viewport.y_min - margin_y)
        & (y <= viewport.y_max + margin_y)
    )
    x[~retained] = np.nan
    y[~retained] = np.nan
    return ProjectedPoints(
        x=x,
        y=y,
        ids=projected.ids,
        labels=projected.labels,
        names=projected.names,
        metadata=dict(projected.metadata),
    )


def point_styles(metadata, *, default_zorder=None):
    """Return renderer styles encoded by a spherical point collection."""
    count = len(metadata.get("style", ()))
    styles = []
    for index in range(count):
        style = dict(metadata["style"][index])
        style.pop("label_offset", None)
        style.pop("fontsize", None)
        style.setdefault("marker", metadata["marker"][index])
        style.setdefault("s", metadata["size"][index])
        style.setdefault("color", metadata["color"][index])
        zorder = metadata["zorder"][index]
        if zorder is None:
            zorder = default_zorder
        if zorder is not None:
            style.setdefault("zorder", zorder)
        styles.append(style)
    return styles


def radial_label_offset(distance):
    """Return a projection-generic radial label-offset callback."""
    distance = float(distance)

    def offset(x, y):
        radius = np.hypot(x, y)
        if radius <= 1.0e-12:
            return 0.0, 0.0
        return distance * x / radius, distance * y / radius

    return offset


def clip_to_latitude(
    spherical,
    projected,
    *,
    minimum=0.0,
    maximum=None,
):
    """Clip corresponding projected geometry by spherical latitude."""
    minimum = float(minimum)
    maximum = None if maximum is None else float(maximum)
    if maximum is not None and minimum > -90.0:
        raise ValueError(
            "Simultaneous minimum and maximum latitude clipping is not "
            "supported."
        )
    latitude_sign = -1.0 if maximum is not None else 1.0
    threshold = -maximum if maximum is not None else minimum
    if threshold <= -90.0 and not isinstance(
        spherical, SphericalPolygons
    ):
        return projected
    if isinstance(spherical, SphericalPoints):
        return _clip_points(
            spherical,
            projected,
            threshold,
            latitude_sign=latitude_sign,
        )
    if isinstance(spherical, SphericalCurves):
        return _clip_curves(
            spherical,
            projected,
            threshold,
            latitude_sign=latitude_sign,
        )
    if isinstance(spherical, SphericalGrid):
        return ProjectedGrid(
            components={
                name: _clip_curves(
                    curves,
                    projected.components[name],
                    threshold,
                    latitude_sign=latitude_sign,
                )
                for name, curves in spherical.components.items()
            },
            metadata=dict(projected.metadata),
        )
    if isinstance(spherical, SphericalPolygons):
        return _clip_polygon_boundaries(
            spherical,
            projected,
            threshold,
            latitude_sign=latitude_sign,
        )
    raise TypeError(
        "Latitude clipping does not support "
        f"{type(spherical).__name__}."
    )


def _clip_points(spherical, projected, minimum, *, latitude_sign=1.0):
    latitude = latitude_sign * spherical.lat_deg
    visible = (
        np.isfinite(latitude)
        & (latitude >= minimum)
    )
    x = np.asarray(projected.x, dtype=float).copy()
    y = np.asarray(projected.y, dtype=float).copy()
    x[~visible] = np.nan
    y[~visible] = np.nan
    return ProjectedPoints(
        x=x,
        y=y,
        ids=projected.ids,
        labels=projected.labels,
        names=projected.names,
        metadata=dict(projected.metadata),
    )


def _clip_curves(
    spherical,
    projected,
    minimum,
    *,
    latitude_sign=1.0,
):
    items = []
    source_indices = []
    for source_index, (latitude, curve, closed) in enumerate(
        zip(spherical.lat_deg, projected, spherical.closed)
    ):
        for x, y in _visible_segments(
            curve.x,
            curve.y,
            latitude_sign * latitude,
            closed=bool(closed),
            minimum=minimum,
        ):
            items.append(
                ProjectedCurve(
                    x=x,
                    y=y,
                    closed=False,
                    name=curve.name,
                )
            )
            source_indices.append(source_index)

    return ProjectedCurves(
        items=items,
        metadata=_subset_metadata(
            projected.metadata,
            source_indices,
            len(projected),
        ),
    )


def clip_polygons_to_latitude(
    spherical,
    projected,
    *,
    minimum=0.0,
):
    """Clip filled polygons against a spherical latitude boundary.

    Unlike ``clip_to_latitude()``, which retains historical boundary-only
    behavior for spherical polygons, this function returns closed
    ``ProjectedPolygons`` suitable for face rendering.
    """
    if not isinstance(spherical, SphericalPolygons):
        raise TypeError("spherical must be SphericalPolygons.")
    if not isinstance(projected, ProjectedPolygons):
        raise TypeError("projected must be ProjectedPolygons.")
    minimum = float(minimum)
    if minimum <= -90.0:
        return projected
    items = []
    source_indices = []
    latitudes = _polygon_latitudes(spherical, projected)
    inversions = np.asarray(
        projected.metadata.get(
            "projection_cap_topology_inversion",
            np.zeros(len(projected), dtype=bool),
        ),
        dtype=bool,
    )
    boundary_radius = _projection_cap_boundary_radius(projected)
    for index, (latitude, polygon) in enumerate(
        zip(latitudes, projected)
    ):
        clipped = _clip_one_polygon_to_latitude(
            polygon,
            latitude,
            minimum,
            boundary_radius=(
                boundary_radius
                if inversions.shape == (len(projected),)
                and inversions[index]
                else None
            ),
        )
        if clipped is not None:
            items.append(clipped)
            source_indices.append(index)

    return ProjectedPolygons(
        items=items,
        metadata=_subset_metadata(
            projected.metadata,
            source_indices,
            len(projected),
        ),
    )


def clip_polygons_to_projection_cap(
    spherical,
    projected,
    *,
    projection,
    angular_radius_deg=80.0,
):
    """Clip spherical polygons to a cap around a projection tangent point.

    This preparation is intended for filled, full-sky polygon layers in a
    regional stereographic chart.  Clipping before projection prevents a
    ring on the far side of the sphere from wrapping around the projection
    antipode and appearing as a viewport-sized patch.

    The cap boundary should normally lie outside the chart viewport.  Its
    only purpose is to provide a safe finite domain for projection.
    """
    if not isinstance(spherical, SphericalPolygons):
        raise TypeError("spherical must be SphericalPolygons.")
    if not isinstance(projected, ProjectedPolygons):
        raise TypeError("projected must be ProjectedPolygons.")
    if len(spherical) != len(projected):
        raise ValueError(
            "Spherical and projected polygon collections must match."
        )
    angular_radius_deg = float(angular_radius_deg)
    if (
        not np.isfinite(angular_radius_deg)
        or angular_radius_deg <= 0.0
        or angular_radius_deg >= 90.0
    ):
        raise ValueError(
            "angular_radius_deg must be finite and between "
            "0 and 90 degrees."
        )

    minimum_z = np.cos(np.radians(angular_radius_deg))
    items = []
    source_indices = []
    for index, (longitude, latitude, polygon) in enumerate(
        zip(spherical.lon_deg, spherical.lat_deg, projected)
    ):
        clipped = _clip_one_polygon_to_projection_cap(
            longitude,
            latitude,
            polygon.name,
            projection,
            minimum_z,
        )
        if clipped is not None:
            items.append(clipped)
            source_indices.append(index)

    return ProjectedPolygons(
        items=items,
        metadata=_subset_metadata(
            projected.metadata,
            source_indices,
            len(projected),
        ),
    )


def project_geometry_for_viewport(
    spherical,
    *,
    projection,
    viewport=None,
    projection_cap_margin_deg=2.0,
):
    """Project geometry through a safe domain for the visible viewport.

    Stereographic projection is finite on the near hemisphere but filled
    full-sky polygon rings can otherwise cross its antipode and wrap back
    across a regional chart.  When a viewport is known, spherical polygons
    are clipped to a cap that contains the complete viewport before any
    planar coordinates are calculated.  Other geometry retains the normal
    projection path.

    The projected viewport and any chart-specific field stop remain later
    clipping stages.  This function only protects projection topology.
    """
    if viewport is None or not isinstance(spherical, SphericalPolygons):
        return projection.project_geometry(spherical)

    angular_radius_deg = projection_cap_for_viewport(
        projection,
        viewport,
        margin_deg=projection_cap_margin_deg,
    )
    if angular_radius_deg is None:
        return projection.project_geometry(spherical)
    return project_polygons_to_projection_cap(
        spherical,
        projection=projection,
        angular_radius_deg=angular_radius_deg,
    )


def projection_cap_for_viewport(
    projection,
    viewport,
    *,
    margin_deg=2.0,
    maximum_deg=89.999,
):
    """Return a near-hemisphere cap containing a projected viewport.

    ``None`` means that the projection does not expose the stereographic
    scale needed to derive the inverse angular radius.
    """
    inverse_radius = getattr(
        projection,
        "angular_radius_for_projected_radius",
        None,
    )
    if not callable(inverse_radius):
        return None
    margin_deg = float(margin_deg)
    maximum_deg = float(maximum_deg)
    if not np.isfinite(margin_deg) or margin_deg < 0.0:
        raise ValueError("margin_deg must be finite and non-negative.")
    if not np.isfinite(maximum_deg) or not 0.0 < maximum_deg < 90.0:
        raise ValueError("maximum_deg must be between 0 and 90 degrees.")

    corners_x = np.asarray(
        (
            viewport.x_min,
            viewport.x_min,
            viewport.x_max,
            viewport.x_max,
        ),
        dtype=float,
    )
    corners_y = np.asarray(
        (
            viewport.y_min,
            viewport.y_max,
            viewport.y_min,
            viewport.y_max,
        ),
        dtype=float,
    )
    planar_radius = float(np.max(np.hypot(corners_x, corners_y)))
    angular_radius_deg = float(inverse_radius(planar_radius))
    return min(maximum_deg, angular_radius_deg + margin_deg)


def project_polygons_to_projection_cap(
    spherical,
    *,
    projection,
    angular_radius_deg=80.0,
):
    """Clip spherical polygons to a safe cap and then project them.

    Unlike :func:`clip_polygons_to_projection_cap`, this is a true
    pre-projection operation: no unsafe full polygon projection is created
    first.
    """
    if not isinstance(spherical, SphericalPolygons):
        raise TypeError("spherical must be SphericalPolygons.")
    angular_radius_deg = float(angular_radius_deg)
    if (
        not np.isfinite(angular_radius_deg)
        or angular_radius_deg <= 0.0
        or angular_radius_deg >= 180.0
    ):
        raise ValueError(
            "angular_radius_deg must be finite and between "
            "0 and 180 degrees."
        )

    minimum_z = np.cos(np.radians(angular_radius_deg))
    items = []
    source_indices = []
    source_latitudes = []
    for index, (longitude, latitude) in enumerate(
        zip(spherical.lon_deg, spherical.lat_deg)
    ):
        name = (
            None
            if spherical.names is None
            else spherical.names[index]
        )
        clipped_result = _clip_one_polygon_to_projection_cap(
            longitude,
            latitude,
            name,
            projection,
            minimum_z,
            return_source_latitudes=True,
        )
        if clipped_result is not None:
            clipped, clipped_latitude = clipped_result
            items.append(clipped)
            source_indices.append(index)
            source_latitudes.append(clipped_latitude)

    metadata = _spherical_collection_metadata(spherical)
    metadata = _subset_metadata(
        metadata,
        source_indices,
        len(spherical),
    )
    metadata["projection_domain_clipped"] = True
    metadata["projection_cap_deg"] = angular_radius_deg
    metadata["projection_source_latitudes"] = tuple(source_latitudes)
    projected = ProjectedPolygons(items=items, metadata=metadata)
    return _apply_projection_cap_topology_complements(
        projected, projection, minimum_z
    )


def _apply_projection_cap_topology_complements(
    projected, projection, minimum_z
):
    inversions = projected.metadata.get(
        "projection_cap_topology_inversion"
    )
    groups = projected.metadata.get("compound_id")
    holes = projected.metadata.get("is_hole")
    if inversions is None or groups is None or holes is None:
        return projected
    inversions = np.asarray(inversions, dtype=bool)
    groups = np.asarray(groups, dtype=object)
    holes = np.asarray(holes, dtype=bool)
    if not (
        inversions.shape == groups.shape == holes.shape == (len(projected),)
    ):
        raise ValueError(
            "Projection-cap topology metadata must contain one value "
            "per polygon ring."
        )
    inverted_groups = tuple(dict.fromkeys(groups[inversions].tolist()))
    if not inverted_groups:
        return projected

    metadata = dict(projected.metadata)
    complemented_holes = holes.copy()
    boundary_source_indices = []
    items = list(projected.items)
    boundary, boundary_latitude = _projection_cap_boundary(
        projection, minimum_z
    )
    for group in inverted_groups:
        positions = np.flatnonzero(groups == group)
        complemented_holes[positions] = ~complemented_holes[positions]
        items.append(boundary)
        boundary_source_indices.append(int(positions[0]))

    source_length = len(projected)
    metadata["is_hole"] = _append_metadata_values(
        complemented_holes,
        boundary_source_indices,
        source_length=source_length,
        appended_value=False,
    )
    for name, value in tuple(metadata.items()):
        if name == "is_hole":
            continue
        appended_value = None
        if name == "projection_source_latitudes":
            appended_value = boundary_latitude
        elif name == "projection_cap_topology_inversion":
            appended_value = False
        metadata[name] = _append_metadata_values(
            value,
            boundary_source_indices,
            source_length=source_length,
            appended_value=appended_value,
        )
    return ProjectedPolygons(items=items, metadata=metadata)


def _append_metadata_values(
    value,
    source_indices,
    *,
    source_length,
    appended_value=None,
):
    count = len(source_indices)
    if count == 0:
        return value
    if (
        isinstance(value, np.ndarray)
        and value.ndim >= 1
        and len(value) == source_length
    ):
        additions = (
            np.full(count, appended_value, dtype=value.dtype)
            if appended_value is not None
            else value[np.asarray(source_indices, dtype=int)]
        )
        return np.concatenate((value, additions))
    if isinstance(value, tuple) and len(value) == source_length:
        additions = tuple(
            appended_value if appended_value is not None else value[index]
            for index in source_indices
        )
        return value + additions
    if isinstance(value, list) and len(value) == source_length:
        additions = [
            appended_value if appended_value is not None else value[index]
            for index in source_indices
        ]
        return value + additions
    return value


def _projection_cap_boundary(projection, minimum_z, *, samples=1441):
    angle = np.linspace(0.0, 2.0 * np.pi, samples, endpoint=False)
    radius = np.sqrt(max(0.0, 1.0 - minimum_z * minimum_z))
    aligned = np.column_stack((
        radius * np.cos(angle),
        radius * np.sin(angle),
        np.full_like(angle, minimum_z),
    ))
    source = _source_vectors_for_aligned_arc(aligned, projection)
    longitude = np.degrees(np.arctan2(source[:, 1], source[:, 0]))
    latitude = np.degrees(
        np.arcsin(np.clip(source[:, 2], -1.0, 1.0))
    )
    x, y = projection.project_spherical(longitude, latitude)
    return (
        ProjectedPolygon(x=x, y=y, name="projection_cap"),
        latitude,
    )


def _clip_one_polygon_to_projection_cap(
    longitude,
    latitude,
    name,
    projection,
    minimum_z,
    *,
    return_source_latitudes=False,
):
    """Clip one ring in projection-aligned unit-vector coordinates."""
    longitude = np.asarray(longitude, dtype=float)
    latitude = np.asarray(latitude, dtype=float)
    if longitude.shape != latitude.shape or longitude.ndim != 1:
        raise ValueError(
            "Spherical polygon coordinates must be matching "
            "one-dimensional arrays."
        )
    finite = np.isfinite(longitude) & np.isfinite(latitude)
    if not np.all(finite) or longitude.size < 3:
        return None

    aligned_lon, aligned_lat = _projection_aligned_coordinates(
        projection, longitude, latitude
    )
    vectors = _unit_vectors(
        aligned_lon,
        aligned_lat,
    )
    source_vectors = _unit_vectors(longitude, latitude)
    if (
        len(vectors) > 1
        and np.allclose(vectors[0], vectors[-1])
    ):
        vectors = vectors[:-1]
        source_vectors = source_vectors[:-1]
    if len(vectors) < 3:
        return None

    output = []
    output_source = []
    pending_exit = False
    outside_angles = []
    leading_outside_angles = []
    previous = vectors[-1]
    previous_source = source_vectors[-1]
    previous_inside = previous[2] >= minimum_z
    for current, current_source in zip(vectors, source_vectors):
        current_inside = current[2] >= minimum_z
        if current_inside:
            if not previous_inside:
                intersection, fraction = _cap_intersection(
                    previous,
                    current,
                    minimum_z,
                    return_fraction=True,
                )
                intersection_source = _slerp(
                    previous_source,
                    current_source,
                    fraction,
                )
                if pending_exit and output:
                    arc = _projection_cap_arc(
                        output[-1],
                        intersection,
                        minimum_z,
                        traversal_angles=outside_angles + [
                            _vector_angle(intersection)
                        ],
                    )
                    source_arc = _source_vectors_for_aligned_arc(
                        arc, projection
                    )
                    output.extend(arc[1:-1])
                    output_source.extend(source_arc[1:-1])
                output.append(intersection)
                output_source.append(intersection_source)
                if not pending_exit:
                    leading_outside_angles.append(
                        _vector_angle(intersection)
                    )
                pending_exit = False
                outside_angles = []
            output.append(current)
            output_source.append(current_source)
        elif previous_inside:
            intersection, fraction = _cap_intersection(
                previous,
                current,
                minimum_z,
                return_fraction=True,
            )
            output.append(intersection)
            output_source.append(
                _slerp(
                    previous_source,
                    current_source,
                    fraction,
                )
            )
            pending_exit = True
            outside_angles = [
                _vector_angle(intersection),
                _vector_angle(current),
            ]
        elif pending_exit:
            outside_angles.append(_vector_angle(current))
        elif not current_inside:
            if not leading_outside_angles:
                leading_outside_angles.append(_vector_angle(previous))
            leading_outside_angles.append(_vector_angle(current))
        previous = current
        previous_source = current_source
        previous_inside = current_inside

    if pending_exit and output:
        first_crossing = next(
            (
                index for index, vector in enumerate(output)
                if np.isclose(vector[2], minimum_z)
            ),
            None,
        )
        if first_crossing is not None:
            arc = _projection_cap_arc(
                output[-1],
                output[first_crossing],
                minimum_z,
                traversal_angles=(
                    outside_angles + leading_outside_angles
                ),
            )
            source_arc = _source_vectors_for_aligned_arc(arc, projection)
            output.extend(arc[1:-1])
            output_source.extend(source_arc[1:-1])

    output, output_source = _deduplicate_vector_pairs(
        output,
        output_source,
    )
    if len(output) < 3:
        return None
    output_source = np.asarray(output_source, dtype=float)
    source_longitude = np.degrees(
        np.arctan2(output_source[:, 1], output_source[:, 0])
    )
    source_latitude = np.degrees(
        np.arcsin(np.clip(output_source[:, 2], -1.0, 1.0))
    )
    x, y = projection.project_spherical(source_longitude, source_latitude)
    polygon = ProjectedPolygon(x=x, y=y, name=name)
    if not return_source_latitudes:
        return polygon
    return polygon, source_latitude


def _projection_cap_arc(
    start,
    end,
    minimum_z,
    *,
    traversal_angles=None,
    maximum_step_deg=0.25,
):
    """Follow the source traversal along a constant-radius cap arc."""
    start_angle = float(np.arctan2(start[1], start[0]))
    end_angle = float(np.arctan2(end[1], end[0]))
    if traversal_angles:
        traversal = np.unwrap(np.asarray(traversal_angles, dtype=float))
        delta = float(traversal[-1] - traversal[0])
    else:
        delta = (
            end_angle - start_angle + np.pi
        ) % (2.0 * np.pi) - np.pi
    count = max(
        1,
        int(np.ceil(abs(np.degrees(delta)) / maximum_step_deg)),
    )
    angle = np.linspace(start_angle, start_angle + delta, count + 1)
    radius = np.sqrt(max(0.0, 1.0 - minimum_z * minimum_z))
    return np.column_stack((
        radius * np.cos(angle),
        radius * np.sin(angle),
        np.full_like(angle, minimum_z),
    ))


def _vector_angle(vector):
    return float(np.arctan2(vector[1], vector[0]))


def _source_vectors_for_aligned_arc(vectors, projection):
    longitude = np.degrees(np.arctan2(vectors[:, 1], vectors[:, 0]))
    latitude = np.degrees(
        np.arcsin(np.clip(vectors[:, 2], -1.0, 1.0))
    )
    frame = getattr(projection, "frame", None)
    if frame is not None:
        source = frame.inverse_transform(longitude, latitude)
        longitude = source.lon_deg
        latitude = source.lat_deg
    elif getattr(projection, "pole", None) == "south":
        latitude = -latitude
    return _unit_vectors(longitude, latitude)


def _projection_aligned_coordinates(projection, longitude, latitude):
    frame = getattr(projection, "frame", None)
    if frame is not None:
        aligned = projection.transform_spherical(longitude, latitude)
        return aligned.lon_deg, aligned.lat_deg
    if getattr(projection, "pole", None) == "south":
        return longitude, -np.asarray(latitude, dtype=float)
    return longitude, latitude


def _unit_vectors(longitude_deg, latitude_deg):
    longitude = np.radians(np.asarray(longitude_deg, dtype=float))
    latitude = np.radians(np.asarray(latitude_deg, dtype=float))
    cos_latitude = np.cos(latitude)
    return np.column_stack(
        (
            cos_latitude * np.cos(longitude),
            cos_latitude * np.sin(longitude),
            np.sin(latitude),
        )
    )


def _cap_intersection(
    start,
    end,
    minimum_z,
    *,
    return_fraction=False,
):
    """Locate a great-circle edge crossing of a constant-radius cap."""
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    low = 0.0
    high = 1.0
    start_inside = start[2] >= minimum_z
    for _ in range(52):
        middle = 0.5 * (low + high)
        candidate = _slerp(start, end, middle)
        if (candidate[2] >= minimum_z) == start_inside:
            low = middle
        else:
            high = middle
    fraction = 0.5 * (low + high)
    intersection = _slerp(start, end, fraction)
    if return_fraction:
        return intersection, fraction
    return intersection


def _slerp(start, end, fraction):
    dot = float(np.clip(np.dot(start, end), -1.0, 1.0))
    angle = float(np.arccos(dot))
    if angle <= 1.0e-12:
        vector = (1.0 - fraction) * start + fraction * end
    else:
        sine = np.sin(angle)
        vector = (
            np.sin((1.0 - fraction) * angle) / sine * start
            + np.sin(fraction * angle) / sine * end
        )
    norm = np.linalg.norm(vector)
    if norm <= 1.0e-15:
        raise ValueError(
            "Cannot interpolate antipodal polygon vertices."
        )
    return vector / norm


def _deduplicate_vectors(vectors):
    cleaned = []
    for vector in vectors:
        if not cleaned or not np.allclose(vector, cleaned[-1]):
            cleaned.append(np.asarray(vector, dtype=float))
    if (
        len(cleaned) > 1
        and np.allclose(cleaned[0], cleaned[-1])
    ):
        cleaned.pop()
    return cleaned


def _deduplicate_vector_pairs(vectors, source_vectors):
    """Deduplicate aligned vertices and their source-frame partners."""
    cleaned = []
    cleaned_source = []
    for vector, source_vector in zip(vectors, source_vectors):
        if not cleaned or not np.allclose(vector, cleaned[-1]):
            cleaned.append(np.asarray(vector, dtype=float))
            cleaned_source.append(
                np.asarray(source_vector, dtype=float)
            )
    if (
        len(cleaned) > 1
        and np.allclose(cleaned[0], cleaned[-1])
    ):
        cleaned.pop()
        cleaned_source.pop()
    return cleaned, cleaned_source


def _projection_cap_boundary_radius(projected):
    for polygon in projected:
        if polygon.name != "projection_cap":
            continue
        radii = np.hypot(polygon.x, polygon.y)
        finite = radii[np.isfinite(radii)]
        if finite.size:
            return float(np.median(finite))
    return None


def _clip_one_polygon_to_latitude(
    polygon,
    latitude,
    minimum,
    *,
    boundary_radius=None,
):
    """Clip one projected polygon using corresponding vertex latitudes."""
    latitude = np.asarray(latitude, dtype=float)
    x = np.asarray(polygon.x, dtype=float)
    y = np.asarray(polygon.y, dtype=float)
    if not (x.shape == y.shape == latitude.shape):
        raise ValueError(
            "Projected polygon coordinates and latitudes must match."
        )
    if x.ndim != 1:
        raise ValueError("Polygon clipping arrays must be one-dimensional.")
    finite = np.isfinite(x) & np.isfinite(y) & np.isfinite(latitude)
    if not np.all(finite) or x.size < 3:
        return None
    if boundary_radius is not None:
        return _clip_one_polygon_to_circular_latitude(
            polygon,
            latitude,
            minimum,
            float(boundary_radius),
        )

    output = []
    previous = (x[-1], y[-1], latitude[-1])
    previous_inside = previous[2] >= minimum

    for current in zip(x, y, latitude):
        current_inside = current[2] >= minimum
        if current_inside:
            if not previous_inside:
                output.append(
                    _latitude_intersection(
                        previous,
                        current,
                        minimum,
                    )
                )
            output.append((float(current[0]), float(current[1])))
        elif previous_inside:
            output.append(
                _latitude_intersection(
                    previous,
                    current,
                    minimum,
                )
            )
        previous = current
        previous_inside = current_inside

    cleaned = []
    for vertex in output:
        if not cleaned or not np.allclose(vertex, cleaned[-1]):
            cleaned.append(vertex)
    if (
        len(cleaned) > 1
        and np.allclose(cleaned[0], cleaned[-1])
    ):
        cleaned.pop()
    if len(cleaned) < 3:
        return None

    clipped_x, clipped_y = zip(*cleaned)
    return ProjectedPolygon(
        x=np.asarray(clipped_x, dtype=float),
        y=np.asarray(clipped_y, dtype=float),
        name=polygon.name,
    )


def _clip_one_polygon_to_circular_latitude(
    polygon,
    latitude,
    minimum,
    boundary_radius,
):
    """Clip a winding ring and close excursions along a circular horizon."""
    x = np.asarray(polygon.x, dtype=float)
    y = np.asarray(polygon.y, dtype=float)
    latitude = np.asarray(latitude, dtype=float)
    output = []
    pending_exit = False
    outside_points = []
    leading_outside_points = []
    previous = (x[-1], y[-1], latitude[-1])
    previous_inside = previous[2] >= minimum

    for current in zip(x, y, latitude):
        current_inside = current[2] >= minimum
        if current_inside:
            if not previous_inside:
                crossing = _latitude_intersection(
                    previous, current, minimum
                )
                if pending_exit and output:
                    arc = _projected_boundary_arc(
                        output[-1],
                        crossing,
                        boundary_radius,
                        traversal_points=outside_points + [crossing],
                    )
                    output.extend(map(tuple, arc[1:-1]))
                elif not pending_exit:
                    leading_outside_points.append(crossing)
                output.append(crossing)
                pending_exit = False
                outside_points = []
            output.append((float(current[0]), float(current[1])))
        elif previous_inside:
            crossing = _latitude_intersection(
                previous, current, minimum
            )
            output.append(crossing)
            pending_exit = True
            outside_points = [
                crossing,
                (float(current[0]), float(current[1])),
            ]
        elif pending_exit:
            outside_points.append(
                (float(current[0]), float(current[1]))
            )
        else:
            if not leading_outside_points:
                leading_outside_points.append(
                    (float(previous[0]), float(previous[1]))
                )
            leading_outside_points.append(
                (float(current[0]), float(current[1]))
            )
        previous = current
        previous_inside = current_inside

    if pending_exit and output:
        first_crossing = next(
            (
                vertex for vertex in output
                if np.isclose(np.hypot(*vertex), boundary_radius)
            ),
            output[0],
        )
        arc = _projected_boundary_arc(
            output[-1],
            first_crossing,
            boundary_radius,
            traversal_points=(
                outside_points + leading_outside_points
            ),
        )
        output.extend(map(tuple, arc[1:-1]))

    cleaned = []
    for vertex in output:
        if not cleaned or not np.allclose(vertex, cleaned[-1]):
            cleaned.append(vertex)
    if len(cleaned) > 1 and np.allclose(cleaned[0], cleaned[-1]):
        cleaned.pop()
    if len(cleaned) < 3:
        return None
    clipped_x, clipped_y = zip(*cleaned)
    return ProjectedPolygon(
        x=np.asarray(clipped_x, dtype=float),
        y=np.asarray(clipped_y, dtype=float),
        name=polygon.name,
    )


def _projected_boundary_arc(
    start,
    end,
    radius,
    *,
    traversal_points,
    maximum_step_deg=0.25,
):
    start_angle = float(np.arctan2(start[1], start[0]))
    traversal = np.asarray(traversal_points, dtype=float)
    if len(traversal) >= 2:
        angles = np.unwrap(np.arctan2(traversal[:, 1], traversal[:, 0]))
        delta = float(angles[-1] - angles[0])
    else:
        end_angle = float(np.arctan2(end[1], end[0]))
        delta = (end_angle - start_angle + np.pi) % (2.0 * np.pi) - np.pi
    count = max(
        1,
        int(np.ceil(abs(np.degrees(delta)) / maximum_step_deg)),
    )
    angles = np.linspace(start_angle, start_angle + delta, count + 1)
    return np.column_stack((radius * np.cos(angles), radius * np.sin(angles)))


def _latitude_intersection(start, end, minimum):
    """Interpolate a projected edge at a spherical latitude crossing."""
    latitude0 = float(start[2])
    latitude1 = float(end[2])
    if np.isclose(latitude0, latitude1):
        fraction = 0.0
    else:
        fraction = (minimum - latitude0) / (
            latitude1 - latitude0
        )
    return (
        float(start[0] + fraction * (end[0] - start[0])),
        float(start[1] + fraction * (end[1] - start[1])),
    )


def _subset_metadata(metadata, indices, source_length):
    """Subset per-entity metadata while preserving collection metadata."""
    subset = {}
    index_array = np.asarray(indices, dtype=int)
    for name, value in dict(metadata).items():
        if isinstance(value, np.ndarray) and value.ndim >= 1:
            if len(value) == source_length:
                subset[name] = value[index_array]
                continue
        if (
            isinstance(value, (list, tuple))
            and not isinstance(value, (str, bytes))
            and len(value) == source_length
        ):
            selected = [value[index] for index in indices]
            subset[name] = (
                tuple(selected)
                if isinstance(value, tuple)
                else selected
            )
            continue
        subset[name] = value
    return subset


def _spherical_collection_metadata(spherical):
    """Return collection metadata in the form used by projections."""
    metadata = dict(spherical.metadata)
    for name in ("ids", "labels", "names"):
        values = getattr(spherical, name, None)
        if values is not None:
            metadata[name] = values.copy()
    return metadata


def _polygon_latitudes(spherical, projected):
    """Return latitudes corresponding exactly to projected vertices."""
    latitudes = projected.metadata.get(
        "projection_source_latitudes"
    )
    if latitudes is None:
        latitudes = spherical.lat_deg
    if len(latitudes) != len(projected):
        raise ValueError(
            "Spherical and projected polygon collections must match."
        )
    return latitudes


def _clip_polygon_boundaries(
    spherical,
    projected,
    minimum,
    *,
    latitude_sign=1.0,
):
    if not isinstance(projected, ProjectedPolygons):
        raise TypeError(
            "SphericalPolygons require ProjectedPolygons."
        )
    items = []
    source_indices = []
    for source_index, (latitude, polygon) in enumerate(
        zip(
            _polygon_latitudes(spherical, projected),
            projected,
        )
    ):
        for x, y in _visible_segments(
            polygon.x,
            polygon.y,
            latitude_sign * latitude,
            closed=True,
            minimum=minimum,
        ):
            items.append(
                ProjectedCurve(
                    x=x,
                    y=y,
                    closed=False,
                    name=polygon.name,
                )
            )
            source_indices.append(source_index)
    return ProjectedCurves(
        items=items,
        metadata=_subset_metadata(
            projected.metadata,
            source_indices,
            len(projected),
        ),
    )


def _visible_segments(x, y, latitude, *, closed, minimum):
    """Return visible fragments with interpolated latitude crossings."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    latitude = np.asarray(latitude, dtype=float)
    if not (x.shape == y.shape == latitude.shape):
        raise ValueError(
            "Projected coordinates and latitude must have matching shapes."
        )
    if x.ndim != 1:
        raise ValueError("Curve clipping arrays must be one-dimensional.")
    if closed and x.size:
        x = np.append(x, x[0])
        y = np.append(y, y[0])
        latitude = np.append(latitude, latitude[0])

    segments = []
    current_x = []
    current_y = []

    def finish():
        nonlocal current_x, current_y
        if len(current_x) >= 2:
            segments.append(
                (
                    np.asarray(current_x, dtype=float),
                    np.asarray(current_y, dtype=float),
                )
            )
        current_x = []
        current_y = []

    def intersection(index):
        latitude0 = latitude[index]
        latitude1 = latitude[index + 1]
        fraction = (
            (minimum - latitude0) / (latitude1 - latitude0)
        )
        return (
            x[index] + fraction * (x[index + 1] - x[index]),
            y[index] + fraction * (y[index + 1] - y[index]),
        )

    for index in range(max(0, x.size - 1)):
        finite0 = np.all(
            np.isfinite((x[index], y[index], latitude[index]))
        )
        finite1 = np.all(
            np.isfinite(
                (x[index + 1], y[index + 1], latitude[index + 1])
            )
        )
        if not finite0 or not finite1:
            finish()
            continue

        visible0 = latitude[index] >= minimum
        visible1 = latitude[index + 1] >= minimum
        if visible0 and not current_x:
            current_x.append(float(x[index]))
            current_y.append(float(y[index]))

        if visible0 and visible1:
            current_x.append(float(x[index + 1]))
            current_y.append(float(y[index + 1]))
        elif visible0 and not visible1:
            crossing_x, crossing_y = intersection(index)
            current_x.append(float(crossing_x))
            current_y.append(float(crossing_y))
            finish()
        elif not visible0 and visible1:
            crossing_x, crossing_y = intersection(index)
            current_x = [float(crossing_x), float(x[index + 1])]
            current_y = [float(crossing_y), float(y[index + 1])]

    finish()
    return segments
