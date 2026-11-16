import unittest

from pulmoslicer_engine.infrastructure.compute_backend import (
    ComputeProbe,
    select_backend,
)


class ComputeBackendTests(unittest.TestCase):
    def test_auto_prefers_cuda(self):
        decision = select_backend(
            ComputeProbe("2.9", cuda_available=True, cuda_name="RTX test")
        )
        self.assertEqual(decision.backend, "cuda")
        self.assertFalse(decision.force_cpu)

    def test_auto_recognizes_rocm_through_torch_cuda_api(self):
        decision = select_backend(
            ComputeProbe(
                "2.9", cuda_available=True, cuda_name="Radeon test", rocm_version="7.2"
            )
        )
        self.assertEqual(decision.backend, "amd_rocm")
        self.assertFalse(decision.force_cpu)

    def test_directml_is_not_silently_used_for_incompatible_model(self):
        decision = select_backend(
            ComputeProbe("2.9", directml_available=True, directml_compatible=False)
        )
        self.assertEqual(decision.backend, "cpu")
        self.assertIn("DirectML", decision.message)

    def test_explicit_unavailable_gpu_fails_instead_of_silent_cpu(self):
        with self.assertRaisesRegex(RuntimeError, "CUDA"):
            select_backend(ComputeProbe("cpu"), "cuda")


if __name__ == "__main__":
    unittest.main()
