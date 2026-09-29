#!/usr/bin/env python3
"""从测试夹具生成数据库导入用 JSON（虚构数据）。

运行：python3 scripts/build_fixtures.py
产出：data/fixtures/equations.json、data/fixtures/surveys.json
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "tests"))

from fixtures import ALL_PLOTS, STRATUM_AREAS_HA, make_book  # noqa: E402

OUT = ROOT / "data" / "fixtures"

# 虚构中心点（福建低山丘陵一带，仅演示坐标；局部坐标平移得到 WGS84 点）
PLOT_ORIGINS = {
    "P01": (117.3200, 26.5500),
    "P02": (117.3550, 26.5720),
    "P03": (117.2800, 26.4900),
    "P04": (117.2650, 26.5050),
}
PLOT_SHAPE_M = (20.0, 30.0)   # 仅用于生成示意边界，面积以 area_ha 为准


def local_to_lnglat(plot_id: str, x_m, y_m):
    ox, oy = PLOT_ORIGINS[plot_id]
    if x_m is None:
        return ox, oy
    lat = oy + y_m / 111_320.0
    lng = ox + x_m / (111_320.0 * 0.894)   # cos(26.55°)≈0.894
    return round(lng, 8), round(lat, 8)


def polygon(plot_id):
    ox, oy = PLOT_ORIGINS[plot_id]
    w, h = PLOT_SHAPE_M
    pts = [(0, 0), (w, 0), (w, h), (0, h), (0, 0)]
    ring = [local_to_lnglat(plot_id, x, y) for x, y in pts]
    return {"type": "Polygon", "coordinates": [ring]}


def tree_json(plot_id, t, survey_no):
    lng, lat = local_to_lnglat(plot_id, t.x_m or 0.0, t.y_m or 0.0)
    return {
        "tag": t.tag,
        "species_code": t.species,
        "status": t.status.value,
        "geom": {"type": "Point", "coordinates": [lng, lat]},
        "plot_x_m": t.x_m,
        "plot_y_m": t.y_m,
        # 虚构原始数据中正常记录都以 cm / m 录入；
        # 单位错误的验收用例由测试单独构造，不污染正式夹具
        "dbh_value": t.dbh_cm,
        "dbh_unit": "cm",
        "height_value": t.height_m,
        "height_unit": "m",
        "remark": t.remark,
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    # ---- 方程 release -------
    book = make_book()
    releases = []
    for rid in book.release_ids:
        rel = book.get(rid)
        releases.append({
            "release_id": rel.release_id,
            "published_on": rel.published_on.isoformat(),
            "description": rel.description,
            "is_active": rid == "eq-2015-v1",
            "payload": {
                "release_id": rel.release_id,
                "published_on": rel.published_on.isoformat(),
                "description": rel.description,
                "equations": [
                    {
                        "equation_id": e.equation_id,
                        "version": e.version,
                        "form": e.form,
                        "params": list(e.params),
                        "biomass_component": e.biomass_component,
                        "species": sorted(e.species),
                        "dbh_domain_cm": list(e.dbh_domain_cm),
                        "region": e.region,
                        "residual_cv": e.residual_cv,
                        "source_citation": e.source_citation,
                        "published_on": e.published_on.isoformat(),
                        "needs_height": e.needs_height,
                        "allometric_formula_human": _formula_text(e),
                    }
                    for e in rel.equations
                ],
            },
        })
    (OUT / "equations.json").write_text(
        json.dumps(releases, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---- 分层 / 样地 / 调查 / 树木 -------
    plots_data = [f() for f in ALL_PLOTS]
    strata = {}
    for d in plots_data:
        strata.setdefault(d["stratum_id"], STRATUM_AREAS_HA[d["stratum_id"]])

    surveys = [
        {"survey_no": "T1-2019", "survey_date": "2019-08-15",
         "status": "approved", "approved_by": "林研站-周工",
         "remark": "第一次调查（虚构）"},
        {"survey_no": "T2-2024", "survey_date": "2024-08-20",
         "status": "approved", "approved_by": "林研站-周工",
         "remark": "第二次调查（虚构，五年间隔）"},
    ]

    plots, trees, crosswalks = [], [], []
    for d in plots_data:
        pid = d["plot_id"]
        plots.append({
            "plot_id": pid,
            "stratum_code": d["stratum_id"],
            "area_ha": d["area_ha"],
            "boundary": polygon(pid),
            "centroid": {"type": "Point",
                         "coordinates": list(PLOT_ORIGINS[pid])},
        })
        for t in d["t1"]:
            trees.append({"plot_id": pid, "survey_no": "T1-2019",
                          **tree_json(pid, t, "T1-2019")})
        for t in d["t2"]:
            trees.append({"plot_id": pid, "survey_no": "T2-2024",
                          **tree_json(pid, t, "T2-2024")})
        for old, new in d["crosswalk"].items():
            crosswalks.append({
                "plot_id": pid, "survey_t1": "T1-2019",
                "survey_t2": "T2-2024", "tag_t1": old, "tag_t2": new,
                "confirmed_by": "复测组-吴工",
                "note": "外业确认改号（漆字脱落重新编号）",
            })

    payload = {
        "meta": {
            "description": "虚构固定样地数据，仅用于系统演示与验收",
            "units": {"dbh": "cm（每条记录显式携带）",
                      "height": "m（每条记录显式携带）",
                      "biomass": "kg 烘干重"},
            "species": {
                "PIMA": "马尾松 Pinus massoniana",
                "CULA": "杉木 Cunninghamia lanceolata",
            },
            "measurement_error_assumption": {"dbh_sd_cm": 0.3,
                                             "height_sd_m": 0.5},
        },
        "strata": [{"code": k, "name": {"H1": "下坡马尾松层",
                                        "H2": "上坡杉木混交层"}[k],
                    "area_ha": v} for k, v in sorted(strata.items())],
        "surveys": surveys,
        "plots": plots,
        "trees": trees,
        "crosswalks": crosswalks,
    }
    (OUT / "surveys.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"written: {OUT/'equations.json'}")
    print(f"written: {OUT/'surveys.json'} "
          f"({len(plots)} plots, {len(trees)} tree records, "
          f"{len(crosswalks)} crosswalks)")


def _formula_text(e):
    if e.form == "power_dbh":
        a, b = e.params
        return f"AGB(kg) = {a} × D(cm)^{b}；适用树种: {sorted(e.species)}"
    if e.form == "power_dbh_height":
        a, b, c = e.params
        return (f"AGB(kg) = {a} × D(cm)^{b} × H(m)^{c}；"
                f"适用树种: {sorted(e.species)}")
    return e.form


if __name__ == "__main__":
    main()
