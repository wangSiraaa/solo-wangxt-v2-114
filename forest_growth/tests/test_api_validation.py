"""API 层单位校验测试（不需要数据库/GDAL）。"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from api.validation import (
    UnitConflictError, UnitPlausibilityError, reconcile_units,
    validate_dbh, validate_height, validate_record_units,
)


class TestApiValidation(unittest.TestCase):
    def test_valid_record_with_explicit_units(self):
        self.assertAlmostEqual(validate_dbh(125.0, "mm"), 12.5)
        self.assertAlmostEqual(validate_height(95.0, "dm"), 9.5)
        # 缺测：None 放行（不变成 0），由业务层判缺测
        self.assertIsNone(validate_dbh(None, "cm"))

    def test_wrong_unit_record_rejected_with_tag(self):
        """验收：测量单位错误（12.5 m 胸径）必须带树木编号被拦截。"""
        with self.assertRaises(UnitPlausibilityError) as ctx:
            validate_record_units(
                tag="P09-999", dbh_value=12.5, dbh_unit="m",
                height_value=20.0, height_unit="m")
        self.assertIn("P09-999", str(ctx.exception))

    def test_record_level_unit_conflict(self):
        with self.assertRaises(UnitConflictError):
            reconcile_units(tag="P01-001", field_name="dbh",
                            unit_a="cm", unit_b="mm")


if __name__ == "__main__":
    unittest.main()
