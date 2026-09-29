"""端到端：用全部虚构样地模拟 services.run_analysis 的计算组装，
并逐项核对 README 承诺的四个验收点在同一流程里同时成立。"""

import json
import unittest
from pathlib import Path

from fixtures import ALL_PLOTS, STRATUM_AREAS_HA, make_book
from core.components import PlotInputs, compute_plot_components
from core.weighting import estimate_population, naive_pooled_estimate

ROOT = Path(__file__).resolve().parents[1]


class TestEndToEndFixtureFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.book = make_book()
        cls.results = {}
        cls.rows = []
        for factory in ALL_PLOTS:
            d = factory()
            inp = PlotInputs(
                plot_id=d["plot_id"], stratum_id=d["stratum_id"],
                area_ha=d["area_ha"], t1=d["t1"], t2=d["t2"],
                crosswalk=d["crosswalk"])
            r = compute_plot_components(inp, cls.book.get("eq-2015-v1"))
            cls.results[d["plot_id"]] = r
            cls.rows.append(r.per_ha_row())
        cls.pop = estimate_population(cls.rows,
                                      stratum_areas_ha=STRATUM_AREAS_HA)

    def test_acceptance_renumber(self):
        """验收点 1：复测改号被交叉表识别为同株，且贡献了生长量。"""
        tags = self.results["P01"].growth.source["tree_tags"]
        self.assertIn("P01-104", tags)

    def test_acceptance_unequal_area(self):
        """验收点 2：面积不等样地 -> 每公顷换算 + 分层加权 ≠ 朴素平均乘面积。"""
        naive = naive_pooled_estimate(
            self.rows, total_area_ha=sum(STRATUM_AREAS_HA.values()))
        for key in ("growth_kg_ha", "mortality_kg_ha", "ingrowth_kg_ha"):
            self.assertNotAlmostEqual(
                self.pop.totals_kg[key], naive["totals_kg"][key], places=3)

    def test_acceptance_unit_error_blocked(self):
        """验收点 3：单位错误记录在边界被拦截（12.5 m 胸径）。"""
        from core.units import UnitPlausibilityError, convert_dbh_to_cm
        with self.assertRaises(UnitPlausibilityError):
            convert_dbh_to_cm([12.5], ["m"])

    def test_acceptance_frozen_release(self):
        """验收点 4：v1 结果不随 v2 发布而改变。"""
        before = self.results["P01"].growth.biomass_kg
        book = make_book()  # 重新注册（含 v2）
        d = ALL_PLOTS[0]()
        again = compute_plot_components(
            PlotInputs(plot_id=d["plot_id"], stratum_id=d["stratum_id"],
                       area_ha=d["area_ha"], t1=d["t1"], t2=d["t2"],
                       crosswalk=d["crosswalk"]),
            book.get("eq-2015-v1"))
        self.assertEqual(before, again.growth.biomass_kg)
        with self.assertRaises(Exception):
            book.require_same_release_for_approved_run(
                approved_release_id="eq-2015-v1",
                requested_release_id="eq-2024-v2")

    def test_all_three_components_have_source_and_uncertainty(self):
        """每个分量都必须输出来源与不确定性假设。"""
        for plot_id, res in self.results.items():
            for comp in (res.growth, res.mortality, res.ingrowth):
                self.assertTrue(comp.source["tree_tags"] or comp.n_trees == 0)
                self.assertIn("release_id", comp.source)
                self.assertIn("measurement_units", comp.source)
                self.assertIn("sampling", comp.uncertainty)
                self.assertIn("missing_treatment", comp.uncertainty)

    def test_distinct_zero_missing_dead_counts(self):
        p01 = self.results["P01"]
        # 零生长、缺测、死亡三者株号集合互不相交
        z = set(p01.zero_growth_tags)
        m = set(p01.missing_measurement_tags)
        d = set(p01.mortality.source["tree_tags"])
        self.assertTrue(z and m and d)
        self.assertFalse(z & m or z & d or m & d)

    def test_fixture_json_is_valid_and_unit_explicit(self):
        data = json.loads((ROOT / "data/fixtures/surveys.json").read_text())
        for t in data["trees"]:
            self.assertIn(t["dbh_unit"], {"mm", "cm", "m", "in"})
            self.assertIn(t["height_unit"], {"mm", "cm", "dm", "m", "ft"})
            # 缺测木：dbh_value 为 null 而不是 0
            if t["tag"] == "P01-006" and t["survey_no"] == "T2-2024":
                self.assertIsNone(t["dbh_value"])


if __name__ == "__main__":
    unittest.main()
