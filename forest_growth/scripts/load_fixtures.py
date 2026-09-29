#!/usr/bin/env python3
"""把 data/fixtures/*.json 导入 PostGIS 数据库。

用法（在 backend/ 下，确保 DJANGO_SETTINGS_MODULE 可导入）：
    python3 scripts/load_fixtures.py --fixture data/fixtures/surveys.json

注意：导入会逐条经过 api.validation 的单位合理性核对，
单位错误记录会被拒绝并打印（不会静默换算入库）。
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--skip-equations", action="store_true")
    args = parser.parse_args()

    import django
    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "forest_station.settings")
    django.setup()

    from django.contrib.gis.geos import GEOSGeometry
    from django.db import transaction
    from inventory.models import (
        EquationReleaseModel, Plot, Stratum, Survey, TagCrosswalk, TreeRecord,
    )

    path = Path(args.fixture)
    data = json.loads(path.read_text(encoding="utf-8"))

    if path.name == "equations.json" and not args.skip_equations:
        for rel in data:
            _, created = EquationReleaseModel.objects.update_or_create(
                release_id=rel["release_id"],
                defaults={"published_on": rel["published_on"],
                          "description": rel["description"],
                          "payload": rel["payload"],
                          "is_active": rel["is_active"]},
            )
            print(("created " if created else "exists  ") + rel["release_id"])
        return

    with transaction.atomic():
        surveys = {}
        for s in data["surveys"]:
            obj, _ = Survey.objects.update_or_create(
                survey_no=s["survey_no"],
                defaults={"survey_date": date.fromisoformat(s["survey_date"]),
                          "status": s["status"],
                          "approved_by": s.get("approved_by", ""),
                          "remark": s.get("remark", "")})
            surveys[s["survey_no"]] = obj

        strata = {}
        for st in data["strata"]:
            obj, _ = Stratum.objects.update_or_create(
                code=st["code"],
                defaults={"name": st["name"], "area_ha": st["area_ha"]})
            strata[st["code"]] = obj

        plots = {}
        for p in data["plots"]:
            obj, _ = Plot.objects.update_or_create(
                plot_id=p["plot_id"],
                defaults={"stratum": strata[p["stratum_code"]],
                          "area_ha": p["area_ha"],
                          "boundary": GEOSGeometry(json.dumps(p["boundary"])),
                          "centroid": GEOSGeometry(json.dumps(p["centroid"]))})
            plots[p["plot_id"]] = obj

        n_ok = n_bad = 0
        from api.validation import validate_record_units, UnitPlausibilityError
        for tr in data["trees"]:
            try:
                validate_record_units(
                    tag=tr["tag"], dbh_value=tr["dbh_value"],
                    dbh_unit=tr["dbh_unit"], height_value=tr["height_value"],
                    height_unit=tr["height_unit"])
            except UnitPlausibilityError as exc:
                n_bad += 1
                print(f"[拒绝-单位错误] {tr['plot_id']} {tr['tag']}: {exc}")
                continue
            TreeRecord.objects.update_or_create(
                plot=plots[tr["plot_id"]], survey=surveys[tr["survey_no"]],
                tag=tr["tag"],
                defaults={"species_code": tr["species_code"],
                          "status": tr["status"],
                          "geom": GEOSGeometry(json.dumps(tr["geom"])),
                          "plot_x_m": tr["plot_x_m"], "plot_y_m": tr["plot_y_m"],
                          "dbh_value": tr["dbh_value"], "dbh_unit": tr["dbh_unit"],
                          "height_value": tr["height_value"],
                          "height_unit": tr["height_unit"],
                          "remark": tr.get("remark", "")})
            n_ok += 1

        for cw in data.get("crosswalks", []):
            TagCrosswalk.objects.update_or_create(
                plot=plots[cw["plot_id"]], survey_t1=surveys[cw["survey_t1"]],
                survey_t2=surveys[cw["survey_t2"]], tag_t1=cw["tag_t1"],
                defaults={"tag_t2": cw["tag_t2"],
                          "confirmed_by": cw.get("confirmed_by", ""),
                          "note": cw.get("note", "")})

    print(f"trees imported: {n_ok} ok, {n_bad} rejected (unit errors)")


if __name__ == "__main__":
    main()
