import unittest

from fixtures import make_book, plot_p01
from core.remeasure import PairStatus, match_trees


class TestRemeasure(unittest.TestCase):
    def setUp(self):
        self.p = plot_p01()

    def _by_status(self, pairs):
        out = {}
        for pair in pairs:
            out.setdefault(pair.status, []).append(pair)
        return out

    def test_renumbered_tree_matched_via_crosswalk(self):
        """复测改号：交叉表优先，P01-004 -> P01-104 应识别为同株 survivor。"""
        pairs = match_trees(t1=self.p["t1"], t2=self.p["t2"],
                            crosswalk=self.p["crosswalk"])
        survivors = {pair.t2.tag: pair for pair in pairs
                     if pair.status == PairStatus.SURVIVOR}
        self.assertIn("P01-104", survivors)
        pair = survivors["P01-104"]
        self.assertEqual(pair.t1.tag, "P01-004")
        self.assertEqual(pair.matched_via, "crosswalk")
        self.assertAlmostEqual(pair.distance_m, 0.054, places=2)

    def test_same_tag_location_conflict_is_not_auto_merged(self):
        """编号相同但位置矛盾（18 m）：必须挂起，不能直接认成同株。"""
        pairs = match_trees(t1=self.p["t1"], t2=self.p["t2"],
                            crosswalk=self.p["crosswalk"])
        conflicts = [pr for pr in pairs
                     if pr.status == PairStatus.UNRESOLVED_LOCATION_CONFLICT]
        self.assertEqual(len(conflicts), 1)
        c = conflicts[0]
        self.assertEqual(c.t1.tag, "P01-007")
        self.assertEqual(c.t2.tag, "P01-007")
        self.assertGreater(c.distance_m, 1.0)      # 默认容差 1 m
        # 矛盾对不得被当成 survivor / mortality / ingrowth 任何一类
        statuses = {pr.status for pr in pairs}
        conflict_tags = {"P01-007"}
        for st in (PairStatus.SURVIVOR, PairStatus.MORTALITY, PairStatus.INGROWTH):
            self.assertFalse(
                any((pr.t1 and pr.t1.tag in conflict_tags)
                    or (pr.t2 and pr.t2.tag in conflict_tags)
                    for pr in pairs if pr.status == st),
                f"位置矛盾对被错误归入 {st}",
            )

    def test_missing_is_distinct_from_death(self):
        """P01-006 胸径漏测 -> 缺测挂起，不得判死亡；P01-005 才是死亡。"""
        pairs = match_trees(t1=self.p["t1"], t2=self.p["t2"],
                            crosswalk=self.p["crosswalk"])
        by_tag = {}
        for pr in pairs:
            for t in (pr.t1, pr.t2):
                if t is not None:
                    by_tag[t.tag] = pr
        self.assertEqual(by_tag["P01-005"].status, PairStatus.MORTALITY)
        self.assertEqual(by_tag["P01-006"].status, PairStatus.SURVIVOR)
        # survivor 但 t2 dbh 缺失，components 层必须把它归入 missing
        self.assertIsNone(by_tag["P01-006"].t2.dbh_cm)

    def test_ingrowth_and_below_threshold(self):
        pairs = match_trees(t1=self.p["t1"], t2=self.p["t2"],
                            crosswalk=self.p["crosswalk"])
        by_status = self._by_status(pairs)
        ingrowth_tags = {pr.t2.tag for pr in by_status.get(PairStatus.INGROWTH, [])}
        self.assertEqual(ingrowth_tags, {"P01-201"})
        below = {pr.t2.tag for pr in by_status.get(PairStatus.BELOW_THRESHOLD_T2, [])}
        self.assertEqual(below, {"P01-202"})


if __name__ == "__main__":
    unittest.main()
