# PULMOSLICER AI — BỘ BÀN GIAO THIẾT KẾ v2.0

**Loại tài liệu:** Software Architecture & Engineering Handover — DESIGN ONLY. **Ngày chốt nội dung:** 15/11/2026. **Trạng thái sản phẩm:** CHƯA VIẾT MÃ NGUỒN. **Phạm vi:** Windows / 3D Slicer / CPU-first / AMD acceleration tùy chọn / offline hospital.

## Mục tiêu của dự án
Đưa thư mục DICOM CT ngực vào 3D Slicer; tạo, kiểm tra và chỉnh sửa mô hình 3D phế quản, động mạch phổi, tĩnh mạch phổi, năm thùy và các vùng phân thùy ước tính; đặt tên các nhánh; đánh dấu tổn thương; lập và so sánh các phương án cắt phân thùy. **Đầu ra AI là gợi ý nghiên cứu cần bác sĩ xác minh; không tự ra quyết định phẫu thuật.**

## Trình tự đọc bắt buộc cho coding agent
1. `01_PRODUCT_CHARTER.md`: phạm vi, ràng buộc và những điều KHÔNG được hứa.
2. `02_ARCHITECTURE.md`: tiến trình, lớp hệ thống, DAG phụ thuộc.
3. `03_MODULAR_CODING_STANDARD.md` + `catalogs/MODULE_CATALOG.csv`: quy tắc file nhỏ, ownership, mô-đun và giới hạn import.
4. `04_CONTRACTS_AND_VERSIONING.md` + `05_DICOM_GEOMETRY.md`: hợp đồng dữ liệu; kiểm tra tọa độ, nguồn gốc.
5. `06_IMAGING_PIPELINE.md`, `07_MODELS_AND_DATA.md`, `08_PTL_GRAPH_ADAPTER.md`, `09_SURGICAL_PLANNING.md`.
6. `10_PERFORMANCE_CPU_AMD.md`, `11_SCHEDULER_STORAGE.md`, `12_SLICER_UX.md`, `13_SECURITY_PRIVACY.md`, `14_WINDOWS_DELIVERY.md`.
7. `15_TEST_STRATEGY.md`, `16_STANDARDS_AND_QUALITY.md`, `17_AGENT_WORK_ORDERS.md`.
8. `catalogs/TASK_BACKLOG.csv`, `TEST_MATRIX.csv`, `RISK_REGISTER.csv`, `REQUIREMENTS_TRACEABILITY.csv`, `SOURCE_REGISTER.csv`.
9. `18_GATES_AND_ACCEPTANCE.md`, `19_DECISIONS_AND_OPEN_ITEMS.md`, `20_GLOSSARY.md`.

## 10 quy tắc tuyệt đối
1. **Không code** khi task thiếu hợp đồng dữ liệu, phụ thuộc hoặc phép thử; mở phiếu `BLOCKED`.
2. Không đưa dữ liệu bệnh nhân thật vào Git, issue tracker, chat với coding agent hoặc báo lỗi.
3. Không dùng một file Python khổng lồ chứa UI, thuật toán, I/O và AI.
4. Không gọi MRML/VTK UI từ background worker; phân chia tiến trình rõ ràng.
5. Không làm thay đổi mask gốc chỉ để bề mặt 3D đẹp hơn; render LOD tách dữ liệu đo đạc.
6. Không coi PTL, BronAtlas, ImPulSe là các extension cài sẵn; kiểm tra riêng mã/weights/data/license.
7. Không cho kết quả AI mặc nhiên mang trạng thái `CLINICIAN_VERIFIED`.
8. Không chạy nhiều mô hình nặng chỉ vì có nhiều nhân CPU; scheduler phải đo RAM và contention.
9. Không hứa thời gian xử lý, độ chính xác hoặc chạy GPU trước benchmark trên máy thật.
10. Không công bố bản dùng lâm sàng khi chưa thẩm định phù hợp, chưa đủ quyền sử dụng và chưa hoàn thành quy trình pháp lý.

## Gate ưu tiên khởi đầu (trong thứ tự)
**G0** khóa phiên bản, xác minh nguồn/giấy phép, mở được module shell trong Slicer. **G1** DICOM đúng + TotalSeg có output nguồn và 3D. **G2** tái lập PTL trên dữ liệu gốc, sau đó mới xây graph adapter. **G3** lobe/A/V/B review được. **G4** territory + lesion + plan ở chế độ nghiên cứu. **G5** profiling CPU/AMD và tối ưu. **G6** installer offline và roundtrip data. **G7** nghiên cứu kiểm định độc lập.

## Mô hình triển khai đầu ra
Bác sĩ cài 3D Slicer (phiên bản được hỗ trợ), chạy một trình cài offline PulmoSlicer AI ký số nếu khả thi, kiểm tra model bundles và cấu hình phần cứng. Máy viện **không cần** cài datasets AirRC, BronAtlas, HiPaS, PTL raw. Trong quá trình phát triển, tất cả thư viện AI đều đặt trong **engine Python độc lập**, không phá môi trường Python của 3D Slicer.

## Điểm chưa chứng minh
PTL→mask TotalSeg; ImPulSe2→CT viện; CPU profile 16/32 GB; ONNX DirectML per-model; DICOM SEG roundtrip; installer Windows sạch. Đánh dấu `NOT_TESTED`, không đổi sang `PASS` nếu chỉ kiểm tra tài liệu.

**Bản này chỉ chứa thiết kế, quy trình, ma trận và tiêu chuẩn; không có file `.py`, `.exe`, mô hình đã tải hay chương trình chạy thử.**
