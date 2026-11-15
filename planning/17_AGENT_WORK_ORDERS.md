# 17 — Playbook giao việc coding agents, không phụ thuộc bối cảnh cuộc trò chuyện

## Agent luôn làm theo thứ tự
1. Đọc `00_START_HERE.md`, bản kiến trúc, spec module tương ứng, contract, test gate.
2. Xác minh nguồn URL và exact commit/spec/model SHA **ở thời điểm làm nhiệm vụ**; log SOURCE_VERIFIED hoặc BLOCKED. Không tự bịa đường dẫn tải checkpoints.
3. Nhận một Task ID từ `catalogs/TASK_BACKLOG.csv`; check phụ thuộc `PASS` và thuộc sở hữu module nào.
4. Trước khi code, viết `implementation_plan` cho task (input/output, files sẽ tạo/chỉnh, rủi ro, acceptance), kỹ sư lead xác nhận.
5. Tạo ít file nhỏ đúng catalog, test âm tính và unit/integration; không thay contract domain nếu không có ADR.
6. Ghi `evidence/`: môi trường, Git commit, commands executed, test outputs, versions SHA, screenshot sanitized, benchmark quality+runtime khi có model.
7. Kết thúc dưới trạng thái `PASS`, `FAIL`, `BLOCKED`, `PARTIAL`; mô tả blocker và cách tái hiện. Không report PASS khi mới tạo file.

## Công việc song song an toàn
Agent A: DICOM+geometry. Agent B: Slicer UI stub dùng contract giả lập. Agent C: engine scheduler/cache. Agent D: model/source/weights license + reproducibility. Agent E: tests/fixtures. Agent F: installer compatibility research. **Không để A/B/C cùng sửa contracts**; bảo vệ schema bằng code owner review.

## Workflow khởi đầu cho code agent (đây là hướng dẫn, không phải script đang có)
**WO-00 Foundation**: xác minh Slicer stable, Windows hardware, chính sách license, repository layout và contract. **WO-01 DICOM**: chọn series+affine, synthetic phantom. **WO-02 A/V/B**: TotalSeg once+source masks. **WO-03 LOBE**: five lobes. **WO-04 PTL original**: author dataset+3 checkpoints. **WO-05 Graph**: parity. **WO-06 Labeling**: branch instances+clinical review. **WO-07 Territory**: baseline + candidate ImPulSe. **WO-08 Planning**: lesion+surgeon interface. **WO-09 Performance**: CPU/AMD measured. **WO-10 Export/Installer**: DICOM SEG roundtrip + Windows offline. **WO-11 Clinical research**: independent evaluation.

## Task completion report (bắt buộc)
| Field | Agent phải điền |
|---|---|
| Task | ID+version workorder |
| Source | canonical repo/URL + pinned commit + license |
| Artifact | changed filenames + module responsibility |
| Contract | schema version, compatibility and migration |
| Verification | executed commands, PASS/FAIL count + logs |
| Performance | paired workload, RAM, wall time, quality delta hoặc NOT_MEASURED |
| Safety | geometry, provenance, PHI, uncertain label and failure paths |
| Exceptions | blockers, risk update, next action |
| Verdict | PASS / FAIL / BLOCKED / PARTIAL; reviewer signature |

## Không làm
Không tạo demo data giả rồi gắn nhãn CT bệnh nhân, không tự sửa reviewer status, không monkeypatch nguồn ngoài không ghi lại, không tắt quality checks để lấy tốc độ, không nhúng cloud APIs trong runtime, không copy hàng nghìn dòng code vào `PulmoSlicerAI.py`.
