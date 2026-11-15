# 01 — Product charter, scope và use cases

## Intended use (giai đoạn nghiên cứu)
Công cụ xử lý CT ngực có hoặc không thuốc cản quang, giúp bác sĩ khám phá hình học giải phẫu; đối chiếu trên MPR CT nguồn; ghi nhận biến thể; dự đoán vùng phân thùy; chuẩn bị và thảo luận phương án cắt phổi. Các kết quả chuyên biệt mạch nhỏ và phân thùy yêu cầu điều kiện ảnh đủ chất lượng và xác nhận bởi phẫu thuật viên.

## Bốn kết quả chủ yếu
- **D1 / Anatomical 3D:** mask 3D của khí–phế quản, PA, PV, lobe và cấu trúc phụ được hiển thị có thể kiểm tra trên lát cắt.
- **D2 / Labeled branch atlas:** danh sách branch instance có tên, gốc/nối, vị trí CT, xác suất/khả năng không xác định và biến thể; không đơn giản chỉ là một màu cho cả động mạch.
- **D3 / Territory estimation:** vùng phân thùy **ước tính** (bronchial/arterial-guided); khác nhau giữa các phương pháp được bộc lộ.
- **D4 / Research surgical plan:** tổn thương do bác sĩ đặt hoặc AI hỗ trợ, chọn vùng dự kiến cắt, phân loại nhánh liên quan, đo khoảng cách CT giả định, báo cáo những yếu tố còn chưa xác nhận.

## Out of scope giai đoạn đầu
Không tự động khuyến nghị phương pháp mổ; không tính chắc chắn margin bệnh phẩm; không suy diễn viable perfusion/ventilation sau mổ; không hiển thị AR/phẫu thuật nội soi trực tiếp; không gửi PACS nếu chưa có quyền; không xử lý ảnh DICOM thiếu geometry bằng phép đo chính xác; không fine-tune 3D CNN trên laptop CPU như yêu cầu tối thiểu.

## Những lớp người dùng
- **Surgeon reviewer:** xác minh từng nhánh, sửa nhãn, duyệt kế hoạch, xem bất định.
- **Radiology reviewer:** kiểm tra chất lượng CT, alignment, mask, tổn thương.
- **Hospital technician:** cài, cập nhật, chẩn đoán lỗi và bảo trì không xem PHI.
- **Research engineer:** quản lý mô hình/dữ liệu/benchmark, không tự đánh dấu kết quả đã được bác sĩ xác minh.

## Success không chỉ là Dice
Đo tính đúng hình học, bỏ sót nhánh có ý nghĩa mổ, đặt tên đúng từng branch, nhầm A/PV, khả năng abstain, phát hiện biến thể, thời gian tới preview và tới kế hoạch có thể xem, thời gian bác sĩ hiệu chỉnh, độ ổn định offline, khả năng cài lại trên máy yếu.

## Kịch bản khó cần hỗ trợ
CT nhiều series/phase; CT không thuốc và CT có thuốc; thùy biến dạng xẹp phổi; khối u sát mạch; tràn dịch; vessel crossing không nối; gốc PV bất thường; B1+2, B7+8; phân thùy không điển hình; ảnh dày >1.5 mm; kích thước bệnh nhân lớn; thiếu RAM; khởi động lại giữa inference; cài offline vào tài khoản Windows không admin; nhiều revisions và bác sĩ khác nhau.

## Phân hạng chức năng theo chứng cứ
- `SUPPORTED`: đủ đầu vào, checkpoint đã qua test, nằm trong protocol đã kiểm định.
- `EXPERIMENTAL`: có kết quả nhưng chưa qua kiểm định ngoài; nhìn thấy cờ và hạn chế xuất.
- `UNAVAILABLE`: không có model/license/hardware; gợi ý chỉnh thủ công.
- `BLOCKED_INPUT`: CT không đủ điều kiện đo; chỉ preview hoặc từ chối.
