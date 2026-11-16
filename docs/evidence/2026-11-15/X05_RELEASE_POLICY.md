# X05 release/SBOM policy

Verdict: **PARTIAL; signing infrastructure not configured**.

Each release must contain source commit, Slicer revision, Python lock, SBOM,
model registry, checkpoint SHA256, code/weight/data licenses, Windows profile,
and executed smoke-test evidence. CPU is mandatory; AMD is an optional pack.
Artifacts may be signed only by the release role after hashes are finalized.

Protected core ownership requires software plus domain review for geometry,
anatomy ontology, clinician-review state, and DICOM SEG. Uninstall must delete
only application-owned files and preserve case vaults, projects, audit records,
and exports. Current repository has no signing key, installer, model bundle, or
release approval; therefore X05 is not PASS.

