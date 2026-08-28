"""Current public-documentation and architecture-authority contracts."""

from pathlib import Path
import ast
import re
import tomllib


ROOT = Path(__file__).resolve().parents[1]
DEVELOPER = ROOT / "docs" / "developer"
ARCHIVE = DEVELOPER / "archive"
CURRENT = ARCHIVE / "architecture_history" / "current_architecture_v0.7.md"
IMPLEMENTED = ARCHIVE / "architecture_history" / "target_architecture_v0.7.md"
V08_CURRENT = ARCHIVE / "architecture_history/current_architecture_v0.8.md"
TARGET = ARCHIVE / "architecture_history/target_architecture_v0.8.md"
ROADMAP = ARCHIVE / "migration_history/wenu_migration_0.7_to_0.8.md"
V09_CURRENT = DEVELOPER / "current_architecture_v0.9.md"
V09_TARGET = ARCHIVE / "architecture_history/target_architecture_v0.9.md"
V09_ROADMAP = ARCHIVE / "migration_history/wenu_migration_0.8_to_0.9.md"
FUTURE_ROADMAP = DEVELOPER / "post_v0.9_architecture_roadmap.md"
V095_TARGET = DEVELOPER / "target_architecture_v0.9.5.md"
COORDINATE_GUIDE = DEVELOPER / "coordinate_system_guide_v0.9.5.md"
COORDINATE_GUIDE_ODT = DEVELOPER / "review" / "coordinate_system_guide_v0.9.5.odt"
INSTRUCTIONS = DEVELOPER / "assistant_instructions.md"
CONFIGURATION_AUDIT = ARCHIVE / "audits/configuration_default_audit.md"
CONFIGURATION_SCHEMA = DEVELOPER / "configuration_schema_v1.md"
DIAGRAMS = DEVELOPER / "diagrams"
PUBLIC_DOCUMENTS = (
    ROOT / "README.md",
    ROOT / "README.es.md",
    DEVELOPER / "implementation_reference.md",
    DEVELOPER / "source_tree.md",
    *sorted((ROOT / "docs" / "user_guide").glob("*.md")),
)
OBSOLETE_IMPORTS = (
    "wenu.spherical",
    "wenu.projected",
    "wenu.spherical_frame",
    "wenu.clipping",
    "wenu.viewport",
    "wenu.projection",
    "wenu.chart",
    "wenu.regional",
    "wenu.styles",
    "wenu.renderers",
)


def read(path):
    return path.read_text(encoding="utf-8")


def fenced_python(path):
    """Return Python code blocks from one Markdown document."""
    blocks = []
    current = None
    for line in read(path).splitlines():
        if line == "```python":
            current = []
        elif line == "```" and current is not None:
            blocks.append("\n".join(current))
            current = None
        elif current is not None:
            current.append(line)
    return blocks


def test_current_architecture_authorities_exist_and_cross_reference():
    assert [
        path
        for path in (
            CURRENT,
            IMPLEMENTED,
            V08_CURRENT,
            TARGET,
            ROADMAP,
            V09_CURRENT,
            V09_TARGET,
            V09_ROADMAP,
            FUTURE_ROADMAP,
            V095_TARGET,
            COORDINATE_GUIDE,
            COORDINATE_GUIDE_ODT,
            INSTRUCTIONS,
        )
        if not path.is_file()
    ] == []

    current = read(CURRENT)
    target = read(V09_TARGET)
    roadmap = read(V09_ROADMAP)

    assert "target_architecture_v0.7.md" in current
    assert "archive/architecture_history/current_architecture_v0.8.md" in target
    assert "archive/migration_history/wenu_migration_0.8_to_0.9.md" in target
    assert "archive/architecture_history/current_architecture_v0.8.md" in roadmap
    assert "archive/architecture_history/target_architecture_v0.9.md" in roadmap


