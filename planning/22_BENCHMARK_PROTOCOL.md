# 22 — Benchmark CPU 16/32GB và ASUS 64GB AMD UMA

## Environment capture (per run)
Windows build, CPU model, logical/physical cores, memory total/free/commit, BIOS UMA setting if visible, GPU driver/directx/backend, SSD free space, Slicer revision, Python runtime, model SHA and inference provider, exact DICOM synthetic/authorized case hashes, source spacing/shape, cold vs warm, test conditions (power/thermal).

## Dataset benchmark tiers
- **SYNTHETIC:** small/medium/large phantom 256³, 512×512×300, full chest large; peak allocation simulated, LPS/RAS correctness.
- **STANDARD:** at least 10 authorized deidentified CT scans representative spacing/contrast; same case list across CPU/AMD.
- **STRESS:** very long 0.5 mm thin-slice, motion artifacts, obese patient, bilateral atelectasis, extensive collaterals and small veins, large lesion.
- **EXTERNAL HOLDOUT:** separate for final quality/clinical validity, not used to tune optimizer.

## Exact comparative measurements
Clock `import`, `canonicalize`, `AVB inference`, `lobe inference`, `graph build`, `3-label inference`, `territory`, `3D first view`, `plan`, `DICOM export`; p50/p90/p99, peak RSS/private bytes/system committed, GPU shared memory peak, CPU utilization/thermal, sustained paging, disk read/write, UI responsiveness and crash.

## Experimental design
Same exact CT/checkpoint/preprocess/crop; run CPU sequential baseline, CPU admitted graph parallel, GPU model-specific, GPU+CPU overlap, warm cache; randomize order to reduce thermal bias; 1 cold and at least 3 warm runs per case; re-run if cache invalidated. Quality parity on native image **must** pass before comparing time.

## Decision criteria
- Optimize for time to **usable reviewed CT-aligned output**, not artificial GPU kernel time.
- GUI main-thread latency p95 target exploratory <250 ms for simple interactions, not hard guarantee; medical expert specifies acceptable branch error/unknown rate **before** holdout.
- Speed optimization rejected if more critical branch omissions, coordinate shifts, errors hidden by confidence threshold, or unstable CPU-only operations.
- Published release profile includes permitted input envelope and observed min/median/p90, not universal laptop claim.

## Representative performance report fields
`run_id, protocol, CT geometry summary, source digest, model hash, provider, cold_warm, step_ms, p90_ms, peak_commit_GB, peak_process_private_GB, gpu_shared_GB, UI_p95_ms, warning count, branch_metrics, pass_fail, environment, evidence_date`.
