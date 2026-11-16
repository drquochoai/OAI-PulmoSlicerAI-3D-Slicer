# X02 license and rights audit

Verdict: **BLOCKED / legal and weight review outstanding**.

- 3D Slicer source distribution: official source identified; bundled extension
  obligations still need release review.
- TotalSegmentator code advertises Apache-2.0 and identifies `lung_vessels` as
  openly available. This does not by itself prove the redistribution rights and
  hashes of every downloaded checkpoint in an offline hospital bundle.
- SlicerTotalSegmentator is a separate convenience extension; it is not the
  TotalSegmentator model publisher and is not treated as permission for weights.
- PTL source at the pinned commit contains Apache-2.0. Its separately hosted
  dataset and three pretrained checkpoints still require license, provenance,
  SHA256, and redistribution evidence. None is packaged.
- AirRC/BronAtlas/HiPaS/Lung3D datasets are not runtime dependencies and must not
  enter the hospital installer.

No model weights or external datasets were downloaded by this implementation.

