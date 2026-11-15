# 24 — Governance, review và change control

## Người phụ trách
**Engineering lead:** architecture/quality/API; **Clinical lead:** anatomy ontology, uncertainty and clinical risks; **Imaging lead:** DICOM geometry; **MLOps lead:** weights/data/benchmark; **Security lead:** patient data and code supply chain; **Release/QA lead:** installer, tests, evidence.

## Quy tắc PR/merge về sau
Một PR/task, module owners rõ, branch bảo vệ. Source commit and tests; thay đổi `domain` anatomy, coordinates, ontology, reviewed state, export DICOM SEG cần dual approval. Không cắt bỏ test để vượt CI. Gộp PR nhỏ; khi thay đổi >3 modules thuộc 2 boundaries thì phải có ADR ngắn giải thích.

## ADR format
`ADR-ID`, date, problem, chosen option, alternatives rejected, dependency effects, safety implications, performance implications, backward compatibility, acceptance tests, owners, decision status.

## Traceability
Requirements ↔ task ↔ module ↔ tests ↔ risk mitigation ↔ versioned evidence. Không chấp nhận source code generated mà không map requirement/test. `catalogs/REQUIREMENTS_TRACEABILITY.csv` là mapping dự kiến, phải refine từng requirement/test trước coding (không tuyên bố hoàn chỉnh vì mapping đại diện).

## Definition of Done (task tương lai)
Đã review source+license, ký contract, code file nhỏ đúng directory, test positive/negative PASS, process/resource safety, documentation, source/model SHA, passing target Windows where applicable, reviewer approval, release gate status updated. Unit tests không thay thế tests hardware/clinical.

## Chế độ bảo trì
Security hotfix bypass feature pipeline chỉ được giải quyết trong emergency branch có QA, migration version, rollback tested. Deprecate API qua SemVer và ít nhất 1 major compatibility window hoặc migration tool; không xóa patient vault dù nâng cấp hỏng.
