# PulmoSlicer AI

Research-only 3D Slicer extension for CT-aligned pulmonary anatomy review. The
implementation follows the gate and vertical-slice plan in `planning/`.

Current implementation status: **S0–S5 partial; PTL A/B/V regional tree labels
are experimental and engineering work remains in progress**. See
[`docs/STATUS.md`](docs/STATUS.md). No clinical-use or clinical-accuracy claim
is made.

## Development check

```powershell
python -m unittest discover -s tests -v
```

The Slicer entry point remains thin. PTL dependencies/checkpoints are installed
into an application-local runtime on first use and are not redistributed in the
extension ZIP.

## Chạy trong 3D Slicer

Xem hướng dẫn tiếng Việt tại
[`docs/HUONG_DAN_CAI_DAT_VA_CHAY_SLICER.md`](docs/HUONG_DAN_CAI_DAT_VA_CHAY_SLICER.md).
Với đường dẫn mặc định của máy phát triển:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Run-PulmoSlicerAI.ps1
```

## Gói ZIP cho Extensions Manager

Tạo gói cài cho Slicer 5.12.4 build 34645:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Build-SlicerExtensionZip.ps1
```

Sau đó trong Slicer chọn **View → Extensions Manager → Install from file...**
và chọn ZIP được tạo trong `dist/`. TotalSegmentator phải được cài trước.

Bản `2026.11.16.10` có one-click lựa chọn `None`, nguồn A/V/B hoặc PTL từng hệ
A/B/V, cây ẩn/hiện Right/Left → lobe → region → system, tự chọn backend có kiểm
chứng, surface preview nhanh/tái tạo mượt, progress/resource panel và PHI-safe JSONL
logs. Performance panel giữ stride 1 cho mô hình 3D và cho phép chọn resource
policy, CPU thread target cùng worker resampling/saving thật của TotalSegmentator.
Trình xuất HTML all-in-one chạy xử lý mesh nặng ở luồng nền, báo tiến độ theo
cấu trúc/công đoạn và cho phép hủy mà không sửa segmentation gốc.
Xem kiểm toán giới hạn A/B/V segmental labels tại
[`docs/PERFORMANCE_AND_ONE_CLICK_AUDIT.md`](docs/PERFORMANCE_AND_ONE_CLICK_AUDIT.md).

