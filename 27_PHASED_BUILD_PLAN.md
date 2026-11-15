# 27 — Lộ trình code theo lát cắt mỏng (vertical slices), không làm đồng loạt 94 file

**Mục tiêu:** người đầu tiên nhận dự án có thể tạo ra một tính năng hoạt động sớm mà không phá kiến trúc hay viết một file 2000 dòng. Mỗi slice tạo **chỉ những module cần thiết**; tài liệu liệt kê các module tương lai, không bắt buộc ngay lập tức có đủ 94 `.py` files.

| Slice | Nhiệm vụ nhỏ | Module IDs ưu tiên | Người dùng sẽ thấy gì khi hoàn thành tương lai | Gate |
|---|---|---|---|---|
| S0 — Design & platform | Lock source Slicer, port map, case vault, Windows matrix | CT01;CT02;DM01;IN01;IN13;IN15 | Chưa cần AI, có hồ sơ/probe | G0 |
| S1 — CT đúng | Series chooser, source geometry, HU, 2D viewer | UI01;UI02;IO01;IO02;IO03;IO04;IO05;UI14;UI18 | Mở CT đúng series, MPR chính xác | G1 |
| S2 — A/V/B đầu tiên | TotalSeg once, masks, preview LOD, job progress | IO06;IO07;IO08;IO10;UI04;UI05;UI15;UI16;IN04;IN05 | 3D động mạch/tĩnh mạch/phế quản, CPU | G1 |
| S3 — Thùy và lưu lại | Five lobes, atomic cache, resume, QC | IO09;IN02;IN03;IN08;QS03;UI03 | 5 thùy + mở lại project không chạy từ đầu | G1 |
| S4 — PTL proof *riêng* | Source/checkpoint, graph features, parity | LB01;GR01;GR02;GR03;GR04;GR05 | Bằng chứng model gốc chạy, chưa nhất thiết UI | G2 |
| S5 — Auto-name có thể sửa | Three PTL adapters, branch instances, ontology+review | LB02;LB03;LB04;LB05;DM03;DM08;DM07;AP06;UI06;UI07;UI08;UI17 | A/B/V branch names + unknown + bác sĩ chỉnh | G3 |
| S6 — Territory+lesion | Two candidate solvers, method comparison, lesion manual | TR01;TR02;TR03;UI09;UI10;PL01;DM04;DM05 | Vùng phân thùy ước tính và nốt u CT | G4 |
| S7 — Planning | Plan candidates, margin CT, branch relations and review | PL03;PL04;PL05;AP07;UI11;DM06;DM09 | So sánh phương án cắt, mặt phẳng dự kiến | G4 |
| S8 — CPU/AMD optimization | Scheduler, native/ONNX, probes, benchmark | IN06;IN07;IN09;IN10;IN11 | CPU 32GB target và AMD optional được đo | G5 |
| S9 — Export/install | DICOM SEG+roundtrip, reports, offline setup/uninstall | EX01;EX02;EX03;EX04;EX05;UI12;IN16 | Cài được trên Windows sạch, export đúng CT nguồn | G6 |
| S10 — Independent validation | Data rights + clinicians + external CT trials | QAs+Clinical study workorders | Clinical research evidence; no automatic clearance claim | G7 |

## Khi nào được chạy song song?
Có thể giao S1 CT geometry và S4 PTL original research song song vì không chia code mutable core. Source/licensing (S0) có thể tiến hành song song với design UI, nhưng **S5 không được claim auto-name trước S4 graph parity PASS**; S6/S7 phụ thuộc nhãn đã được review hoặc manual fallback; S8 được benchmark từ S2 chứ không đợi toàn bộ AI.

## Điều kiện chuyển slice
Mỗi slice: (a) code vừa đủ module, (b) tests âm tính, (c) contract/schema, (d) evidence Windows hay model theo gate, (e) người khác review, (f) không vi phạm LOC/import rules. Không mở S10 chỉ vì S9 installer có thể chạy được.
