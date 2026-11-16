# S9 — Interactive all-in-one HTML export

Status: implemented engineering slice; synthetic/offline smoke PASS; clinical
quality validation pending.

## Contract and boundaries

- Contract `1.0.0`; surface-only research/display derivative.
- Source MRML segmentation and closed surface remain unchanged.
- Metadata is allowlisted; arbitrary node/display names are not exported.
- Default selection is every valid allowlisted structure supplied by the active
  PulmoSlicer workflow. Export never starts missing AI stages.
- RAS world coordinates are converted to web X-right/Y-superior/Z-posterior in
  millimetres with the transform recorded in the manifest.

## Modules

| Module | Responsibility |
|---|---|
| `html_export/contracts.py` | Versioned options, mesh and result DTOs |
| `html_export/anatomy.py` | Stable ID/hierarchy allowlist |
| `html_export/color_templates.py` | Versioned sRGB palettes |
| `html_export/mesh_pipeline.py` | Deep-copy, smooth, decimate and QA |
| `html_export/mesh_codec.py` | Deterministic binary/gzip chunks |
| `html_export/html_writer.py` | CSP, manifest, PHI scan and atomic write |
| `html_export/exporter.py` | Slicer orchestration and per-node fault isolation |
| `html_export_panel.py` | Small Slicer UI section |

## Release gates still open

- benchmark on representative authorized thin-slice CT cases;
- centerline endpoint/branch survival QA against source vessels;
- browser matrix beyond the tested local Edge build;
- clinical review of palette and acceptable surface displacement thresholds;
- signed package, clean-machine install and independent reviewer sign-off.

Evidence: `docs/evidence/2026-11-16/HTML_EXPORT_ENGINEERING_REPORT.md`.
