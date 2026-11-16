# S5 subset — manual branch representation and review safety

**Status:** PARTIAL. PTL auto-labeling remains BLOCKED by WO-04/G2.

The implemented fallback represents airway, pulmonary-artery, and
pulmonary-vein branch instances with stable IDs, multi-parent topology, LPS-mm
centerlines, source-mask hash, provenance status, and explicit UNKNOWN/VARIANT.
It does not force pulmonary veins into a single-root tree.

The current ontology is deliberately marked DRAFT and contains only safety
fallbacks plus B1+2/B7+8 fused-bronchus examples. It must not be expanded into
a clinical claim without the domain owner. Review records bind to one exact
artifact digest; only the clinician UI authority can issue accepted/corrected/
rejected decisions, and upstream changes create a new STALE record.

Slicer branch-tree/focus widgets, audit persistence, complete ontology, and
dual-clinician validation remain not implemented/not tested.

