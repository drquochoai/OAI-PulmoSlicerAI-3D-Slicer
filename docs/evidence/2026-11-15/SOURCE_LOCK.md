# Source lock — 2026-11-15

Status: **PARTIAL**. This record pins engineering candidates; it does not grant
redistribution rights for model weights or datasets.

| Component | Candidate pin | Evidence status | Release decision |
|---|---|---|---|
| 3D Slicer | 5.12.4, revision 34645, Git `4e21c19d8360242d88d6ca2490bf52400441b8e1` | Official release/download records checked | Target baseline; local executable not found, smoke test blocked |
| TotalSegmentator | 2.18.0, Git tag `184fa4765456492b2ab81a981cc387465906b003` | Official upstream tag/changelog/registry contract checked | Engine candidate; exact wheel and every weight SHA still required |
| `lung_vessels` | `lung_airways`, `lung_airways_wall`, `lung_arteries`, `lung_veins` | Upstream registry/class map checked | Full-resolution CPU command only until quality benchmark |
| Five lobes | `total` task classes 10–14 by names, not hard-coded indices | Upstream class map checked | Probe installed registry before use |
| SlicerTotalSegmentator | Git `d8eda9f6615c9c59c899a9ca9694aef2fc82712c` | Official extension HEAD observed | Reference only; not embedded engine architecture |
| PTL/IPGN | HINTLab `pulmonary-tree-labeling`, Git `27fdace577293a29480bce4f00efba7501cadd20` | Official repository and author-described 3 checkpoints observed | BLOCKED: checkpoint SHA/license audit/original reproduction missing |

Important upstream fact: TotalSegmentator 2.18.0 includes a DICOM export
anterior/posterior mirroring fix. PulmoSlicer therefore does not accept an older
unverified export path merely because its 3D surface looks correct.

