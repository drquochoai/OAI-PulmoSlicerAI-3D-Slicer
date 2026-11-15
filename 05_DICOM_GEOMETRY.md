# 05 — DICOM, coordinate safety, provenance

## Chọn ảnh
Chỉ nhận đúng selected *CT SeriesInstanceUID* và SOPInstanceUID set. Tạo bảng series: acquisition datetime, contrast metadata (nếu có), slice thickness, spacing, convolution kernel, reconstruction series, study/series IDs (chỉ vault), FoR UID, missing slice count, spacing variance, pixel data consistency; không suy đoán có thuốc chỉ từ tên series. Khi nhiều series, bác sĩ phải chọn rõ.

## QA trước khi inference
- Validate SOP UID unique, transfer syntax đọc được, pixel type, rescale slope/intercept; HU sau transform hợp lý, không giả định tất cả DICOM trực tiếp HU.
- Xác thực Rows/Columns, PixelSpacing, ImageOrientationPatient, ImagePositionPatient; tính normal và projected z, kiểm tra gaps/overlaps, duplicate, gantry tilt, variable spacing.
- Kiểm tra đa frame Enhanced CT khác single-frame classic; metadata mỗi frame; không ghép trộn các acquisition / phase.
- Kiểm tra FoR UID, vùng phủ phổi, hình học oblique, ảnh lật/hướng lệch; 3D từ dữ liệu thiếu chỗ phải có cảnh báo.
- Chuẩn hóa IJK→LPS (mm) một lần, lưu biến đổi *thuận và nghịch* và toàn bộ lịch sử resampling. Kiểm thử RAS↔LPS với phantoms bất đối xứng.
- Native geometry vẫn phải lưu bất biến; downsample preview không dùng làm measurement.
- Với CT kém chất lượng (lát dày, motion, atelectasis, noncontrast khiến A/V separation kém): `INPUT_LIMITED`, giới hạn AI auto-name, không giấu lỗi.

## Gốc dữ liệu và an toàn
`case_id` random; PHI nằm trong case vault ACL riêng, các manifest từ công cụ AI không chứa họ tên, MRN, UID nhận dạng trừ protected source manifest. Không tự xóa metadata trong DICOM gốc để rồi mất FoR và reference; de-identify bằng quy trình có mapping bảo vệ khi tạo bộ nghiên cứu.

## DICOM SEG xuất ra
Theo DICOM PS3.3 Segmentation IOD, dữ liệu SEG phải tham chiếu ảnh nguồn, cùng Frame of Reference khi có FoR. **Không bắt buộc có cùng pixel spacing/grid nếu được mô tả đúng theo chuẩn.** Cần test segment labels/codes, spatial transforms, referenced SOPs, geometry, identity, xem lại trong Slicer và một DICOM reader độc lập. STL không thay thế DICOM SEG và không chứa đủ semantics/provenance.

## Phantom tests bắt buộc
Hình bất đối xứng có marker left/right; 3 orientations axial/sagittal/oblique; anisotropic spacing; mirrored z order; missing middle slice; duplicate SOPs; nonunit slope/intercept; multi-series same folder; negative dimension; multi-frame; FoR mismatch; roundtrip mask volume↔Slicer↔DICOM SEG với tolerance định trước.

## Gate
Không vượt G1 nếu một phantom bị đảo trái–phải, mất frame, sai đơn vị mm hoặc SEG thiếu references; không được sửa bằng cách đảo trục bằng tay khi không có bằng chứng geometry.
