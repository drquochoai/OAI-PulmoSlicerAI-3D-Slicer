# S0 implementation plan — Foundation

**Date:** 2026-11-15. **Gate:** G0. **Status:** PARTIAL / awaiting independent
review and a real Slicer smoke test.

## Inputs and outputs

- Inputs: versioned job envelopes, DICOM-derived geometry metadata, case IDs,
  structured events, and an explicit host compatibility description.
- Outputs: validated requests, immutable LPS-mm geometry, protected case
  workspace paths, PHI-minimized JSONL events, and compatibility findings.

## Files and module ownership

- CT01 `contract_registry.py`: SemVer compatibility registry.
- CT02 `request_validator.py`: strict job-envelope validation.
- DM01 `case_geometry.py`: immutable LPS geometry value object.
- IN01 `case_vault.py`: workspace creation and containment checks.
- IN13 `safe_event_logger.py`: allow-listed, sanitized diagnostic events.
- IN15 `installer_compatibility_checker.py`: explicit support-matrix check.
- UI00 `PulmoSlicerAI.py`: thin Slicer registration/widget shell only.

## Failure cases and acceptance

Reject unsupported contract majors, malformed hashes/IDs, singular or non-LPS
affines, paths escaping the vault, unsafe log fields/control characters, and
unsupported Slicer/Windows/Python combinations. Unit tests cover positive and
negative paths. A Slicer 5.12.4 Windows load test remains required before G0.

## Safety boundaries

No model is loaded, no patient pixels are read, and no clinician review state
can be created. Source UIDs and patient paths are not accepted in diagnostic
events. This slice does not close licensing, model, clinical, or installer
risks.

