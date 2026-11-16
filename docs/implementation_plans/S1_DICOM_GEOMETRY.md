# S1 implementation plan — DICOM and geometry

**Date:** 2026-11-15. **Work order:** WO-01. **Status:** PARTIAL.

The first implementation accepts classic single-frame CT metadata, requires an
explicit SeriesInstanceUID, rejects duplicate SOPs/mixed FoR/inconsistent
geometry/slice gaps, builds a DICOM-native IJK-to-LPS affine, tests LPS↔RAS and
left/right markers, and applies per-instance HU slope/intercept without changing
stored source values.

Enhanced multi-frame CT, compressed transfer-syntax integration tests, actual
Slicer MRML import, and authorized DICOM fixtures remain blocked/not tested.
They must not be inferred from the synthetic header tests.

