# 10 — CPU/AMD performance architecture, mục tiêu đo và lựa chọn backend

## Phân hạng cấu hình (mục tiêu nghiên cứu, CHƯA CERTIFIED)
| Profile | RAM | GPU | Quy tắc admission ban đầu | Đối tượng |
|---|---|---|---|---|
| `LITE` | 16 GB | không cần | một heavy worker, preview/manual, có quyền BLOCK detailed CT lớn | laptop nhỏ, research restricted |
| `STANDARD` | 32 GB | không cần | một heavy worker + một lightweight khi measured free commit đủ | máy bệnh viện mục tiêu |
| `PERFORMANCE` | 64 GB | AMD UMA tùy chọn | một heavy + 2 light (thử thêm khi benchmark) | ASUS phát triển và workstation |
| `EXTENDED` | >=96 GB | tùy chọn | profiling, không mở vô hạn | labs nghiên cứu |

32 GB/64 GB chỉ là **planning envelope**, chưa chứng minh tải được từng CT. Chứng nhận compatibility bằng peak memory thực nghiệm và p90 latency của workload đại diện.

## Đo hiệu năng đầu-cuối
`TTFI`, `TTF3D`, `TTLABEL`, `TTPLAN`, `TTREVIEW`, peak process/private bytes, system commit, GPU dedicated/shared memory, disk I/O, wall clock cold/warm, user-interface p95 response, number of reloads, cache hit rate, branch accuracy và quality regressions. Dùng ít nhất 10 ca đại diện trên mỗi profile khi khám phá; mở rộng holdout kiểm định và ghi CI nếu kết luận hiệu năng lâm sàng. Kết quả không thể so sánh khi model version/input crop thay đổi.

## Scheduler resource envelope
Đặt reserve động cho Windows+Slicer, user applications và biến động; stage estimate từ historical measured peak upper-bound; nếu không có profile, phân loại HIGH và cho chạy riêng; sampling RSS/commit/OS pagefault; stop/degrade khi approaching budget; ghi `RESOURCE_THROTTLED`, không để OS swap dài phút mới cảnh báo. “Có 64 GB RAM” không đồng nghĩa GPU chia sẻ cộng thêm 64 GB VRAM.

## Backend policy theo từng model
- `CPU_NATIVE` universal; `CPU_ONNX` optional; `AMD_ONNX_WINML` thử nghiệm; `DML` compatibility adapter; ROCm Windows development only khi **SKU driver+torch support verified**.
- PTL có PyTorch-Geometric/custom kernels: không hứa export ONNX; chỉ chuyển model nào vượt parity.
- DML: session `ORT_SEQUENTIAL`, disable memory pattern, **không concurrent Run cùng session**. Có thể chạy nhiều sessions nhưng phải benchmark contention và UMA paging.
- GPU có thể nhanh hơn cho CNN, chậm hơn cho small GNN/graph due host-device transfer; chọn backend theo measured p90+quality, không theo tên card.
- INT8/FP16: thử từng model trên native CT và tiny branches, không cấp mặc định.

## Image pipeline fast path
- Preview có hình sau khi mask hợp lệ nhỏ nhất sẵn sàng; mesh LOD dùng để xem.
- Detailed ROI có halo đủ, phải bao trùm hilar roots; native-detail theo vùng, blockwise overlap và kiểm seam.
- CPU thread pool giới hạn, tránh ITK/OpenMP/MKL/ORT/PyTorch oversubscription.
- CT format nguồn chỉ convert một lần, zero-copy/memmap *khi an toàn và tương thích*; không đưa volume qua Qt signals hay JSON.
- Show/hide branches bằng VTK actor caching; cập nhật camera/color không làm rerun model.

## Tiêu chí ưu tiên tối ưu
1) Không thay đổi tính đúng geometry; 2) không bỏ sót critical branches; 3) cải thiện p90 time-to-review; 4) giữ RAM trong quota; 5) không làm treo Slicer. **Không tối ưu bằng xóa đi các voxels nhánh nhỏ mà không có QA.**

## Bài benchmark đối chứng bắt buộc
Cùng bộ CT, cùng SHA model, cold vs warm, CPU vs AMD, max RSS, same preprocessing, native spacing, time per DAG node, kernel GPU thực sự dùng hay hidden CPU fallback, parity numerical + topology + branch label. Không cần NVIDIA/CUDA ở bất kỳ release tier nào.
