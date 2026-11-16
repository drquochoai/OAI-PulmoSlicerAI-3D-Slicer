# GPU/backend diagnosis — 2026-11-16

Verdict: **CPU fallback is correct for the currently installed runtime; AMD GPU
execution is not yet certified.**

## Observed machine/runtime

- CPU/APU: AMD Ryzen AI MAX+ 392, 24 logical processors.
- Display device: AMD Radeon 8060S, PCI `VEN_1002&DEV_1586`.
- Windows driver: `32.0.22032.16001`, dated 2026-05-11.
- Slicer embedded PyTorch: `2.15.0+cpu`.
- Probe: CUDA built `false`, CUDA available `false`, HIP/ROCm version absent,
  MPS unavailable.
- PulmoSlicer package installed under Slicer at diagnosis time:
  `2026.11.16.1`, not the new package.

Shared VRAM is memory that the integrated GPU may borrow from system RAM. It
does not provide a PyTorch compute provider by itself. TotalSegmentator 2.14 in
the installed Slicer accepts only `gpu` (PyTorch CUDA API), `mps`, or `cpu` and
therefore resolves this CPU-only torch build to CPU.

Microsoft's DirectML PyTorch backend is a separate preview package, while the
TotalSegmentator CLI/nnUNet path installed here has no `directml` device option.
It must not be reported as active or used through an untested operator fallback.

## Screenshot/log interpretation

The visible Slicer session log contains SampleData loading and no
PulmoSlicer/TotalSegmentator run record. The screenshot shows already-created
dense closed surfaces while Slicer is in the Segmentations module. Therefore
the exact blocked operation cannot be proven from the log, but synchronous
closed-surface conversion/smoothing on Slicer's main thread is a strong
candidate. GPU inference would not accelerate that VTK CPU conversion.

## Changes in package 2026.11.16.5

- Default changed from forced CPU to an explicit automatic policy:
  CUDA → ROCm exposed through the PyTorch CUDA API → compatible DirectML adapter
  (none for TotalSegmentator) → CPU.
- The UI displays the resolved backend and records it in the PHI-safe run log.
- Explicit CUDA/ROCm selection fails with a clear error instead of silently
  claiming GPU while running CPU.
- PTL also uses CUDA/ROCm automatically when its PyTorch runtime exposes a real
  device.
- Default 3-D representation uses smoothing `0.0`; Slicer documents this as the
  faster surface-update setting. Balanced/detailed profiles remain selectable.
- Progress callbacks yield to the Qt event loop and PTL/surface stages are
  visible in the progress panel.

## AMD ROCm boundary

AMD now lists the Ryzen AI MAX+ 392 / Radeon 8060S (`gfx1151`) in its ROCm
hardware support. A supported GPU is necessary but not sufficient: a separate
ROCm PyTorch runtime, driver probe, TotalSegmentator compatibility run, and
paired CPU/GPU geometry/topology/branch parity benchmark are still required.

The official ROCm 7.2.1 Windows torch wheel alone is about 783 MiB and the
custom ROCm library wheel about 467 MiB, before the remaining SDK and installed
files. Replacing Slicer's shared torch package would risk breaking other
extensions, so the planned implementation is an isolated worker. Until that
worker passes parity, the automatic policy correctly chooses CPU on this
installation.
