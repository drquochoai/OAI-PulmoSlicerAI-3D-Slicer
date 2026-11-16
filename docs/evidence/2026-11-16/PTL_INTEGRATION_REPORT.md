# PTL integration report — 2026-11-16

Verdict: **PARTIAL / EXPERIMENTAL**, suitable for research review only.

## Locked inputs

- Upstream: HINTLab `pulmonary-tree-labeling`.
- Commit: `27fdace577293a29480bce4f00efba7501cadd20`.
- Source archive SHA-256:
  `3081003d761687c6dc7f63f3632d03f435bdec568195a56a0ed9bef1450ea37e`.
- Official public fixture: `pulse_00007`; the downloaded fixture and weights
  remain ignored local research inputs and are not in the extension ZIP.
- Checkpoint SHA-256:
  - airway: `728b45ab71f84975231e98f062934e2dfe2ec966d65eef5874161d9bae222a4c`;
  - artery: `95c0f0fdba2bfd9157b8b7abbe5495720c4695b4171ed1964a6360c5c09ccc59`;
  - vein: `18248cef574421289744efb595de0391d1b4bc186320c85eae150aef665310a6`.

Upstream does not state a separate redistribution license for the checkpoint
files. PulmoSlicer therefore downloads them from the author-provided IDs on
first use, verifies hashes, marks them non-redistributable, and never includes
them in the extension ZIP.

## Author-graph reproduction

CPU inference used the author GraphML and the exact point/graph construction
semantics reconstructed from the released loader.

| Tree | Nodes / directed edges | Accuracy | Macro Dice, present classes |
|---|---:|---:|---:|
| Airway | 171 / 342 | 0.890731 | 0.778480 |
| Artery | 764 / 1530 | 0.880212 | 0.840497 |
| Vein | 709 / 1416 | 0.820934 | 0.760967 |

All predicted and reference class IDs 1–19 were present. There is no signed
author expected-metric manifest, so this is reproduction evidence, not a claim
of bit-exact parity with an author-published result.

## Native mask-to-graph adapter

The distributed adapter uses deterministic 3-D skeletonization, 26-neighbour
connectivity, collapsed junction cliques and degree-two path reduction. It does
not distribute or call VesselVio. On the same fixture:

| Tree | Native nodes / edges | Accuracy | Macro Dice | Dice delta vs author graph |
|---|---:|---:|---:|---:|
| Airway | 177 / 177 | 0.890171 | 0.777587 | -0.000893 |
| Artery | 895 / 896 | 0.902237 | 0.877080 | +0.036583 |
| Vein | 753 / 752 | 0.808114 | 0.742487 | -0.018480 |

This supports functional compatibility on one case but does not close the
planned graph-parity or transfer-validation gates. The vein difference and
the node/edge-count differences require multi-case review.

## Slicer integration evidence

- 52 Python unit/integration tests: PASS.
- Synthetic headless Slicer 5.12.4 bridge: PASS for all three source roles,
  stable segment IDs, binary labelmap transfer and closed-surface creation.
- Packaged widget smoke: PASS; PTL setup/action/one-click controls are present.
- Clean first-use setup smoke in headless Slicer: PASS; dependency install,
  pinned source download, all three checkpoint downloads and SHA-256 checks
  completed without patient data.
- No patient data was accessed by these smoke tests.

## Explicit remaining boundary

The implemented output labels voxels belonging to the airway, pulmonary artery
and pulmonary vein masks by 18 pulmonary regions plus the central class. It is
not yet a lobe-constrained pulmonary parenchymal territory reconstruction.
Therefore the full S1–S10 segmentectomy model remains incomplete until the
territory method and clinical validation are implemented.
