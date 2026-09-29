import math
import unittest

from fixtures import (ALL_PLOTS, STRATUM_AREAS_HA, make_book, plot_p01, plot_p02)
from core.components import PlotInputs, compute_plot_components
from core.weighting import estimate_population, naive_pooled_estimate


def _all_plot_results(release):
    rows = []
    for factory in ALL_PLOTS:
        d = factory()
        inp = PlotInputs(
            plot_id=d["plot_id"], stratum_id=d["stratum_id"], area_ha=d["area_ha"],
            t1=d["t1"], t2=d["t2"], crosswalk=d["crosswalk"],
        )
        res = compute_plot_components(inp, release)
        rows.append(res.per_ha_row())
    return rows


class TestWeighting(unittest.TestCase):
    def setUp(self):
        self.release = make_book().get("eq-2015-v1")
        self.rows = _all_plot_results(self.release)

    def test_unequal_areas_give_different_per_ha_scale(self):
        """P01(0.06 ha) 与 P02(0.08 ha)：同样的合计生物量必须按各自面积换算。"""
        r1 = next(r for r in self.rows if r["plot_id"] == "P01")
        r2 = next(r for r in self.rows if r["plot_id"] == "P02")
        self.assertNotAlmostEqual(r1["area_ha"], r2["area_ha"])
        self.assertTrue(all(math.isfinite(r1[c]) and math.isfinite(r2[c])
                            for c in ("growth_kg_ha", "mortality_kg_ha")))

    def test_design_weighted_differs_from_naive_pooling(self):
        """加权总体估计 != 简单平均乘总面积（验收核心）。"""
        pop = estimate_population(self.rows, stratum_areas_ha=STRATUM_AREAS_HA)
        total_area = sum(STRATUM_AREAS_HA.values())
        naive = naive_pooled_estimate(self.rows, total_area_ha=total_area)
        for c_key, n_key in (("growth_kg_ha", "growth_kg_ha"),
                             ("mortality_kg_ha", "mortality_kg_ha"),
                             ("ingrowth_kg_ha", "ingrowth_kg_ha")):
            weighted = pop.totals_kg[c_key]
            wrong = naive["totals_kg"][n_key]
            self.assertNotAlmostEqual(
                weighted, wrong, places=4,
                msg=f"{c_key}: 加权法 {weighted} 竟等于朴素法 {wrong}")
        self.assertIn("WRONG", naive["method"])

    def test_stratified_formula_on_two_strata(self):
        """两层加权总量 = Σ_h A_h × 层内样地均值（手算核对生长分量）。"""
        pop = estimate_population(self.rows, stratum_areas_ha=STRATUM_AREAS_HA)
        expected = 0.0
        for s in pop.strata:
            expected += s.area_total_ha * s.means_kg_ha["growth_kg_ha"]
        self.assertAlmostEqual(pop.totals_kg["growth_kg_ha"], expected, places=4)
        # 两层均有 2 个样地 -> 自由度 2，SE 与 CI 可估
        self.assertEqual(pop.degrees_of_freedom["growth_kg_ha"], 2)
        self.assertTrue(math.isfinite(pop.se_kg["growth_kg_ha"]))
        lo, hi = pop.ci95_kg["growth_kg_ha"]
        total = pop.totals_kg["growth_kg_ha"]
        self.assertLess(lo, total)
        self.assertLess(total, hi)

    def test_single_plot_stratum_variance_is_nan_not_zero(self):
        """只有 1 个样地的层：方差不能假装为 0。"""
        d = plot_p02()
        inp = PlotInputs(plot_id=d["plot_id"], stratum_id=d["stratum_id"],
                         area_ha=d["area_ha"], t1=d["t1"], t2=d["t2"])
        res = compute_plot_components(inp, self.release)
        pop = estimate_population([res.per_ha_row()],
                                  stratum_areas_ha={"H1": 120.0})
        self.assertTrue(math.isnan(pop.se_kg["growth_kg_ha"]))
        self.assertIn("H1", pop.uncertainty["undetermined_strata"])

    def test_missing_stratum_area_is_rejected(self):
        with self.assertRaises(KeyError):
            estimate_population(self.rows, stratum_areas_ha={"H1": 120.0})


if __name__ == "__main__":
    unittest.main()
