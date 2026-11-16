# WO-04 PTL author-original reproduction

Verdict: **BLOCKED**. Automatic branch naming is disabled by design.

Reviewed upstream commit: `27fdace577293a29480bce4f00efba7501cadd20`.
The repository source is Apache-2.0, but that observation does not establish the
license or redistribution permission of the separate Google Drive dataset and
pretrained checkpoints.

Concrete blockers found:

- no checkpoint hashes or signed manifest in the upstream repository;
- author dependency export is `linux-64` and includes CUDA/PyTorch 1.13;
- the entry point selects `cuda:1` whenever CUDA is available, which is unsafe
  on a single-GPU machine and is not an approved Windows/CPU runtime contract;
- graph inputs use padded `Data.x` coordinate tensors with different maxima
  (airway 519, artery 1813, vein 1691), directed `edge_index`, voxel-index
  coordinates, and `-10` padding;
- dataset/GraphML preprocessing and expected author fixture outputs have not
  been acquired or reproduced.

Implemented now: a manifest probe that fails closed unless all three role
checkpoints have a verified SHA256, explicit license ID, reviewed source commit,
graph-contract version, and author-original reproduction flag. A field-by-field
graph parity comparator covers node count/coordinates, edge orientation,
padding, coordinate semantics, and normalization. It is not evidence that the
adapter itself is compatible.

