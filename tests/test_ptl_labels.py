import unittest

from pulmoslicer_engine.adapters.labeling.ptl_labels import (
    ptl_class_labels,
    ptl_region_metadata,
    ptl_segment_id,
)


class PtlLabelTests(unittest.TestCase):
    def test_all_three_roles_have_18_regions_and_central_class(self):
        for role, prefix in (("airway", "B"), ("artery", "A"), ("vein", "V")):
            labels = ptl_class_labels(role)
            self.assertEqual(set(labels), set(range(1, 20)))
            self.assertEqual(labels[1], f"{prefix}1 Right")
            self.assertEqual(labels[11], f"{prefix}1+2 Left")
            self.assertEqual(labels[19], f"{prefix}0 Central/out-of-lung")

    def test_stable_ids_include_role_side_and_class(self):
        self.assertEqual(ptl_segment_id("artery", 1), "PTL_A_R_01")
        self.assertEqual(ptl_segment_id("vein", 18), "PTL_V_L_18")
        self.assertEqual(ptl_segment_id("airway", 19), "PTL_B_C_19")

    def test_regions_map_to_right_three_lobes_and_left_two_lobes(self):
        self.assertEqual(ptl_region_metadata(4)["lobe"], "Middle")
        self.assertEqual(ptl_region_metadata(10)["side"], "Right")
        self.assertEqual(ptl_region_metadata(11)["region"], "S1+2")
        self.assertEqual(ptl_region_metadata(16)["region"], "S7+8")


if __name__ == "__main__":
    unittest.main()
