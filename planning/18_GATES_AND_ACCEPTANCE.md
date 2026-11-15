# 18 — Release gates, definition-of-done và điều kiện NO-GO

| Gate | Điều kiện PASS | NO-GO |
|---|---|---|
| G0: Design freeze | source/versions/security/requirements/contracts/module ownership đã duyệt | source weights/license mơ hồ; thiếu CT hợp pháp |
| G1: Slicer + CT | CT series đúng, HU+geometry phantom PASS, A/V/B/lobes masks reviewable, UI responsive | wrong left/right, missing FoR, CT bị trộn series |
| G2: PTL reproducibility | all 3 original-checkpoint author fixtures reproduced, graph parity field-by-field, branch extraction có provenance | chỉ exit code 0; incompatible tensor features |
| G3: Branch review | clinician có thể focus/edit/reject/unknown và audit; stale invalidation đúng | model được phép auto verify, missing variant/branch locators |
| G4: Territory/lesion/plan | lesion correct CT coords, method-specific territory, margin CT hypothetical, reviewer can compare/reject | mặt phẳng hiển thị như chắc chắn, forced plan when uncertain |
| G5: Performance | STABLE CPU on target profile, peak memory budget, no unacceptable quality regression, GPU measured parity | RAM paging thrash, fast mode mất critical branch |
| G6: Offline distribution | clean Win install/uninstall/rollback, no CUDA/network, SEG source references roundtrip | uninstall xóa bệnh án, no offline model bundle rights |
| G7: Clinical research | independent dataset + dual expert review, risk residual reviewed, regulator/intended-use reviewed | kết luận clinical safe từ Dice/QA kỹ thuật |

## Quy tắc kết luận
**Design ready**: đủ nguồn và specs nhưng chưa chạy thật. **Engineering proof**: software thực thi trên synthetic+authorized case theo acceptance. **Clinical research validated**: independent results; không tự gọi “medical-device cleared”. Mỗi gate có reviewer và ngày duyệt.

## QoS provisional thresholds phải đo, không giả PASS
UI p95 click-to-response mục tiêu thử nghiệm <250ms cho thao tác thông thường, không bao gồm tính toán; memory must stay under actual safe commit headroom, no swap storms; first preview cần benchmark baseline thay vì cam kết số phút. Critical anatomy error tolerance do clinical lead pre-register trước holdout, không đặt sau khi xem kết quả.

## Quy trình nhận hàng của lead
Với mỗi work order: verify source SHA, read changed module list, read negative test logs, run install/smoke, inspect output CT slices, review risk register, đánh dấu PASS có người ký. Nếu chỉ có mô tả, status NOT_RUN.
