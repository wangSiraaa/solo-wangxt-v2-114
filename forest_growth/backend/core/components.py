"""单个样地的生长 / 死亡 / 进界分量计算。

三类概念严格区分（README 表格的代码实现）：

* **真实零生长**：两期都测到胸径且 |Δdbh| <= zero_growth_epsilon_cm
  （由胸径卡尺测量误差决定，默认 0.3 cm）—— 是有效 survivor，Δ=0 保留。
* **缺测**：身份确认但某一期没有测量（``dbh_cm is None``）—— 不插补、
  不计零，从生长量的完整木分析中剔除，并计入不确定性说明。
* **死亡**：t2 状态显式为 dead / 伐桩 —— 不与缺测混淆。

位置矛盾对一律不参与任何分量。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

import numpy as np

from .allometry import EquationRelease, first_order_biomass_cv
from .remeasure import MatchedPair, PairStatus, match_trees, TreeObs

DEFAULT_ZERO_GROWTH_EPSILON_CM = 0.3   # 胸径重复测量误差半宽
DEFAULT_DBH_MEASUREMENT_SD_CM = 0.3
DEFAULT_HEIGHT_MEASUREMENT_SD_M = 0.5


class NegativeGrowthError(ValueError):
    """存活木胸径负生长超出测量误差，疑似编号/测量错误，必须核实。"""


@dataclass(frozen=True)
class PlotInputs:
    plot_id: str
    area_ha: float
    t1: Sequence[TreeObs]
    t2: Sequence[TreeObs]
    stratum_id: str = "S1"
    crosswalk: Optional[Dict[str, str]] = None
    ingrowth_threshold_cm: float = 5.0
    xy_tolerance_m: float = 1.0
    zero_growth_epsilon_cm: float = DEFAULT_ZERO_GROWTH_EPSILON_CM


@dataclass
class ComponentEstimate:
    """一个分量的估计值、来源与不确定性假设。"""

    component: str                       # growth / mortality / ingrowth
    n_trees: int                         # 参与计算的株数（样地内）
    biomass_kg: float                    # 样地内合计 kg
    biomass_kg_per_ha: float
    mean_dbh_increment_cm: Optional[float] = None
    source: Dict = field(default_factory=dict)
    uncertainty: Dict = field(default_factory=dict)


@dataclass
class PlotResult:
    plot_id: str
    stratum_id: str
    area_ha: float
    pairs: List[MatchedPair]
    growth: ComponentEstimate
    mortality: ComponentEstimate
    ingrowth: ComponentEstimate
    # 分类清单（用于 React 个体复测视图与审计）
    zero_growth_tags: List[str] = field(default_factory=list)
    negative_growth_tags: List[str] = field(default_factory=list)
    missing_measurement_tags: List[str] = field(default_factory=list)
    unresolved_tags: List[str] = field(default_factory=list)
    balance_check: Dict = field(default_factory=dict)

    def per_ha_row(self) -> Dict[str, float]:
        return {
            "plot_id": self.plot_id,
            "stratum_id": self.stratum_id,
            "area_ha": self.area_ha,
            "growth_kg_ha": self.growth.biomass_kg_per_ha,
            "mortality_kg_ha": self.mortality.biomass_kg_per_ha,
            "ingrowth_kg_ha": self.ingrowth.biomass_kg_per_ha,
        }


def compute_plot_components(
    inp: PlotInputs,
    release: EquationRelease,
    *,
    biomass_component: str = "agb_oven_dry_kg",
    raise_on_negative: bool = False,
) -> PlotResult:
    """计算样地三分量（生物量口径，kg 与 kg/ha）。

    release 必须显式传入：每次计算都可追溯到具体方程集版本，
    已确认结果不会因登记了新方程而变化（release 本身不可变）。
    """
    if inp.area_ha <= 0:
        raise ValueError(f"样地 {inp.plot_id} 面积必须为正，得到 {inp.area_ha}")

    pairs = match_trees(
        t1=inp.t1, t2=inp.t2, crosswalk=inp.crosswalk,
        xy_tolerance_m=inp.xy_tolerance_m,
        ingrowth_threshold_cm=inp.ingrowth_threshold_cm,
    )

    growth_tags, zero_tags, neg_tags, missing_tags, unresolved_tags = [], [], [], [], []
    growth_b1, growth_b2, growth_dbh_inc, growth_cv2 = [], [], [], []

    mort_kg, mort_tags, mort_cv2 = [], [], []
    in_kg, in_tags, in_cv2 = [], [], []

    b1_total = 0.0   # t1 全部存活木（用于平衡核对）
    b2_total = 0.0   # t2 全部存活木 + 进界

    for p in pairs:
        if p.status == PairStatus.SURVIVOR:
            a, b = p.t1, p.t2
            growth_tags.append(b.tag)

            # 身份确认为存活但某一期胸径缺失：缺测，不查方程、不插补、不计零
            if a.dbh_cm is None or b.dbh_cm is None:
                missing_tags.append(b.tag)
                continue

            # 生物量（两期都算，便于平衡核对）
            eq1 = release.lookup(a.species, a.dbh_cm, biomass_component)
            eq2 = release.lookup(b.species, b.dbh_cm, biomass_component)
            ba = float(eq1.evaluate(a.dbh_cm, a.height_m))
            bb = float(eq2.evaluate(b.dbh_cm, b.height_m))
            b1_total += ba
            b2_total += bb

            delta = b.dbh_cm - a.dbh_cm
            if delta < -inp.zero_growth_epsilon_cm:
                neg_tags.append(b.tag)
                if raise_on_negative:
                    raise NegativeGrowthError(
                        f"样地 {inp.plot_id} 树木 {b.tag} 胸径增量 {delta:.2f} cm "
                        f"超出测量误差 ±{inp.zero_growth_epsilon_cm} cm，需核实"
                    )
                continue  # 负生长存疑：不参与生长合计
            if abs(delta) <= inp.zero_growth_epsilon_cm:
                zero_tags.append(b.tag)   # 真实零生长：Δ 视为 0，保留
                growth_dbh_inc.append(0.0)
                growth_b1.append(ba)
                growth_b2.append(bb)
                growth_cv2.append(first_order_biomass_cv(eq2) ** 2)
                continue

            growth_dbh_inc.append(delta)
            growth_b1.append(ba)
            growth_b2.append(bb)
            growth_cv2.append(first_order_biomass_cv(eq2) ** 2)

        elif p.status == PairStatus.MORTALITY:
            a = p.t1
            mort_tags.append(a.tag)
            eq = release.lookup(a.species, a.dbh_cm, biomass_component)
            bm = float(eq.evaluate(a.dbh_cm, a.height_m))
            mort_kg.append(bm)
            b1_total += bm
            mort_cv2.append(first_order_biomass_cv(eq) ** 2)

        elif p.status == PairStatus.INGROWTH:
            b = p.t2
            in_tags.append(b.tag)
            eq = release.lookup(b.species, b.dbh_cm, biomass_component)
            bi = float(eq.evaluate(b.dbh_cm, b.height_m))
            in_kg.append(bi)
            b2_total += bi
            in_cv2.append(first_order_biomass_cv(eq) ** 2)

        elif p.status == PairStatus.UNRESOLVED_MISSING:
            tag = (p.t1.tag if p.t1 else p.t2.tag)
            missing_tags.append(tag)
            unresolved_tags.append(tag)
        elif p.status == PairStatus.UNRESOLVED_LOCATION_CONFLICT:
            unresolved_tags.append(p.t1.tag)
        # BELOW_THRESHOLD_T2 不进任何分量

    growth_delta_kg = float(np.sum(np.asarray(growth_b2) - np.asarray(growth_b1))) \
        if growth_b2 else 0.0
    mortality_kg = float(np.sum(mort_kg)) if mort_kg else 0.0
    ingrowth_kg = float(np.sum(in_kg)) if in_kg else 0.0

    common_source = {
        "release_id": release.release_id,
        "biomass_component": biomass_component,
        "plot_id": inp.plot_id,
        "area_ha": inp.area_ha,
        "measurement_units": {"dbh": "cm", "height": "m", "biomass": "kg"},
    }
    missing_assumption = (
        "完整木分析（complete-case）：缺测木不插补、不计零，从生长均值中剔除；"
        "最坏情形见 uncertainty.missing_bounds")

    growth = ComponentEstimate(
        component="growth",
        n_trees=len(growth_dbh_inc),
        biomass_kg=growth_delta_kg,
        biomass_kg_per_ha=growth_delta_kg / inp.area_ha,
        mean_dbh_increment_cm=(float(np.mean(growth_dbh_inc))
                               if growth_dbh_inc else None),
        source={**common_source, "tree_tags": growth_tags,
                "kind": "两期实测胸径 + 异速方程推算两期生物量之差",
                "zero_growth_tags": zero_tags},
        uncertainty={
            "sampling": "样地层面方差在总体加权阶段估计",
            "measurement": {"dbh_sd_cm": DEFAULT_DBH_MEASUREMENT_SD_CM,
                            "height_sd_m": DEFAULT_HEIGHT_MEASUREMENT_SD_M,
                            "zero_growth_epsilon_cm": inp.zero_growth_epsilon_cm},
            "equation_mean_cv": (float(np.sqrt(np.mean(growth_cv2)))
                                 if growth_cv2 else None),
            "missing_treatment": missing_assumption,
            "n_missing": len(missing_tags),
        },
    )
    mortality = ComponentEstimate(
        component="mortality",
        n_trees=len(mort_tags),
        biomass_kg=mortality_kg,
        biomass_kg_per_ha=mortality_kg / inp.area_ha,
        source={**common_source, "tree_tags": mort_tags,
                "kind": "t2 确认死亡（伐桩/枯立），生物量取 t1 实测胸径推算"},
        uncertainty={
            "sampling": "样地层面方差在总体加权阶段估计",
            "measurement": {"dbh_sd_cm": DEFAULT_DBH_MEASUREMENT_SD_CM},
            "equation_mean_cv": (float(np.sqrt(np.mean(mort_cv2)))
                                 if mort_cv2 else None),
            "missing_treatment": "只有 t2 未见、无死亡证据的个体记为缺测而非死亡",
        },
    )
    ingrowth = ComponentEstimate(
        component="ingrowth",
        n_trees=len(in_tags),
        biomass_kg=ingrowth_kg,
        biomass_kg_per_ha=ingrowth_kg / inp.area_ha,
        source={**common_source, "tree_tags": in_tags,
                "kind": f"t2 新出现且胸径 >= {inp.ingrowth_threshold_cm} cm，"
                        f"生物量取 t2 实测胸径推算"},
        uncertainty={
            "sampling": "样地层面方差在总体加权阶段估计",
            "measurement": {"dbh_sd_cm": DEFAULT_DBH_MEASUREMENT_SD_CM},
            "equation_mean_cv": (float(np.sqrt(np.mean(in_cv2)))
                                 if in_cv2 else None),
            "missing_treatment": "未达起测径阶个体单列，不计入进界",
        },
    )

    # 平衡核对：B2 ≈ B1 + 生长 - 死亡 + 进界（只在已确认身份的个体之间）
    expected_b2 = b1_total + growth_delta_kg - mortality_kg + ingrowth_kg
    balance = {
        "b1_kg_resolved": b1_total,
        "b2_kg_resolved": b2_total,
        "expected_b2_kg": expected_b2,
        "residual_kg": b2_total - expected_b2,
        "note": "残差应≈0；不为零说明有缺测/未决个体被排除在分量外",
    }

    return PlotResult(
        plot_id=inp.plot_id, stratum_id=inp.stratum_id, area_ha=inp.area_ha,
        pairs=pairs, growth=growth, mortality=mortality, ingrowth=ingrowth,
        zero_growth_tags=zero_tags, negative_growth_tags=neg_tags,
        missing_measurement_tags=missing_tags, unresolved_tags=unresolved_tags,
        balance_check=balance,
    )