def test_historical_documents_are_archived_and_not_active_authorities():
    assert (ARCHIVE / "README.md").is_file()
    assert not (ROOT / "docs" / "obsolete").exists()
    for name in (
        "current_architecture_v0.4.md",
        "current_architecture_v0.5.md",
        "current_architecture_v0.6.md",
        "current_architecture_v0.7.md",
        "target_architecture_v0.5.md",
        "target_architecture_v0.6.md",
        "target_architecture_v0.7.md",
        "current_architecture_v0.8.md",
        "target_architecture_v0.8.md",
        "target_architecture_v0.9.md",
    ):
        assert (ARCHIVE / "architecture_history" / name).is_file()
        assert not (DEVELOPER / name).exists()
    for name in (
        "wenu_migration_0.4_to_0.5.md",
        "wenu_migration_0.5_to_0.6.md",
        "wenu_migration_0.6_to_0.7.md",
        "wenu_migration_0.7_to_0.8.md",
        "wenu_migration_0.8_to_0.9.md",
    ):
        assert (ARCHIVE / "migration_history" / name).is_file()
        assert not (DEVELOPER / name).exists()
    assert (ARCHIVE / "pre_versioned" / "architecture.md").is_file()


def test_current_diagrams_are_an_inspection_interface():
    readme = read(DIAGRAMS / "README.md")

    for name in (
        "current_architecture_v0.9_overview",
        "coordinate_transformation_as_is_v0.9",
        "coordinate_transformation_target_49bc",
        "coordinate_static_structure_as_is_v0.9",
        "coordinate_static_structure_target_49bc",
        "coordinate_runtime_sequence_target_49bc",
    ):
        assert (DIAGRAMS / f"{name}.dot").is_file()
        assert (DIAGRAMS / f"{name}.svg").is_file()
        assert name in readme

    assert "human inspection interface" in readme
    assert "49B introduces typed astronomical-state vocabulary" in readme
    assert "49C introduces one coordinate service" in readme
    assert "every astronomical object obtains its native position" in readme
    assert "observer context enters only" in readme
    assert "actual classes" in readme
    assert "inherits" in readme
    assert "runtime calls or returns" in readme
    assert "No parallel astronomical\nstate hierarchy is proposed" in readme
    assert "direct counterpart to the current static-structure" in readme
    assert "retains the same `SkyLayer` inheritance hierarchy" in readme
    assert "`PositionProvider` is the boundary for all astronomical objects" in readme
    assert "requires only another\nprovider implementation" in readme
    assert "deliberately large canvas" in readme
    assert (
        ARCHIVE / "diagram_history" / "target_architecture_v0.5_combined.dot"
    ).is_file()
    assert (
        ARCHIVE / "diagram_history" / "target_architecture_v0.5_combined.svg"
    ).is_file()
    assert not (DIAGRAMS / "target_architecture_v0.5_combined.dot").exists()
    assert not (DIAGRAMS / "target_architecture_v0.5_combined.svg").exists()



def test_v095_coordinate_target_and_living_guide_are_reviewable():
    target = read(V095_TARGET)
    guide = read(COORDINATE_GUIDE)

    assert "**Status:** Proposed review baseline; not implemented" in target
    assert "PositionProvider" in target
    assert "CoordinateService" in target
    assert "49B.1" in target
    assert "49C.4" in target
    assert "does not claim a\n`v0.9.5` Git tag" in target

    for phrase in (
        "Position generation versus coordinate transformation",
        "International Celestial Reference System",
        "FK5 equatorial coordinates",
        "Galactic coordinates",
        "Ecliptic coordinates",
        "Horizontal AltAz coordinates",
        "TEME",
        "Current transformation inventory and 0.9.5 destination",
        "Wenu object catalogue and provenance",
        "ESA Hipparcos Catalogue I/239",
        "OpenNGC",
        "Gaia DR3",
        "Minimal architecture 0.9.5 roadmap",
    ):
        assert phrase in guide

    assert COORDINATE_GUIDE_ODT.stat().st_size > 10_000

def test_v08_release_evidence_remains_closed():
    target = read(TARGET)
    roadmap = read(ROADMAP)
    readme = read(ROOT / "README.md")

    assert "**Status:** Implemented" in target
    assert "**Release:** 0.8.0" in target
    assert "**Status:** Complete" in roadmap
    assert "Milestone 46E" in roadmap
    assert "annotated Git tag `v0.8.0`" in roadmap
    assert "Version 0.8.0 remains the latest tagged" in readme


def test_v09_architecture_is_closed_and_current():
    current = read(V09_CURRENT)
    target = read(V09_TARGET)
    roadmap = read(V09_ROADMAP)
    implementation = read(DEVELOPER / "implementation_reference.md")
    source_tree = read(DEVELOPER / "source_tree.md")
    readme = read(ROOT / "README.md")
    instructions = read(INSTRUCTIONS)

    assert "**Status:** Implemented current architecture" in current
    assert "**Baseline commit:** `5da93cc`" in current
    assert "optional night edition remains a later appearance experiment" in current.lower()
    assert "**Status:** Implemented; retained as the accepted design record" in target
    assert "**Status:** Complete" in roadmap
    assert "**Current authority:** `current_architecture_v0.9.md`" in roadmap
    assert "**Architecture version:** 0.9" in implementation
    assert "**Architecture version:** 0.9" in source_tree
    assert "v0.9 architecture is complete" in readme
    assert "current_architecture_v0.9.md" in instructions


