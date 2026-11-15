# 13 — Security, patient privacy, model supply chain

## Local-first/privacy by design
Không có Internet requirement trong runtime (sau chuẩn bị bundle). Không telemetry mặc định, không cloud sync, không auto-update ngoài thông báo; Windows local ACL cho case vault, minimum privilege. Không ghi PHI trong shell log, exception, screenshot CI, crash dump, user report. Để người dùng chọn share diagnostic log **đã loại PHI**; tool phải kiểm tra không còn protected tags trong filenames/path.

## Zero trust đối với source/model
- Repo URL, commit hash, release tag, author/publisher; download weights với SHA256; kiểm tra license code/data/weights riêng.
- Không tự chạy checkpoint pickle từ nguồn không tin cậy; sandbox nguồn bên thứ ba, dùng safe loading phù hợp khi có.
- Quyền phân phối phụ thuộc từng package/weights; OSS code ≠ quyền đóng gói mọi trọng số; source register phải có evidence.
- Software Bill of Materials (SBOM), phụ thuộc khóa version, audit CVE/SCA; cập nhật khẩn theo policy, có rollback.

## Threat scenarios
DICOM ác ý/hỏng; path traversal (`../`), symlink junction escape, zip bombs, embedded Unicode; command injection qua patient filename; DLL search hijacking trong installer; malicious model file; worker process mở network; unintentional PHI in metrics; overwriting data by uninstall; tampering with `REVIEWED_ACCEPTED` flag; review impersonation.

## Controls
Reject paths outside vault; no `shell=True`; sanitize ANSI/control chars; protected case manifest; immutable append-only signed/tamper-evident audit design (signing mechanism review trước coding); enforce main application as only issuer of clinician reviewer events with authenticated local identity; record time+actor+artifact hash; backup encryption plan; hospital IT policy for access and retention.

## Dữ liệu nghiên cứu
Có văn bản cho phép dữ liệu và quy trình ẩn danh trước khi dùng cho training / test / bug report; tách clinical private vault khỏi dev fixture. DICOM deidentification cần giữ geometry và tham chiếu pseudonymized; quản lý mapping gốc trong nơi được bảo vệ. License and consent matrix per dataset/site.

## Incident & recovery
Lưu data có backup; cập nhật rollback không xóa clinical data; security incident response (disable auto export, quarantine suspicious package, reverify checksums), retention schedule do bệnh viện duyệt.
