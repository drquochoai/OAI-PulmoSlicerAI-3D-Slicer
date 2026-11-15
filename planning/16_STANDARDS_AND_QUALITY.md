# 16 — International quality system references, không tự tuyên bố chứng nhận

## Các chuẩn làm định hướng
- **IEC 62304:2006 + AMD1:2015** — vòng đời software thiết bị y tế: kế hoạch, yêu cầu, thiết kế, tích hợp, xác minh, maintain, problem resolution; nếu sản phẩm nằm phạm vi điều chỉnh cần xác định safety class theo quy trình có thẩm quyền.
- **ISO 14971:2019** — risk management trong toàn vòng đời, từ hazard → hazardous situation → harm, biện pháp giảm thiểu, residual risk, postmarket signal.
- **IEC 62366-1:2015 + AMD1:2020** — usability engineering giảm use error; check cảnh báo, nhầm màu, nhầm series, người dùng bấm xác nhận.
- **ISO 13485:2016** — tham chiếu QMS tổ chức phát triển/phát hành thiết bị y tế (nếu áp dụng).
- **ISO/IEC 25010:2023** — mô hình chất lượng phần mềm: performance, reliability, security, maintainability, portability và yếu tố khác.
- **NIST AI RMF 1.0** — hướng quản trị AI, đo độ tin cậy và quản lý rủi ro; tự nguyện, không thay thế quy định pháp lý.
- **DICOM PS3.3 Segmentation IOD** — SEG metadata, nguồn ảnh tham chiếu, Frame of Reference.

Tài liệu chuẩn có bản quyền: chỉ dẫn URL chính thức, không sao chép tiêu chuẩn toàn văn. Đây là **alignment plan**, KHÔNG chứng minh sản phẩm đã chứng nhận hoặc tuân thủ đầy đủ.

## Hồ sơ vòng đời sẽ sinh ra trong lúc coding
SRS requirements traceability; architecture/SDD; SOUP/OTS inventory; source and model SBOM; test and verification reports; cybersecurity assessment; FMEA and risk controls; training data provenance; usability observations; anomaly register; deployment/rollback and complaint handling; change impact analysis; design history. Phần tạo ra trong tương lai phải có người duyệt.

## Phân vai kiểm soát
Tech lead chịu API/architecture, clinical lead chịu anatomy/review/clinical thresholds, QA lead chịu acceptance evidence, security lead chịu privacy/installer, MLOps lead chịu model cards/data leakage; reviewer khác coder ở critical geometry/clinical safety.

## Risk control priority
Design out the error > automated detection > visible warning/instruction. Không dùng disclaimer làm kiểm soát chính khi có thể phát hiện lỗi geometry/hazard bằng phần mềm.

## Regulatory scope
Mục đích ban đầu là nghiên cứu và hỗ trợ quan sát, chưa có tuyên bố thiết bị y tế đã được phép dùng lâm sàng. Quyền dùng CT bệnh viện, trách nhiệm sản xuất/đăng ký phần mềm như trang thiết bị y tế, bảo vệ dữ liệu cá nhân phải được pháp chế và cơ sở y tế xác minh trước bất kỳ triển khai thực tế nào.
