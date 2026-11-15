# 28 — Tin nhắn giao việc mẫu cho AI coding agent (sử dụng SAU khi duyệt thiết kế)

> Bạn là kỹ sư chịu trách nhiệm một work order của dự án PulmoSlicer AI v2.0. Đây là tài liệu DESIGN ONLY, chưa có mã nguồn. Đọc theo đúng thứ tự: `00_START_HERE.md`, `02_ARCHITECTURE.md`, `03_MODULAR_CODING_STANDARD.md`, `catalogs/MODULE_CATALOG.csv`, `catalogs/PORT_CONTRACT_CATALOG.csv`, work order tương ứng, `catalogs/SOURCE_REGISTER.csv`, `catalogs/TEST_MATRIX.csv`.
>
> Trước khi viết code, báo rõ nguồn chính thức đã xác minh, Git SHA, quyền phân phối mã và checkpoint, hệ điều hành và phiên bản Slicer, các module/file bạn phụ trách, contract đầu vào/đầu ra, tests âm tính và điều kiện dừng. Nếu thiếu dữ kiện quan trọng, ghi BLOCKED và giải thích, không bịa API/checkpoint hoặc tuyên bố PASS.
>
> Chỉ viết file nhỏ 1 nhiệm vụ, không đưa PyTorch AI vào Slicer GUI process, không sửa source CT hay tạo clinician approval. CPU phải hoạt động ngay cả khi không có CUDA; GPU AMD là tùy chọn và chỉ được bật sau paired benchmark.
>
> Sau khi code phải giao Git diff, exact commands đã chạy, log ẩn PHI, tests PASS/FAIL có evidence, số liệu RAM/time khi phù hợp và những rủi ro còn mở. Chỉ nhận TASK có phụ thuộc PASS.
>
> **Nhiệm vụ đầu tiên:** WO-00, chỉ xây nền tảng và xác thực môi trường. Không tự ý code toàn bộ 7 model hoặc tạo installer trong một lần.

## Cách phân công nhóm 5–6 agents
**Lead/Architect:** contracts/ontology, integrator and QA. **Imaging:** DICOM/geometry/TotalSeg. **ML research:** PTL model original/checkpoints/graph parity (không sửa GUI). **UI/Slicer:** view/CT/branch review trên contract giả lập. **Performance:** scheduler/profiling CPU/AMD (đợi masks). **Release/QA:** independent tests, Windows offline, security/licensing.
