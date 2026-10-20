"""Stellar SVG measurements and actual-catalogue atlas count appendices.

Areas describe complete vector silhouettes, excluding strokes. Count markers
whose centres survive SVG clipping; partially clipped markers retain full area.
Overlapping atlas pages contribute separate appearances of the same star.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import numpy as np
from matplotlib.path import Path as VectorPath


SVG = "http://www.w3.org/2000/svg"
NUMBER = r"[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?"
TOKENS = re.compile(rf"[A-Za-z]|{NUMBER}")
GAUSS_X, GAUSS_W = np.polynomial.legendre.leggauss(4)
GAUSS_T = (GAUSS_X + 1) / 2


def catalogue_star_counts(stars, magnitude_limit):
    """Cumulative actual catalogue counts, independent of page appearances."""
    geometry = stars.native_positions()
    identifiers = np.asarray(geometry.ids)
    # Preserve first-HIP/source order without re-reading raw source positions.
    _, first = np.unique(identifiers, return_index=True)
    first.sort()
    identifiers = identifiers[first]
    magnitudes = np.asarray(geometry.metadata["magnitude"], dtype=float)[first]
    ra = np.asarray(geometry.lon_deg, dtype=float)[first]
    dec = np.asarray(geometry.lat_deg, dtype=float)[first]
    finite = np.isfinite(magnitudes) & np.isfinite(ra) & np.isfinite(dec)
    selected = finite & (magnitudes <= magnitude_limit)
    values, frequency = np.unique(magnitudes[selected], return_counts=True)
    cumulative = np.cumsum(frequency)
    return dict(schema_version=1, document_kind="wenu-atlas-catalogue-star-counts",
        catalogue="Hipparcos", identifier="HIP", scope="complete design, not chart appearances",
        magnitude_limit=float(magnitude_limit), selected_count=int(np.count_nonzero(selected)),
        invalid_count=int(np.count_nonzero(~finite)),
        fainter_count=int(np.count_nonzero(finite & ~selected)),
        magnitude=values.tolist(), cumulative_count=cumulative.tolist(),
        log10_cumulative_count=np.log10(cumulative).tolist()), identifiers[selected], magnitudes[selected]


def render_catalogue_star_counts(stars, output_prefix, *, magnitude_limit, page, dpi, provenance):
    """Appendix from catalogue photometry; the existing atlas batch owns export."""
    import matplotlib.pyplot as plt
    from .regional import ExportOptions
    data, identifiers, magnitudes = catalogue_star_counts(stars, magnitude_limit)
    data["provenance"] = dict(provenance)
    prefix = Path(output_prefix)
    with Path(str(prefix) + "_catalogue.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("HIP", "magnitude"))
        writer.writerows(zip(identifiers, magnitudes))
    Path(str(prefix) + ".json").write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    figure = plt.figure(figsize=(page.width_mm / 25.4, page.height_mm / 25.4), dpi=dpi)
    try:
        figure.suptitle(f"Atlas catalogue star counts ({data['selected_count']:,} stars)", fontsize=18, y=.94)
        figure.text(.5, .885, f"Hipparcos · magnitude ≤ {magnitude_limit:g}\nEach HIP identifier is counted once", ha="center", fontsize=12)
        ax = figure.add_axes((.15, .25, .8, .56))
        if data["selected_count"]:
            ax.step(data["magnitude"], data["log10_cumulative_count"], where="post", color="#183b56")
        else:
            ax.text(.5, .5, "No catalogue stars satisfy the atlas selection", transform=ax.transAxes, ha="center")
        ax.set_xlabel("Catalogue magnitude m", fontsize=14)
        ax.invert_xaxis()
        ax.set_ylabel("log₁₀ N(≤ m)", fontsize=14)
        ax.tick_params(labelsize=12)
        ax.grid(alpha=.25)
        figure.text(.15, .15, "Counts use actual catalogue photometry and finite sky positions.\n"
            "Overlapping chart appearances are not counted again.\n"
            "This curve covers the complete atlas design, even in a sample batch.", fontsize=12, va="top")
        export = ExportOptions(dpi=dpi, bbox_inches=None)
        for suffix in ("png", "pdf", "svg"):
            export.save(figure, Path(str(prefix) + "." + suffix))
    finally:
        plt.close(figure)
    return data


def _numbers(text):
    if re.sub(NUMBER, "", text).strip(" ,\t\n\r"):
        raise ValueError(f"Invalid SVG numeric list: {text}")
    return [float(item) for item in re.findall(NUMBER, text)]


def _transform(text):
    result = np.eye(3)
    remainder = re.sub(r"([A-Za-z]+)\s*\(([^)]*)\)", "", text or "")
    if remainder.strip(" ,\t\n"):
        raise ValueError(f"Unsupported SVG transform: {text}")
    for name, args in re.findall(r"([A-Za-z]+)\s*\(([^)]*)\)", text or ""):
        values = _numbers(args)
        operation = np.eye(3)
        if name == "matrix" and len(values) == 6:
            a, b, c, d, e, f = values
            operation = np.array([[a, c, e], [b, d, f], [0, 0, 1.]])
        elif name == "translate" and len(values) in (1, 2):
            operation[:2, 2] = values[0], values[1] if len(values) == 2 else 0
        elif name == "scale" and len(values) in (1, 2):
            operation[0, 0] = values[0]
            operation[1, 1] = values[-1]
        elif name == "rotate" and len(values) in (1, 3):
            angle = np.deg2rad(values[0])
            operation[:2, :2] = [[np.cos(angle), -np.sin(angle)],
                                   [np.sin(angle), np.cos(angle)]]
            if len(values) == 3:
                centre = np.array(values[1:])
                operation[:2, 2] = centre - operation[:2, :2] @ centre
        elif name in {"skewX", "skewY"} and len(values) == 1:
            operation[0 if name == "skewX" else 1,
                      1 if name == "skewX" else 0] = np.tan(np.deg2rad(values[0]))
        else:
            raise ValueError(f"Unsupported SVG transform: {name}({args})")
        result = result @ operation
    if not np.isfinite(result).all():
        raise ValueError("Nonfinite SVG transform")
    return result


def _path(data):
    """Parse the line/quadratic/cubic path subset emitted for Wenu markers."""
    tokens = TOKENS.findall(data or "")
    if re.sub(TOKENS, "", data or "").strip(" ,\t\n\r"):
        raise ValueError("Invalid SVG path")
    vertices, codes = [], []
    current = np.zeros(2)
    start = current.copy()
    command = None
    index = 0
    while index < len(tokens):
        if tokens[index].isalpha():
            command = tokens[index]
            index += 1
        if command is None or command.upper() not in {"M", "L", "H", "V", "C", "Q", "Z"}:
            raise ValueError(f"Unsupported SVG path command: {command}")
        upper = command.upper()
        if upper == "Z":
            vertices.append(start.copy())
            codes.append(VectorPath.CLOSEPOLY)
            current = start.copy()
            command = None
            continue
        count = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "Q": 4}[upper]
        if index + count > len(tokens) or any(t.isalpha() for t in tokens[index:index + count]):
            raise ValueError("Incomplete SVG path segment")
        values = np.array([float(t) for t in tokens[index:index + count]])
        index += count
        relative = command.islower()
        if upper in {"H", "V"}:
            point = current.copy()
            axis = 0 if upper == "H" else 1
            point[axis] = values[0] + (current[axis] if relative else 0)
            points = point.reshape(1, 2)
        else:
            points = values.reshape(-1, 2) + (current if relative else 0)
        code = {"M": VectorPath.MOVETO, "C": VectorPath.CURVE4,
                "Q": VectorPath.CURVE3}.get(upper, VectorPath.LINETO)
        vertices.extend(points)
        codes.extend([code] * len(points))
        current = points[-1].copy()
        if upper == "M":
            start = current.copy()
            command = "l" if relative else "L"
    if not vertices or not np.isfinite(vertices).all():
        raise ValueError("Empty or nonfinite SVG path")
    return VectorPath(np.asarray(vertices), codes)


def _shape(element):
    tag = element.tag.rsplit("}", 1)[-1]
    if tag == "path":
        return _path(element.get("d"))
    if tag == "circle":
        centre = np.array([float(element.get("cx", 0)), float(element.get("cy", 0))])
        radius = float(element.get("r", 0))
        circle = VectorPath.unit_circle()
        return VectorPath(circle.vertices * radius + centre, circle.codes)
    if tag == "rect":
        x, y = float(element.get("x", 0)), float(element.get("y", 0))
        w, h = float(element.get("width", 0)), float(element.get("height", 0))
        return VectorPath([(x, y), (x+w, y), (x+w, y+h), (x, y+h), (x, y)],
                          [1, 2, 2, 2, 79])
    raise ValueError(f"Unsupported star/clip shape: {tag}")


def _filled_area(path):
    """Green's integral; Gaussian quadrature is exact for these Bezier segments."""
    area = 0.0
    current = start = origin = np.zeros(2)
    def segment(points):
        # Subtract a nearby origin to avoid cancellation for tiny distant stars.
        points = np.array(points) - origin
        if len(points) == 2:
            return (points[0, 0]*points[1, 1] - points[0, 1]*points[1, 0]) / 2
        p = points
        t = GAUSS_T[:, None]
        if len(p) == 3:
            curve = (1-t)**2*p[0] + 2*(1-t)*t*p[1] + t**2*p[2]
            derivative = 2*((1-t)*(p[1]-p[0]) + t*(p[2]-p[1]))
        else:
            curve = (1-t)**3*p[0] + 3*(1-t)**2*t*p[1] + 3*(1-t)*t**2*p[2] + t**3*p[3]
            derivative = 3*((1-t)**2*(p[1]-p[0]) + 2*(1-t)*t*(p[2]-p[1]) + t**2*(p[3]-p[2]))
        return np.dot(GAUSS_W, curve[:, 0]*derivative[:, 1] - curve[:, 1]*derivative[:, 0]) / 4
    for values, code in path.iter_segments(curves=True, simplify=False):
        if code == VectorPath.MOVETO:
            area += segment([current, start])
            current = start = origin = np.array(values)
        elif code == VectorPath.CLOSEPOLY:
            area += segment([current, start])
            current = start
        else:
            points = np.asarray(values).reshape(-1, 2)
            area += segment([current, *points])
            current = points[-1]
    area += segment([current, start])
    return abs(float(area))


