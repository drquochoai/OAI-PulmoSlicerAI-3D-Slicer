# 29 — Manifest và cấu trúc phát hành extension trên Windows (chỉ thiết kế)

## Cách Slicer nhận ra extension
Thiết kế một **thin scripted loadable module** entrypoint dự kiến `PulmoSlicerAI.py` (Module Catalog UI00) để Slicer đăng ký module, metadata, icon, widgets; file này không chứa TotalSeg, PTL, DICOM internals, VTK meshing. Module code thật nằm trong các package con được test riêng. Tạo `CMakeLists.txt`/extension descriptor `.s4ext` đúng quy trình của Slicer sau khi chốt exact stable Slicer version; **`.s4ext` là mô tả metadata chứ không là file installer tự chạy**. Gói extension cài qua Extensions Manager / Install from file hoặc bộ cài enterprise.

## Bốn tầng bản phát hành
1. **Slicer Stable** (người dùng cài riêng hoặc bộ cài chính thức được viện duyệt) — viewer Qt/VTK/ITK/MRML.
2. **PulmoSlicer extension package** — thin launcher + UI + Slicer bridges; tương thích một hoặc nhiều stable revisions được kiểm thử.
3. **PulmoAI CPU runtime** — isolated Python env, package frozen, safe worker entrypoint (IN00), CPU models; không chèn PyTorch vào Slicer Python.
4. **Optional AMD provider/model pack** — riêng và chỉ bật với driver/model đã benchmark; không cản CPU fallback.

## Release packs để máy viện cấu hình thấp
- **Lite (16GB, giới hạn):** extension UI, CPU engine, essential model pack, preview/manual, heavy task serialized và CT envelope rõ ràng.
- **Standard (32GB target):** mọi core feature đã được chứng minh trên profile, one heavy task, efficient cache.
- **Performance (64GB ASUS AMD):** như Standard plus optional WinML/DirectML model-specific acceleration, shared-memory budget monitor.

Một PC có thể chuyển profile mà không thay file của bệnh nhân. “Lite” không được hứa chạy đầy đủ chức năng cho CT quá lớn; mô tả `SUPPORTED / LIMITED / BLOCKED` dựa trên memory admission.

## Hospital installation UX mục tiêu
- Máy cài sẵn 3D Slicer → double-click offline `PulmoSlicerAI-Setup.exe` (chưa tạo) → tự phát hiện version, kiểm tra RAM/SSD/license/model bundle → cài extension+runtime+approved checkpoints → mở Slicer thấy module → chọn DICOM và dùng.
- Nếu Slicer khác version, hiển thị rõ version yêu cầu, **không âm thầm copy vào thư mục sai**.
- Nếu 16GB/không GPU, fallback CPU Lite; không yêu cầu CUDA hay tắt Defender.
- Model packs có source/version/weight SHA, EULA/license rights, checksums; tránh copy datasets huấn luyện vào viện.
- Uninstall/upgrade chỉ sửa application data, **không xóa source CT, project, audit hoặc exports**.

## Smoke tests phát hành tối thiểu
Extension load in Slicer; CPU worker subprocess start; synthetic DICOM right-left geometry; model registry and output class map; A/V/B masks shown; shutdown/resume; Windows offline; no-admin; Unicode; alternate supported Slicer version; old projects load unchanged; reviewer audit intact.

## Trước khi agent viết code cần xác minh
Official Slicer `ScriptedLoadableModule` template; extension packaging procedures; compatibility with embedded Python; Qt API; wheel availability for target CPU ISA; `SlicerTotalSegmentator` extension lessons; `totalseg_info` task classes; win32 process/ACL handling and model packs. Chỉ chốt setup implementation sau when source revision pinned.
