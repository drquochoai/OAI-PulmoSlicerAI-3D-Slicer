"""Deterministic compute-backend selection with explicit fallback provenance."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ComputeProbe:
    torch_version: str
    cuda_available: bool = False
    cuda_name: str = ""
    rocm_version: str = ""
    mps_available: bool = False
    directml_available: bool = False
    directml_compatible: bool = False


@dataclass(frozen=True)
class BackendDecision:
    backend: str
    force_cpu: bool
    attempted: tuple[str, ...]
    message: str


def select_backend(probe: ComputeProbe, preference: str = "auto") -> BackendDecision:
    """Select only backends that the current TotalSegmentator runtime can execute.

    ROCm PyTorch exposes its HIP device through the PyTorch ``cuda`` API. DirectML
    is recorded but rejected unless the model-specific adapter has passed its
    compatibility gate; TotalSegmentator's CLI has no DirectML device option.
    """

    allowed = {"auto", "cuda", "amd_rocm", "mps", "cpu"}
    if preference not in allowed:
        raise ValueError(f"unsupported compute preference: {preference}")

    is_rocm = bool(probe.rocm_version)
    gpu_backend = "amd_rocm" if is_rocm else "cuda"
    gpu_ready = probe.cuda_available

    if preference == "cpu":
        return BackendDecision("cpu", True, ("cpu",), "CPU được chọn thủ công")
    if preference == "cuda":
        if gpu_ready and not is_rocm:
            return BackendDecision("cuda", False, ("cuda",), f"CUDA: {probe.cuda_name}")
        raise RuntimeError("CUDA không khả dụng trong PyTorch của 3D Slicer")
    if preference == "amd_rocm":
        if gpu_ready and is_rocm:
            return BackendDecision(
                "amd_rocm", False, ("amd_rocm",),
                f"AMD ROCm {probe.rocm_version}: {probe.cuda_name}",
            )
        raise RuntimeError(
            "AMD ROCm chưa khả dụng trong runtime đã kiểm chứng; không dùng shared VRAM giả lập"
        )
    if preference == "mps":
        if probe.mps_available:
            return BackendDecision("mps", False, ("mps",), "Apple MPS")
        raise RuntimeError("Apple MPS không khả dụng")

    attempted = ["cuda", "amd_rocm", "directml", "cpu"]
    if gpu_ready:
        return BackendDecision(
            gpu_backend,
            False,
            tuple(attempted[: 2 if is_rocm else 1]),
            f"Tự động chọn {gpu_backend}: {probe.cuda_name}",
        )
    if probe.directml_available and not probe.directml_compatible:
        reason = "DirectML có mặt nhưng TotalSegmentator chưa tương thích; fallback CPU"
    else:
        reason = "Không có CUDA/ROCm tương thích; fallback CPU"
    return BackendDecision("cpu", True, tuple(attempted), reason)


def probe_torch_backend(torch_module) -> ComputeProbe:
    cuda_available = bool(torch_module.cuda.is_available())
    name = ""
    if cuda_available:
        name = str(torch_module.cuda.get_device_name(0))
    mps = bool(
        hasattr(torch_module.backends, "mps")
        and torch_module.backends.mps.is_available()
    )
    return ComputeProbe(
        torch_version=str(torch_module.__version__),
        cuda_available=cuda_available,
        cuda_name=name,
        rocm_version=str(getattr(torch_module.version, "hip", "") or ""),
        mps_available=mps,
    )
