"""按抽样设计加权的总体估计。

流程（与「全部树木简单平均后乘面积」的错误做法严格区分）：

1. 样地内单木合计先除以样地面积 -> 每公顷值 ``y_ha``；
   面积不等的样地由此自然得到正确尺度。
2. 分层估计：样地均值 ``(1/n_h) Σ w_i y_ha,i``，``w_i`` 为单木包含概率
   倒数在样地内的归一化权重（等概率抽样时全为 1）。
3. 总体：``Σ_h A_h · ŷ_h``，``A_h`` 为层总面积（公顷）。
4. 方差：层内样地间方差 / n_h，按 A_h² 汇总；给出 SE、自由度与 95% t 区间。

另提供 :func:`naive_pooled_estimate` —— 故意实现的错误方法，
只用于验收对照与测试，报告中必须标注 ``method_warning``。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

import numpy as np
from .scipy_stats_compat import t as t_dist  # 见本目录兼容垫片

from .components import PlotResult

COMPONENTS = ("growth_kg_ha", "mortality_kg_ha", "ingrowth_kg_ha")


@dataclass
class StratumResult:
    stratum_id: str
    area_total_ha: float
    n_plots: float
    means_kg_ha: Dict[str, float]
    var_means_kg_ha: Dict[str, float]
    totals_kg: Dict[str, float]


@dataclass
class PopulationResult:
    components: List[str]
    totals_kg: Dict[str, float]
    se_kg: Dict[str, float]
    ci95_kg: Dict[str, tuple]
    strata: List[StratumResult]
    degrees_of_freedom: Dict[str, int]
    method: str = "stratified_design_weighted"
    source: Dict = field(default_factory=dict)
    uncertainty: Dict = field(default_factory=dict)


@dataclass(frozen=True)
class PlotWeight:
    plot_id: str
    stratum_id: str
    tree_inclusion_weights: Optional[Dict[str, float]] = None  # tag -> 1/π


def estimate_population(
    plot_rows: Sequence[Dict[str, float]],
    *,
    stratum_areas_ha: Dict[str, float],
    plot_weights: Optional[Sequence[PlotWeight]] = None,
    confidence: float = 0.95,
) -> PopulationResult:
    """分层抽样总体估计。

    Parameters
    ----------
    plot_rows : 每行必须含 plot_id, stratum_id, area_ha 以及
        growth_kg_ha / mortality_kg_ha / ingrowth_kg_ha（来自 PlotResult）。
    stratum_areas_ha : 层总面积（公顷）。
    plot_weights : 可选的单木包含概率倒数；样地分量已是合计口径时，
        这些权重仅用于文档与未来的单木级扩展，等概率设计可省略。
    """
    weights_by_plot = {w.plot_id: w for w in (plot_weights or [])}
    rows_by_stratum: Dict[str, List[Dict[str, float]]] = {}
    for row in plot_rows:
        rows_by_stratum.setdefault(row["stratum_id"], []).append(row)

    strata_results: List[StratumResult] = []
    totals = {c: 0.0 for c in COMPONENTS}
    var_total = {c: 0.0 for c in COMPONENTS}
    dof = {c: 0 for c in COMPONENTS}

    for sid, rows in rows_by_stratum.items():
        if sid not in stratum_areas_ha:
            raise KeyError(f"缺少层 {sid} 的总面积 stratum_areas_ha")
        A_h = float(stratum_areas_ha[sid])
        n_h = len(rows)
        means, var_means, totals_h = {}, {}, {}
        for c in COMPONENTS:
            vals = np.array([r[c] for r in rows], dtype=float)
            if not np.all(np.isfinite(vals)):
                raise ValueError(f"层 {sid} 的 {c} 含非有限值，拒绝估计")
            mean_h = float(np.mean(vals))          # 等概率设计；单木权重在样地内已合计
            if n_h > 1:
                # 简单随机/系统抽样常用的样地间无偏方差
                s2 = float(np.var(vals, ddof=1))
                var_mean = s2 / n_h
            else:
                # n=1 无法从数据估计层内方差：显式记录为缺失，不假装为 0
                var_mean = float("nan")
            means[c] = mean_h
            var_means[c] = var_mean
            totals_h[c] = A_h * mean_h
            totals[c] += totals_h[c]
            if not math.isnan(var_mean):
                var_total[c] += A_h**2 * var_mean
                dof[c] += n_h - 1

        strata_results.append(StratumResult(
            stratum_id=sid, area_total_ha=A_h, n_plots=n_h,
            means_kg_ha=means, var_means_kg_ha=var_means, totals_kg=totals_h,
        ))

    se, ci = {}, {}
    alpha = 1.0 - confidence
    for c in COMPONENTS:
        v = var_total[c]
        se[c] = math.sqrt(v) if v > 0 else float("nan")
        if dof[c] > 0 and math.isfinite(se[c]):
            tcrit = float(t_dist.ppf(1 - alpha / 2, dof[c]))
            ci[c] = (totals[c] - tcrit * se[c], totals[c] + tcrit * se[c])
        else:
            ci[c] = (float("nan"), float("nan"))

    return PopulationResult(
        components=list(COMPONENTS),
        totals_kg=totals, se_kg=se, ci95_kg=ci, strata=strata_results,
        degrees_of_freedom=dof,
        source={
            "estimator": "Ŷ = Σ_h A_h · mean_i(y_ha,i);  y_ha,i = Σ_tree / area_i",
            "stratum_areas_ha": stratum_areas_ha,
            "n_plots": len(plot_rows),
            "weighting": (
                "样地等概率；单木包含概率权重经 PlotWeight 登记（本数据为等概率）"
                if plot_weights else "样地等概率，无单木不等概权重"),
        },
        uncertainty={
            "sampling": "分层估计，层内样地间方差/n_h，按 A_h² 汇总",
            "confidence": confidence,
            "undetermined_strata": [
                s.stratum_id for s in strata_results
                if any(math.isnan(v) for v in s.var_means_kg_ha.values())
            ],
            "note": ("仅 1 个样地的层无法估计层内方差，SE/CI 记为 NaN 而非 0；"
                     "测量误差与方程残差 CV 在样地分量 uncertainty 中给出，"
                     "需要联合传播时在分析运行中显式开启"),
        },
    )


def naive_pooled_estimate(
    plot_rows: Sequence[Dict[str, float]],
    *,
    total_area_ha: float,
) -> Dict[str, float]:
    """**错误方法（仅用于验收对照）**：把所有样地的每公顷值简单平均再乘总面积。

    正确做法见 :func:`estimate_population`。本函数同时提供一个更朴素的
    「单木平均乘面积」入口（见 README 验收说明），二者都必须在报告中标红。
    """
    arr = {c: np.mean([r[c] for r in plot_rows]) for c in COMPONENTS}
    return {
        "totals_kg": {c: arr[c] * total_area_ha for c in COMPONENTS},
        "method": "naive_mean_then_multiply_area (WRONG for stratified/unequal-area)",
        "method_warning": (
            "此结果未按抽样设计加权，也未正确处理不等面积样地，"
            "严禁作为研究站正式估计"),
    }
