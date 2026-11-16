# Slicer smoke report — 2026-11-15

Verdict: **PASS for module load and dependency discovery**.

Executed `scripts/Test-SlicerEnvironment.ps1` against:

- Slicer 5.12.4 / build 34645 / source `4e21c19`;
- embedded Python 3.12.10;
- Windows 11 x64, AMD Ryzen AI MAX+ 392, 24 logical processors, 61079 MB
  physical memory as reported by Slicer;
- installed TotalSegmentator extension source `d8eda9f`.

Observed capabilities:

- required: DICOM PASS, SegmentEditor PASS, TotalSegmentator PASS;
- PulmoSlicerAI scripted module registration PASS;
- recommended: SlicerVMTK/ExtractCenterline PASS,
  SegmentEditorExtraEffects/DrawTube PASS, MarkupsToModel PASS;
- no patient data accessed by the test.

Installed Python packages inspected separately: TotalSegmentator 2.14.0,
PyTorch 2.15.0+cpu, nnUNetv2 2.8.1, pydicom 3.0.2.

This smoke test does not prove model inference quality, branch labeling,
territory accuracy, performance, DICOM SEG export, or clinical validity.

