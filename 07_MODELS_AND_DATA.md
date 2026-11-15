# 07 — Model registry, training/reference data và clinical evidence

## Phân biệt rõ model, weights, dataset và algorithm
| Thành phần | Runtime cần tại viện | Nhiệm vụ | Ghi chú |
|---|---|---|---|
| TotalSegmentator `lung_vessels` | engine+checkpoint | 4 masks artery, vein, airway, wall | Model đã có; không tự đặt A1/V1/B1 |
| 5-lobe segmentation | verified checkpoint+task | RUL/RML/RLL/LUL/LLL | Có thể dùng task `total` chứa lobes, kiểm tra version class map |
| PTL/IPGN Airway | một model/checkpoint riêng | nhãn giải phẫu bronchial graph | Không cài PTL dataset trên máy viện |
| PTL/IPGN Artery | một model/checkpoint riêng | tên động mạch | Phụ thuộc adapter graph đúng |
| PTL/IPGN Vein | một model/checkpoint riêng | tên tĩnh mạch | Xử lý multiple ostia, vein plexus |
| ImPulSe2/territory candidate | ứng viên **chưa chốt** | dự đoán vùng phân thùy | Phải được tái lập và kiểm định; có baseline hình học độc lập |
| Lung lesion AI | **tùy chọn, chưa chọn** | hỗ trợ segmentation nốt u | Manual ROI luôn được phép |
| BronAtlas | không | dữ liệu huấn luyện/kiểm thử gán nhãn phế quản | không phải mô hình triển khai |
| PTL dataset 799 | không | source/processed graph cho reproducibility | không đồng nghĩa 799 CT raw độc lập |
| AirRC/HiPaS/Lung3D | không | training, external reference, shape priors | cần chống trùng nguồn, license matrix |

## Chính sách model registry
Mỗi model có `model_id`, publisher, upstream repo URL, exact Git SHA, checkpoint SHA256, task/classes, input tensor shape/dtype/spacing, preprocessing, output classes, affine, supported protocol, license code/weights/data, risk level, CPU backend tested, AMD backend tested, cold/warm latency, peak RAM, clinical external test status. `DEMO`, `REPRODUCED`, `ENGINE_VERIFIED`, `EXTERNALLY_VALIDATED`, `RELEASE_APPROVED` không được dùng thay thế nhau.

## Source acquisition / provenance
1. Download từ repo chính thức hoặc publisher; ghi URL/etag/date, SHA256; kiểm tra quyền redistribution.
2. Tài liệu tác giả là **giả thuyết tương thích**, chưa đủ xác nhận môi trường Windows CPU; đọc implementation, requirements, checkpoint loader.
3. Pin exact revision; không coi `main` là release fixed.
4. Run author-original fixture; output evidence riêng; sau đó mới chuyển CT mới.
5. Nếu dependency Linux/CUDA-only, isolation test patch có ADR; không buộc laptop chạy CUDA.
6. Xử lý checkpoint pickle một cách thận trọng; chỉ chạy nguồn tin cậy có kiểm soát.

## Train vs inference
Máy viện chỉ inference, không cài cả kho train. Máy ASUS 64 GB dành cho inference, QA, benchmark, GNN fine-tuning nhỏ nếu hợp lý; training 3D CNN full-res hàng trăm CT trên CPU không phải tiêu chí sản phẩm. Nếu cần huấn luyện GPU, có thể làm trong hạ tầng riêng, chuyển weights đã phê duyệt về CPU/AMD inference.

## No magic model count
Số **logical AI roles** dự kiến 5 core + 2 optional ≠ số quy trình nặng hoặc tổng số checkpoints thực tế. Một nhiệm vụ TotalSeg `total`/`lung_vessels` có thể chứa nhiều mạng; registry phải ghi số checkpoint và bộ nhớ thật. Không hứa 7 model đồng thời trong 32 GB.
