# 20 — Glossary ngắn cho coding agent

- **A/V/B:** pulmonary arteries / veins / bronchial tree. A1/V1/B1 là anatomical branch names, không phải output layer index tự động.
- **AirRC, BronAtlas, HiPaS, Lung3D, PTL dataset:** bộ dữ liệu hoặc nguồn nghiên cứu, không phải các plugin Slicer bắt buộc phải cài.
- **PTL/IPGN:** thuật toán/checkpoints gán nhãn cây giải phẫu qua graph/point field; cần graph input parity.
- **ImPulSe:** phương pháp neural implicit/shape reconstruction vùng phân thùy, experimental integration.
- **DICOM SEG:** đối tượng DICOM phân đoạn có reference tới ảnh nguồn, không phải STL.
- **NRRD/NIfTI:** định dạng volume/mask, không thay thế raw DICOM provenance.
- **MRML/VTK:** hệ đối tượng ảnh và rendering Slicer; chỉ cập nhật trên main thread.
- **LPS/RAS/IJK:** coordinate frames (mm vs voxel indices). Đổi hệ trục sai có thể đảo trái/phải.
- **Graph parity:** so sánh graph tự tạo với graph tác giả PTL, gồm feature order/units/topology/normalization.
- **Branch instance:** đối tượng nhánh riêng có stable ID, gốc/con, tên và mask/centerline locator.
- **Uncertainty/abstain:** AI từ chối khẳng định khi ngoài phân bố hoặc ambiguous; tốt hơn tên sai tự tin.
- **ROI / native resolution / halo:** crop giải phẫu, giữ voxel/spacing phù hợp và đệm ở viền tránh bỏ sót nhánh.
- **LOD:** level of detail của mesh chỉ để render mượt, không được dùng làm geometry đo đạc.
- **UMA / shared VRAM:** bộ nhớ GPU tích hợp chia sẻ với RAM hệ thống; không tăng tổng RAM vật lý.
- **DirectML/WinML:** giải pháp inference dùng GPU Windows không CUDA; model hỗ trợ phụ thuộc operator.
- **SOUP/SBOM:** phần mềm nguồn ngoài/manifest phần mềm, có kiểm soát version and license.
- **Gate:** điểm chặn tiếp tục triển khai dựa trên evidence.
- **Design-only:** tài liệu đặc tả, không phải code có thể chạy.
