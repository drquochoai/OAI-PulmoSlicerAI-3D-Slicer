# PulmoSlicer AI v2.0 — Software Engineering Blueprint (DESIGN ONLY)

**Ngày:** 15/11/2026. **Dành cho:** kỹ sư phần mềm, AI coding agents, chuyên gia CT/phẫu thuật và QA. **Không có mã nguồn trong gói.**

## Tải về và đọc theo thứ tự
Bắt đầu với [`00_START_HERE.md`](00_START_HERE.md), tiếp theo là [`01_PRODUCT_CHARTER.md`](01_PRODUCT_CHARTER.md), [`02_ARCHITECTURE.md`](02_ARCHITECTURE.md), [`03_MODULAR_CODING_STANDARD.md`](03_MODULAR_CODING_STANDARD.md). Đọc file `catalogs/MODULE_CATALOG.csv` để biết module/file nhỏ nào cần viết trong tương lai. Các workorder nằm ở `workorders/`.

## Kế hoạch xây dựng
**G0 Foundation → G1 DICOM/5 lobes/A-V-B → G2 PTL original+Graph parity → G3 Anatomical review → G4 Territory/lesion/plan → G5 CPU/AMD performance → G6 Windows installer/SEG export → G7 Clinical study validation.** Có thể phát triển các việc độc lập song song, nhưng merge theo gate và contracts.

## 7 mô hình AI không có nghĩa cần 7 models nạp cùng lúc
1) A/V/B segmentation, 2) 5-lobe segmentation, 3) bronchial labeling, 4) artery labeling, 5) vein labeling = core roles; 6) territory model, 7) lesion model = optional/experimental roles. Runtime phải có manual/degraded pathway nếu model không đạt điều kiện. Data như BronAtlas/AirRC/HiPaS không phải module cài ở bệnh viện.

## Nội dung từng tài liệu
| File | Vai trò |
|---|---|
| `00_START_HERE` | 10 quy tắc không thể bỏ |
| `01_PRODUCT_CHARTER` | intended use, out-of-scope, personas, outcomes |
| `02_ARCHITECTURE` | 3D Slicer UI, domain, isolated engines, DAG |
| `03_MODULAR_CODING_STANDARD` | quy chuẩn file nhỏ, SOLID, dependency policy |
| `04_CONTRACTS_AND_VERSIONING` | contracts, geometry, revision, cache, states |
| `05_DICOM_GEOMETRY` | DICOM input, LPS/RAS, HU, SEG references |
| `06_IMAGING_PIPELINE` | xử lý ảnh và 3D nhanh mà giữ nhánh nhỏ |
| `07_MODELS_AND_DATA` | AI model roles, datasets, license, runtime |
| `08_PTL_GRAPH_ADAPTER` | PTL repro + graph parity + instance mapping |
| `09_SURGICAL_PLANNING` | territory, tumor, CT estimate, surgeon review |
| `10_PERFORMANCE_CPU_AMD` | 16/32/64GB, GPU AMD optional, benchmark |
| `11_SCHEDULER_STORAGE` | DAG scheduler, atomic cache, resume |
| `12_SLICER_UX` | step-by-step UI và controls |
| `13_SECURITY_PRIVACY` | patient vault, PHI, supply chain |
| `14_WINDOWS_DELIVERY` | extension package + offline engine installer |
| `15_TEST_STRATEGY` | từ design test tới Windows/clinical validation |
| `16_STANDARDS_AND_QUALITY` | IEC/ISO/NIST/DICOM alignment |
| `17_AGENT_WORK_ORDERS` | agent contract, merge rules, evidence |
| `18_GATES_AND_ACCEPTANCE` | G0–G7 và điểm dừng |
| `19_DECISIONS_AND_OPEN_ITEMS` | ADR và unresolved research |
| `20_GLOSSARY` | từ vựng chung |
| `21_DATASET_MODEL_DUE_DILIGENCE` | dữ liệu/labels/overlap/legal |
| `22_BENCHMARK_PROTOCOL` | paired CPU/AMD evidence |
| `23_FAILURE_INJECTION` | crash, paging, missing model, stale |
| `24_REVIEW_AND_GOVERNANCE` | code review, QA, change control |
| `25_HANDOFF_TEMPLATE` | biên bản tiếp nhận task |
| `26_AUDIT_NOTES` | sửa so với v1.3 |

| `27_PHASED_BUILD_PLAN` | lộ trình lát cắt nhỏ, không phải làm 94 modules cùng lúc |
| `28_COPY_TO_AGENT_FIRST_MESSAGE` | lời giao nhiệm vụ agent và cách làm bằng chứng |

| `29_SLICER_EXTENSION_PACKAGING_BLUEPRINT` | cách Slicer nhận extension, 3 pack và cài viện |

## Các bảng máy-đọc-được
`MODULE_CATALOG.csv`: modules/file tương lai, `PORT_CONTRACT_CATALOG.csv`: interface → provider/consumer, `MODEL_PACK_PLAN.csv`: 7 role packs, `TASK_BACKLOG.csv`: đầu việc, `TEST_MATRIX.csv`: kiểm thử **chưa chạy**, `RISK_REGISTER.csv`: FMEA sơ bộ, `REQUIREMENTS.csv`, `REQUIREMENTS_TRACEABILITY.csv`, `SOURCE_REGISTER.csv`, `RELEASE_CHECKLIST.csv`.

## Danh sách việc đầu tiên cho người mới
**WO-00** nguồn/OS/versions/giấy phép; **WO-01** DICOM geometry; **WO-02** TotalSeg A/V/B; **WO-03** lobe; **WO-04** PTL author original; **WO-05** graph parity. Không vượt G2 bằng cách chỉ làm GUI 3D. Mỗi workorder có checklist và output evidence.

## Điểm chưa thể kết luận
Không có kiểm chứng hiệu năng 32GB, không có benchmark GPU Radeon, PTL graph compatibility chưa chứng minh và ImPulSe chưa có xác nhận lâm sàng. **Phần mềm chưa tồn tại, hồ sơ không dùng để ra quyết định mổ.**