def _mm(value):
    match = re.fullmatch(rf"\s*({NUMBER})(mm|cm|in|pt|px)?\s*", value or "")
    if not match:
        raise ValueError("SVG dimensions must have absolute mm/cm/in/pt/px units")
    result = float(match[1]) * {"mm": 1, "cm": 10, "in": 25.4,
                              "pt": 25.4/72, "px": 25.4/96, None: 25.4/96}[match[2]]
    if not np.isfinite(result) or result <= 0:
        raise ValueError("SVG physical dimensions must be finite and positive")
    return result


def read_star_markers(filename):
    """Return one record per centre-visible filled stellar marker in an SVG."""
    root = ET.parse(filename).getroot()
    if root.tag != f"{{{SVG}}}svg":
        raise ValueError("Input must be an SVG document")
    view = _numbers(root.get("viewBox", ""))
    if len(view) != 4 or min(view[2:]) <= 0:
        raise ValueError("SVG requires a positive viewBox")
    sx, sy = _mm(root.get("width"))/view[2], _mm(root.get("height"))/view[3]
    if not np.isclose(sx, sy, rtol=1e-5):
        raise ValueError("Nonuniform root viewport scaling is unsupported")
    by_id = {e.get("id"): e for e in root.iter() if e.get("id")}
    records = []
    star_scope_found = False
    cache = {}
    clip_shapes = {}

    def clip_visible(reference, point, matrix, seen=()):
        match = re.fullmatch(r"url\(#([^)]*)\)", reference)
        if not match or match[1] not in by_id or match[1] in seen:
            raise ValueError(f"Invalid/cyclic clip reference: {reference}")
        clip = by_id[match[1]]
        if clip.get("clipPathUnits", "userSpaceOnUse") != "userSpaceOnUse":
            raise ValueError("Object-bounding-box clip paths are unsupported")
        base = matrix @ _transform(clip.get("transform"))
        for child in clip:
            transform = base @ _transform(child.get("transform"))
            local = np.linalg.solve(transform, [*point, 1])[:2]
            if child not in clip_shapes:
                clip_shapes[child] = _shape(child)
            if clip_shapes[child].contains_point(local, radius=1e-9):
                nested = child.get("clip-path")
                if not nested or clip_visible(nested, point, transform, (*seen, match[1])):
                    return True
        return False

    def visit(element, matrix, style, opacity, stellar, clips, role, references=()):
        nonlocal star_scope_found
        tag = element.tag.rsplit("}", 1)[-1]
        if tag in {"defs", "clipPath", "metadata"}:
            return
        style = dict(style)
        for key in ("fill", "fill-opacity", "visibility", "display"):
            if element.get(key) is not None:
                style[key] = element.get(key)
        declarations = dict(pair.strip().split(":", 1) for pair in element.get("style", "").split(";") if ":" in pair)
        style.update({k.strip(): v.strip() for k, v in declarations.items()})
        opacity *= float(declarations.get("opacity", element.get("opacity", 1)))
        if style.get("display") == "none" or opacity == 0:
            return
        matrix = matrix @ _transform(element.get("transform"))
        path = element.get("data-wenu-semantic-path", "").split("/")
        if "furniture" in path or "legends" in path:
            return
        if element.get("data-wenu-layer") == "stars" or "stars" in path:
            stellar = True
            star_scope_found = True
        role = element.get("data-wenu-paint-role", role)
        if role in {"multiple_stars", "variable_stars", "labels"}:
            return
        clip = element.get("clip-path", declarations.get("clip-path"))
        if clip and clip != "none":
            clips = (*clips, (clip, matrix))
        if tag == "use":
            href = element.get("href", element.get("{http://www.w3.org/1999/xlink}href", ""))
            if stellar:
                if not href.startswith("#") or href[1:] not in by_id or href in references:
                    raise ValueError(f"Invalid/cyclic marker reference: {href}")
                placement = np.eye(3)
                placement[:2, 2] = float(element.get("x", 0)), float(element.get("y", 0))
                visit(by_id[href[1:]], matrix @ placement, style, opacity, stellar,
                      clips, role, (*references, href))
            return
        if stellar and tag in {"path", "circle"}:
            if style.get("fill", "black") == "none" or float(style.get("fill-opacity", 1)) == 0 or style.get("visibility") in {"hidden", "collapse"}:
                return
            key = (tag, element.get("d"), element.get("r"), element.get("cx"), element.get("cy"))
            if key not in cache:
                shape = _shape(element)
                # SVG circle elements are exact circles, unlike Bezier circle paths.
                area = np.pi * float(element.get("r", 0))**2 if tag == "circle" else _filled_area(shape)
                bounds = shape.get_extents()
                cache[key] = area, np.array([(bounds.x0+bounds.x1)/2, (bounds.y0+bounds.y1)/2, 1])
            area, centre = cache[key]
            area *= abs(np.linalg.det(matrix[:2, :2])) * sx * sy
            centre = (matrix @ centre)[:2]
            if area <= 0 or not all(clip_visible(c, centre, m) for c, m in clips):
                return
            if not (view[0] <= centre[0] <= view[0]+view[2] and view[1] <= centre[1] <= view[1]+view[3]):
                return
            records.append({"source": str(filename), "marker": len(records)+1,
                            "area_mm2": area, "x_mm": (centre[0]-view[0])*sx,
                            "y_mm": (centre[1]-view[1])*sy, "paint_role": role or "stars"})
            return
        for child in element:
            visit(child, matrix, style, opacity, stellar, clips, role, references)

    visit(root, np.eye(3), {}, 1.0, False, (), "")
    if not star_scope_found:
        raise ValueError(f"No Wenu stellar semantic layer found in {filename}")
    return records


