# X01 platform matrix

Verdict: **PARTIAL** (Slicer module smoke PASS; release governance still open).

Development host observed on 2026-11-15:

- Windows kernel `10.0.26300.0`, build `26300.9974`, x64, 24 logical processors.
- Repository base commit `54789b4feb4480f6f6da5f58590ce7032d13fea7`.
- Test runtime: official Python 3.12.10 embeddable, workspace-local only.
- pydicom 3.0.1, workspace-local test dependency.
- Slicer was located at `D:\Program Files\3D Slicer 5.12.4`; module registration
  and required/recommended extension capability checks passed headlessly.

Release baseline is Slicer 5.12.4 revision 34645 on Windows x86-64. The runtime
checker deliberately rejects other versions until each is smoke-tested. Host
RAM/GPU could not be read with current restricted permissions, so hardware
profile is now observed by Slicer as about 61 GB RAM with AMD Ryzen AI MAX+ 392;
GPU acceleration itself remains unbenchmarked.