def test_v09_plan_records_paired_physical_planisphere_contract():
    current = read(V08_CURRENT)
    target = read(V09_TARGET)
    roadmap = read(V09_ROADMAP)

    for phrase in (
        "**Baseline commit:** `c169162`",
        "Projection gap",
        "Physical-product gap",
    ):
        assert phrase in current
    for phrase in (
        "polar azimuthal-equidistant projection",
        "-90 degrees through +20 degrees",
        "+90 degrees through -20 degrees",
        "glued back to back",
        "opposite",
        "365 daily ticks",
        "20:00 through 04:00",
        "Localization is the last",
    ):
        assert phrase in target
    for phrase in (
        "Milestone 48B",
        "Milestone 48C",
        "Milestone 48D",
        "Milestone 48E",
        "Wednesday, 2026-08-19",
        "Milestone 48G",
        "Milestone 48J",
        "Milestone 48K",
    ):
        assert phrase in roadmap


def test_release_version_comes_from_scm_with_v08_archive_fallback():
    project = tomllib.loads(read(ROOT / "pyproject.toml"))

    assert project["project"]["dynamic"] == ["version"]
    assert project["tool"]["setuptools_scm"]["fallback_version"] == "0.8.0"


def test_assistant_instructions_name_current_architecture_authorities():
    instructions = read(INSTRUCTIONS)
    for name in (
        "current_architecture_v0.9.md",
        "archive/architecture_history/target_architecture_v0.9.md",
        "archive/migration_history/wenu_migration_0.8_to_0.9.md",
        "implementation_reference.md",
        "source_tree.md",
        "coordinate_transformation_audit_09a2afd.md",
        "post_v0.9_architecture_roadmap.md",
    ):
        assert name in instructions
    assert "historical evidence, not active" in instructions


def test_post_v09_roadmap_records_coordinate_svg_and_temporal_direction():
    roadmap = read(FUTURE_ROADMAP)
    for phrase in (
        "Two independent development tracks",
        "One astronomical coordinate service",
        "Position-provider boundary",
        "SVG product verification",
        "Temporal sequence contract",
        "Fixed sky and rotating horizon",
        "tools/render_circumpolar_movie.py",
        "simulation time",
        "time scale",
        "TEME",
        "SGP4",
        "complete-render path as a correctness oracle",
    ):
        assert phrase in roadmap


def test_v08_roadmap_records_ordinary_interface_and_static_sequences():
    target = read(TARGET)
    roadmap = read(ROADMAP)

    for phrase in (
        "Three-stage ordinary Python interface",
        "observer-independent loaded-content container",
        "Defining a projection and applying it are separate operations",
        "fewer than 70 lines",
        "Reproducible image-frame sequences",
        "does not encode movies",
    ):
        assert phrase in target

    for phrase in (
        "Milestone 46C.8G",
        "Milestone 46C.8O",
        "Pass observer explicitly through canonical execution",
        "Decouple maximal-sphere construction",
        "one observer-independent canonical maximal sphere",
        "fewer-than-70-line declarative examples",
        "movie encoding",
        "Hawaii-to-Tahiti",
        "coordinate-epoch precession",
    ):
        assert phrase in roadmap


def test_horizon_roadmap_separates_boundary_reference_and_mask_roles():
    target = read(TARGET)
    roadmap = read(ROADMAP)

    for phrase in (
        "Observer-horizon roles",
        "`--horizon`",
        "`--horizon-mask`",
        "deliberately not opaque",
        "paints one effective outside mask exactly once",
        "idempotent no-ops for a planisphere",
    ):
        assert phrase in target
    for phrase in (
        "Milestone 46C.8Q.1",
        "Milestone 46C.8Q.3",
        "Milestone 46C.8Q.4",
        "Milestone 46C.8Q.5",
        "Milestone 46C.8Q.9",
        "preventing accumulated opacity",
        "runtime behavior remains",
        "declaration and adapter plumbing",
        "reference appearance and mask behavior remain",
        "mask-opening geometry preparation",
    ):
        assert phrase in roadmap


