# 08 — PTL/IPGN, graph preparation, branch naming

## Đây là điểm chặn kỹ thuật lớn nhất
PTL sử dụng biểu diễn point–graph/implicit fields; `lung_vessels` cung cấp semantic voxel mask, **không** phải bộ graph/tensor sẵn sàng. Không được giả định PTL tự đặt tên từng mesh branch. Cần kiểm tra class/instance semantics thực sự của checkpoint trước.

## Các gate chi tiết
- **PTL-A Original reproduction:** clone repo nguồn và pin commit, review specs và loader (có thể đường dẫn/requirements Linux/CUDA), obtain checkpoint author, run 1 case original airway, artery, vein; đối chiếu output với author reference. Thiếu author expected result → PARTIAL.
- **PTL-B Graph parity:** với fixture nguồn, tạo graph từ binary mask; đối chiếu node count, edge count, root(s), degree distribution, physical coords, `pos`, `x` feature ordering, units, normalization, edge index orientation, sampling, intermediate tensors. Tolerance pre-register. **Một sai lệch quan trọng → BLOCKED**.
- **PTL-C Branch-instance extraction:** từ output class/point field trích ra *named individual segments*, giải quyết phân đoạn nhánh chung, nhánh giao cắt, multi-root PV; map ontology và lưu CT locator. Không nối mạch chỉ vì gần nhau.
- **PTL-D Transfer validation:** tập CT ngoài nguồn PTL, do 2 người đọc độc lập; đo exact branch identity, wrong artery↔vein, missing critical branch, patient-level complete accuracy, variant, invalid abstain.

## Data semantics đặc biệt
`BranchInstance` phải có stable ID, parent IDs list (không áp mô hình một gốc cho PV nếu không phù hợp), child IDs, centerline, junctions, source label, confidence, status `UNKNOWN/VARIANT` và link tới mask. Nhiều cây thuộc cùng một system có thể thành forest; các nhánh PV intersegmental không nhất thiết đồng bộ 1:1 với các nhánh phế quản.

## Failed case UX
Nếu PTL unavailable/failed: vẫn hiển thị artery/vein/bronchial semantic masks; bật branch editing thủ công; gán manual label overlay có provenance; không đi tiếp territory có yêu cầu nhánh chưa được review, trừ khi use case cho phép ước tính giới hạn với cảnh báo.

## Dữ liệu BronAtlas
Chủ yếu dành cho train/validate phế quản; mã nhãn có các nhánh ghép như LB1+2, LB7+8 và bất thường. Không lấy BronAtlas làm ground truth cho tự động đặt tên động mạch/tĩnh mạch. Sử dụng split theo patient/source và kiểm tra overlaps với PTL/LIDC.

## Phép thử bắt buộc
Branch Y; crossed without intersection; two roots; tortuous vessel; disconnected distal; left-lung fusion; pulmonary vein anomalous drainage; name ambiguity; one-voxel bridge; swap RAS/LPS; graph parity negative case; author-original exact reproducibility; patient-level holdout. Mỗi lỗi phải hiển thị vị trí trên CT, không chỉ hiện danh sách error.
