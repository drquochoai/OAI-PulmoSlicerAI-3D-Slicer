# Interactive HTML export — engineering evidence

Date: 2026-11-16. Status: engineering proof on synthetic geometry; clinical
validation is not claimed.

## Locked web viewer inputs

| Component | Version | Use | License |
|---|---:|---|---|
| Three.js | 0.187.0 | WebGL renderer and OrbitControls | MIT |
| esbuild | 0.28.2 | Reproducible development-time bundle | MIT |

`viewer_bundle.js` SHA-256:

```text
62d6b9eaa6093ba3c92ff13084bda7f19c4cb58e731ab57d9b4c16cc606c307d
```

The bundle retains the Three.js license header. The exported artifact has no
external script, stylesheet, font, model or network request. Content Security
Policy sets `connect-src 'none'` and limits workers/images to embedded blob/data
content.

## Implemented contract

- contract `1.0.0`, viewer `1.0.0`;
- one `.html` written via `.partial` then atomic rename;
- default selection: every valid allowlisted PulmoSlicer structure supplied by
  the current workflow;
- allowlisted anonymous metadata only; no CT voxels or raw DICOM metadata;
- independent gzip mesh chunks, SHA-256 per chunk and source geometry hash;
- Slicer world RAS converted to web `X=Right, Y=Superior, Z=Posterior`, units mm;
- source closed surface is deep-copied; smoothing and decimation apply only to
  the export derivative;
- conservative topology/component/displacement QA with automatic source-mesh
  fallback for a failing structure.

## Tests actually run

- `PythonSlicer.exe -m unittest discover -s tests -p test_*.py`: 66 tests PASS.
- Slicer 5.12.4 headless synthetic export: five structures, 4,584 triangles,
  single HTML generated.
- Microsoft Edge headless `file://` offline render: five of five chunks ready;
  tree, palette, camera controls and WebGL surface visible.
- Slicer 5.12.4 headless UI construction: default profile `standard`, default
  palette `pulmoslicer-surgical-contrast-v1`, and default all-valid selection
  verified.
- Responsive-worker regression: five synthetic structures exported in the
  background while the Qt timer fired 122 times; progress advanced through 32
  distinct values from 0 to 100 and produced a 1,078,920-byte HTML file.

## Responsiveness defect corrected in `.10`

The `.9` exporter called VTK smoothing/decimation synchronously from the Qt
button handler. On a real high-resolution first segment, the run log contained
only `run_started`, the screen remained visually at `0%`, and Windows marked
Slicer not responding. `.10` captures detached polydata on the main thread and
runs all expensive VTK filters, encoding and file assembly in a daemon worker.
The main thread polls a message queue every 100 ms, updates one live progress
line, samples CPU/RAM and supports cooperative cancellation between stages.

## Residual limitations

- Synthetic geometry is not clinical anatomy and cannot prove branch survival
  on patient cases.
- Aorta from TotalSegmentator is a continuous mask. Ascending/arch/descending
  separation still requires a landmark/centerline review implementation.
- Segmental parenchymal territories, automated tumor segmentation, DICOM SEG
  roundtrip and clinical validation remain separate gates.
