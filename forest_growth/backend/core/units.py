"""单位换算与合理性核对。

规则：原始记录必须显式携带单位；计算核心内部统一使用胸径 cm、树高 m。
任何单位冲突或超出该单位合理区间的值都抛出异常，由 API 层转成 422，
绝不静默换算（例如字段写 cm、实际录入 0.25 这种疑似以米录入的记录）。
"""

from __future__ import annotations

import numpy as np

# ---- 到内部基准单位（DBH: cm, 树高: m）的换算系数 -------------------------
DBH_TO_CM = {
    "mm": 0.1,
    "cm": 1.0,
    "m": 100.0,
    "in": 2.54,
}
HEIGHT_TO_M = {
    "mm": 0.001,
    "cm": 0.01,
    "dm": 0.1,
    "m": 1.0,
    "ft": 0.3048,
}

# 合理性区间（内部基准单位）。用于拦截「单位标错」而不是做生长判断。
# 立木胸径现实范围：0.5 cm（幼苗）~ 400 cm（极端巨树）。
DBH_PLAUSIBLE_CM = (0.5, 400.0)
# 树高现实范围：0.1 m ~ 160 m。
HEIGHT_PLAUSIBLE_M = (0.1, 160.0)


class UnitConflictError(ValueError):
    """同一逻辑量的多条记录声明了互相矛盾的单位。"""


class UnitPlausibilityError(ValueError):
    """换算后的数值超出该量纲的合理区间，疑似单位标错。"""


def convert_dbh_to_cm(values, units, *, record_ids=None, strict: bool = True):
    """把胸径数组换算成 cm。

    Parameters
    ----------
    values : array_like
        原始胸径数值。
    units : str | sequence[str]
        每个值对应的单位（可整体一个字符串，或逐值给出）。
    record_ids : sequence, optional
        与值对齐的记录编号，用于错误信息定位。
    strict : bool
        True 时对越界值抛 UnitPlausibilityError；False 时返回掩码数组
        （合法位置为 cm 值，非法位置为 nan）而不抛异常，供批量导入核对。

    注意：本函数不判断「同一棵树两条记录单位不一致」—— 那是记录级冲突，
    由 :func:`assert_same_unit` 在归组时检查。
    """
    return _convert(
        values, units, DBH_TO_CM, DBH_PLAUSIBLE_CM,
        kind="DBH", target_unit="cm", record_ids=record_ids, strict=strict,
    )


def convert_height_to_m(values, units, *, record_ids=None, strict: bool = True):
    """把树高数组换算成 m。语义同 :func:`convert_dbh_to_cm`。"""
    return _convert(
        values, units, HEIGHT_TO_M, HEIGHT_PLAUSIBLE_M,
        kind="树高", target_unit="m", record_ids=record_ids, strict=strict,
    )


def assert_same_unit(unit_a: str, unit_b: str, *, tree_tag, field: str) -> None:
    """同一棵树同一字段的两条记录单位必须一致，否则拒绝并要求核实。

    允许换算后核对是有意不做的：外业流水中两条记录的单位不一致往往意味着
    设备/人员切换，属于数据质量事件，应回到原始记录核实，而不是替调查员决定。
    """
    if unit_a != unit_b:
        raise UnitConflictError(
            f"树木 {tree_tag} 的 {field} 记录单位冲突: {unit_a!r} != {unit_b!r}；"
            f"请核实原始调查表后再入库"
        )


def _convert(values, units, factors, plausible, *, kind, target_unit,
             record_ids, strict):
    arr = np.asarray(values, dtype=float)
    if isinstance(units, str):
        if units not in factors:
            raise ValueError(f"未知{kind}单位: {units!r}，支持: {sorted(factors)}")
        unit_arr = np.full(arr.shape, units, dtype=object)
    else:
        unit_arr = np.asarray(units, dtype=object)
        if unit_arr.shape != arr.shape:
            raise ValueError("values 与 units 形状不一致")
        bad = {u for u in unit_arr.tolist() if u not in factors}
        if bad:
            raise ValueError(f"未知{kind}单位: {sorted(map(str, bad))}")

    factor = np.array([factors[u] for u in unit_arr.tolist()], dtype=float)
    converted = arr * factor

    lo, hi = plausible
    invalid = ~np.isfinite(converted) | (converted < lo) | (converted > hi)
    if invalid.any():
        idx = np.flatnonzero(invalid)
        details = []
        for i in idx[:10]:
            rid = record_ids[i] if record_ids is not None else i
            details.append(
                f"记录 {rid}: 原值={arr[i]} {unit_arr[i]} -> {converted[i]} {target_unit}"
            )
        msg = (
            f"{len(idx)} 条{kind}记录换算为 {target_unit} 后超出合理区间 "
            f"[{lo}, {hi}]，疑似单位标错:\n  " + "\n  ".join(details)
        )
        if strict:
            raise UnitPlausibilityError(msg)
        converted = converted.astype(float)
        converted[invalid] = np.nan
    return converted
