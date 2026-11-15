# 03 — Quy chuẩn module/file nhỏ theo engineering quốc tế

## Nguyên tắc nền tảng
**SRP/SOLID**, Dependency Inversion, Ports-and-Adapters, typed contracts, design-for-testability, separation of concerns, convention over magic. **Modular monolith** tốt hơn microservices trong bài toán offline một máy. Module nhỏ để dễ sửa và AI agent có thể sở hữu độc lập; **không tách 1 dòng thành nhiều file vô nghĩa**.

## Quy tắc bắt buộc với coding agent ở giai đoạn sau
1. Một file `.py` có **một trách nhiệm thay đổi chính**. Ví dụ `dicom_series_validator.py` chỉ validate series; không vừa chọn UI, vừa inference, vừa xuất SEG.
2. **Mềm:** mục tiêu 100–250 logical LOC/file, review nếu >300, không cho file >400 LOC nếu không có ADR được duyệt (không tính dữ liệu schema/auto-generated). Function mục tiêu <=35 LOC và <=4 tham số nghiệp vụ trực tiếp; dùng DTO khi nhiều tham số. Đây là guardrail bảo trì, không phải quy chuẩn ISO.
3. Chỉ `domain` chứa luật giải phẫu, chỉ `infrastructure` chứa IO/hệ thống; `presentation` không có thuật toán CV, Torch, dicom pixel arithmetic.
4. Public interface phải có contract version, type, units, coordinate frame, input/output, error states, deterministic policy, test ID. Không trao đổi `dict` vô danh giữa modules.
5. Không dùng global mutable state; không import vòng; không dùng side effects khi import; không giấu tải checkpoint trong constructor UI.
6. Dependency direction: `presentation -> application -> domain/ports`, `adapters -> ports/domain`, domain không import ngoài standard/typing. Một ngoại lệ phải có ADR.
7. Giới hạn một nhóm file/module do một coding agent phụ trách. Chỉ kiến trúc sư chỉnh `contracts`/ontology khi có ADR và tăng version.
8. Không viết code thí nghiệm trực tiếp trong `stable/`; prototype ở nhánh riêng với hạn ngày xóa/hợp nhất, không copy code chưa kiểm tra từ upstream.
9. Logs cấu trúc có `stage_id`, `job_id` ngẫu nhiên, error_code, duration, model hash; không ghi họ tên, UID gốc, đường dẫn chứa tên bệnh nhân hoặc pixels.
10. Test unit phải mock ports, integration dùng synthetic/consented fixture, external model tests lưu evidence riêng. Version migration và backward-compat phải có test.
11. Kiểm tra typing, lint, formatting, security dependency scan, test, API contract và manifest trước khi merge; review ≥1 người độc lập với module lâm sàng/geometry.
12. No silent fallback: CPU fallback xuất telemetry và provenance; lobe/model missing hoặc CT không đủ chất lượng phải thể hiện rõ.

## Directory blueprint — chỉ là KẾ HOẠCH, chưa tạo source files
```text
pulmoslicer-ai/
  docs/                    # specs, ADRs, model cards, verification reports
  contracts/               # versioned schema and ontology definitions
  slicer_extension/
    presentation/          # small widgets, view states, screen mapping
    slicer_bridge/         # MRML/VTK/DICOM adapters only
    application_client/    # worker invocation + read-only status
  engine/
    domain/                # immutable entities, validation & rules
    application/           # use cases, stage orchestration, scheduler
    ports/                 # interfaces only
    adapters/
      dicom/               # read/normalize DICOM
      segmentation/        # TotalSeg/native wrappers
      graph/               # centerline and PTL features
      labeling/            # IPGN/PTL and manual label adapter
      territories/         # reconstruction candidates
      oncology/            # lesion and margin geometry
      export/              # DICOM SEG/NRRD/STL/report adapters
      cpu/                 # CPU native + ONNX
      amd/                 # GPU provider probe + ONNX adapter
    infrastructure/        # atomic files, jobs, hashes, logging, Windows
  distribution/            # packaging design, no model weights in Git
  tests/                   # geometry, contracts, fake AI, integration, E2E
  benchmarks/              # benchmark protocol & approved evidence only
```

## Các cấp granularity
- **File**: chức năng tương đối độc lập, tên action/subject, không quá nhiều trạng thái.
- **Package/module**: 3–12 file cùng bounded context; `__init__` xuất API tối thiểu.
- **Capability**: nhóm module và một contract version rõ, có owner.
- **Worker process**: ranh giới bộ nhớ/driver, không đồng nghĩa một process mỗi file.

## Quy tắc chủ sở hữu
`Geometry` + `Ontology` + `ReviewState` là **protected core**: thay đổi phải được 2 người review (software + domain). GUI và speed adapters thay độc lập nhưng chỉ có quyền gọi contract, không ghi giá trị clinical verification.

## Cơ chế từ chối merge
Không merge nếu thiếu test âm tính, thiếu source/weight hash, không khóa version, data format mơ hồ, không có benchmark quality khi optimize, dùng `shell=True` với đầu vào người dùng, hoặc dùng file xóa nhầm vault khi uninstall.

**Chi tiết từng file dự kiến nằm tại `catalogs/MODULE_CATALOG.csv`; mục `line_budget` là planning cap và được sửa qua ADR trước khi coding.**
