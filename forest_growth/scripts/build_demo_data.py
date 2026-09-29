#!/usr/bin/env python3
"""生成前端离线演示用 demoData.js（调用同一套 core 计算，避免逻辑分叉）。"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "tests"))

from fixtures import ALL_PLOTS, STRATUM_AREAS_HA, make_book  # noqa: E402
from core.components import PlotInputs, compute_plot_components  # noqa: E402
from core.weighting import estimate_population  # noqa: E402
from dataclasses import asdict  # noqa: E402
import math  # noqa: E401


def obs(o):
    if o is None:
        return None
    d = asdict(o)
    d["status"] = o.status.value
    return d


def comp(c):
    return {"component": c.component, "n_trees": c.n_trees,
            "biomass_kg": c.biomass_kg,
            "biomass_kg_per_ha": c.biomass_kg_per_ha,
            "mean_dbh_increment_cm": c.mean_dbh_increment_cm,
            "source": c.source, "uncertainty": c.uncertainty}


def clean(v):
    if isinstance(v, float) and math.isnan(v):
        return None
    if isinstance(v, dict):
        return {k: clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [clean(x) for x in v]
    return v


book = make_book()
release = book.get("eq-2015-v1")
plot_payloads, rows = [], []
plot_features = []
for f in ALL_PLOTS:
    d = f()
    inp = PlotInputs(plot_id=d["plot_id"], stratum_id=d["stratum_id"],
                     area_ha=d["area_ha"], t1=d["t1"], t2=d["t2"],
                     crosswalk=d["crosswalk"])
    r = compute_plot_components(inp, release)
    rows.append(r.per_ha_row())
    pairs = [{"status": p.status.value,
              "tag_t1": p.t1.tag if p.t1 else None,
              "tag_t2": p.t2.tag if p.t2 else None,
              "distance_m": p.distance_m, "matched_via": p.matched_via,
              "note": p.note,
              "t1": obs(p.t1), "t2": obs(p.t2)} for p in r.pairs]
    plot_payloads.append({
        "plot_id": r.plot_id, "stratum_id": r.stratum_id,
        "area_ha": r.area_ha,
        "growth": comp(r.growth), "mortality": comp(r.mortality),
        "ingrowth": comp(r.ingrowth),
        "zero_growth_tags": r.zero_growth_tags,
        "negative_growth_tags": r.negative_growth_tags,
        "missing_measurement_tags": r.missing_measurement_tags,
        "unresolved_tags": r.unresolved_tags,
        "balance_check": r.balance_check, "pairs": pairs,
    })

pop = estimate_population(rows, stratum_areas_ha=STRATUM_AREAS_HA)
surveys = json.loads((ROOT / "data/fixtures/surveys.json").read_text())["plots"]

payload = {
    "survey_t1": "T1-2019", "survey_t2": "T2-2024",
    "release_id": release.release_id,
    "population": clean({
        "totals_kg": pop.totals_kg, "se_kg": pop.se_kg,
        "ci95_kg": {k: list(v) for k, v in pop.ci95_kg.items()},
        "degrees_of_freedom": pop.degrees_of_freedom,
        "method": pop.method, "source": pop.source,
        "uncertainty": pop.uncertainty,
    }),
    "plots": [clean(p) for p in plot_payloads],
    "_plots": [
        {"plot_id": p["plot_id"], "stratum_code": p["stratum_code"],
         "area_ha": p["area_ha"], "boundary": p["boundary"],
         "centroid": p["centroid"]}
        for p in surveys
    ],
}

out = ROOT / "frontend/src/demoData.js"
out.write_text(
    "// 由 scripts/build_demo_data.py 自动生成（与后端共用 core 计算逻辑）\n"
    "// 仅在 DRF 后端不可达时用于界面演示；正式数据以 /api 为准。\n"
    "const demoData = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n\n"
    "export default demoData;\n",
    encoding="utf-8")
print("written:", out)