def test_configuration_default_audit_covers_every_public_responsibility():
    audit = read(CONFIGURATION_AUDIT)
    roadmap = read(ROADMAP)

    for phrase in (
        "public default",
        "derived value",
        "invariant",
        "implementation detail",
        "observer",
        "subject",
        "family geometry",
        "detail",
        "style",
        "output mode",
        "grids/references",
        "furniture",
        "product",
        "export",
        "line_width",
        "line_style",
        "Duplication and conflict register",
        "Output-mode transformation inventory",
    ):
        assert phrase in audit
    assert "Milestone 46D.1A" in roadmap
    assert "Milestone 46D.1B" in roadmap
    for phrase in (
        "Exact ordered value inventory",
        "Atlas-print semantic style",
        "Mode palettes and transformations",
        "Furniture, legends, grids, and implementation constants",
        "minimum area `1.0`, maximum area `40.0`",
        "style `dotted`",
        "style `solid`",
        "style `dashed`",
    ):
        assert phrase in audit
    assert "**Final status:** Implemented" in roadmap


def test_user_overlay_boundary_is_currently_documented():
    current = read(CURRENT)
    roadmap = read(ROADMAP)
    implementation = read(DEVELOPER / "implementation_reference.md")
    source_tree = read(DEVELOPER / "source_tree.md")

    for phrase in (
        "Milestone 46D.5A",
        "strict partial-user-document boundary",
        "Sequential loads share no mutable",
        "Milestone 46D.5B",
    ):
        assert phrase in current
    for phrase in (
        "Milestone 46D.5A",
        "recursive non-mutating merge",
        "omitted-versus-explicit argument precedence",
    ):
        assert phrase in roadmap
    for phrase in (
        "load_configuration(path=None)",
        "load_configuration_defaults(path=None)",
        "ConfigurationDefaults",
    ):
        assert phrase in implementation
    assert "src/wenu/configuration/translation.py" in source_tree


def test_user_overlay_runtime_precedence_is_currently_documented():
    current = read(CURRENT)
    roadmap = read(ROADMAP)
    implementation = read(DEVELOPER / "implementation_reference.md")
    source_tree = read(DEVELOPER / "source_tree.md")

    for phrase in (
        "Milestone 46D.5B",
        "one frozen aggregate",
        "`--config PATH`",
        "before maximal-sphere construction",
    ):
        assert phrase in current
    for phrase in (
        "**Final status:** Implemented",
        "product arguments retain `None` as the omission sentinel",
        "packaged-only behavior is unchanged",
    ):
        assert phrase in roadmap
    for phrase in (
        "load_configuration_defaults(\"my-wenu.toml\")",
        "configuration=configuration",
        "explicitly present on the command line override it",
    ):
        assert phrase in implementation
    for phrase in (
        "Milestone 46D.5B",
        "no active-configuration singleton exists",
    ):
        assert phrase in source_tree


def test_installed_wenu_chart_boundary_is_currently_documented():
    current = read(CURRENT)
    roadmap = read(ROADMAP)
    implementation = read(DEVELOPER / "implementation_reference.md")
    source_tree = read(DEVELOPER / "source_tree.md")

    for phrase in (
        "Milestone 46D.6",
        "one `wenu_chart` command",
        "never imports\nexample modules",
    ):
        assert phrase in current
    for phrase in (
        "**Final status:** Implemented",
        "all five chart-family subcommands plus `defaults`",
        "deterministic `--write` output remains Milestone 46D.7",
    ):
        assert phrase in roadmap
    for phrase in (
        "wenu_chart regional --constellations Cen,Cru,Mus",
        "`--observer-location`",
        "does not import or execute example scripts",
    ):
        assert phrase in implementation
    for phrase in (
        "src/wenu/cli/chart.py",
        "`generate_celestial_sphere()`",
        "do not import `example_scripts`",
    ):
        assert phrase in source_tree


