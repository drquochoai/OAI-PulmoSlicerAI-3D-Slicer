# 09 — Anatomy, territory và surgical planning nghiên cứu

## Ontology (do clinical domain owner phê duyệt)
- Phổi phải: RUL/RML/RLL; phổi trái: LUL/LLL; có lingula S4/S5. Bộ mã hỗ trợ thùy/phân thùy liên quan, fused bronchi (ví dụ B1+2, B7+8), V theo biến thể đổ về, subsegments và unknown.
- Branch IDs tách khỏi *display name* và *model class index*. `A1` không có nghĩa chỉ một ống duy nhất ở mọi cá thể; các nhánh chung hoặc biến thể được phép nhiều instance hoặc nhãn không chắc chắn.
- Graph airway/PA/PV có lineage khác nhau; không ép nối PV thành tree 1 root.

## Territory estimation không phải ground truth phẫu thuật
Đề xuất baseline hình học theo *airway-guided* và *artery-guided* với constraint lobe và vessel centerline, plus uncertainty; các mô hình như ImPulSe2 chỉ được đưa vào sau repro + calibration. Luôn lưu method, training domain, CT protocol và map vùng bất đồng. Tĩnh mạch liên phân thùy hỗ trợ ranh giới nhưng không được gọi là ranh giới nhìn thấy trực tiếp trong CT.

## Lesion workflow
Manual 2D/3D ROI trước; optional AI nodule segmentation khi có model được phê duyệt; lesion UID, multiple lesions, manual edits, solidity/ground-glass là metadata người đọc xác nhận (không tự giả phân loại), source CT. Chỉ bác sĩ chốt lựa chọn vùng dự kiến cắt.

## Plan candidates
Chọn một hay nhiều phân thùy ước tính, candidate resection volume, cutting boundary mask, đánh dấu bronchial/PA/PV branches dự kiến liên quan (review required), cấu trúc cần bảo tồn, lesion overlay, khoảng cách Euclidean/shortest distance giả định từ tumor boundary đến proposed cut surface, volume ratio (ước lượng CT). `margin_estimated_ct` được gắn disclaimer **không phải bệnh phẩm thực tế**; tránh gọi “margin đạt chuẩn” chỉ từ CT.

## Human review gates
Trước khi export report có dấu **reviewed**, bác sĩ phải xác nhận ít nhất: đúng CT/side/lobe, lesion, các nhánh liên quan, uncertainty, plan selection, nguồn tham chiếu. Nếu đổi lesion hay mask/branch sau đó, chứng thực trước chuyển STALE và yêu cầu tái duyệt.

## Failure situations
CT không đủ tương phản để phân biệt PA/PV, nhánh mạch vượt phân thùy, mạch đến từ segment khác, u sát pleura/hilum, atelectasis/mass distortion, nhiều lesion, segment atlas không khớp -> `LIMITED/REVIEW_REQUIRED`; tuyệt đối không vẽ nhánh tưởng tượng hay auto-delete branch crossing.

## Tiêu chí kiểm định cuối
Đánh giá phân tách: territory Dice/surface error (có reference chuyên gia), branch-preservation decision agreement, critical branch omission, QA/abstain, reviewer time, confidence calibration; đối chiếu CT nguồn và trường hợp phẫu thuật khi có dữ liệu hợp pháp; đánh giá độc lập theo protocol và subgroup, không chỉ số Dice tổng thể.
