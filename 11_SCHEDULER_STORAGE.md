# 11 — Scheduler, resumability, cache, storage và lỗi

## Local workflow engine
DAG nodes giữ `state` riêng; không dùng DB server. Chỉ định file manifest/case stage có schema version, lock file theo PID/job ID và lease timeout. Single writer cho mỗi stage, artifact result atomic. Multiple readers chỉ đọc artifacts đã validate. Không dùng Redis, Docker hoặc cloud làm yêu cầu cài tại bệnh viện.

## Stage state machine
`QUEUED → ADMITTED → RUNNING → WRITING → VALIDATING → COMPLETE`. `BLOCKED_DEPENDENCY`, `BLOCKED_RESOURCE`, `BLOCKED_LICENSE`, `FAILED_RETRYABLE`, `FAILED_FATAL`, `CANCELLED`, `STALE` phân biệt rõ. User cancel → worker process group termination có timeout và artifact incomplete bị cô lập, không để `COMPLETE` giả.

## Phân luồng thông minh
- Tác vụ heavy (TotalSeg A/V/B, lobe, high-res territory) cùng lúc tối đa 1 theo default STANDARD. Light (graph/QC/mesh) chạy cùng nhau khi token đủ.
- Resource tokens: RAM_peak_measured, CPU_threads, GPU_session, IO_MBps, UI_reserve; không tính riêng RAM GPU UMA như ngân sách độc lập.
- Stage priority: foreground preview, user-requested ROI > background enrichment; ưu tiên interactive và huỷ task cũ không còn cần thiết.
- Worker pools: giới hạn 1 CPU heavy worker, 0/1 GPU worker; không tạo 7 python processes/7 model copies trên máy 16/32 GB.
- DAG incremental invalidation dựa trên digest dependencies và code/model/params. UI render chỉ đổi camera/opacity giữ cache.

## Disk space và data retention
Path case riêng có ACL: `source/`, `derived/`, `jobs/`, `revisions/`, `exports/`, `audit/`, `trash_quarantine/`. Raw DICOM immutable; không thay UID source. Cần storage quota per case, chống đầy disk, cleanup theo LRU **chỉ dữ liệu recomputable chưa duyệt**, confirmation trước xóa dữ liệu nghiên cứu. Cài/uninstall không xóa case vault.

## Crash recovery
Sau lỗi/khởi động lại: scan completed manifests, verify sha, detect `.partial`, giữ nguyên reviewed revision, stage còn lỗi cho retry; không rerun metadata/segmentation nếu exact inputs unchanged. Fail closed với corrupt hash. Logs sanitized có stable error code và action button như `Retry stage`, `Open issue report`, `View CT coordinate issue`, nhưng UI action phải thực sự có handler.

## Khả năng truy vết/phiên bản
Model update hoặc code update không tự overwrite plan cũ; phân nhánh case revisions, history diff nhãn và ROI, reviewer provenance. Hash data + affine + preprocessing + checkpoint + version + backend precision. Timeout, stale locks và rerun behavior phải test trên Windows.

## Phép thử lỗi bắt buộc
Mất điện sau 80% writes; remove temp file; disk full; SHA mismatch; repeated job submission; duplicate case IDs; source file moved; stage cancellation while worker child running; stale review after lesion edit; no permissions; Unicode paths; long Windows paths; antivirus lock; simultaneous user open. Phải khôi phục về trạng thái nhất quán, không xóa ca.
