import math
import unittest

from fixtures import make_book, plot_p01
from core.components import PlotInputs, compute_plot_components
from core.remeasure import PairStatus


class TestComponents(unittest.TestCase):
    def setUp(self):
        d = plot_p01()
        self.inp = PlotInputs(
            plot_id=d["plot_id"], stratum_id=d["stratum_id"], area_ha=d["area_ha"],
            t1=d["t1"], t2=d["t2"], crosswalk=d["crosswalk"],
        )
        self.release = make_book().get("eq-2015-v1")
        self.res = compute_plot_components(self.inp, self.release)

    def test_true_zero_growth_kept_as_survivor(self):
        """P01-003 Δdbh=0.1 cm ≤ 0.3 cm 误差：真实零生长，保留且 Δ 记 0。"""
        self.assertIn("P01-003", self.res.zero_growth_tags)
        self.assertNotIn("P01-003", self.res.missing_measurement_tags)
        self.assertIsNotNone(self.res.growth.mean_dbh_increment_cm)
        # 零生长株仍计入生长株数（Δ=0），不是剔除
        self.assertGreaterEqual(self.res.growth.n_trees, 4)

    def test_missing_measurement_excluded_not_zero_filled(self):
        """P01-006 缺胸径：缺测，不插补、不计零。"""
        self.assertIn("P01-006", self.res.missing_measurement_tags)
        self.assertNotIn("P01-006", self.res.zero_growth_tags)
        self.assertTrue(
            self.res.growth.uncertainty["missing_treatment"].startswith("完整木分析"),
        )

    def test_mortality_uses_t1_biomass_and_is_distinct(self):
        tags = self.res.mortality.source["tree_tags"]
        self.assertEqual(tags, ["P01-005"])
        self.assertGreater(self.res.mortality.biomass_kg, 0.0)
        self.assertEqual(self.res.mortality.n_trees, 1)

    def test_ingrowth_uses_t2_biomass(self):
        self.assertEqual(self.res.ingrowth.source["tree_tags"], ["P01-201"])
        self.assertGreater(self.res.ingrowth.biomass_kg, 0.0)

    def test_location_conflict_excluded_from_all_components(self):
        self.assertIn("P01-007", self.res.unresolved_tags)
        for comp in (self.res.growth, self.res.mortality, self.res.ingrowth):
            self.assertNotIn("P01-007", comp.source["tree_tags"])

    def test_per_hectare_scaling_and_balance(self):
        ha = self.inp.area_ha
        self.assertAlmostEqual(
            self.res.growth.biomass_kg_per_ha,
            self.res.growth.biomass_kg / ha, places=6)
        # 已决个体上的平衡恒等式：B2 = B1 + 生长 - 死亡 + 进界
        b = self.res.balance_check
        self.assertAlmostEqual(b["residual_kg"], 0.0, places=4)

    def test_source_and_uncertainty_documented(self):
        for comp in (self.res.growth, self.res.mortality, self.res.ingrowth):
            self.assertIn("release_id", comp.source)
            self.assertEqual(comp.source["release_id"], "eq-2015-v1")
            self.assertIn("measurement_units", comp.source)
            self.assertEqual(comp.source["measurement_units"]["dbh"], "cm")
            self.assertIn("equation_mean_cv", comp.uncertainty)
            self.assertIn("missing_treatment", comp.uncertainty)


if __name__ == "__main__":
    unittest.main()
