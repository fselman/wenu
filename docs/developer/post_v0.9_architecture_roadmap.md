## Current forward roadmap

This is the single active sequence after merge commit `b877a74`. Completed
milestone detail belongs in `archive/`; the historical sections below retain
architectural rationale and accepted boundaries.

| Order | Milestone | Outcome |
|---:|---|---|
| 1 | 50A.5D.1B | Observer-dependent sampled Horizons comet model magnitude, explicitly not a visibility prediction. |
| 2 | 50A.5D.3 | Renderer-neutral text and JSON moving-object reports from already realized temporal results. |
| 3 | 50A.5E.0 | Audit the distributable Wenu asteroid/comet database, scientific representation, provenance, coverage, and lifecycle. |
| 4 | 50A.5E.1 | Build and verify a versioned distributable database, including important minor bodies and all governed dwarf planets. |
| 5 | 50A.5E.2 | Add the `wenu-database` policy and default cache → provider → database resolution order. |
| 6 | 50A.5E.3 | Add safe cache inspection, dry-run, pruning, and explicit minor-body cache flushing. |
| 7 | 50A.6 | Close minor-body provenance, public interfaces, validation, documentation, and PNG/PDF/SVG acceptance. |
| 8 | 50S.0 | Accepted satellite catalogue, provider, crossing, acceleration, illumination, photometry, and validation decisions. |
| 9 | 50S.1 | Define the provider-neutral satellite crossing domain. |
| 10 | 50S.2 | Add the policy-compliant cached SatChecker crossing adapter. |
| 11 | 50S.3A | Audit honest sampled-candidate reports, shared-path drawing, and semantic identity. |
| 12 | 50S.3B | Implement deterministic reports and drawable sampled-candidate tracks. |
| 13 | 50S.4 | Add a small local snapshot, validated SGP4/topocentric machinery, and specimen builder. |
| 14 | 50S.5 | Implement the complete local FoV-crossing oracle. |
| 15 | 50S.6 | Add conservative plane/phase/state filters and optional benchmark-justified HEALPix/time indexing. |
| 16 | 50S.7 | Add independent illumination, shadow-transition, and observer-night geometry. |
| 17 | 50S.8 | Add empirical object/family/population brightness models with uncertainty and explicit unknowns. |
| 18 | 50S.9 | Estimate detector-level trail contamination separately from apparent magnitude. |
| 19 | 50S.10 | Produce night/season/sky-position statistics and close the satellite program. |
| 20 | 50B.0 | Review accepted publication, printing, typography, accessibility, and atlas practice. |
| 21 | 50B.1 | Adopt Wenu physical-output profiles and numerical publication standards. |
| 22 | 50B.2 | Measure representative products at declared physical dimensions. |
| 23 | 50B.3 | Implement monochrome and limited-grayscale publication profiles. |
| 24 | 50B.4 | Perform physical print, reduction, grayscale, and photocopy acceptance. |
| 25 | 50B.5 | Close publication styles with accepted standards, examples, limitations, and evidence. |

## 1. Purpose and authority
