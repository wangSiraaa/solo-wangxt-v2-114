"""两次调查的个体身份匹配。

硬性规则
--------
* 外业复测交叉表（tag 改号映射）优先；
* 同号匹配必须通过平面位置容差检查；编号相同但位置矛盾时，输出
  ``UNRESOLVED_LOCATION_CONFLICT``，**先核实，不能直接认成同株**，
  既不计生长也不计死亡/进界；
* 「第二次没测到」与「第二次确认死亡」严格区分（缺测 vs 死亡）。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Sequence, Tuple

DEFAULT_XY_TOLERANCE_M = 1.0


class PairStatus(str, Enum):
    SURVIVOR = "survivor"                    # 两次均存活且身份确认
    MORTALITY = "mortality"                  # t1 存活、t2 确认死亡（伐桩/枯立）
    INGROWTH = "ingrowth"                    # t2 新进界（达起测径阶、无 t1 前身）
    UNRESOLVED_LOCATION_CONFLICT = "unresolved_location_conflict"
    UNRESOLVED_MISSING = "unresolved_missing"  # 身份/死亡无法确认的缺测
    BELOW_THRESHOLD_T2 = "below_threshold_t2"  # t2 测到但未达起测胸径，不计进界


class TreeStatus(str, Enum):
    ALIVE = "alive"
    DEAD = "dead"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class TreeObs:
    """一次调查中对一株树的观测记录。

    位置 ``x_m`` / ``y_m`` 为样地局部坐标（米）；数据库中另有 PostGIS 地理坐标。
    ``dbh_cm`` 为 None 表示该次调查缺测（树在、身份可确认，但未测胸径）。
    """

    tag: str
    species: Optional[str]
    status: TreeStatus
    x_m: Optional[float]
    y_m: Optional[float]
    dbh_cm: Optional[float]
    height_m: Optional[float] = None
    remark: str = ""


@dataclass(frozen=True)
class MatchedPair:
    status: PairStatus
    t1: Optional[TreeObs]
    t2: Optional[TreeObs]
    distance_m: Optional[float] = None
    matched_via: str = "tag"                 # "crosswalk" | "tag" | "none"
    note: str = ""

    @property
    def is_resolved(self) -> bool:
        return self.status in (PairStatus.SURVIVOR, PairStatus.MORTALITY,
                               PairStatus.INGROWTH, PairStatus.BELOW_THRESHOLD_T2)


def _distance(a: TreeObs, b: TreeObs) -> Optional[float]:
    if None in (a.x_m, a.y_m, b.x_m, b.y_m):
        return None
    return math.hypot(a.x_m - b.x_m, a.y_m - b.y_m)


def match_trees(
    *,
    t1: Sequence[TreeObs],
    t2: Sequence[TreeObs],
    crosswalk: Optional[Dict[str, str]] = None,
    xy_tolerance_m: float = DEFAULT_XY_TOLERANCE_M,
    ingrowth_threshold_cm: float = 5.0,
) -> List[MatchedPair]:
    """匹配两次调查的林木个体。

    Parameters
    ----------
    crosswalk : dict
        外业确认的改号映射 ``{t1_tag: t2_tag}``。复测改号以此为最高优先级。
    xy_tolerance_m : float
        同号（或交叉表映射）两点允许的最大平面位移；超过即位置矛盾，挂起核实。
    ingrowth_threshold_cm : float
        进界起测胸径。t2 新出现且未达此径阶 -> BELOW_THRESHOLD_T2，不计进界。
    """
    crosswalk = crosswalk or {}
    t1_by_tag: Dict[str, TreeObs] = {t.tag: t for t in t1}
    t2_by_tag: Dict[str, TreeObs] = {t.tag: t for t in t2}

    if len(t1_by_tag) != len(t1) or len(t2_by_tag) != len(t2):
        raise ValueError("同一次调查内树木编号不允许重复")

    pairs: List[MatchedPair] = []
    consumed_t2: set[str] = set()

    # ---- 1) 交叉表：显式改号映射，最高优先级 -------------------------------
    for old_tag, new_tag in crosswalk.items():
        a = t1_by_tag.get(old_tag)
        b = t2_by_tag.get(new_tag)
        if a is None:
            raise KeyError(f"交叉表引用了 t1 不存在的编号 {old_tag!r}")
        if b is None:
            # 交叉表声称改号但新编号在 t2 没找到：可能是死亡后补登记/缺测
            pairs.append(MatchedPair(
                PairStatus.UNRESOLVED_MISSING, a, None,
                matched_via="crosswalk",
                note=f"交叉表 {old_tag}->{new_tag}，但 t2 无 {new_tag} 记录，待核实",
            ))
            continue
        consumed_t2.add(new_tag)
        dist = _distance(a, b)
        if dist is not None and dist > xy_tolerance_m:
            pairs.append(MatchedPair(
                PairStatus.UNRESOLVED_LOCATION_CONFLICT, a, b, dist,
                matched_via="crosswalk",
                note=(f"交叉表 {old_tag}->{new_tag} 但位置相差 {dist:.2f} m "
                      f"> 容差 {xy_tolerance_m} m，改号与位置矛盾，需核实"),
            ))
            continue
        pairs.append(_classify_resolved(a, b, dist, matched_via="crosswalk"))

    # ---- 2) 同号匹配 + 位置容差 --------------------------------------------
    for tag, a in t1_by_tag.items():
        if tag in crosswalk:
            continue                          # 已在交叉表处理
        b = t2_by_tag.get(tag)
        if b is None:
            # t2 完全没有这个编号
            if a.status == TreeStatus.DEAD:
                continue                      # t1 就已记死亡，不属于本期死亡
            pairs.append(MatchedPair(
                PairStatus.UNRESOLVED_MISSING, a, None,
                note="t2 未见该编号且无交叉表，不能推断死亡，按缺测挂起",
            ))
            continue
        consumed_t2.add(tag)
        dist = _distance(a, b)
        if dist is not None and dist > xy_tolerance_m:
            # 编号相同但位置矛盾：先核实，不能直接认成同株
            pairs.append(MatchedPair(
                PairStatus.UNRESOLVED_LOCATION_CONFLICT, a, b, dist,
                matched_via="tag",
                note=(f"同号 {tag} 但位置相差 {dist:.2f} m > 容差 "
                      f"{xy_tolerance_m} m，可能是重号/补号，禁止自动合并"),
            ))
            continue
        pairs.append(_classify_resolved(a, b, dist, matched_via="tag"))

    # ---- 3) t2 未被消费的记录：进界或未达径阶 ------------------------------
    for b in t2:
        if b.tag in consumed_t2:
            continue
        if b.status == TreeStatus.DEAD:
            # 新编号即死亡木：无 t1 前身，无法计入本期死亡，挂起核实
            pairs.append(MatchedPair(
                PairStatus.UNRESOLVED_MISSING, None, b,
                note="t2 新编号即死亡，缺少 t1 身份，需核实是否漏登",
            ))
        elif b.dbh_cm is not None and b.dbh_cm >= ingrowth_threshold_cm:
            pairs.append(MatchedPair(
                PairStatus.INGROWTH, None, b, matched_via="none",
                note=f"t2 新进界木，胸径 {b.dbh_cm} cm >= {ingrowth_threshold_cm} cm",
            ))
        else:
            pairs.append(MatchedPair(
                PairStatus.BELOW_THRESHOLD_T2, None, b, matched_via="none",
                note="t2 测到但未达起测胸径，不计进界",
            ))

    return pairs


def _classify_resolved(a: TreeObs, b: TreeObs, dist, *, matched_via: str) -> MatchedPair:
    """身份已确认（交叉表或同号且位置一致）后的状态判定。"""
    if a.status == TreeStatus.DEAD:
        return MatchedPair(
            PairStatus.UNRESOLVED_MISSING, a, b, dist, matched_via=matched_via,
            note="t1 已登记死亡但 t2 又出现存活记录，状态矛盾，需核实",
        )
    if b.status == TreeStatus.DEAD:
        return MatchedPair(
            PairStatus.MORTALITY, a, b, dist, matched_via=matched_via,
            note="t1 存活、t2 确认死亡（伐桩/枯立木）",
        )
    if b.status == TreeStatus.UNKNOWN or a.status == TreeStatus.UNKNOWN:
        return MatchedPair(
            PairStatus.UNRESOLVED_MISSING, a, b, dist, matched_via=matched_via,
            note="存活状态未知，按缺测挂起",
        )
    return MatchedPair(PairStatus.SURVIVOR, a, b, dist, matched_via=matched_via)
