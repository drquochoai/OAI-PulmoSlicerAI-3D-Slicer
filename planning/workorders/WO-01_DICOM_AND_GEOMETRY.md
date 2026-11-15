# WO-01 — DICOM_AND_GEOMETRY

**Gate:** G1. **Owner:** Imaging Engineer. **Status:** DESIGN ONLY / NOT STARTED. **Source of truth:** `00_START_HERE.md` + relevant modules in `catalogs/MODULE_CATALOG.csv` and `G1` tasks in `catalogs/TASK_BACKLOG.csv`.

## Mục tiêu cụ thể
Lấy đúng CT Series, geometry LPS/RAS, HU, multi-frame và synthetic phantoms.

## Công việc liên quan
X06 (xem bảng backlog). Chỉ bắt đầu khi tiền nhiệm PASS, không chỉ DESIGN COMPLETE.

## Checklist coding agent khi triển khai trong tương lai
1. Kiểm tra source register: official URL, exact version, licenses/weights SHA, compatibility của OS/CPU. Nếu link không truy cập được ghi BLOCKED_SOURCE.
2. Kiểm tra Module Catalog: sở hữu file nào, module phụ thuộc, direction of imports, line budget và contract.
3. Viết kế hoạch thực thi cho từng nhiệm vụ nhỏ, nêu failure case và test unit/contract trước khi viết code.
4. Chỉ tạo/chỉnh file thuộc module ownership được phép; nếu cần đổi protected geometry/ontology/review, tạo ADR và xin review.
5. Thực hiện positive+negative tests trên fixtures tổng hợp; integration và benchmark nếu thuộc image pipeline.
6. Kiểm tra state correctness, resumability, memory budget, privacy, provenance; không report success dựa trên exit code.
7. Lập evidence pack: commands actually executed, version+commit, stdout/stderr sanitized, expected/actual, screenshots không PHI, resource numbers, reviewer sign-off.
8. Cập nhật task/test/risk/gate trạng thái đúng thực tế; chưa thử trên Windows thì ghi NOT_TESTED_WINDOWS.

## Bằng chứng yêu cầu
Series selection, canonical CT, affine tests, input failure matrix.

## Điều kiện dừng/không được làm sai
Reject wrong-side/mixed phase; maintain source UID mapping. Mọi kết quả phải có model/data SHA và CT-source provenance nếu tạo ra từ ảnh.

## Báo cáo hoàn tất
`Task ID | code changes | run commands | test IDs with results | performance/quality | risks addressed | residual blockers | next action | reviewer | PASS/FAIL/PARTIAL/BLOCKED`.
