# 12 — 3D Slicer UX, interaction, surgical review

## One-screen primary workflow
Tabs: `1 Nhập CT` → `2 Dựng hình` → `3 Xem nhánh A/V/B` → `4 Phân thùy & U` → `5 Kế hoạch` → `6 Xác nhận & Xuất`. Không yêu cầu mở Command Prompt hoặc chọn 7 model thủ công. Tiếng Việt là mặc định, thuật ngữ chuyên môn bằng Anh/Latin có tooltip.

## Màn hình từng bước
1. **Import:** browse folder DICOM, series list có phase, slice thickness, notes/quality, nút chọn rõ; khi insufficient inputs, warning có cách sửa.
2. **Reconstruction:** 2D axial/coronal/sagittal+3D synchronized; tiến độ theo stage, thời gian đã đo (không ETA hư cấu), CPU/RAM live, Preview/Detailed, Stop/Pause/Resume.
3. **Branch:** cây hierarchy có search A1/B1/V1; click nhánh → focus CT 2D+3D; provenance AI vs manual, uncertainty badge, button accept/edit/reject, variants.
4. **Territory:** thể hiện phế quản-guided vs artery-guided, uncertainty/disagreement; 5 lobes toggle, vùng cắt proposed, intersegmental vein overlay.
5. **Lesion:** manual segmentation tools, multiple nodules, location/margin CT estimate; lesion edits invalidate plan có lý do.
6. **Report:** checklist clinician review; export segmentation/3D/report; không cho report `verified` nếu stale/blocked.

## UI performance engineering
Slicer Qt main thread phải responsive; worker nặng chạy ngoài; import preview tối thiểu, lazy VTK actors, LOD dynamic, trackball rotate, asynchronous progress; không tạo mọi 3D mesh full-resolution cùng lúc. Thao tác hide/show chỉ thay actor visibility, không rerun.

## Error classification với hành động thật
`MISSING_DICOM_TAG`, `AMBIGUOUS_SERIES`, `INVALID_GEOMETRY`, `INSUFFICIENT_CONTRAST`, `MODEL_MISSING`, `MODEL_LICENSE_BLOCKED`, `INSUFFICIENT_RAM`, `PTL_INCOMPATIBLE_GRAPH`, `GPU_PROVIDER_FAILED`, `STAGE_CANCELLED`, `INVALID_EXPORT_REFERENCES`, `STALE_REVIEW`. Mỗi error gồm `human_message`, `debug_code`, `safe_action`, link docs; nếu không có handler thì chỉ hiển thị hướng dẫn, không tạo nút vô tác dụng.

## Accessibility & surgical safety
Không chỉ dùng màu phân biệt động/tĩnh/phế quản; hỗ trợ text label, keyboard shortcut, zoom/focus, toggle opacity, rendering legend. Không để phế quản màu xanh và vein cùng sắc chỉ vì theme. Trên CT gốc đánh dấu confidence. Khóa nút xác nhận nếu source geometry sai; phải xác nhận bằng thao tác bác sĩ.

## Workflow acceptance demo
Một người dùng không biết Python phải mở Slicer, chọn CT, dựng 3D, tìm A2, sửa nhãn, chỉnh lesion, quan sát plan stale rồi tái duyệt và xuất báo cáo mà không dùng terminal. Đo số click, tỷ lệ lỗi chọn nhầm series, thời gian đến review, không giả định thành công chỉ vì GUI hiện cửa sổ.
