import unittest
from uuid import uuid4

from pulmoslicer_engine.application.review_usecase import (
    ReviewAuthority, ReviewAuthorizationError, record_review
)
from pulmoslicer_engine.domain.anatomy_ontology import AnatomyOntology, AnatomyOntologyError
from pulmoslicer_engine.domain.branch_instance import (
    BranchInstance, BranchInstanceError, BranchLabelStatus, BranchSystem
)
from pulmoslicer_engine.domain.review_record import ReviewStatus


HASH = "f" * 64


class BranchReviewTests(unittest.TestCase):
    def test_vein_may_have_multiple_parents_without_nearest_merge(self):
        branch = BranchInstance(
            branch_id=str(uuid4()),
            system=BranchSystem.PULMONARY_VEIN,
            parent_ids=(str(uuid4()), str(uuid4())),
            child_ids=(),
            centerline_lps_mm=((1.0, 2.0, 3.0), (2.0, 3.0, 4.0)),
            source_mask_sha256=HASH,
            display_label="Unknown pulmonary vein",
            label_status=BranchLabelStatus.UNKNOWN,
        )
        self.assertEqual(len(branch.parent_ids), 2)

    def test_unknown_cannot_display_false_confidence(self):
        with self.assertRaisesRegex(BranchInstanceError, "false numeric certainty"):
            BranchInstance(
                str(uuid4()), BranchSystem.AIRWAY, (), (), ((0, 0, 0), (1, 1, 1)),
                HASH, "Unknown", BranchLabelStatus.UNKNOWN, 0.99
            )

    def test_fused_variants_are_explicit_and_system_checked(self):
        ontology = AnatomyOntology()
        self.assertEqual(ontology.resolve("B1+2", BranchSystem.AIRWAY).fused_components, ("B1", "B2"))
        with self.assertRaises(AnatomyOntologyError):
            ontology.resolve("B1+2", BranchSystem.PULMONARY_ARTERY)

    def test_worker_cannot_forge_clinician_acceptance(self):
        with self.assertRaises(ReviewAuthorizationError):
            record_review(ReviewAuthority.WORKER, HASH, "reviewer-1", ReviewStatus.REVIEWED_ACCEPTED, "ok")
        review = record_review(
            ReviewAuthority.CLINICIAN_UI, HASH, "reviewer-1", ReviewStatus.REVIEWED_CORRECTED, "manual correction"
        )
        self.assertEqual(review.status, ReviewStatus.REVIEWED_CORRECTED)

    def test_upstream_change_marks_review_stale(self):
        review = record_review(
            ReviewAuthority.CLINICIAN_UI, HASH, "reviewer-1", ReviewStatus.REVIEWED_ACCEPTED, "inspected CT"
        )
        stale = review.invalidate("e" * 64, str(uuid4()))
        self.assertEqual(stale.status, ReviewStatus.STALE)
        self.assertEqual(stale.supersedes_review_id, review.review_id)


if __name__ == "__main__":
    unittest.main()