def test_editable_configuration_template_is_currently_documented():
    current = read(CURRENT)
    roadmap = read(ROADMAP)
    implementation = read(DEVELOPER / "implementation_reference.md")
    source_tree = read(DEVELOPER / "source_tree.md")

    for phrase in (
        "Milestone 46D.7",
        "exact UTF-8 bytes",
        "profile inheritance is deliberately deferred",
    ):
        assert phrase in current
    for phrase in (
        "**Final status:** Implemented",
        "`wenu_chart defaults --write PATH`",
        "overlay per invocation and no inheritance",
    ):
        assert phrase in roadmap
    for phrase in (
        "`dashed`, `dotted`, `dash_dot`, and `none`",
        "deterministically replaced",
        "One invocation accepts one overlay",
    ):
        assert phrase in implementation
    for phrase in (
        "`write_defaults_template()`",
        "exact UTF-8 bytes",
        "does not\nserialize typed translations",
    ):
        assert phrase in source_tree


def test_configuration_schema_v1_freezes_structure_and_validation():
    schema = read(CONFIGURATION_SCHEMA)
    roadmap = read(ROADMAP)

    assert "**Schema version:** `1`" in schema
    ordered_sections = (
        "`observer`",
        "`subjects`",
        "`families`",
        "`detail`",
        "`styles`",
        "`modes`",
        "`grids_references`",
        "`furniture`",
        "`products`",
        "`export`",
    )
    positions = [schema.index(f"### {section}") for section in ordered_sections]
    assert positions == sorted(positions)

    for phrase in (
        "schema_version = 1",
        "color`, `line_width`, and `line_style`",
        "`solid`, `dashed`, `dotted`, `dash_dot`, or `none`",
        "Unknown sections and keys are errors",
        "complete configuration path",
        "invalid colors",
        "contradictory combinations",
        "executable expressions",
        "Python class names",
        "renderer operations",
        "catalogue joins",
        "imports",
        "arbitrary code",
        "styles.atlas.horizon.line_style",
    ):
        assert phrase in schema

    assert "### Milestone 46D.2" in roadmap
    assert "configuration_schema_v1.md" in roadmap
    assert "This milestone adds no parser" in roadmap


def test_configuration_runtime_migration_is_closed_before_user_overlays():
    roadmap = read(ROADMAP)
    architecture = read(CURRENT)

    for phrase in (
        "Milestone 46D.4D",
        "[products.default]",
        "compatibility API",
        "canonical runtime",
        "Explicit values retain precedence",
    ):
        assert phrase in roadmap
        assert phrase in architecture
    assert "**Final status:** Implemented" in roadmap


def test_documented_python_is_syntactically_valid():
    for document in (
        ROOT / "README.md",
        DEVELOPER / "implementation_reference.md",
    ):
        for block in fenced_python(document):
            ast.parse(block, filename=str(document))


def test_documented_canonical_public_imports_execute():
    namespace = {}
    import_block = fenced_python(
        DEVELOPER / "implementation_reference.md"
    )[0]
    exec(import_block, namespace)
    for name in (
        "AllSkyChart",
        "compose_chart",
        "LegendOptions",
        "RegionalChart",
        "FullSkyChart",
        "CircumpolarChart",
        "BinocularChart",
    ):
        assert name in namespace


def test_public_documents_do_not_recommend_obsolete_imports():
    violations = []
    for path in PUBLIC_DOCUMENTS:
        text = read(path)
        for obsolete in OBSOLETE_IMPORTS:
            pattern = re.compile(
                rf"\b(?:from|import)\s+{re.escape(obsolete)}(?=\s|$)"
            )
            if pattern.search(text):
                violations.append(f"{path.relative_to(ROOT)}: {obsolete}")
    assert violations == []


def test_polar_physical_style_checkpoint_is_documented():
    roadmap = read(ARCHIVE / "migration_history/wenu_migration_0.8_to_0.9.md")
    architecture = read(ARCHIVE / "architecture_history/current_architecture_v0.8.md")
    reference = read(DEVELOPER / "implementation_reference.md")
    acceptance = read(ARCHIVE / "acceptance_history/visual_acceptance_48e2.md")

    for phrase in (
        "Milestone 48E.2",
        "PolarPlanisphereStylePalette",
        "render_48e2_polar_preview.py",
    ):
        assert (
            phrase in roadmap
            or phrase in architecture
            or phrase in reference
        )
    assert "polar-planisphere-south.png" in acceptance
    assert "polar-planisphere-north.png" in acceptance
    assert "--projection stereographic" in acceptance