def resolved_sizing_record(stars, limit):
    """Freeze the actual policy and vector symbol, independent of defaults."""
    from dataclasses import asdict
    from matplotlib.markers import MarkerStyle
    marker = MarkerStyle("o")
    shape = marker.get_path().transformed(marker.get_transform())
    sizing = stars.magnitude_sizing
    formula = {
        "legacy": "S = clamp(scale * 10**(exponent * (reference - m)), minimum_area, maximum_area); A = circle_factor * area_scale * S",
        "quadratic": "d_mm = dmin_mm + a_mm * max(0, size_reference_magnitude - m)**2; A = circle_factor * area_scale * (72*d_mm/25.4)**2",
        "linear": "d_mm = dmin_mm + a_mm * max(0, size_reference_magnitude - m); A = circle_factor * area_scale * (72*d_mm/25.4)**2",
        "asinh": "d_mm = dmin_mm + a_mm * asinh(max(0, size_reference_magnitude - m)/b_mag); A = circle_factor * area_scale * (72*d_mm/25.4)**2",
    }[sizing.algorithm]
    return dict(schema_version=1, sizing=asdict(sizing), area_scale=stars.area_scale,
        magnitude_limit=limit, ordinary_magnitude_scale=stars.ordinary_magnitude_scale,
        ordinary_magnitude_offset=stars.ordinary_magnitude_offset,
        draw_bright_symbols=stars.draw_bright_symbols,
        marker_vertices=shape.vertices.tolist(), marker_codes=shape.codes.tolist(),
        area_units="mm2", diameter_units="mm", formula=formula)


