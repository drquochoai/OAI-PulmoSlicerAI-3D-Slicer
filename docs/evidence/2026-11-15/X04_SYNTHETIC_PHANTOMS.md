# X04 synthetic geometry phantoms

Verdict: **PARTIAL engineering fixtures**.

The automated suite contains two provenance-free geometry packs:

1. Axial classic CT metadata with asymmetric LPS left/right markers, anisotropic
   0.6 × 0.8 × 1.5 mm spacing, non-unit HU slope/intercept, duplicate-SOP and
   missing-slice negative variants. A two-file DICOM instance is written in a
   temporary directory with pydicom and scanned using `stop_before_pixels`.
2. Oblique orientation with the slice normal along LPS +X, analytic expected
   affine, forward/inverse coordinate roundtrip, and mirrored-marker failure.

These cover classic single-frame CT only. Enhanced multi-frame, compressed pixel
transfer syntaxes, gantry tilt, and Slicer/DICOM SEG roundtrips remain open.

