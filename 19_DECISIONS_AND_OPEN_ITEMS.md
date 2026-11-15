# 19 — Architecture Decision Records (ADR), giả định và vấn đề mở

| ADR | Quyết định | Lý do | Có thể xem xét lại khi |
|---|---|---|---|
| ADR-001 | 3D Slicer Scripted Extension | Tránh viết lại 3D viewer và workflow CT | version incompatibility |
| ADR-002 | Engine Python process riêng | Không xung đột PyTorch/Slicer, cô lập crash | có runtime native ổn định hơn |
| ADR-003 | CPU-first, AMD optional | Windows viện không có CUDA | backend parity benchmark |
| ADR-004 | File-based artifacts, no DB server | Offline, dễ sao lưu và resume | đồng thời nhiều user/collaboration server |
| ADR-005 | LPS-mm exchange | DICOM-native, geometry consistency | cần chuẩn khác do tích hợp đã chứng minh |
| ADR-006 | Masks immutable; meshes derived | Không mất nhánh do smoothing/LOD | không thay đổi |
| ADR-007 | 5 core model roles + 2 optional | CPU/RAM efficient, staged rollout | evidence changes |
| ADR-008 | Clinical approval only in UI by human | Safety and audit | no |
| ADR-009 | Lazy preview and native detailed ROI | Speed without small branch loss | regression tests |
| ADR-010 | Single heavy task default | Small machine stability | paired resource profiling |
| ADR-011 | PTL phased gates | Not plug-and-play with TotalSeg | adapter proven |
| ADR-012 | ImPulSe optional experimental | source reproduction pending | model validation successful |
| ADR-013 | Offline installer two-layer | Easy hospital distribution | audited native runtime approach |
| ADR-014 | Contracts SemVer and file ownership | parallel coding agents safely | stronger typed IDL chosen |
| ADR-015 | Clinic research-only initial claim | clinical validation/regulatory missing | approvals and clinical evidence |

## Điều chưa thể chốt trước khi chạy thực tế
1. Exact Slicer stable and Python versions at engineering start.
2. 32GB CT volume envelope vs max original thickness/voxels acceptable.
3. TotalSeg lobes and lung_vessels output class-map at pinned version.
4. PTL source branch/weights license, original results, CPU compatibility, graph parser.
5. ImPulSe2 original pretrained files compatible, weights rights, generalization.
6. Radeon backend actual provider / per operator performance for exact ASUS SKU.
7. DICOM SEG export workflow, dcmqi version and cross-viewer roundtrip.
8. Clinical risk tolerance, independent dataset size and reviewers, privacy approvals.
9. Whether models with restricted/commercial usage may be bundled in distribution.
10. Installer route .s4ext descriptor vs package and standalone `.exe` validation on target Slicer.

Không được tự biến mục OPEN thành CLOSED bằng cách viết một đoạn văn; cần bằng chứng ngoài phần thiết kế.
