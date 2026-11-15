# 06 — Chiến lược xử lý ảnh siêu nhanh, không hy sinh nhánh mạch

## Hai tầng xử lý độc lập
**Preview:** ưu tiên TTFI/TTF3D, có thể dùng mask thô/low-LOD mesh từ segmentation hợp lệ. Preview dán nhãn `PREVIEW — NOT FOR PLANNING`. **Detailed:** giữ spacing/ROI native đã kiểm định, full-resolution masks, graph, label, territory + quality. Không suy luận nhánh nhỏ từ hình preview.

## Chuỗi A/V/B
Load selected DICOM một lần → geometry validated canonical CT → lấy vùng phổi để giảm không gian ngoài ngực (crop có halo và bảo toàn hilum) → inference `lung_vessels` **một lần** để tạo artery/vein/airway/wall → validate shape/affine → lưu mask gốc immutable → tạo connected components/skeleton/centerline độc lập, có QA topology → branch labeling. Không chạy model riêng 3 lần cho cùng task bốn lớp.

## Lobe segmentation
Chạy task lobe riêng (model tổng hoặc pretrained đã xác minh đúng 5 nhãn); không nhầm `lung_vessels` với segmentation 5 thùy. Khi crop song song với lung_vessels, dùng cùng canonical transforms nhưng không đè lên source.

## Tối ưu theo thứ tự rủi ro thấp → cao
1. Tránh decode DICOM nhiều lần, tránh copy 3D arrays giữa tiến trình.
2. Cache kết quả theo `(source hash, affine, model/checkpoint hash, params, code revision)`; kết quả hiển thị không thay đổi segmentation.
3. Reuse TotalSeg mask, chạy song song graph per-class nếu tài nguyên cho phép.
4. Tăng tốc mesh và view bằng LOD, chỉ hiển thị structures trong ROI, incremental update.
5. ROI native-resolution và overlapped tiles có halo, QA boundary seams, giữ vessel root nằm trong vùng khảo sát; tuyệt đối không crop mất hilum/segment target.
6. Tối ưu memory layout, dtypes và lazy loads; tránh duplicate CT full-volume trong Python+Slicer cùng lúc nếu profile không đủ RAM.
7. ONNX CPU khi model support; quantize INT8 chỉ sau phép thử *small-branch* không giảm hiệu năng có ý nghĩa.
8. AMD GPU chỉ khi provider realmente chạy kernel trên GPU và có cải thiện paired end-to-end latency/quality.

## Đồng bộ vs song song
Độc lập: DICOM metadata QA trên series khác nhau (không phải pixels PHI) có thể chạy song song; A/V/B graph instances sau segmentation; mesh preview sau mask đủ; lesion manual/UI song song với đặt nhãn; source/lobe segmentation song song **chỉ ở cấu hình có RAM đo đủ**. Không song song: graph phụ thuộc mask; territory phụ thuộc lobes và branch identities đã review/override; plan phụ thuộc lesion/territory; export reviewed plan phụ thuộc review current.

## Parallelism guardrails
- Tránh nested over-subscription OpenMP/ITK/BLAS/PyTorch/ONNX; một scheduler cấp CPU thread tokens.
- DirectML session: `ORT_SEQUENTIAL`, `enable_mem_pattern=false`, không gọi `Run` nhiều luồng trên cùng session.
- GPU shared UMA không phải RAM cộng thêm; tải mô hình đồng thời có thể tăng paging.
- Không spawn/kill worker liên tục: amortize initialization nhưng giải phóng tensor và session khi vượt threshold.

## Năm lỗi ảnh đặc biệt
Disconnected 1-voxel distal branch; PA/PV touching same slice; false bridge crossing; hole/gap after resampling; mask tạo mesh đẹp nhưng source mask sai. Từng lỗi có quality flag, CT-side locator, phép thử phantom.
