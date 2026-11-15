# 23 — Failure injection, contingency và phục hồi

## Phương pháp
Không chỉ viết happy path. Mỗi module phải nêu trạng thái lỗi có thể xảy ra, cách xử lý an toàn, cách kiểm chứng, phục hồi dữ liệu. Ưu tiên lỗi nguy hiểm trong mổ hơn lỗi UI thông thường.

| Failure | Expected behavior | Recovery |
|---|---|---|
| DICOM khác Frame of Reference | Chặn geometry-based reconstruction | Chọn series có FoR đúng, xem chi tiết |
| Lung_vessels checkpoint unavailable | Chuyển chế độ manual/view CT, không giả mask | Cài approved checkpoint offline |
| PTL graph parity fail | Tắt automatic labels, vẫn giữ A/V/B masks | Sửa adapter và chạy parity test |
| ImPulSe2 source chưa tái lập | Không hiển thị territory AI như verified | Geometric baseline + explicit experimental |
| GPU AMD driver incompatible | Chuyển CPU có cảnh báo nguồn telemetry | Cập nhật driver được phê duyệt; rerun backend check |
| RAM rất thấp | Thông báo không đủ memory, deferred/downgrade | Chọn ROI/CPU lite hoặc máy RAM cao hơn |
| App crash sau mask stage | Không overwrite original mask | Resume completed cache digest |
| Disk full giữa xuất SEG | Temp artifact quarantine; no success | Tăng dung lượng và export lại |
| DICOM SEG không đọc lại | Reject export | Kiểm tra source refs/FoR/code table |
| Đổi lesion sau review | Review/plan stale và export verified disabled | Bác sĩ review lại |
| Missing clinical reviewer | Label AI remains suggested | Bác sĩ review thủ công |
| CT insufficient for A/V discrimination | Set unknown and no false confidence | Repeat CT if clinically indicated by treating team |

## Drill diễn tập release
Mất điện/kill process, resume after restart, full SSD, duplicate job, two Slicer windows open same case, no admin, no network, Windows Defender quarantine and rollback, source model invalid SHA, workstation out of disk during installer. Trước và sau drill ghi hash của source CT và reviewed files, phải không thay đổi.

## Error taxonomy
`INPUT_INVALID`, `INPUT_LIMITED`, `GEOMETRY_INVALID`, `MODEL_MISSING`, `MODEL_INCOMPATIBLE`, `LICENSE_BLOCKED`, `RESOURCE_DENIED`, `WORKER_CRASH`, `CANCELLED`, `STORE_CORRUPT`, `EXPORT_REFERENCE_INVALID`, `REVIEW_STALE`, `UNSUPPORTED_BACKEND`. Không chuyển lỗi sang trạng thái COMPLETE.
