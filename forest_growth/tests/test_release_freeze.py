import unittest

from fixtures import make_book
from core.allometry import (
    EquationBook, FrozenReleaseError, SpeciesNotCoveredError,
)


class TestReleaseFreeze(unittest.TestCase):
    def setUp(self):
        self.book = make_book()
        self.v1 = self.book.get("eq-2015-v1")
        self.v2 = self.book.get("eq-2024-v2")

    def test_frozen_release_cannot_be_overwritten(self):
        """已发布 release 同 ID 再发布必须被拒。"""
        with self.assertRaises(FrozenReleaseError):
            self.book.publish(self.v1)

    def test_same_release_reproduces_same_biomass(self):
        """用 v1 重算多年后仍得到完全相同的结果（方程内容冻结）。"""
        eq = self.v1.lookup("PIMA", 20.0)
        first = float(eq.evaluate(20.0))
        # 即使注册表中已有 v2，v1 的查找仍返回 v1 方程
        eq_again = self.book.get("eq-2015-v1").lookup("PIMA", 20.0)
        self.assertEqual(eq.equation_id, "PIMA-AGB-2015")
        self.assertEqual(float(eq_again.evaluate(20.0)), first)

    def test_new_equation_does_not_silently_change_approved_run(self):
        """已确认调查版用 v1：请求 v2 且未显式允许时必须拒绝。"""
        with self.assertRaises(FrozenReleaseError):
            self.book.require_same_release_for_approved_run(
                approved_release_id="eq-2015-v1",
                requested_release_id="eq-2024-v2",
            )

    def test_explicit_recreate_creates_new_run_instead_of_overwrite(self):
        chosen = self.book.require_same_release_for_approved_run(
            approved_release_id="eq-2015-v1", requested_release_id="eq-2024-v2",
            allow_recreate=True)
        self.assertEqual(chosen, "eq-2024-v2")
        # 旧 release 依然存在且未变
        self.assertEqual(
            float(self.v1.lookup("PIMA", 20.0).evaluate(20.0)),
            float(self.book.get("eq-2015-v1").lookup("PIMA", 20.0).evaluate(20.0)),
        )

    def test_unknown_species_rejected_not_borrowed(self):
        with self.assertRaises(SpeciesNotCoveredError):
            self.v1.lookup("QUFA", 20.0)   # 栓皮栎不在适用树种清单

    def test_v1_and_v2_give_different_numbers_by_design(self):
        """证明两个 release 确有差异，前述冻结规则才有意义。"""
        b1 = float(self.v1.lookup("PIMA", 20.0).evaluate(20.0))
        b2 = float(self.v2.lookup("PIMA", 20.0).evaluate(20.0))
        self.assertNotAlmostEqual(b1, b2, places=6)


if __name__ == "__main__":
    unittest.main()
