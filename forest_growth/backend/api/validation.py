"""入库前的单位/数值校验纯函数。

不依赖 Django ORM，便于在测试中直接验证；序列化器与批量导入脚本共用。
单位错误（如胸径 12.5 m）在这里就被拦截，返回给 API 422，而不是静默换算。
"""

from __future__ import annotations

from core.units import (
    UnitConflictError,
    UnitPlausibilityError,
    assert_same_unit,
    convert_dbh_to_cm,
    convert_height_to_m,
)


def validate_dbh(value, unit: str, *, record_id: str = "?"):
    """返回换算后的 cm；缺测（value is None）放行但必须显式标记。"""
    if value is None:
        return None
    return float(convert_dbh_to_cm([value], [unit], record_ids=[record_id])[0])


def validate_height(value, unit: str, *, record_id: str = "?"):
    if value is None:
        return None
    return float(convert_height_to_m([value], [unit], record_ids=[record_id])[0])


def validate_record_units(*, tag: str, dbh_value, dbh_unit: str,
                          height_value, height_unit: str):
    """单条记录入库前校验；错误信息带树木编号便于外业定位。"""
    validate_dbh(dbh_value, dbh_unit, record_id=tag)
    validate_height(height_value, height_unit, record_id=tag)


def reconcile_units(*, tag: str, field_name: str, unit_a: str, unit_b: str):
    """同树同字段两条记录单位一致性（记录级冲突，拒绝静默选择）。"""
    assert_same_unit(unit_a, unit_b, tree_tag=tag, field=field_name)


__all__ = [
    "UnitConflictError",
    "UnitPlausibilityError",
    "validate_dbh",
    "validate_height",
    "validate_record_units",
    "reconcile_units",
]