def test_polar_reference_review_corrections_are_documented():
    roadmap = read(ARCHIVE / "migration_history/wenu_migration_0.8_to_0.9.md")
    target = read(ARCHIVE / "architecture_history/target_architecture_v0.9.md")
    acceptance = read(ARCHIVE / "acceptance_history/visual_acceptance_48e3.md")

    for phrase in (
        "Milestone 48E.3",
        "+20/-20-degree overlap",
        "0h/6h/12h/18h meridians",
        "short declination ticks",
        "corrected stereographic handedness",
    ):
        assert phrase in roadmap or phrase in target or phrase in acceptance


def test_current_svg_documents_use_one_editable_text_contract():
    roadmap = " ".join(
        (ARCHIVE / "milestone_history/49f_svg/svg_output_audit_and_plan.md")
        .read_text(encoding="utf-8")
        .split()
    )
    implementation = (DEVELOPER / "implementation_reference.md").read_text(
        encoding="utf-8"
    )
    source_tree = (DEVELOPER / "source_tree.md").read_text(encoding="utf-8")

    for value in (
        "SVG has one public text contract",
        "--format {png,pdf,svg}",
        "PDF is the publication product",
        "SVG is the editable vector product",
    ):
        assert value in roadmap

    assert "support two explicit SVG font policies" not in roadmap
    assert "wenu.output_policy.OutputFormat" in implementation
    assert "wenu.svg_document.annotate_semantic_svg()" in implementation
    assert "src/wenu/output_policy.py" in source_tree
    assert "src/wenu/svg_document.py" in source_tree


def test_readmes_advertise_the_svg_user_contract():
    for filename in ("README.md", "README.es.md"):
        text = (ROOT / filename).read_text(encoding="utf-8")
        assert "--format svg" in text
        assert "docs/user_guide/svg_output.md" in text


def test_svg_paint_order_record_rejects_semantic_inference():
    record = (
        ARCHIVE / "milestone_history/49f_svg/svg_exact_paint_order_49f4a.md"
    ).read_text(encoding="utf-8")
    normalized = " ".join(record.split())

    for value in (
        "What is the object?",
        "When is it drawn?",
        "does not classify the object",
        "must never be inferred to be a star",
        "does not contain or reconstruct astronomical knowledge",
        "Hierarchical grouping remains a later",
    ):
        assert value in normalized


def test_svg_semantic_naming_ledger_records_designer_contract():
    ledger = (
        ARCHIVE / "milestone_history/49f_svg/svg_semantic_naming_ledger_49f5a.md"
    ).read_text(encoding="utf-8")

    for value in (
        "unique among its siblings",
        "does not repeat information",
        "only when a designer can usefully style",
        "Lines-Western",
        "system agnostic",
        "mag-minus-1",
        "count does not change identity",
        "unexpected generic editable Matplotlib objects",
    ):
        assert value in ledger


def test_svg_cross_product_acceptance_records_all_products():
    text = (
        ARCHIVE / "milestone_history/49f_svg/svg_cross_product_acceptance_49f6.md"
    ).read_text(encoding="utf-8")

    for value in (
        "Milestone 49F.6",
        "all-sky",
        "planisphere",
        "regional",
        "circumpolar",
        "binocular",
        "polar page, south",
        "polar page, north",
        "polar pouch",
        "catalog_1636_283",
        "Inkscape 1.4.4",
        "1688 passed in 58.90s",
    ):
        assert value in text


def test_temporal_sequence_contract_separates_physical_and_playback_time():
    contract = (
        ARCHIVE / "milestone_history/49g_temporal/temporal_sequence_contract_49g1.md"
    ).read_text(encoding="utf-8")
    roadmap = (
        DEVELOPER / "post_v0.9_architecture_roadmap.md"
    ).read_text(encoding="utf-8")
    legacy = (
        ARCHIVE / "roadmap_history/polar_delivery_and_astrometry_roadmap.md"
    ).read_text(encoding="utf-8")
    implementation = (
        DEVELOPER / "implementation_reference.md"
    ).read_text(encoding="utf-8")
    source_tree = (
        DEVELOPER / "source_tree.md"
    ).read_text(encoding="utf-8")

    for value in (
        "TemporalTimeline",
        "PlaybackSpec",
        "simulation duration",
        "Playback speed must never be interpreted as physical time",
        "CelestialSphere.draw_chart()",
        "29 passed in 3.42s",
    ):
        assert value in contract

    assert "49G.1 immutable timeline and playback vocabulary" in roadmap
    assert "does not compete" in legacy
    assert "Temporal sequence vocabulary (Milestone 49G.1)" in implementation
    assert "Temporal sequence modules (Milestone 49G.1)" in source_tree


