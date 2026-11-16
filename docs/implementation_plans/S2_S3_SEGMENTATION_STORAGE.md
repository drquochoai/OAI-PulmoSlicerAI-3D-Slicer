# S2/S3 implementation plan — segmentation boundary and persistence

**Date:** 2026-11-15. **Status:** PARTIAL / model runtime not executed.

This slice probes the machine-readable TotalSegmentator registry, requires the
exact four `lung_vessels` classes, constructs one full-resolution CPU command,
requires its run report and all output masks, and separately verifies the five
lobe names from the `total` task. Mask metadata must match the immutable source
shape, affine, and hash before it can become a `SegmentationArtifact`.

The storage subset creates content-addressed cache keys and promotes staged
artifacts atomically only after hashing. It never alters source masks for visual
quality. Real TotalSegmentator execution, mask NIfTI header inspection, Slicer
rendering, cancellation, and crash-resume on Windows remain NOT_TESTED.

