import unittest

import numpy as np

from core.units import (
    DBH_TO_CM, HEIGHT_TO_M, UnitConflictError, UnitPlausibilityError,
    assert_same_unit, convert_dbh_to_cm, convert_height_to_m,
)


class TestUnits(unittest.TestCase):
    def test_conversions(self):
        np.testing.assert_allclose(
            convert_dbh_to_cm([125, 12.5, 0.125, 10.0], ["mm", "cm", "m", "in"]),
            [12.5, 12.5, 12.5, 25.4], rtol=1e-9)
        np.testing.assert_allclose(
            convert_height_to_m([100, 10, 32.8084], ["dm", "m", "ft"]),
            [10.0, 10.0, 10.0], rtol=1e-3)

    def test_dbh_12_5_metres_rejected(self):
        """单位错误核对：胸径 12.5 m（1250 cm）必须拦截，不能静默当 12.5。"""
        with self.assertRaises(UnitPlausibilityError) as ctx:
            convert_dbh_to_cm([12.5], ["m"], record_ids=["X1"])
        self.assertIn("X1", str(ctx.exception))

    def test_dbh_2500_cm_rejected(self):
        with self.assertRaises(UnitPlausibilityError):
            convert_dbh_to_cm([2500.0], ["cm"])

    def test_suspicious_cm_value_that_is_actually_metres_flagged(self):
        """字段写 cm、录入 0.25（疑似米）：换算后 0.25 cm < 0.5 cm 下界，拦截。"""
        with self.assertRaises(UnitPlausibilityError):
            convert_dbh_to_cm([0.25], ["cm"])

    def test_strict_false_returns_nan_mask(self):
        out = convert_dbh_to_cm([12.0, 9999.0], ["cm", "cm"], strict=False)
        self.assertTrue(np.isnan(out[1]))
        self.assertEqual(out[0], 12.0)

    def test_record_level_unit_conflict(self):
        """同树同字段两条记录单位不一致：记录级冲突，拒绝并要求核实。"""
        with self.assertRaises(UnitConflictError):
            assert_same_unit("cm", "mm", tree_tag="P01-001", field="dbh")

    def test_unknown_unit_rejected(self):
        with self.assertRaises(ValueError):
            convert_dbh_to_cm([12.0], ["cmm"])


if __name__ == "__main__":
    unittest.main()
