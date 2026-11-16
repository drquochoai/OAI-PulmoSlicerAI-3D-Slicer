from dataclasses import FrozenInstanceError
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from pulmoslicer_engine.contracts.contract_registry import ContractRegistry, ContractVersionError
from pulmoslicer_engine.contracts.request_validator import RequestValidationError, validate_job_request
from pulmoslicer_engine.domain.case_geometry import CaseGeometry, GeometryError
from pulmoslicer_engine.infrastructure.case_vault import CaseVault, VaultSecurityError
from pulmoslicer_engine.infrastructure.installer_compatibility_checker import TargetSystem, check_compatibility
from pulmoslicer_engine.infrastructure.safe_event_logger import UnsafeEventError, safe_event


HASH = "a" * 64


class ContractTests(unittest.TestCase):
    def test_registry_accepts_same_major_older_minor(self):
        registry = ContractRegistry({"JobRequest": "1.2.0"})
        self.assertEqual(registry.require_readable("JobRequest", "1.1.0"), "1.2.0")

    def test_registry_rejects_unknown_major(self):
        with self.assertRaisesRegex(ContractVersionError, "INCOMPATIBLE_CONTRACT"):
            ContractRegistry().require_readable("JobRequest", "2.0.0")

    def test_job_request_is_strict(self):
        payload = {
            "contract_version": "1.0.0",
            "job_id": str(uuid4()),
            "case_id": str(uuid4()),
            "stage_id": "geometry_validate",
            "input_hashes": [HASH],
            "parameters": {},
        }
        self.assertEqual(validate_job_request(payload).stage_id, "geometry_validate")
        payload["patient_name"] = "forbidden"
        with self.assertRaises(RequestValidationError):
            validate_job_request(payload)


class GeometryTests(unittest.TestCase):
    def geometry(self, affine=None):
        return CaseGeometry(
            shape_ijk=(10, 20, 30),
            spacing_mm=(0.7, 0.7, 1.0),
            ijk_to_lps=affine or (0.7, 0, 0, 10, 0, 0.7, 0, 20, 0, 0, 1, 30, 0, 0, 0, 1),
            frame_of_reference_uid="1.2.3.4",
            source_volume_sha256=HASH,
        )

    def test_lps_to_ras_preserves_superior_and_flips_first_two_axes(self):
        geometry = self.geometry()
        self.assertEqual(geometry.index_to_lps((1, 2, 3)), (10.7, 21.4, 33.0))
        self.assertEqual(geometry.index_to_ras((1, 2, 3)), (-10.7, -21.4, 33.0))

    def test_geometry_is_immutable(self):
        with self.assertRaises(FrozenInstanceError):
            self.geometry().units = "cm"

    def test_singular_affine_rejected(self):
        with self.assertRaisesRegex(GeometryError, "singular"):
            self.geometry((0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1))

    def test_analytic_inverse_roundtrip(self):
        geometry = self.geometry()
        point = (3.25, 8.5, 12.0)
        recovered = geometry.lps_to_index(geometry.index_to_lps(point))
        for actual, expected in zip(recovered, point):
            self.assertAlmostEqual(actual, expected)


class InfrastructureTests(unittest.TestCase):
    def test_vault_layout_and_traversal_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            vault = CaseVault(Path(directory) / "vault")
            case_id = str(uuid4())
            case_path = vault.create_case(case_id)
            self.assertTrue((case_path / "source").is_dir())
            with self.assertRaises(VaultSecurityError):
                vault.contained_path(case_id, "source", "../outside.dcm")

    def test_safe_event_redacts_identifiers_and_rejects_fields(self):
        event = safe_event({"message": "MRN=123 C:\\Patients\\Alice\\scan.dcm 1.2.840.3.4"})
        self.assertNotIn("Alice", event["message"])
        self.assertNotIn("1.2.840", event["message"])
        with self.assertRaises(UnsafeEventError):
            safe_event({"patient_name": "Alice"})

    def test_support_matrix_is_explicit(self):
        supported = check_compatibility(TargetSystem(22631, "amd64", "5.12.4", 34645, (3, 12), 32))
        self.assertTrue(supported.supported)
        self.assertEqual(supported.profile, "STANDARD")
        rejected = check_compatibility(TargetSystem(19045, "amd64", "5.10.0", 1, (3, 9), 8))
        self.assertFalse(rejected.supported)
        self.assertIn("INSUFFICIENT_RAM", rejected.findings)


if __name__ == "__main__":
    unittest.main()
