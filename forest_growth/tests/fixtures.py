"""测试共用夹具：虚构方程集与四片样地两次调查数据。"""

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from core.allometry import AllometricEquation, EquationBook, EquationRelease
from core.remeasure import TreeObs, TreeStatus


def make_book() -> EquationBook:
    """两版方程 release：v1 已确认，v2 仅用于验证「不静默改变」。"""
    book = EquationBook()
    v1 = EquationRelease(
        release_id="eq-2015-v1",
        published_on=date(2015, 3, 1),
        description="研究站 2015 年马尾松/杉木地上生物量方程（虚构，仅测试）",
        equations=(
            # 罗云翔等风格的幂函数：AGB = 0.1056 * D^2.40（虚构参数）
            AllometricEquation(
                equation_id="PIMA-AGB-2015", version="1.0",
                form="power_dbh", params=(0.1056, 2.40),
                biomass_component="agb_oven_dry_kg",
                species=frozenset({"PIMA"}),       # Pinus massoniana 马尾松
                dbh_domain_cm=(5.0, 80.0), region="南方低山丘陵",
                residual_cv=0.18,
                source_citation="虚构文献: 罗云翔 2015 马尾松生物量模型(测试用)",
                published_on=date(2015, 3, 1),
            ),
            AllometricEquation(
                equation_id="CULA-AGB-2015", version="1.0",
                form="power_dbh_height", params=(0.071, 2.10, 0.65),
                biomass_component="agb_oven_dry_kg",
                species=frozenset({"CULA"}),       # Cunninghamia lanceolata 杉木
                dbh_domain_cm=(5.0, 60.0), region="南方低山丘陵",
                residual_cv=0.15, needs_height=True,
                source_citation="虚构文献: 陈宗昊 2015 杉树干材+树高方程(测试用)",
                published_on=date(2015, 3, 1),
            ),
        ),
    )
    v2 = EquationRelease(
        release_id="eq-2024-v2",
        published_on=date(2024, 6, 1),
        description="2024 修订：马尾松参数更新（虚构）；杉木沿用 v1",
        equations=(
            AllometricEquation(
                equation_id="PIMA-AGB-2024", version="2.0",
                form="power_dbh", params=(0.1180, 2.38),
                biomass_component="agb_oven_dry_kg",
                species=frozenset({"PIMA"}),
                dbh_domain_cm=(5.0, 90.0), region="南方低山丘陵",
                residual_cv=0.16,
                source_citation="虚构文献: 罗云翔 2024 马尾松修订模型(测试用)",
                published_on=date(2024, 6, 1),
            ),
            AllometricEquation(
                equation_id="CULA-AGB-2015", version="1.0",
                form="power_dbh_height", params=(0.071, 2.10, 0.65),
                biomass_component="agb_oven_dry_kg",
                species=frozenset({"CULA"}),
                dbh_domain_cm=(5.0, 60.0), region="南方低山丘陵",
                residual_cv=0.15, needs_height=True,
                source_citation="虚构文献: 陈宗昊 2015 杉树干材+树高方程(测试用)",
                published_on=date(2015, 3, 1),
            ),
        ),
    )
    book.publish(v1)
    book.publish(v2)
    return book


# ---------------------------------------------------------------------------
# 样地 P01（层 H1，面积 0.06 ha = 600 m²）：覆盖复测改号、零生长、缺测、
# 死亡、进界、同号位置矛盾。
# ---------------------------------------------------------------------------
def plot_p01():
    t1 = [
        TreeObs("P01-001", "PIMA", TreeStatus.ALIVE, 5.0, 5.0, 12.0, 9.0),
        TreeObs("P01-002", "PIMA", TreeStatus.ALIVE, 8.0, 3.0, 14.5, 10.5),
        # 真实零生长：两期胸径差在 0.3 cm 卡尺误差内
        TreeObs("P01-003", "CULA", TreeStatus.ALIVE, 12.0, 7.0, 18.0, 13.0),
        # 复测改号：外业确认 P01-004 -> P01-104（位置一致）
        TreeObs("P01-004", "PIMA", TreeStatus.ALIVE, 16.0, 9.0, 20.0, 14.0),
        # t2 确认死亡（伐桩）
        TreeObs("P01-005", "CULA", TreeStatus.ALIVE, 20.0, 12.0, 22.0, 15.0),
        # t2 树在但胸径漏测 -> 缺测（不是零生长）
        TreeObs("P01-006", "PIMA", TreeStatus.ALIVE, 22.0, 15.0, 24.0, 16.0),
        # 同号位置矛盾：t2 的 P01-007 出现在 18 m 外，疑似重号
        TreeObs("P01-007", "PIMA", TreeStatus.ALIVE, 3.0, 20.0, 16.2, 11.0),
        TreeObs("P01-008", "CULA", TreeStatus.ALIVE, 25.0, 6.0, 10.0, 8.0),
    ]
    t2 = [
        TreeObs("P01-001", "PIMA", TreeStatus.ALIVE, 5.05, 5.02, 12.8, 9.4),
        TreeObs("P01-002", "PIMA", TreeStatus.ALIVE, 8.0, 3.05, 15.3, 11.0),
        TreeObs("P01-003", "CULA", TreeStatus.ALIVE, 12.0, 7.0, 18.1, 13.1),
        TreeObs("P01-104", "PIMA", TreeStatus.ALIVE, 16.05, 9.02, 21.2, 14.6),
        TreeObs("P01-005", "CULA", TreeStatus.DEAD, 20.0, 12.0, None, None,
                remark="伐桩，确认死亡"),
        TreeObs("P01-006", "PIMA", TreeStatus.ALIVE, 22.0, 15.0, None, None,
                remark="胸径漏测"),
        TreeObs("P01-007", "PIMA", TreeStatus.ALIVE, 21.0, 4.0, 17.0, 12.0,
                remark="编号漆字模糊，疑似补号"),
        TreeObs("P01-008", "CULA", TreeStatus.ALIVE, 25.0, 6.02, 10.9, 8.5),
        # 进界木
        TreeObs("P01-201", "PIMA", TreeStatus.ALIVE, 10.0, 18.0, 6.2, 4.5),
        # 测到但未达 5 cm 起测径阶：不计进界
        TreeObs("P01-202", "CULA", TreeStatus.ALIVE, 14.0, 2.0, 3.4, 2.6),
    ]
    crosswalk = {"P01-004": "P01-104"}
    return {
        "plot_id": "P01", "stratum_id": "H1", "area_ha": 0.06,
        "t1": t1, "t2": t2, "crosswalk": crosswalk,
    }


