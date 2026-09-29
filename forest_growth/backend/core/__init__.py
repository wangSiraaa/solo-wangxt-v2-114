"""固定样地复测分析的纯计算核心。

本包不依赖 Django / PostgreSQL，可独立运行与测试：
- units:     单位换算与合理性核对
- allometry: 异速生长方程（版本化、适用树种显式记录）
- remeasure: 两次调查的个体身份匹配（改号、位置矛盾核实）
- components: 生长 / 死亡 / 进界 / 缺测分量
- weighting: 按抽样设计加权的总体估计
"""

from .allometry import (
    AllometricEquation,
    EquationRelease,
    EquationBook,
    SpeciesNotCoveredError,
    FrozenReleaseError,
)
from .units import (
    DBH_TO_CM,
    HEIGHT_TO_M,
    UnitConflictError,
    UnitPlausibilityError,
    convert_dbh_to_cm,
    convert_height_to_m,
)
from .remeasure import (
    TreeObs,
    MatchedPair,
    PairStatus,
    match_trees,
    DEFAULT_XY_TOLERANCE_M,
)
from .components import PlotInputs, PlotResult, compute_plot_components
from .weighting import (
    StratumResult,
    PopulationResult,
    estimate_population,
    naive_pooled_estimate,
)

__all__ = [
    "AllometricEquation",
    "EquationRelease",
    "EquationBook",
    "SpeciesNotCoveredError",
    "FrozenReleaseError",
    "DBH_TO_CM",
    "HEIGHT_TO_M",
    "UnitConflictError",
    "UnitPlausibilityError",
    "convert_dbh_to_cm",
    "convert_height_to_m",
    "TreeObs",
    "MatchedPair",
    "PairStatus",
    "match_trees",
    "DEFAULT_XY_TOLERANCE_M",
    "PlotInputs",
    "PlotResult",
    "compute_plot_components",
    "StratumResult",
    "PopulationResult",
    "estimate_population",
    "naive_pooled_estimate",
]
