# 21 — Dataset/model acquisition: quy trình kiểm tra thay vì tải bừa

## Không cho rằng tất cả dữ liệu độc lập
AirRC gồm 254 CT lấy từ LUNA16; một dataset khác có thể cùng nguồn. BronAtlas có 100 CT 20 nhãn phế quản (10 phải, 8 trái, MAIN, ABN). PTL công bố 799 subjects binary A/V/B with processed graphs và pretrained IPGN. Lung3D thiên về shape-based segment reconstruction, không phải hàng trăm CT độc lập. HiPaS có subset khoảng 250 chest CT A/V annotations nhưng chuẩn hóa dữ liệu; cần đọc phạm vi labels/độ phủ nhánh. Đối chiếu ảnh duplicate bằng hash và image similarity, không chia train/test theo tên file.

## Protocol đánh giá nguồn
1. **Identity:** publisher, DOI, accession version, official URL, latest commit; tên dataset tránh trùng.
2. **License:** dataset, pretrained weights, source code, ảnh CT gốc, model derivative, redistribution riêng.
3. **CT geometry:** raw DICOM? NIfTI? NPZ normalized? spacing, orientation, rescale/HU, FoR preserved?
4. **Labels:** semantic A/V/B vs named branch vs lobe vs territory vs vessel intra/interseg; full tree vs partial; one lung vs both.
5. **Population:** CT contrast phase, slice thickness, cancer/healthy, scanners, ethnicity/sites and sampling biases, quality of annotation, expert consensus.
6. **Splits:** patient-level, hospital-level, benchmark-source level; deduplicate and blacklist overlap sources.
7. **Build:** does original code reproduce author metric using original fixture? Were author checkpoints downloaded and hashed? Are custom CUDA kernels needed?
8. **Release:** external metric and qualitative error review; declare unsupported domain. If any answer absent, `OPEN` not assumed OK.

## Bộ đánh giá nguồn dữ liệu
Nguồn open không bảo đảm đủ accuracy cho surgery planning. Nếu thiếu nhãn tĩnh mạch liên phân thùy/vascular branch instance, phải thu thập gold standard lâm sàng riêng có giấy phép, review độc lập và protocol; tránh pseudo-label AI-to-AI tự khuếch đại lỗi.

## Quản lý dữ liệu không huấn luyện trên laptop bệnh viện
Source datasets đặt trong `research_data` riêng có access control, không copy vào offline installer. Chỉ export checkpoint approved, ontology, class map và model cards. Nếu dataset buộc sử dụng trong viện theo restricted license, require data-use agreement and approval.
