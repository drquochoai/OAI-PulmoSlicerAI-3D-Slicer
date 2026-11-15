# 26 — Những thay đổi quan trọng so với kế hoạch v1.3

## Cải thiện về quản trị code
- Chốt chính sách mỗi file nhỏ 1 trách nhiệm, soft <=250 logical LOC và review >300; tối đa 400 chỉ khi ADR, tránh giant Slicer module.
- Lập danh mục file-level `MODULE_CATALOG` với input/output, dependency, thread context và criticality; dùng Ports & Adapters để coding agents triển khai riêng.
- Tách schema/ontology/geometry/review state thành protected core, đổi phải ADR và dual review.

## Cải thiện tốc độ và máy yếu
- Tách việc nạp mô hình vào worker ngoài Slicer, không dùng quá nhiều process hoặc copy volume qua IPC.
- Triển khai hai bước preview/detailed, lazy VTK/LOD, crop native ROI kèm halo, cache theo digest, resource tokens.
- Đầu tư benchmark **p90 end-to-end** và lỗi nhánh mạch trước việc tối ưu hiệu năng thô. No unlimited parallelism.
- 16GB là Lite hạn chế, 32GB là mục tiêu Standard phải đo, ASUS 64GB AMD là Performance optional (shared memory không cộng thêm).

## Cải thiện an toàn và khoa học
- Phân biệt A/V/B semantic mask vs branch instance naming; PTL original/graph parity là gate bắt buộc.
- Đánh dấu Lung3D/ImPulSe ứng viên territory chưa verified; không coi tất cả dữ liệu open là CT độc lập.
- Bổ sung DICOM SEG source UID/FoR independent reader roundtrip.
- Kết quả territory và margin chỉ là CT-based hypothetical, có cảnh báo bất đồng/uncertainty/unknown.
- Bảo vệ reviewer acceptance khỏi worker, hủy hiệu lực plan đúng dependencies sau chỉnh sửa.

## Sự thật về trạng thái dự án
Toàn bộ tài liệu mới chỉ là **DESIGN ONLY**; chưa viết `.py`, chưa tải model weights, chưa tạo `.exe`, chưa chạy Slicer, chưa đo GPU AMD và chưa nghiên cứu kiểm định trên CT. Bất kỳ câu PASS nào trong tương lai phải có evidence riêng ngoài bộ hồ sơ này.
