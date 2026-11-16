# Kiểm toán hiệu năng và mục tiêu một click

Ngày kiểm tra: 16/11/2026. Baseline: Slicer 5.12.4 build 34645,
TotalSegmentator 2.14.0, PyTorch 2.15.0+cpu.

## Kết luận ngắn

- Lựa chọn `Fast` trước đây **không có tác dụng** với task `lung_vessels` trong
  extension TotalSegmentator đang cài. Task chỉ công bố `normal`; logic tự đổi
  giá trị khác về `normal`. PulmoSlicer AI đã bỏ lựa chọn gây hiểu nhầm này.
- Nút một click luôn chạy năm thùy và chỉ chạy thêm phần người dùng chọn:
  `None`, nguồn A/V/B gộp, PTL B, PTL A, PTL V hoặc cả ba. Với PTL, task
  `lung_vessels` của TotalSegmentator vẫn tạo một lượt cả ba mask nguồn vì model
  này không có task con riêng; extension chỉ bỏ suy luận PTL và mesh của các hệ
  không chọn. Widget và cầu nối PTL–MRML đã qua smoke test bằng Slicer thật với
  dữ liệu tổng hợp.
- PTL đã được tích hợp ở mức **nghiên cứu/thử nghiệm**: 18 lớp vùng giải phẫu
  cộng lớp central/out-of-lung cho từng cây airway, artery và vein. Checkpoint
  được tải ở lần dùng đầu và kiểm tra SHA-256; weights không nằm trong ZIP.
- Mục tiêu segmentectomy hoàn chỉnh **chưa đạt** vì output hiện tại chỉ chia
  voxel của ba cây A/B/V. Chưa có thể tích nhu mô S1–S10 được giới hạn bởi thùy
  và tĩnh mạch liên phân thùy, cũng chưa có validation lâm sàng.
- TotalSegmentator được gọi với `interactive=False`: lựa chọn quality/backend đã
  chốt trước khi chạy, không còn hộp thoại Fast/Full-resolution chặn run không
  có người canh. GPU ưu tiên không khả dụng sẽ fallback tự động.
- Log UI giữ một dòng phần trăm đang chạy cho mỗi tác vụ con; JSONL vẫn giữ chuỗi
  telemetry đầy đủ phục vụ benchmark.

## Bằng chứng thời gian từ log hiện có

Log Slicer ngày 14/11/2026 ghi một run `lung_vessels` CPU:

| Stage | Quan sát |
|---|---:|
| Tổng thời gian từ `Processing started` | 493,81 giây |
| Download model task 117 | khoảng 27 giây, 230 MB |
| Download crop model | khoảng 7 giây, 135 MB |
| Rough crop 8/8 | khoảng 14 giây |
| Detailed inference 144/144 | khoảng 368 giây |
| `Predicted in` do TotalSegmentator báo | 379,56 giây |
| Resample detailed ROI | 8,83 giây |

Command thực tế chỉ có `--device cpu --ml --task lung_vessels`; không có
`--fast`. Dữ liệu định danh và đường dẫn nguồn không được chép vào báo cáo này.

## CPU và RAM

Máy có 24 logical CPU và 12 lõi vật lý. Mã TotalSegmentator 2.14 gọi
`torch.set_num_threads(multiprocessing.cpu_count())` khi chạy CPU, tức upstream
đã yêu cầu 24 logical thread. CPU Task Manager khoảng 50% có thể tương ứng 12
lõi vật lý đã bão hòa; không tự chứng minh còn có thể tăng tốc gấp đôi. Convolution
3D cũng có thể bị giới hạn bởi memory bandwidth, cache hoặc stage tuần tự. RAM
trống không phải tài nguyên cần phải lấp đầy.

UI mới cung cấp các policy Tự động, CPU khoảng 85%, trần RAM 85%, kết hợp và
Thủ công. Thread target được áp dụng trong một child-process wrapper cục bộ,
không sửa package TotalSegmentator đã cài. TotalSegmentator còn nhận đúng hai
tham số song song upstream hỗ trợ: `--nr_thr_resamp` và `--nr_thr_saving`.
Mặc định upstream tương ứng là 1 và 6. Chính mã 2.14 ghi chú rằng tăng
resampling lên 4 CPU có thể chậm hơn 1, vì vậy profile Tự động giữ 1.

