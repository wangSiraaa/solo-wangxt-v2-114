"""ORM 模型与计算核心之间的桥接层。

所有「读数 -> 计算对象」的转换集中在此：单位在边界换算、方程 release
从数据库冻结 payload 重建、分析运行的方程变更保护也在这里执行。
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import date

from core.allometry import (
    AllometricEquation,
    EquationBook,
    EquationRelease,
    FrozenReleaseError,
)
from core.components import PlotInputs, compute_plot_components
from core.remeasure import TreeObs, TreeStatus
from core.weighting import estimate_population
from core.units import convert_dbh_to_cm, convert_height_to_m

from .validation import validate_record_units


# 进程内方程注册表（发布动作幂等）
_BOOK = EquationBook()


def build_release_from_payload(payload: dict) -> EquationRelease:
    equations = tuple(
        AllometricEquation(
            equation_id=e["equation_id"],
            version=e["version"],
            form=e["form"],
            params=tuple(e["params"]),
            biomass_component=e["biomass_component"],
            species=frozenset(e["species"]),
            dbh_domain_cm=tuple(e["dbh_domain_cm"]),
            region=e["region"],
            residual_cv=e["residual_cv"],
            source_citation=e["source_citation"],
            published_on=date.fromisoformat(e["published_on"]),
            needs_height=e.get("needs_height", False),
        )
        for e in payload["equations"]
    )
    return EquationRelease(
        release_id=payload["release_id"],
        published_on=date.fromisoformat(payload["published_on"]),
        description=payload["description"],
        equations=equations,
    )


def get_release(release_model) -> EquationRelease:
    """从数据库取冻结 release；注册表幂等，保证重算结果可复现。"""
    rid = release_model.release_id
    if rid not in _BOOK.release_ids:
        _BOOK.publish(build_release_from_payload(release_model.payload))
    return _BOOK.get(rid)


def tree_obs_from_record(rec) -> TreeObs:
    """TreeRecord -> 计算核心 TreeObs（边界处做单位换算与合理性核对）。"""
    if rec.dbh_value is None:
        dbh_cm = None
    else:
        dbh_cm = float(convert_dbh_to_cm(
            [rec.dbh_value], [rec.dbh_unit], record_ids=[rec.tag])[0])
    if rec.height_value is None:
        height_m = None
    else:
        height_m = float(convert_height_to_m(
            [rec.height_value], [rec.height_unit], record_ids=[rec.tag])[0])
    return TreeObs(
        tag=rec.tag, species=rec.species_code,
        status=TreeStatus(rec.status),
        x_m=rec.plot_x_m, y_m=rec.plot_y_m,   # 由 annotate 注入
        dbh_cm=dbh_cm, height_m=height_m,
        remark=rec.remark,
    )


def _validate_run_release_policy(*, approved_run, requested_release_id: str,
                                 allow_recreate: bool) -> str:
    if approved_run is None or approved_run.status != "approved":
        return requested_release_id
    return _BOOK.require_same_release_for_approved_run(
        approved_release_id=approved_run.equation_release.release_id,
        requested_release_id=requested_release_id,
        allow_recreate=allow_recreate,
    )


def run_analysis(*, run, release_model, plot_inputs_by_id: dict,
                 stratum_areas_ha: dict, allow_recreate: bool = False) -> dict:
    """执行一次分析运行并写回 result_payload（调用方负责事务与持久化）。"""
    # 已确认 run 的方程冻结保护
    _validate_run_release_policy(
        approved_run=run if run.pk else None,
        requested_release_id=release_model.release_id,
        allow_recreate=allow_recreate,
    )
    release = get_release(release_model)

    plot_results, rows = [], []
    for inp in plot_inputs_by_id.values():
        res = compute_plot_components(inp, release)
        plot_results.append(res)
        rows.append(res.per_ha_row())

    population = estimate_population(rows, stratum_areas_ha=stratum_areas_ha)

    payload = {
        "survey_t1": run.survey_t1.survey_no,
        "survey_t2": run.survey_t2.survey_no,
        "release_id": release.release_id,
        "population": {
            "totals_kg": population.totals_kg,
            "se_kg": _clean(population.se_kg),
            "ci95_kg": {k: list(v) for k, v in population.ci95_kg.items()},
            "degrees_of_freedom": population.degrees_of_freedom,
            "method": population.method,
            "source": population.source,
            "uncertainty": population.uncertainty,
        },
        "plots": [_plot_payload(r) for r in plot_results],
    }
    return payload


def _clean(d):
    import math
    return {k: (None if isinstance(v, float) and math.isnan(v) else v)
            for k, v in d.items()}


def _component_payload(c):
    return {
        "component": c.component,
        "n_trees": c.n_trees,
        "biomass_kg": c.biomass_kg,
        "biomass_kg_per_ha": c.biomass_kg_per_ha,
        "mean_dbh_increment_cm": c.mean_dbh_increment_cm,
        "source": c.source,
        "uncertainty": c.uncertainty,
    }


def _plot_payload(res):
    return {
        "plot_id": res.plot_id,
        "stratum_id": res.stratum_id,
        "area_ha": res.area_ha,
        "growth": _component_payload(res.growth),
        "mortality": _component_payload(res.mortality),
        "ingrowth": _component_payload(res.ingrowth),
        "zero_growth_tags": res.zero_growth_tags,
        "negative_growth_tags": res.negative_growth_tags,
        "missing_measurement_tags": res.missing_measurement_tags,
        "unresolved_tags": res.unresolved_tags,
        "balance_check": res.balance_check,
        "pairs": [
            {
                "status": p.status.value,
                "tag_t1": p.t1.tag if p.t1 else None,
                "tag_t2": p.t2.tag if p.t2 else None,
                "distance_m": p.distance_m,
                "matched_via": p.matched_via,
                "note": p.note,
                "t1": _obs(p.t1),
                "t2": _obs(p.t2),
            }
            for p in res.pairs
        ],
    }


def _obs(o):
    return None if o is None else asdict(o) | {"status": o.status.value}