def test_observer_time_sequence_reserves_astrometric_epoch_ownership():
    contract = (
        ARCHIVE / "milestone_history/49g_temporal/observer_time_sequence_49g2.md"
    ).read_text(encoding="utf-8")
    timeline = (
        ARCHIVE / "milestone_history/49g_temporal/temporal_sequence_contract_49g1.md"
    ).read_text(encoding="utf-8")
    roadmap = (
        DEVELOPER / "post_v0.9_architecture_roadmap.md"
    ).read_text(encoding="utf-8")
    implementation = (
        DEVELOPER / "implementation_reference.md"
    ).read_text(encoding="utf-8")
    source_tree = (
        DEVELOPER / "source_tree.md"
    ).read_text(encoding="utf-8")

    for value in (
        "ObserverTimeChartSequenceRequest",
        "generate_observer_time_chart_sequence()",
        "catalogue reference epoch",
        "celestial realization epoch",
        "provider evaluation instant",
        "Gaia DR3 J2016.0 TCB",
        "must not be forced into UTC datetimes",
        "Real-render acceptance",
        "894 × 927",
        "expected six-hour sky",
        "permanent integration test",
        "74 passed in 26.69s",
        "1708 passed in 81.99s",
    ):
        assert value in contract

    assert "Proper motion must not be expressed" in timeline
    assert "49G.2 observer-time" in roadmap
    assert "Observer-time chart sequence (Milestone 49G.2)" in implementation
    assert "Observer-time sequence orchestration" in source_tree



def test_sequence_manifest_documents_safe_restart_and_resume():
    contract = (
        ARCHIVE / "milestone_history/49g_temporal/sequence_manifest_49g3.md"
    ).read_text(encoding="utf-8")
    roadmap = (
        DEVELOPER / "post_v0.9_architecture_roadmap.md"
    ).read_text(encoding="utf-8")
    implementation = (
        DEVELOPER / "implementation_reference.md"
    ).read_text(encoding="utf-8")
    source_tree = (
        DEVELOPER / "source_tree.md"
    ).read_text(encoding="utf-8")

    for value in (
        "ObserverTimeSequenceManifest",
        "SequenceRestartPolicy",
        "restart_policy=\"restart\"",
        "recorded filename, byte count, and SHA-256",
        "incompatible manifest before rendering",
        "real canonical PNG generation",
        "CLI/configuration exposure is implemented downstream in Milestone 49G.4",
        "real restart/resume acceptance complete",
        "selective resume",
        "82 passed in 27.29s",
        "1721 passed in 83.03s",
    ):
        assert value in contract

    assert "49G.3 deterministic manifest" in roadmap
    assert "acceptance complete" in roadmap
    assert "Deterministic sequence manifests (Milestone 49G.3)" in (
        implementation
    )
    assert "Sequence manifest and resume (Milestone 49G.3)" in source_tree


def test_temporal_sequence_cli_documents_shared_translation_and_acceptance():
    contract = (
        ARCHIVE / "milestone_history/49g_temporal/temporal_sequence_cli_49g4.md"
    ).read_text(encoding="utf-8")
    roadmap = (
        DEVELOPER / "post_v0.9_architecture_roadmap.md"
    ).read_text(encoding="utf-8")
    implementation = (
        DEVELOPER / "implementation_reference.md"
    ).read_text(encoding="utf-8")
    source_tree = (
        DEVELOPER / "source_tree.md"
    ).read_text(encoding="utf-8")
    schema = (
        DEVELOPER / "configuration_schema_v1.md"
    ).read_text(encoding="utf-8")

    for value in (
        "49G.4",
        "--sequence-stop",
        "--sequence-frames",
        "same immutable `ChartRequest`",
        "complete translated effective configuration",
        "eaf7f6d8cfbfb27376baf85bfb80613a86b67f0f0a40458961386299efac2f68",
        "pixel-identical decoded RGBA",
        "compressed PNG bytes differed",
        "163 passed in 28.30s",
        "1744 passed in 80.10s",
    ):
        assert value in contract

    assert "49G.4 installed CLI" in roadmap
    assert "implemented and accepted" in roadmap
    assert "Temporal sequence CLI and configuration (Milestone 49G.4)" in (
        implementation
    )
    assert "Temporal sequence CLI modules (Milestone 49G.4)" in source_tree

    assert "### `sequence`" in schema
    assert "playback_duration" in schema
