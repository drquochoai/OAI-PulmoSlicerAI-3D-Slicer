# 04 — Interface contracts, types, schema versioning

## Hợp đồng tổng quát
Tất cả artifact có `contract_version` (SemVer), `artifact_id` (random), `case_id` giả danh, `source_artifact_hashes`, `created_at`, `software_revision`, `model_id`, `model_weight_sha256`, `coordinate_frame`, `units`, `stage_status`, `warnings`, `validation_report_ref`. Không dùng file path hoặc SOP UID làm định danh duy nhất của patient.

## 12 DTO / contracts phải đặc tả trước coding
| Contract | Input | Output bắt buộc | Rủi ro cần chặn |
|---|---|---|---|
| `SeriesSelection` | danh sách series DICOM | UID, modality, slice count, spacing, phase info, selection reason | Trộn series hoặc phase |
| `ImageGeometry` | DICOM pixel modules | `IJK→LPS` affine 4×4, shape, spacing, orientation, slice mapping, FoR UID | đảo trái–phải / sai mm |
| `CanonicalVolume` | DICOM selected | immutable volume + provenance + image hash | interpolation/hụt ảnh |
| `SegmentationArtifact` | volume+model+task | mask(s), class map, affine, source ref, QC | mask lệch CT |
| `GraphArtifact` | binary mask | node/edge IDs, positions in mm, radius, degree, connected components, provenance | nối sai mạch |
| `BranchPrediction` | graph+model | candidates, names, confidence/score, abstain reason, branch instances | ý nghĩa class không rõ |
| `HumanReview` | artifact version | reviewer, accepted/edited/rejected, timestamp, reason, immutable revision | tự giả trạng thái approved |
| `TerritoryCandidate` | lobe+reviewed structures | territory mask/mesh, method, discrepancy map, limitations | mặt phẳng ảo thành chắc chắn |
| `LesionArtifact` | manual/AI ROI | lesion mask, method, CT source+review | u nằm sai vị trí |
| `PlanCandidate` | lesion+territory+branch decisions | target volumes, hypothetical margin, risk flags | xem như chỉ định mổ |
| `JobManifest` | stage+dependencies | status, limits, progress, outputs hashes | nửa file nhưng đánh SUCCEEDED |
| `ExportManifest` | reviewed case | source reference, annotation/export provenance, validation findings | DICOM SEG sai nguồn |

## Quy tắc geometry
Frame tiêu chuẩn trao đổi **LPS mm** với affine chính xác; Slicer UI có thể dùng RAS nhưng bridge chịu trách nhiệm chuyển. Chứa `coordinate_system` rõ; không được coi NIfTI index và DICOM pixel grid giống nhau chỉ vì kích thước bằng nhau. `source_volume_hash + affine_hash` cùng tham gia cache key.

## Schema lifecycle
- Breaking change (field semantics/units/geometry/enum): tăng major, cần migration.
- Backward compatible optional field: tăng minor; bugfix doc/validator: patch.
- Reader xử lý major không hỗ trợ → `INCOMPATIBLE_CONTRACT`, không tự bỏ field cốt lõi.
- Contract examples phải có cả **valid + invalid**; test schema, roundtrip, wrong enum, missing FoR, extra field, stale ref.

## Cơ chế trạng thái / quyền
`CREATED → RUNNING → STAGED → VALIDATED → COMPLETE`; `FAILED`, `CANCELLED`, `BLOCKED`, `STALE` là nhánh khác. `COMPLETE` chỉ có nghĩa **máy tạo ra artifact hợp lệ kỹ thuật**, không có nghĩa giải phẫu đã duyệt. Quy trình review độc lập: `UNREVIEWED → REVIEWED_ACCEPTED/REVIEWED_CORRECTED/REJECTED`; có thể `STALE` khi upstream đổi. Worker không được có API tạo `REVIEWED_ACCEPTED`.

## Case versioning / invalidation
- Đổi source CT/affine: invalid mọi derivatives.
- Đổi mask phế quản: invalid graph airway, label airway, territories/plans/reviews liên quan; giữ nguyên mask A/V nếu độc lập.
- Đổi nhãn nhánh nhưng không đổi mask: invalid subtree territory/plan và review downstream; giữ CT/segmentation.
- Đổi vị trí u: invalid margin và plan, không rerun CT/A/V/B.
- Đổi màu hoặc camera: chỉ invalidate view cache, không chạy AI lại.
- Đổi model/backend: tạo artifact mới có provenance; không âm thầm thay dữ liệu đã duyệt.

## Bảo đảm artifact
Single-writer stage; `.partial` temp directory; validate files, dimensions, counts, affine, checksums; atomic rename cùng ổ đĩa; immutable `result.manifest`; redo/resume bằng hash. Không xóa artifact đã duyệt khi cache cleanup.
