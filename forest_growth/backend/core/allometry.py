"""异速生长方程：版本化、适用树种显式记录、冻结不可静默改变。

设计原则
--------
1. 每条方程显式声明：函数形式、参数、生物量分量、**适用树种**、
   适用胸径区间、适用区域、残差变异系数、文献来源、发布日期。
2. 方程集合打包成不可变的 ``EquationRelease``（方程集版本）。
   已冻结 release 的任何内容变更都会抛错 —— 已确认的调查版分析结果
   不能被新方程静默改变。
3. 想用新方程？发布一个新 release，再创建一次新的 ``AnalysisRun``；
   旧 run 与旧 release 原样保留，可随时复现旧结果。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date
from typing import Callable, FrozenSet, Optional, Tuple

import numpy as np


class SpeciesNotCoveredError(ValueError):
    """树种不在任何已登记方程的适用树种清单中（禁止借用近似树种）。"""


class EquationOutOfDomainError(ValueError):
    """胸径超出方程适用区间，外推不允许静默发生。"""


class FrozenReleaseError(RuntimeError):
    """试图修改已冻结 release，或对已确认分析结果静默套用新方程。"""


# ---- 支持的函数形式（显式记录，便于复现与文献核对） -----------------------
SUPPORTED_FORMS: dict[str, Callable[..., np.ndarray]] = {
    # 经典幂函数（B 单位 kg，d 为 cm，h 为 m）
    "power_dbh": lambda d, h, a, b: a * np.power(d, b),
    "power_dbh_height": lambda d, h, a, b, c: a * np.power(d, b) * np.power(h, c),
    "ln_linear_dbh_height": lambda d, h, a, b, c:
        np.exp(a + b * np.log(d) + c * np.log(h)),
}


@dataclass(frozen=True)
class AllometricEquation:
    """一条异速生长方程的完整元数据。"""

    equation_id: str
    version: str
    form: str                       # SUPPORTED_FORMS 的键
    params: Tuple[float, ...]       # 按 form 签名顺序的参数
    biomass_component: str          # 如 "stem_oven_dry_kg" / "agb_oven_dry_kg"
    species: FrozenSet[str]         # 适用树种代码，显式枚举
    dbh_domain_cm: Tuple[float, float]
    region: str                     # 适用区域
    residual_cv: float              # 残差变异系数（不确定性传播用）
    source_citation: str
    published_on: date
    needs_height: bool = False

    def evaluate(self, dbh_cm, height_m=None):
        """向量化计算。输入必须是内部基准单位（cm / m）。"""
        if self.form not in SUPPORTED_FORMS:
            raise ValueError(f"方程 {self.equation_id} 的形式 {self.form!r} 不受支持")
        d = np.asarray(dbh_cm, dtype=float)
        h = np.asarray(height_m, dtype=float) if height_m is not None else None
        if self.needs_height and h is None:
            raise ValueError(f"方程 {self.equation_id} 需要树高，但未提供")
        lo, hi = self.dbh_domain_cm
        out_of_domain = (d < lo) | (d > hi)
        if np.any(out_of_domain):
            bad = d[out_of_domain]
            raise EquationOutOfDomainError(
                f"方程 {self.equation_id}（{self.form}）适用胸径 [{lo}, {hi}] cm，"
                f"出现域外值: {bad.tolist()[:10]}"
            )
        fn = SUPPORTED_FORMS[self.form]
        args = (d, h, *self.params)
        return fn(*args)

    def applies_to(self, species_code: str, dbh_cm: float) -> bool:
        lo, hi = self.dbh_domain_cm
        return species_code in self.species and lo <= dbh_cm <= hi


@dataclass(frozen=True)
class EquationRelease:
    """不可变的方程集版本（一次冻结、永久可复现）。"""

    release_id: str
    published_on: date
    description: str
    equations: Tuple[AllometricEquation, ...]
    _frozen: bool = field(default=True, compare=False)

    def __post_init__(self):
        # frozen dataclass 内部用 object.__setattr__；这里只做发布时校验
        ids = [e.equation_id for e in self.equations]
        if len(ids) != len(set(ids)):
            raise ValueError(f"release {self.release_id} 内方程 ID 重复: {ids}")
        for e in self.equations:
            if e.form not in SUPPORTED_FORMS:
                raise ValueError(f"方程 {e.equation_id} 使用未登记形式 {e.form!r}")

    def lookup(self, species_code: str, dbh_cm: float,
               component: str = "agb_oven_dry_kg") -> AllometricEquation:
        candidates = [
            e for e in self.equations
            if e.biomass_component == component and e.applies_to(species_code, dbh_cm)
        ]
        if not candidates:
            # 区分「树种不支持」与「径阶超界」，便于外业定位
            species_known = any(species_code in e.species for e in self.equations)
            if not species_known:
                raise SpeciesNotCoveredError(
                    f"release {self.release_id} 中没有适用于树种 "
                    f"{species_code!r} 的 {component} 方程；禁止借用其它树种方程"
                )
            raise EquationOutOfDomainError(
                f"树种 {species_code} 的胸径 {dbh_cm} cm 超出 release "
                f"{self.release_id} 中任何 {component} 方程的适用区间"
            )
        if len(candidates) > 1:
            raise ValueError(
                f"release {self.release_id} 对 {species_code}/{component}/"
                f"{dbh_cm} cm 命中多条方程，必须消除歧义"
            )
        return candidates[0]


class EquationBook:
    """登记全部已发布 release 的注册表。只增不改。"""

    def __init__(self):
        self._releases: dict[str, EquationRelease] = {}

    def publish(self, release: EquationRelease) -> None:
        if release.release_id in self._releases:
            raise FrozenReleaseError(
                f"release {release.release_id} 已发布且冻结，不能覆盖；"
                f"新参数请发布新版本"
            )
        self._releases[release.release_id] = release

    def get(self, release_id: str) -> EquationRelease:
        try:
            return self._releases[release_id]
        except KeyError:
            raise KeyError(f"未知方程 release: {release_id!r}") from None

    def require_same_release_for_approved_run(
        self, *, approved_release_id: str, requested_release_id: str,
        allow_recreate: bool = False,
    ) -> str:
        """已确认的分析运行不允许被新方程静默改变。

        - 请求的 release 与确认时一致：直接返回（用于复现旧结果）。
        - 不一致且未显式 ``allow_recreate``：抛 FrozenReleaseError。
        - 不一致且显式 ``allow_recreate=True``：返回新 release_id，
          调用方必须新建一条 AnalysisRun，而不是覆盖旧 run。
        """
        if requested_release_id == approved_release_id:
            return approved_release_id
        if not allow_recreate:
            raise FrozenReleaseError(
                f"该调查版本已用 release {approved_release_id} 确认；"
                f"请求改用 {requested_release_id} 属于方程变更，"
                f"必须显式 allow_recreate 并新建分析运行，禁止静默改写"
            )
        return requested_release_id

    @property
    def release_ids(self) -> Tuple[str, ...]:
        return tuple(self._releases)


def first_order_biomass_cv(equation: AllometricEquation,
                           dbh_cv: float = 0.01) -> float:
    """方程残差 CV 与胸径测量相对误差按幂指数传播的一阶近似。

    对 B = a·d^b： (σ_B/B)² ≈ (residual_cv)² + (b·dbh_cv)²。
    对含树高形式同理，树高项在调用处另行累加。
    """
    form = equation.form
    b_exponent = {"power_dbh": 1, "power_dbh_height": 1,
                  "ln_linear_dbh_height": 1}[form]
    b_value = equation.params[b_exponent]
    return math.sqrt(equation.residual_cv**2 + (b_value * dbh_cv) ** 2)
