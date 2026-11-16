# Engineering test report — 2026-11-15

Command executed:

```powershell
& '.\.tools\python-3.12.10\python.exe' -c "import sys,unittest; sys.path[:0]=['.','.tools/site-packages']; suite=unittest.defaultTestLoader.discover('tests'); result=unittest.TextTestRunner(verbosity=1).run(suite); raise SystemExit(not result.wasSuccessful())"
```

Result: **32 tests passed**, including one real pydicom header integration test.
Coverage includes contract incompatibility, immutable LPS geometry, analytic
roundtrip, left/right mirror detection, explicit series selection, duplicate SOP,
slice gaps, HU transform, PHI redaction, vault traversal, TotalSegmentator class
map/CPU command, mask geometry mismatch, atomic storage, simulated crash, and
tamper detection, PTL bundle/hash/reproduction gates, graph parity, multi-parent
vein instances, fused-label safety, worker review rejection, and stale review.

Not executed: Slicer load/MRML, TotalSegmentator inference, PTL, NIfTI mask
inspection, clinical CT, GPU/AMD, DICOM SEG, installer, performance or clinical
review. Overall gate verdict remains **PARTIAL**.

