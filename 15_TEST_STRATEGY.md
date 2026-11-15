# 15 — Chương trình kiểm thử đa tầng (test pyramid + safety gates)

## Cấp 0 — Design artifact validation
Tính đầy đủ task ID, depends, module mapping, contract versions, source URLs, ADR, license evidence, test coverage. **Không tương đương kiểm thử phần mềm chạy**.

## Cấp 1 — Unit tests
Geometry affine/coordinate, HU slope, schema validators, graph invariants, ontology, review state, plan invalidation, scheduler resource admission, file safety. Dùng synthetic fixtures; failure cases thiết kế trước. Test deterministic CPU không yêu cầu model weights.

## Cấp 2 — Contract tests
Slicer ↔ worker request, version compatibility, mask shape/affine, label instance mapping, model adapter class map, export manifest. Invalid/future major version phải fail rõ. File path hostile không ra ngoài vault.

## Cấp 3 — Integration
Synthetic DICOM → series selection → model stub → preview rendering → graph fixture → review state → export; original TotalSeg inference trên 1 CT licensed; PTL repro trên author fixture; optional territory model test. Tất cả phải capture model SHA and logs.

## Cấp 4 — End-to-end Windows
Open Slicer, import single/multi series, run native CPU, progress, restart, resume, edit, mark stale, export/re-import DICOM SEG and STL, clean Win install, antivirus, low-memory mode, offline.

## Cấp 5 — Model evaluation
Independent holdout without training overlap, phantom stress tests, images noncontrast/contrast/spacing/vendor, worst-case critical branch. Metrics: branch-level precision/recall, per-patient exact graph, segment territory error, lesion mask accuracy if enabled, abstention calibration, reviewer burden. Report confidence intervals and subgroup errors.

## Cấp 6 — Human factors/clinical research
Protocol approval, dual readers, interobserver disagreements, usability, where AI false confidence led to mistakes, traceability of corrections, comparison to CT manual planning. Must not imply cleared for surgical decisions.

## Negative tests không được bỏ
- mirrored IJK/LPS/RAS, multiple FoR, duplicate SOP, wrong CT series, partial rescale, mask geometry mismatch.
- vein multiple roots, crossing unconnected vessels, false branch bridge, ambiguous label, model incompatible graph.
- outdated plan after editing lesion, worker forged approval, user cancels during atomic commit.
- memory pressure, disk full, driver missing, unsupported AMD operator, DML concurrent calls, aliasing due low-res, Windows clean offline.
- export SEG source refs wrong, roundtrip visually matched but spatial shifted, stale review still shown in report.

## Test evidence policy
Mỗi test lưu `test_id`, inputs synthetic/pseudonymous, expected vs actual, environment, code/model sha, date, screenshots only if deidentified, human sign-off as applicable. No “PASS” based only on no exception. Regression baseline versioned and archived.

Các bài test chi tiết trong `catalogs/TEST_MATRIX.csv`, liên kết requirement IDs, module IDs và gate.
