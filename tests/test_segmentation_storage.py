import json
from pathlib import Path
import tempfile
import unittest
from uuid import uuid4

from pulmoslicer_engine.adapters.segmentation.lobe_inference_adapter import build_lobe_command
from pulmoslicer_engine.adapters.segmentation.mask_geometry_validator import MaskMetadata, validate_masks
from pulmoslicer_engine.adapters.segmentation.totalseg_inference_adapter import build_lung_vessels_command
from pulmoslicer_engine.adapters.segmentation.totalseg_registry_probe import (
    AVB_CLASSES, LOBE_CLASSES, TotalSegProbeError, parse_registry
)
from pulmoslicer_engine.domain.case_geometry import CaseGeometry
from pulmoslicer_engine.domain.segmentation_artifact import SegmentationArtifact, SegmentationArtifactError
from pulmoslicer_engine.infrastructure.atomic_artifact_store import AtomicArtifactStore
from pulmoslicer_engine.infrastructure.cache_key_builder import build_cache_key


HASH = "c" * 64
AFFINE = (1, 0, 0, 10, 0, 1, 0, 20, 0, 0, 1, 30, 0, 0, 0, 1)


def registry():
    return {
        "totalsegmentator_version": "2.18.0",
        "tasks": {
            "lung_vessels": {
                "modality": "CT", "license_required": False,
                "classes": {str(i): name for i, name in enumerate(sorted(AVB_CLASSES), 1)},
            },
            "total": {
                "modality": "CT", "license_required": False,
                "classes": {str(i): name for i, name in enumerate(sorted(LOBE_CLASSES), 10)},
            },
        },
    }


class SegmentationTests(unittest.TestCase):
    def geometry(self):
        return CaseGeometry((5, 4, 3), (1, 1, 1), AFFINE, "1.2.3", HASH)

    def test_registry_probe_and_commands_are_exact_and_cpu_first(self):
        avb = parse_registry(registry(), "lung_vessels", AVB_CLASSES)
        command = build_lung_vessels_command(Path("ct.nii.gz"), Path("output"), avb)
        self.assertEqual(command.count("lung_vessels"), 1)
        self.assertEqual(command[command.index("--device") + 1], "cpu")
        self.assertNotIn("--fast", command)
        lobes = parse_registry(registry(), "total", LOBE_CLASSES)
        lobe_command = build_lobe_command(Path("ct.nii.gz"), Path("lobes"), lobes)
        self.assertTrue(LOBE_CLASSES.issubset(lobe_command))

    def test_wrong_avb_class_map_is_blocked(self):
        payload = registry()
        payload["tasks"]["lung_vessels"]["classes"].pop("1")
        with self.assertRaisesRegex(TotalSegProbeError, "incompatible"):
            parse_registry(payload, "lung_vessels", AVB_CLASSES)

    def test_mask_geometry_mismatch_is_reported(self):
        geometry = self.geometry()
        masks = tuple(MaskMetadata(name, geometry.shape_ijk, AFFINE, 5, HASH) for name in AVB_CLASSES)
        self.assertTrue(validate_masks(masks, AVB_CLASSES, geometry).valid)
        bad = masks[:-1] + (MaskMetadata(masks[-1].class_name, (1, 1, 1), AFFINE, 0, HASH),)
        report = validate_masks(bad, AVB_CLASSES, geometry)
        self.assertFalse(report.valid)
        self.assertTrue(any(item.startswith("SHAPE_MISMATCH") for item in report.findings))
        self.assertTrue(any(item.startswith("EMPTY_MASK") for item in report.findings))

    def test_artifact_cannot_claim_unvalidated_or_wrong_source(self):
        geometry = self.geometry()
        args = dict(
            artifact_id=str(uuid4()), source_volume_sha256=HASH, geometry=geometry,
            class_map={1: "lung_airways"}, mask_sha256_by_class={"lung_airways": "d" * 64},
            model_id="totalsegmentator/lung_vessels", model_weight_sha256="e" * 64,
        )
        self.assertEqual(SegmentationArtifact(**args).stage_status, "VALIDATED")
        with self.assertRaises(SegmentationArtifactError):
            SegmentationArtifact(**{**args, "stage_status": "COMPLETE"})


class StorageTests(unittest.TestCase):
    def test_cache_key_changes_with_affine_and_model(self):
        first = build_cache_key(HASH, AFFINE, "a" * 64, {"task": "avb"}, "rev1")
        second = build_cache_key(HASH, (*AFFINE[:-1], 2), "a" * 64, {"task": "avb"}, "rev1")
        self.assertNotEqual(first, second)

    def test_atomic_store_commits_and_detects_tamper(self):
        with tempfile.TemporaryDirectory() as directory:
            store = AtomicArtifactStore(Path(directory))
            with store.stage("artifact-1") as staging:
                (staging / "mask.bin").write_bytes(b"immutable mask")
            self.assertTrue(store.verify("artifact-1"))
            (Path(directory) / "artifact-1" / "mask.bin").write_bytes(b"tampered")
            self.assertFalse(store.verify("artifact-1"))

    def test_failed_stage_remains_partial_not_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            store = AtomicArtifactStore(Path(directory))
            with self.assertRaisesRegex(RuntimeError, "simulated crash"):
                with store.stage("artifact-2") as staging:
                    (staging / "mask.bin").write_bytes(b"partial")
                    raise RuntimeError("simulated crash")
            self.assertFalse((Path(directory) / "artifact-2").exists())
            quarantined = store.quarantine_partial("artifact-2", Path(directory) / "quarantine")
            self.assertIsNotNone(quarantined)


if __name__ == "__main__":
    unittest.main()
