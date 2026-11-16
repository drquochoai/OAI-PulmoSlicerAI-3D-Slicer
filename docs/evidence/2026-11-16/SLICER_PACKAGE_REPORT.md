# Slicer extension package report — 2026-11-16

Target: 3D Slicer 5.12.4, build 34645, Windows amd64.

Artifact:

`dist/34645-win-amd64-PulmoSlicerAI-gitlocal-2026-11-16.zip`

SHA256 at the time of this report:

`acb1b727b33da780ce87d7e9bdb5afda7063405c0af46f4c11edf2ea0b050584`

Verified:

- PowerShell package builder syntax: PASS.
- Archive contains one CPack-style top-level directory: PASS.
- Slicer Extensions Manager `extractExtensionArchive`: PASS.
- Extracted `lib/Slicer-5.12/qt-scripted-modules/PulmoSlicerAI.py`: PASS.
- Headless Slicer module discovery: PASS.
- Display path `Chest by bsquochoainew → PulmoSlicer AI for segmentectomy`: PASS.
- Scripted widget construction and CT/segmentation selectors: PASS.
- PTL selector, setup button and one-click `None`/source/B/A/V/all options: PASS.
- Tooltips, explicit dependency/flow note and collapsed advanced actions: PASS.
- Rolling progress replaces earlier percentages for the same named subtask: PASS.
- TotalSegmentator programmatic runs are non-interactive after pre-run choices: PASS.
- Performance controls expose locked stride 1, resource policy, CPU target,
  resampling workers and saving workers: PASS.
- Scoped TotalSegmentator CLI wrapper accepts thread target and official
  `--nr_thr_resamp`/`--nr_thr_saving` options without modifying the installed extension: PASS.
- Source/lobes/PTL output-role isolation and shared-selector regression fixture: PASS.
- One-click resume reuses valid source/lobe/PTL stages instead of overwriting or rerunning them: PASS.
- Auto backend selector and explicit resolved-backend status: PASS.
- Fast unsmoothed 3-D surface and later balanced regeneration: PASS on synthetic MRML bridge.
- Packaged native graph/inference engine import: PASS.
- Synthetic PTL-to-MRML voxel transfer, stable IDs, role-selective inference,
  Right/Left hierarchy, visibility toggle and 3-D surface: PASS.
- Real Subject Hierarchy child folders Right/Left → lobe → B/A/V/Lung: PASS.
- Compact progress panel, resource telemetry and safe JSONL logger load: PASS.
- Packaged `.10` asynchronous HTML worker, granular structure/stage progress,
  cancellation button and responsive Qt event loop regression: PASS.
- One-click base 3D action is wired; inference was not run on patient data.
- TotalSegmentator dependency discovery: PASS.
- Patient data accessed during smoke test: false.

The smoke test did not run model inference and is not clinical validation.