def _record_area(record, magnitudes):
    from .style_components import StellarMagnitudeSizing
    from wenu.rendering.preparation import configured_magnitude_sizes
    if record.get("schema_version") != 1:
        raise ValueError("Unsupported stellar sizing record version")
    sizing = StellarMagnitudeSizing(**record["sizing"])
    shape = VectorPath(np.asarray(record["marker_vertices"]), np.asarray(record["marker_codes"], dtype=np.uint8))
    factor = _filled_area(shape) * (25.4 / 72)**2 * record["area_scale"]
    values = np.asarray(magnitudes) * record["ordinary_magnitude_scale"] + record["ordinary_magnitude_offset"]
    return configured_magnitude_sizes(values, sizing, limiting_magnitude=record["magnitude_limit"]) * factor


def _verified_sizing(files):
    policies = []
    for filename in sorted(files):
        manifest_path = filename.parent / "manifest.json"
        if not manifest_path.is_file():
            return None, "No atlas batch manifest beside every input SVG"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("document_kind") != "wenu-atlas-chart-batch":
            return None, "Inputs are not atlas batch chart exports"
        digest = hashlib.sha256(filename.read_bytes()).hexdigest()
        if manifest.get("products", {}).get(filename.name) != digest:
            return None, "An SVG differs from its atlas manifest; magnitude references omitted"
        record = manifest.get("stellar_sizing")
        if record is None:
            # Explicit compatibility for original atlas-print manifests.
            presentation = manifest["presentation"]
            if presentation["style"] != "atlas" or presentation.get("mode", "print") != "print":
                return None, "Historical references require the atlas-print preset"
            from dataclasses import replace
            from .presets import AtlasChartStyle
            stars = AtlasChartStyle().stars
            stars = replace(stars, area_scale=stars.area_scale * presentation.get("star_size_scale", 1.0)**2)
            record = resolved_sizing_record(stars, presentation["star_magnitude_limit"])
        if record["draw_bright_symbols"]:
            return None, "Separate bright-star shapes do not admit a single circular-symbol reference"
        _record_area(record, [0])  # Validate the frozen schema before plotting.
        policies.append(record)
    if any(policy != policies[0] for policy in policies):
        return None, "Magnitude references require a single compatible resolved sizing policy"
    return policies[0], "Resolved sizing policy, verified against SVG manifest hashes"


def _reference_guides(record, areas):
    # Invert the frozen monotone curve numerically, including flat ends, rather
    # than maintaining a second algebraic version of each sizing algorithm.
    limit = record["magnitude_limit"]
    sample = np.linspace(min(-2., limit - 1), limit, 10001)
    sample_areas = _record_area(record, sample)
    brightest = float(np.interp(max(areas), sample_areas[::-1], sample[::-1])) if len(areas) else -2.
    start = int(np.floor(brightest + 1e-4))
    values = list(np.arange(start, np.ceil(limit), dtype=float))
    values = [value for value in values if value < limit - 1e-8] + [float(limit)]
    guides = []
    for value in values:
        area = float(_record_area(record, [value])[0])
        if guides and np.isclose(area, guides[-1]["area_mm2"], rtol=1e-10):
            guides[-1]["magnitude_max"] = float(value)
            guides[-1]["label"] = f"{guides[-1]['magnitude']:g}–{value:g}"
        else:
            guides.append(dict(magnitude=float(value), area_mm2=area, label=f"{value:g}"))
    # Add the exact beginning of legacy minimum saturation to its range label.
    sizing = record["sizing"]
    if sizing["algorithm"] == "legacy" and sizing["exponent"] > 0:
        ref = limit if sizing["reference"] == "limiting_magnitude" else sizing["reference_magnitude"]
        plateau = (ref + np.log10(sizing["scale"] / sizing["minimum_area"]) / sizing["exponent"]
                   - record["ordinary_magnitude_offset"]) / record["ordinary_magnitude_scale"]
        if limit > plateau:
            guides = [guide for guide in guides if guide["magnitude"] < plateau]
            guides.append(dict(magnitude=float(plateau), magnitude_max=float(limit),
                area_mm2=float(_record_area(record, [plateau])[0]), label=f"{plateau:.2f}–{limit:g}"))
    return guides


def magnitude_guides(files, areas):
    record, status = _verified_sizing(files)
    return ([] if record is None else _reference_guides(record, areas)), status


