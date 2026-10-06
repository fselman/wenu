"""Designation notes for stars retained by the canonical chart render."""

from __future__ import annotations

import json
from pathlib import Path

from wenu.stellar_research import load_stellar_research
from wenu.star_designations import (
    preferred_designation,
    designation_parts,
    constellation_code,
)
from .spatial_selection import projected_points_in_chart
from .chart_legend_workflow import RenderedChartWithLegends


def build_stellar_report(export, *, title, constellations=()):
    """Describe already projected stars without realizing coordinates again.

    Inclusion means a stellar point survived the chart's ordinary geometry
    selection and clipping. Labels need not be enabled; masks remain visual
    overlays, not additional catalogue selection or visibility calculations.
    """
    research = load_stellar_research()
    entries = {}
    rendering = export.rendering
    if isinstance(rendering, RenderedChartWithLegends):
        rendering = rendering.rendering
    for layer in rendering.layers:
        if getattr(layer.layer, "layer_name", None) != "stars":
            continue
        points = layer.projected
        formatter = None
        render = export.layer_options.get(layer.layer, {}).get("render", {})
        if callable(render):
            render = render(layer.spherical, points)
        if render.get("draw_labels", False):
            formatter = render.get("label_formatter")
        records = points.metadata.get("star_designations")
        visible = projected_points_in_chart(points, export.composition.context)
        for index in range(len(points)):
            if not visible[index]:
                continue
            hip = int(points.ids[index])
            if hip not in research or hip in entries:
                continue
            case = research.get(hip)
            record = None if records is None else records[index]
            kind = "flamsteed" if case["field"] == "flam" else "bayer"
            assignment = None
            basis = None
            uncertainty = None
            if record is not None:
                try:
                    assignment = preferred_designation(
                        record,
                        kind,
                        constellations,
                        preferred=research.shared_preference(hip, kind),
                    )
                    if assignment is not None:
                        preference = research.shared_preference(hip, kind)
                        scopes = {
                            constellation_code(value)
                            for value in constellations
                        }
                        matches = {
                            claim.code
                            for claim in record.candidates(kind)
                            if designation_parts(claim.code, kind)[1] in scopes
                        }
                        if preference is not None and len(matches) == 1:
                            basis = "Requested constellation; existing Wikidata alias"
                        elif preference is not None:
                            basis = (
                                "WGSN catalogue identifier; existing Wikidata alias"
                                if kind == "bayer"
                                else "Modern cross-index consensus; existing Wikidata alias (not WGSN arbitration)"
                            )
                        else:
                            basis = "Active Wikidata assignment"
                except ValueError as error:
                    uncertainty = str(error)
            if assignment is None and uncertainty is None:
                uncertainty = (
                    f"No active Wikidata {kind} assignment for this HIP."
                )
            entries[hip] = {
                "hip": hip,
                "displayed_label": None
                if formatter is None
                else formatter(hip),
                "assignment": assignment,
                "assignment_basis": basis,
                "assignment_caution": uncertainty,
                "research": case,
            }
    return {
        "schema": "wenu-stellar-chart-report/1",
        "title": title,
        "chart_output": str(export.output),
        "constellations": sorted(set(constellations)),
        "scope": "Designation research for retained stellar points; not a complete interesting-object catalogue or visibility prediction.",
        "handling_policy": "Fernando approved Wikidata baseline plus contextual shared-star labels and discrepancy reporting on 2026-10-06; individual research questions remain open.",
        "research_sha256": research.source_sha256,
        "policy_sha256": research.policy_sha256,
        "sources": json.loads(research.sources_json),
        "objects": [entries[hip] for hip in sorted(entries)],
    }


def stellar_report_markdown(report):
    """Render one deterministic human-readable report, including zero cases."""
    lines = [
        f"# Stellar designation notes: {report['title']}",
        "",
        report["scope"],
        "",
        report["handling_policy"],
        "",
        f"Chart: `{report['chart_output']}`",
        "",
    ]
    if not report["objects"]:
        lines += [
            "No stars from the 77-case research list occur in this chart.",
            "",
        ]
    for entry in report["objects"]:
        case = entry["research"]
        note = case["research"]
        lines += [
            f"## HIP {entry['hip']} — {case['classification']}",
            "",
            f"Displayed label: {entry['displayed_label'] or '(no stellar label)'}. Assignment: {entry['assignment'] or '(missing or ambiguous)'}.",
            "",
        ]
        if entry["assignment_caution"]:
            lines += [entry["assignment_caution"], ""]
        if entry["assignment_basis"]:
            lines += [f"Assignment basis: {entry['assignment_basis']}.", ""]
        for source, values in case["source_values"].items():
            lines.append(f"- {source}: {', '.join(values) or '(missing)'}")
        lines += [
            "",
            note["assessment"],
            "",
            f"Open question: {note['open_question']}",
            "",
            f"Evidence: {note['evidence_locator']}",
            "",
            f"Confidence: {note['classification_confidence']}. Scope: {case['reporting']['publication_status']}.",
            "",
            "Sources:",
            "",
        ]
        for key in note["sources"]:
            source = report["sources"][key]
            lines.append(f"- [{source['title']}]({source['url']})")
        lines.append("")
    lines += [
        f"Research SHA-256: `{report['research_sha256']}`",
        "",
        f"Policy SHA-256: `{report['policy_sha256']}`",
        "",
    ]
    return "\n".join(lines)


def write_stellar_report(export, *, title, constellations=()):
    """Write Markdown and structured JSON next to one chart output."""
    report = build_stellar_report(
        export, title=title, constellations=constellations
    )
    output = Path(export.output)
    paths = tuple(
        output.with_name(output.name + ".stars." + suffix)
        for suffix in ("md", "json")
    )
    paths[0].write_text(stellar_report_markdown(report), encoding="utf-8")
    paths[1].write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return paths
