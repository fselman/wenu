"""Measure filled star markers in Wenu SVGs without loading a celestial sphere.

Areas describe complete vector silhouettes, excluding strokes. Count markers
whose centres survive SVG clipping; partially clipped markers retain full area.
Overlapping atlas pages contribute separate appearances of the same star.
"""

from __future__ import annotations

import argparse
import csv
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


def analyze(inputs, output_prefix, bins=30):
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
        stars = read_star_markers(filename)
        records.extend(stars)
        per_file.append({"source": str(filename), "star_appearances": len(stars)})
    if not records:
        raise ValueError("No centre-visible filled stars found")
    areas = np.array([row["area_mm2"] for row in records])
    low, high = np.log10(areas.min()), np.log10(areas.max())
    if np.isclose(low, high):
        low, high = low-0.05, high+0.05
    edges = np.linspace(low, high, bins+1)
    counts, _ = np.histogram(np.log10(areas), edges)
    centres = (edges[:-1]+edges[1:])/2
    prefix = Path(output_prefix)
    destinations = [Path(str(prefix)+suffix) for suffix in (
        "_stars.csv", "_bins.csv", "_summary.json", ".png", ".pdf", ".svg")]
    if not prefix.parent.is_dir() or any(p.exists() for p in destinations):
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
        with matplotlib.rc_context({"svg.fonttype": "none"}):
            for destination in destinations[3:]:
                figure.savefig(destination, dpi=180)
    finally:
        plt.close(figure)
    with destinations[0].open("x", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    with destinations[1].open("x", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(["area_low_mm2", "area_high_mm2", "log10_area_centre", "count", "log10_count"])
        for left, right, centre, count in zip(edges[:-1], edges[1:], centres, counts):
            writer.writerow([10**left, 10**right, centre, int(count), np.log10(count) if count else ""])
    summary = {"schema_version": 1, "star_appearances": len(records), "files": per_file,
               "area_units": "mm2", "bins": bins, "binning": "equal log10 area intervals",
               "area_min_mm2": float(areas.min()), "area_max_mm2": float(areas.max()),
               "count_policy": "centre-visible filled markers; repeated charts count separate appearances",
               "area_policy": "full SVG silhouette, excluding stroke, even at a clipped edge"}
    destinations[2].write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path, help="Chart SVGs or atlas output directories")
    parser.add_argument("--output-prefix", required=True, type=Path, help="New versioned output stem")
    parser.add_argument("--bins", type=int, default=30, help="Equal-width log10 area bins (default: 30)")
    args = parser.parse_args(argv)
    try:
        summary = analyze(args.inputs, args.output_prefix, args.bins)
    except (ValueError, OSError, ET.ParseError) as error:
        parser.error(str(error))
    print(f"Counted {summary['star_appearances']} star appearances in {len(summary['files'])} SVG files")
    print(f"Outputs: {args.output_prefix}.* and CSV/JSON sidecars")


if __name__ == "__main__":
    main()