# ---------------------------------------------------------------------------
# 样地 P02（层 H1，面积 0.08 ha）：面积不同；正常生长 + 一株死亡 + 一株进界。
# ---------------------------------------------------------------------------
def plot_p02():
    t1 = [
        TreeObs("P02-001", "PIMA", TreeStatus.ALIVE, 4.0, 4.0, 15.0, 11.0),
        TreeObs("P02-002", "CULA", TreeStatus.ALIVE, 9.0, 9.0, 19.0, 14.0),
        TreeObs("P02-003", "PIMA", TreeStatus.ALIVE, 14.0, 3.0, 23.0, 16.5),
    ]
    t2 = [
        TreeObs("P02-001", "PIMA", TreeStatus.ALIVE, 4.05, 4.0, 16.1, 11.6),
        TreeObs("P02-002", "CULA", TreeStatus.DEAD, 9.0, 9.0, None, None,
                remark="枯立木"),
        TreeObs("P02-003", "PIMA", TreeStatus.ALIVE, 14.02, 3.02, 24.1, 17.0),
        TreeObs("P02-101", "CULA", TreeStatus.ALIVE, 20.0, 20.0, 7.0, 5.0),
    ]
    return {
        "plot_id": "P02", "stratum_id": "H1", "area_ha": 0.08,
        "t1": t1, "t2": t2, "crosswalk": {},
    }


# ---------------------------------------------------------------------------
# 样地 P03、P04（层 H2，各 0.05 ha）：让两层都有 ≥2 个样地方差估计。
# ---------------------------------------------------------------------------
def plot_p03():
    t1 = [
        TreeObs("P03-001", "CULA", TreeStatus.ALIVE, 2.0, 2.0, 11.0, 8.5),
        TreeObs("P03-002", "PIMA", TreeStatus.ALIVE, 7.0, 6.0, 17.0, 12.0),
    ]
    t2 = [
        TreeObs("P03-001", "CULA", TreeStatus.ALIVE, 2.0, 2.02, 12.0, 9.0),
        TreeObs("P03-002", "PIMA", TreeStatus.ALIVE, 7.02, 6.0, 18.2, 12.6),
        TreeObs("P03-101", "PIMA", TreeStatus.ALIVE, 11.0, 10.0, 5.6, 4.0),
    ]
    return {"plot_id": "P03", "stratum_id": "H2", "area_ha": 0.05,
            "t1": t1, "t2": t2, "crosswalk": {}}


def plot_p04():
    t1 = [
        TreeObs("P04-001", "PIMA", TreeStatus.ALIVE, 3.0, 8.0, 20.0, 14.0),
        TreeObs("P04-002", "CULA", TreeStatus.ALIVE, 8.0, 3.0, 13.0, 10.0),
    ]
    t2 = [
        TreeObs("P04-001", "PIMA", TreeStatus.ALIVE, 3.02, 8.0, 20.9, 14.4),
        TreeObs("P04-002", "CULA", TreeStatus.DEAD, 8.0, 3.0, None, None),
    ]
    return {"plot_id": "P04", "stratum_id": "H2", "area_ha": 0.05,
            "t1": t1, "t2": t2, "crosswalk": {}}


ALL_PLOTS = [plot_p01, plot_p02, plot_p03, plot_p04]
STRATUM_AREAS_HA = {"H1": 120.0, "H2": 80.0}