Mỗi run ghi elapsed time, CPU hệ thống, RAM, stage, thread target, stride và số
worker vào JSONL. Chỉ đổi profile mặc định nếu nhiều warm-run cùng một CT cho
thấy nhanh hơn mà geometry, topology và segment output không thay đổi.

## Tại sao không bỏ lát 1, 3, 5, 7

DICOM series được ghép thành một thể tích 3D rồi TotalSegmentator chạy
sliding-window/patch inference; không phải xử lý độc lập từng ảnh 2D. Bỏ xen kẽ
lát cắt làm tăng slice spacing, thay đổi affine và có thể làm mất nhánh nhỏ hoặc
tạo đứt đoạn. Đây không phải fast path hợp lệ cho output segmentectomy.

Vì chỉ có một thể tích, không tồn tại queue “4 ảnh rồi tăng lên 5 ảnh” để bộ điều
khiển tự động mở rộng. Patch 3D do nnU-Net quản lý nội bộ và không thể thay đổi
số patch đang bay từ Slicer khi child process đã khởi động. Cố chạy nhiều chunk
độc lập có thể nhân RAM, tranh memory bandwidth và tạo đường nối giả ở biên.
Do đó extension hiển thị rõ `Stride 1` và không cung cấp lựa chọn bỏ lát gây sai.

Mục tiêu CPU 85% là best effort, không phải cam kết. RAM 85% được hiểu là trần
an toàn: profile này giảm worker ghi file; extension không cấp phát dữ liệu giả
chỉ để làm đầy RAM. Một hard memory cap có thể giết tiến trình trước khi kịp lưu
kết quả nên chưa được dùng.

Các hướng tối ưu được phép benchmark:

1. warm model cache, không tải/install lại;
2. cache NIfTI canonical và masks theo source/model hash;
3. benchmark 12 so với 24 thread, cold và warm;
4. không chạy A/V/B và lobes đồng thời trước khi đo memory-bandwidth contention;
5. nghiên cứu runtime ROCm Windows tách biệt cho Ryzen AI MAX+ 392, không thay
   PyTorch CPU đang hoạt động bên trong Slicer;
6. chỉ thử crop/blockwise/ONNX khi parity geometry, topology và nhánh nhỏ đạt.

## Kiểm toán nhãn giải phẫu

Ký hiệu đúng theo hệ:

- động mạch phổi: `A...`;
- phế quản: `B...`;
- tĩnh mạch phổi: `V...`.

Do đó `B1`, `B2`, `B3` không phải nhãn động mạch. Bên trái có các nhánh/vùng
gộp và biến thể; ontology phải hỗ trợ fused/variant/unknown, không ép mọi ca
thành 20 nhãn độc lập. Thuật ngữ segmentectomy còn yêu cầu territory nhu mô,
không chỉ chia cây động mạch.

Trạng thái hiện tại:

| Gate | Trạng thái |
|---|---|
| Mask airway/artery/vein gộp | IMPLEMENTED, cần review CT thực |
| Năm thùy | IMPLEMENTED, cần review CT thực |
| 3D closed surface | IMPLEMENTED sau validation output |
| A/B/V regional tree labels | EXPERIMENTAL — author fixture reproduced; native adapter và Slicer bridge PASS trên một fixture |
| Cây ẩn/hiện Right/Left → lobe → region → A/B/V/Lung | IMPLEMENTED; smoke test signal visibility PASS |
| Subject Hierarchy Right/Left → lobe → B/A/V/Lung | IMPLEMENTED; child-folder smoke test PASS |
| Territory nhu mô S1–S10 | NOT STARTED — phụ thuộc reviewed branch labels |
| End-to-end một click trên CT hợp pháp | NOT TESTED; automation mới dùng dữ liệu tổng hợp/fixture tác giả |

Không được đổi gate sang PASS chỉ vì giao diện có một nút.
