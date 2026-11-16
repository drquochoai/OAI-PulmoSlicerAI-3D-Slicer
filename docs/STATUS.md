# Implementation status

Last updated: 2026-11-16. Product claim: **research engineering prototype only**.

| Slice | Engineering status | Evidence / blocker |
|---|---|---|
| S0 Foundation | PARTIAL | Contracts, LPS geometry, vault, safe logs, compatibility probe and thin Slicer shell implemented. Slicer 5.12.4 module/dependency smoke PASS; license sign-off, signing and independent review remain absent. |
| S1 CT correct | PARTIAL | Classic CT series/header scan, explicit selection, geometry QA, affine, left/right and HU tests implemented. Enhanced multi-frame, compressed pixel integration and MRML not tested. |
| S2 A/V/B | PARTIAL | Slicer UI now selects CT/output nodes and invokes TotalSegmentator `lung_vessels`, then requires stable airway/artery/vein segment IDs. No model inference was run in automated tests. |
| S3 Lobes/storage | PARTIAL | UI invokes the five-lobe subset, validates IDs and creates closed-surface display. Cache/atomic storage tests pass; real mask persistence and resume remain untested. |
| S4 PTL proof | PARTIAL / EXPERIMENTAL | Pinned author source, all three checkpoint hashes, author fixture reproduction, native graph adapter and Slicer A/B/V label bridge are implemented. One public case is insufficient for transfer/clinical validation; native vein graph Dice is 0.0185 below the author graph on that case, and checkpoint redistribution rights remain unstated. |
| S5 Branch review | PARTIAL | PTL voxel labels for 18 pulmonary regions per selected airway/artery/vein tree now run from the UI. Real Subject Hierarchy folders and a visibility tree organize Right/Left → lobe → B/A/V/Lung. Safe branch-instance, unknown/variant, fused labels and human-only review state exist, but instance-level review UI and external validation remain absent. |
| S6 Territory/lesion | NOT STARTED | Requires reviewed/manual branches and clinical method acceptance; no fabricated territory output. |
| S7 Planning | NOT STARTED | Requires reviewed lesion/territory/branch artifacts and surgeon workflow. |
| S8 CPU/AMD optimization | PARTIAL | Auto backend policy prefers an actually available CUDA/ROCm PyTorch device and falls back to CPU; unsupported DirectML is never reported as active. The UI exposes a truthful stride-1 policy, resource profiles, CPU thread target and TotalSegmentator resampling/saving workers through a scoped child-process wrapper. Fast 3-D preview, UI event yielding and live telemetry are implemented. Dynamic 85%-utilization control is not valid for this 3-D inference structure; paired CT benchmarks and an isolated AMD ROCm worker remain absent. |
| S9 Export/install | PARTIAL | Install-from-file ZIP `.10` for build 34645 is generated. A single-file offline interactive HTML exporter, anatomy allowlist, background derivative mesh smoothing/QA, granular progress, cancellation, color templates, PHI scan, atomic write and browser viewer are implemented. Synthetic Slicer-to-HTML, responsive Qt worker and Edge `file://` smoke PASS. DICOM SEG, patient-case quality validation, independent roundtrip, clean-machine install and signing remain absent. |
| S10 Validation | NOT STARTED | Requires lawful independent dataset, dual clinical reviewers, protocol and governance. |

## Verified locally

- 66 unit/integration tests pass on Slicer Python 3.12.10.
- Python compilation succeeds for engine, extension shell, and tests.
- Headless Slicer PTL-to-MRML bridge smoke PASS with synthetic data: stable
  A/B/V segment IDs, role-selective output, voxel transfer, closed-surface creation,
  anatomy hierarchy and visibility toggle.
- Source widget smoke PASS with tooltips, explicit flow note, role/None selector,
  one-line rolling progress and one-click action present.
- Subject Hierarchy smoke PASS for `Right → Upper → A → A1 Right` and
  `Right → Upper → Lung → lung_upper_lobe_right`.
- Output-role isolation regression smoke PASS: source/lobes/PTL cannot share a
  writable segmentation node; valid completed stages are reused on resume.
- Interactive HTML smoke PASS: five synthetic structures exported through VTK,
  all five decoded in Edge offline, default all-valid selection and Standard
  color/profile UI verified from the staged package.
- Optional thoracic context subset includes aorta/arch branches, ribs 1–12,
  sternum and T1–T12; clavicles, scapulae and costal cartilage are excluded.

## Next executable gate actions

1. Capture model weight hashes and a reproducible run report from one
   authorized/deidentified TotalSegmentator CT run. The installed 2.14.0 package
   predates the planned 2.18.0 engine contract and must not be silently upgraded.
2. Add NIfTI header/voxel validation and MRML LPS↔RAS bridge tests.
3. Run native graph parity on additional authorized cases, resolve checkpoint
   licensing, and validate all A/B/V labels with two independent clinical
   reviewers before any clinical claim.
4. Implement and validate lobe-constrained parenchymal S1–S10 territory
   reconstruction; current PTL output labels tree voxels, not lung parenchyma.