def analyze(inputs, output_prefix, bins=30, show_magnitudes=True, atlas_report=False):
    """Write per-marker CSV, logarithmic-bin CSV, summary and PNG/PDF/SVG."""
    if type(bins) is not int or bins < 1:
        raise ValueError("bins must be a positive integer")
    files = set()
    for value in inputs:
        path = Path(value)
        if path.is_dir():
            files.update(p.resolve() for p in path.glob("chart-*.svg") if re.fullmatch(r"chart-\d+\.svg", p.name))
        elif path.is_file():
            files.add(path.resolve())
        else:
            raise ValueError(f"Input not found: {path}")
    if not files:
        raise ValueError("No chart SVG files found")
    records, per_file = [], []
    for filename in sorted(files):
        try:
            stars = read_star_markers(filename)
        except ValueError as error:
            manifest_path = filename.parent / "manifest.json"
            manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
            if "No Wenu stellar semantic layer" not in str(error) or "stars" in manifest.get("presentation", {}).get("layers", ["stars"]):
                raise
            stars = []
        records.extend(stars)
        per_file.append({"source": str(filename), "star_appearances": len(stars)})
        if atlas_report:
            for row in stars:
                row["source"] = filename.name
            per_file[-1]["source"] = filename.name
    areas = np.array([row["area_mm2"] for row in records])
    record, guide_status = _verified_sizing(files) if show_magnitudes else (None, "Disabled")
    guides = [] if record is None else _reference_guides(record, areas)
    budget, budget_status = (_verified_area_budget(files, record, areas) if record is not None
                             else (None, "No verified sizing policy"))
    low, high = (np.log10(areas.min()), np.log10(areas.max())) if len(areas) else (-1., 1.)
    if np.isclose(low, high):
        low, high = low-0.05, high+0.05
    edges = np.linspace(low, high, bins+1)
    counts, _ = np.histogram(np.log10(areas), edges)
    centres = (edges[:-1]+edges[1:])/2
    prefix = Path(output_prefix)
    destinations = [Path(str(prefix)+suffix) for suffix in (
        "_stars.csv", "_bins.csv", "_summary.json", ".png", ".pdf", ".svg")]
    report_destinations = [Path(str(prefix)+suffix) for suffix in (
        "-report.png", "-report.pdf", "-report.svg", "-report_data.json")]
    budget_destinations = [Path(str(prefix)+suffix) for suffix in
        ("_area-budget.png", "_area-budget.pdf", "_area-budget.svg", "_area-budget.json", "_area-budget.csv")]
    if record is not None and show_magnitudes:
        destinations_to_check = destinations + report_destinations + (budget_destinations if budget else [])
    else:
        destinations_to_check = destinations
    if not prefix.parent.is_dir() or any(p.exists() for p in destinations_to_check):
        raise ValueError("Output parent must exist and all output filenames must be new")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    figure, ax = plt.subplots(figsize=(8, 6), layout="constrained")
    try:
        nonzero = counts > 0
        ax.scatter(centres[nonzero], np.log10(counts[nonzero]), color="black")
        ax.set(xlabel="log₁₀ star symbol area [mm²]",
               ylabel="log₁₀ number of star appearances per bin",
               title=f"{len(records):,} stellar markers in {len(files)} SVG chart(s)")
        ax.grid(alpha=0.25)
        if guides:
            for guide in guides:
                ax.axvline(np.log10(guide["area_mm2"]), color="#547a96",
                           linestyle="--", linewidth=0.8, alpha=0.7)
            top = ax.secondary_xaxis("top")
            top.set_xticks([np.log10(guide["area_mm2"]) for guide in guides],
                          labels=[guide["label"] for guide in guides])
            top.set_xlabel("Stellar magnitude (range where symbol size is clamped)")
            top.tick_params(labelsize=9, labelrotation=35)
            ax.set_title(ax.get_title(), pad=85)
        with matplotlib.rc_context({"svg.fonttype": "none"}):
            for destination in destinations[3:]:
                figure.savefig(destination, dpi=180)
    finally:
        plt.close(figure)
    with destinations[0].open("x", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=["source", "marker", "area_mm2", "x_mm", "y_mm", "paint_role"])
        writer.writeheader()
        writer.writerows(records)
    with destinations[1].open("x", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(["area_low_mm2", "area_high_mm2", "log10_area_centre", "count", "log10_count"])
        for left, right, centre, count in zip(edges[:-1], edges[1:], centres, counts):
            writer.writerow([10**left, 10**right, centre, int(count), np.log10(count) if count else ""])
    summary = {"schema_version": 1, "star_appearances": len(records), "files": per_file,
               "area_units": "mm2", "bins": bins, "binning": "equal log10 area intervals",
               "area_min_mm2": float(areas.min()) if len(areas) else None, "area_max_mm2": float(areas.max()) if len(areas) else None,
               "magnitude_guides": guides, "magnitude_guide_status": guide_status,
               "magnitude_area_budget": budget, "magnitude_area_budget_status": budget_status,
               "count_policy": "centre-visible filled markers; repeated charts count separate appearances",
               "area_policy": "full SVG silhouette, excluding stroke, even at a clipped edge"}
    destinations[2].write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")
    if record is not None and show_magnitudes:
        _write_sizing_report(prefix, summary, record, edges, counts, guides, files, atlas_report)
    if budget is not None:
        _write_area_budget(prefix, budget, json.loads((sorted(files)[0].parent/"manifest.json").read_text()).get("page", {}))
    return summary


def _write_sizing_report(prefix, summary, record, edges, counts, guides, files, atlas_report):
    """One report page: measured counts, frozen law and reproducible parameters."""
    import matplotlib
    import matplotlib.pyplot as plt
    import textwrap
    manifest = json.loads((sorted(files)[0].parent / "manifest.json").read_text())
    page = manifest.get("page", {})
    width = page.get("width_mm", 254) / 25.4
    height = page.get("height_mm", 203.2) / 25.4
    figure = plt.figure(figsize=(width, height))
    grid = figure.add_gridspec(2, 2, width_ratios=(2.2, 1),
        left=.08, right=.97, bottom=.09, top=.80, hspace=.48, wspace=.30)
    histogram = figure.add_subplot(grid[0, 0])
    law = figure.add_subplot(grid[1, 0])
    details = figure.add_subplot(grid[:, 1])
    details.set_axis_off()
    try:
        figure.suptitle("Stellar sizing report", y=.96, fontsize=16)
        figure.text(.08, .88,
            f"{summary['star_appearances']:,} appearances in {len(files)} charts; "
            f"magnitude limit {record['magnitude_limit']:g}", fontsize=10)
        nonzero = counts > 0
        centres = (edges[:-1] + edges[1:]) / 2
        histogram.scatter(centres[nonzero], np.log10(counts[nonzero]), s=14, color="black")
        histogram.set(xlabel="log₁₀ filled symbol area [mm²]", ylabel="log₁₀ N per area bin")
        if guides:
            for guide in guides:
                histogram.axvline(np.log10(guide["area_mm2"]), color="#547a96", ls="--", lw=.7)
            top = histogram.secondary_xaxis("top")
            top.set_xticks([np.log10(g["area_mm2"]) for g in guides], labels=[g["label"] for g in guides])
            top.set_xlabel("Stellar magnitude")
            top.tick_params(labelsize=8, labelrotation=30)
        sizing = record["sizing"]
        endpoint = max(record["magnitude_limit"], sizing["size_reference_magnitude"] if sizing["algorithm"] != "legacy" else record["magnitude_limit"])
        magnitudes = np.linspace(-2, endpoint, 501)
        areas = _record_area(record, magnitudes)
        law.plot(magnitudes, np.log10(areas), color="#547a96")
        law.axvline(record["magnitude_limit"], color="0.5", ls=":", label="Selection limit")
        law.set(xlabel="Stellar magnitude", ylabel="log₁₀ filled symbol area [mm²]")
        law.legend(fontsize=8)
        for ax in (histogram, law):
            ax.grid(alpha=.2)
            ax.tick_params(labelsize=8)
        presentation = manifest.get("presentation", {})
        lines = [f"Algorithm: {sizing['algorithm']}",
            f"Style: {presentation.get('style', 'recorded')}",
            f"Mode: {presentation.get('mode', 'print')}",
            f"Page: {width*25.4:g} × {height*25.4:g} mm", "", "Formula:"]
        lines += textwrap.wrap(record["formula"], 39)
        lines += ["", "Resolved parameters:"]
        relevant = (("reference", "reference_magnitude", "scale", "exponent", "minimum_area", "maximum_area")
                    if sizing["algorithm"] == "legacy" else
                    ("dmin_mm", "a_mm", "b_mag", "size_reference_magnitude"))
        lines += [f"{key}: {sizing[key]}" for key in relevant]
        lines += [f"area_scale: {record['area_scale']:g}", "", "A: filled SVG area in mm²",
                  "S: scatter size in points²", "Stroke excluded.", "",
                  "Repeated stars on overlapping", "charts count separate appearances."]
        details.text(0, 1, "\n".join(lines), va="top", fontsize=8, linespacing=1.35)
        # Draw actual-size reference glyphs in physical report coordinates.
        sample_mags = np.unique(np.linspace(-1, record["magnitude_limit"], 5).round())
        sample_areas = _record_area(record, sample_mags)
        factor = _filled_area(VectorPath(np.asarray(record["marker_vertices"]),
                             np.asarray(record["marker_codes"], dtype=np.uint8))) * (25.4/72)**2
        samples = figure.add_axes((.70, .035, .27, .065))
        samples.set_axis_off()
        samples.set_xlim(-.5, len(sample_mags)-.5)
        samples.set_ylim(-1, 1)
        samples.scatter(np.arange(len(sample_mags)), np.full(len(sample_mags), .25), s=sample_areas/factor, color="black")
        for index, magnitude in enumerate(sample_mags):
            samples.text(index, -.55, f"{magnitude:g}", ha="center", fontsize=8)
        with matplotlib.rc_context({"svg.fonttype": "none"}):
            for suffix in ("png", "pdf", "svg"):
                figure.savefig(Path(str(prefix) + f"-report.{suffix}"), dpi=180)
        report = dict(schema_version=1, document_kind="wenu-stellar-sizing-report",
            policy=record, summary=summary,
            curve=dict(magnitudes=magnitudes.tolist(), areas_mm2=areas.tolist(),
                diameters_mm=np.sqrt(4*areas/np.pi).tolist()),
            histogram=dict(log10_area_edges=edges.tolist(), counts=counts.tolist()),
            page=dict(width_mm=width*25.4, height_mm=height*25.4))
        Path(str(prefix) + "-report_data.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    finally:
        plt.close(figure)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path, help="Chart SVGs or atlas output directories")
    parser.add_argument("--output-prefix", required=True, type=Path, help="New versioned output stem")
    parser.add_argument("--bins", type=int, default=30, help="Equal-width log10 area bins (default: 30)")
    parser.add_argument("--no-magnitude-guides", action="store_true",
                        help="Omit magnitude references from verified atlas batch manifests")
    args = parser.parse_args(argv)
    try:
        summary = analyze(args.inputs, args.output_prefix, args.bins,
                          show_magnitudes=not args.no_magnitude_guides)
    except (ValueError, OSError, ET.ParseError) as error:
        parser.error(str(error))
    print(f"Counted {summary['star_appearances']} star appearances in {len(summary['files'])} SVG files")
    print(f"Outputs: {args.output_prefix}.* and CSV/JSON sidecars")
    print(f"Magnitude references: {summary['magnitude_guide_status']}")


if __name__ == "__main__":
    main()


def preview_main(argv=None):
    """Tool adapter for a catalogue-free, physically sized appearance preview."""
    from .style_overrides import add_magnitude_sizing_arguments, magnitude_sizing_from_arguments
    parser = argparse.ArgumentParser(description="Preview stellar diameter, area and actual-size symbols; no sky or catalogue is loaded.", allow_abbrev=False)
    add_magnitude_sizing_arguments(parser)
    parser.add_argument('--style', choices=('atlas', 'cartoon'), default='atlas')
    parser.add_argument('--mode', choices=('print', 'presentation'), default='print')
    parser.add_argument('--family', choices=('regional', 'binocular'), default='regional')
    parser.add_argument('--star-size-scale', type=float, default=1)
    parser.add_argument('--magnitude-limit', type=float, default=8)
    parser.add_argument('--magnitude-min', type=float, default=-2)
    parser.add_argument('--width-mm', type=float, default=353)
    parser.add_argument('--height-mm', type=float, default=250)
    parser.add_argument('--dpi', type=int)
    parser.add_argument('--output-prefix', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        from .style_components import StellarMagnitudeSizing
        policy = magnitude_sizing_from_arguments(args, StellarMagnitudeSizing())
        result = preview_stellar_sizes(args.output_prefix, policy=policy,
            style=args.style, mode=args.mode, family=args.family,
            star_size_scale=args.star_size_scale, magnitude_limit=args.magnitude_limit,
            magnitude_min=args.magnitude_min, width_mm=args.width_mm,
            height_mm=args.height_mm, dpi=args.dpi)
    except (ValueError, TypeError, OSError) as exc:
        parser.error(str(exc))
    for path in result:
        print(path)
    return 0


def preview_stellar_sizes(prefix, *, policy, style='atlas', mode='print',
                          family='regional', star_size_scale=1, magnitude_limit=8,
                          magnitude_min=-2, width_mm=353, height_mm=250, dpi=None):
    """Resolve canonical composition, then render a non-astronomical swatch sheet."""
    from .composition import compose_chart
    from .detail import DetailOverrides
    from .modes import PrintMode, PresentationMode
    from .regional import RegionalChart
    from .style_overrides import ChartStyleOverrides
    from wenu.rendering.preparation import configured_magnitude_sizes
    import matplotlib
    import matplotlib.pyplot as plt
    if style not in {'atlas', 'cartoon'} or mode not in {'print', 'presentation'}:
        raise ValueError('Unsupported style or mode.')
    if family not in {'regional', 'binocular'}:
        raise ValueError('Unsupported chart family.')
    values = (width_mm, height_mm, magnitude_min, magnitude_limit)
    if not all(np.isfinite(value) for value in values) or min(width_mm, height_mm) <= 0:
        raise ValueError('Dimensions must be positive and all range values finite.')
    if not -2 <= magnitude_min < magnitude_limit <= 11:
        raise ValueError('Magnitude range must increase within -2 through 11.')
    if dpi is not None and (isinstance(dpi, bool) or not isinstance(dpi, int) or dpi <= 0):
        raise ValueError('DPI must be a positive integer.')
    prefix = Path(prefix)
    outputs = [Path(str(prefix)+suffix) for suffix in ('.png', '.pdf', '.svg', '_data.json', '.csv')]
    if not prefix.parent.is_dir() or any(p.exists() or p.is_symlink() for p in outputs):
        raise ValueError('Output parent must exist and all output filenames must be new.')
    chart = RegionalChart(45, 0, 45, 65)
    if family == 'binocular':
        from .binocular import BinocularChart
        chart = BinocularChart(45, 0, field_diameter_deg=10)
    mode_type = PrintMode if mode == 'print' else PresentationMode
    mode_options = dict(width_inches=width_mm/25.4, height_inches=height_mm/25.4)
    if dpi is not None:
        mode_options['dpi'] = dpi
    composition = compose_chart(chart, style=style, mode=mode_type(**mode_options),
        detail_overrides=DetailOverrides(star_magnitude_limit=magnitude_limit),
        style_overrides=ChartStyleOverrides(stellar_magnitude_sizing=policy,
                                           star_size_scale=star_size_scale))
    stars = composition.style.stars
    if stars.draw_bright_symbols:
        raise ValueError('This preview supports circular base symbols; use linear, asinh or quadratic to preview the complete magnitude range without legacy bright-star shapes.')
    record = resolved_sizing_record(stars, magnitude_limit)
    magnitudes = np.linspace(magnitude_min, magnitude_limit, 501)
    areas = _record_area(record, magnitudes)
    scatter_sizes = configured_magnitude_sizes(
        magnitudes*stars.ordinary_magnitude_scale+stars.ordinary_magnitude_offset,
        stars.magnitude_sizing, limiting_magnitude=magnitude_limit)*stars.area_scale
    diameters = np.sqrt(scatter_sizes)*25.4/72
    samples = np.unique(np.r_[magnitude_min,
        np.arange(np.ceil(magnitude_min), magnitude_limit+1e-8), magnitude_limit])
    sample_sizes = configured_magnitude_sizes(
        samples*stars.ordinary_magnitude_scale+stars.ordinary_magnitude_offset,
        stars.magnitude_sizing, limiting_magnitude=magnitude_limit)*stars.area_scale
    figure = plt.figure(figsize=(width_mm/25.4, height_mm/25.4), dpi=composition.mode.dpi)
    try:
        figure.suptitle(f'Stellar sizing preview — {policy.algorithm}', fontsize=16)
        figure.text(.08, .90, f'{style} / {mode} / {family}; diameter multiplier {star_size_scale:g}; '
                    f'{width_mm:g} × {height_mm:g} mm', fontsize=10)
        axes = figure.subplots(1, 2)
        figure.subplots_adjust(left=.08, right=.95, bottom=.45, top=.83, wspace=.32)
        axes[0].plot(magnitudes, diameters)
        axes[0].set(xlabel='Stellar magnitude', ylabel='Symbol diameter [mm]')
        axes[1].plot(magnitudes, np.log10(areas))
        axes[1].set(xlabel='Stellar magnitude', ylabel='log₁₀ filled symbol area [mm²]')
        for ax in axes:
            ax.grid(alpha=.25)
        swatches = figure.add_axes((.08, .19, .87, .16), facecolor=composition.style.canvas.sky_color)
        swatches.set(xlim=(-.5, len(samples)-.5), ylim=(-1, 1), xticks=[], yticks=[])
        swatches.scatter(np.arange(len(samples)), np.zeros(len(samples)), s=sample_sizes,
                         color=stars.color, linewidths=0)
        label_color = stars.label_color or stars.color
        for i, magnitude in enumerate(samples):
            swatches.text(i, -.65, f'{magnitude:g}', ha='center', color=label_color, fontsize=9)
        swatches.set_title('Actual-size symbols; print the PDF at 100% (no fit-to-page)', fontsize=10)
        figure.text(.08, .11, f'dmin={policy.dmin_mm:g} mm; a={policy.a_mm:g} mm; '
                    f'b={policy.b_mag:g} mag; sizing reference={policy.size_reference_magnitude:g} mag'
                    if policy.algorithm != 'legacy' else record['formula'], fontsize=9)
        figure.text(.08, .06, 'Screen zoom changes apparent size. Physical diameter policies use explicit mm; '
                    'print/presentation changes palette and raster DPI.', fontsize=9)
        with matplotlib.rc_context({'svg.fonttype':'none'}):
            for path in outputs[:3]:
                figure.savefig(path, dpi=composition.mode.dpi)
        payload = dict(schema_version=1, document_kind='wenu-stellar-sizing-preview',
            policy=record, style=style, mode=mode, family=family,
            star_size_scale=star_size_scale, width_mm=width_mm, height_mm=height_mm,
            dpi=composition.mode.dpi, magnitudes=magnitudes.tolist(),
            diameters_mm=diameters.tolist(), areas_mm2=areas.tolist(),
            sample_magnitudes=samples.tolist())
        outputs[3].write_text(json.dumps(payload, indent=2, allow_nan=False)+'\n')
        with outputs[4].open('w', newline='') as stream:
            writer = csv.writer(stream)
            writer.writerow(('magnitude', 'diameter_mm', 'filled_area_mm2'))
            writer.writerows(zip(magnitudes, diameters, areas))
    finally:
        plt.close(figure)
    return outputs


def magnitude_area_budget(magnitudes, record, chart_area_mm2):
    """One-magnitude ink budgets from exact rendered-star magnitudes, not inversion."""
    magnitudes = np.asarray(magnitudes, dtype=float)
    if not np.isfinite(magnitudes).all() or not np.isfinite(chart_area_mm2) or chart_area_mm2 <= 0:
        raise ValueError('Area budgets require finite magnitudes and positive chart area.')
    areas = _record_area(record, magnitudes)
    bins = []
    for lower in sorted(set(np.floor(magnitudes).astype(int))):
        selected = (magnitudes >= lower) & (magnitudes < lower+1)
        area = float(areas[selected].sum())
        bins.append(dict(magnitude_min=int(lower), magnitude_max=int(lower+1),
            count=int(selected.sum()), area_mm2=area,
            chart_fraction=area/chart_area_mm2))
    return dict(schema_version=1, chart_area_mm2=float(chart_area_mm2),
        count=len(magnitudes), total_area_mm2=float(areas.sum()), bins=bins,
        interval_policy='[lower,upper); exact integer magnitudes belong to the next interval',
        area_policy='sum of full circular base-symbol areas; strokes and overlap union excluded')


def _verified_area_budget(files, record, measured_areas):
    """Bind exact-magnitude budgets to chart/report hashes and measured SVG totals."""
    budgets = []
    for filename in sorted(files):
        manifest = json.loads((filename.parent/'manifest.json').read_text())
        report_path = filename.with_name(filename.stem+'_report_data.json')
        if not report_path.is_file():
            return None, 'Exact rendered-magnitude data absent; no inference from symbol size'
        if manifest.get('products', {}).get(report_path.name) != hashlib.sha256(report_path.read_bytes()).hexdigest():
            return None, 'Chart report differs from its manifest; area budget omitted'
        report = json.loads(report_path.read_text())
        budget = report.get('stellar_area_budget')
        if budget is None or report.get('stellar_sizing') != record:
            return None, 'Compatible exact-magnitude budget absent'
        budgets.append(dict(source=filename.name, **budget))
    if sum(b['count'] for b in budgets) != len(measured_areas) or not np.isclose(
        sum(b['total_area_mm2'] for b in budgets), measured_areas.sum(), rtol=1e-6, atol=1e-8):
        raise ValueError('Rendered-magnitude budgets disagree with measured SVG counts/areas.')
    chart_area = sum(b['chart_area_mm2'] for b in budgets)
    combined = {}
    for budget in budgets:
        for row in budget['bins']:
            target = combined.setdefault(row['magnitude_min'], dict(
                magnitude_min=row['magnitude_min'], magnitude_max=row['magnitude_max'], count=0, area_mm2=0.))
            target['count'] += row['count']
            target['area_mm2'] += row['area_mm2']
    total_area = sum(row['area_mm2'] for row in combined.values())
    for row in combined.values():
        row['chart_fraction'] = row['area_mm2']/chart_area
        row['symbol_area_fraction'] = row['area_mm2']/total_area if total_area else 0.
    return dict(schema_version=1, bins=[combined[k] for k in sorted(combined)],
        charts=budgets, chart_area_mm2=chart_area, total_area_mm2=total_area,
        chart_fraction=total_area/chart_area, count=sum(b['count'] for b in budgets),
        count_policy='appearances; overlapping charts repeat stars',
        area_policy='summed full base-symbol ink, not actual covered union area'), 'Exact rendered magnitudes; report and SVG hashes verified'


def _write_area_budget(prefix, budget, page):
    import matplotlib
    import matplotlib.pyplot as plt
    rows = budget['bins']
    labels = [f"{r['magnitude_min']} to {r['magnitude_max']}" for r in rows]
    figure, axes = plt.subplots(1, 2, figsize=(page.get('width_mm', 353)/25.4, page.get('height_mm', 250)/25.4), layout='constrained')
    try:
        axes[0].bar(labels, [r['area_mm2'] for r in rows])
        axes[0].set(title='Symbol area by magnitude interval', ylabel='Summed filled symbol area [mm²]')
        axes[1].bar(labels, [100*r['chart_fraction'] for r in rows])
        axes[1].set(title='Contribution relative to chart frames', ylabel='Fraction of summed chart-frame area [%]')
        for ax in axes:
            ax.tick_params(axis='x', labelrotation=55)
            ax.set_xlabel('Magnitude interval [lower, upper)')
            ax.grid(axis='y', alpha=.2)
        figure.suptitle(f"Stellar area budget — {budget['count']:,} appearances; "
                       f"summed ink {100*budget['chart_fraction']:.2f}% of chart frames")
        with matplotlib.rc_context({'svg.fonttype':'none'}):
            for suffix in ('png', 'pdf', 'svg'):
                figure.savefig(Path(str(prefix)+f'_area-budget.{suffix}'), dpi=180)
    finally:
        plt.close(figure)
    Path(str(prefix)+'_area-budget.json').write_text(json.dumps(budget, indent=2, allow_nan=False)+'\n')
    with Path(str(prefix)+'_area-budget.csv').open('w', newline='') as stream:
        fields = ('magnitude_min','magnitude_max','count','area_mm2','chart_fraction','symbol_area_fraction')
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

