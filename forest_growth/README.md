# 固定样地生长、死亡与进界分析系统（林业研究站）

比较固定样地（permanent sample plot, PSP）**两次调查**之间的：

- **生长量（survivor growth）**：两次调查均存活的复测木
- **死亡量（mortality）**：第一次调查存活、第二次调查确认死亡
- **进界量（ingrowth / recruitment）**：第二次调查新进入起测径阶的林木
- **缺测（missing measurement）**：身份可确认但某次测量缺失 —— 与真实零生长、死亡严格区分

技术栈：React（样地位置与个体复测展示）· Django REST Framework（API）· NumPy（计算）·
PostgreSQL + PostGIS（树木编号、测量高度、样地边界）。

## 目录结构

```
forest_growth/
├── backend/                 Django + DRF
│   ├── api/                 视图、序列化器、URL
│   ├── inventory/           PostGIS 模型与迁移
│   └── core/                纯 Python/NumPy 计算核心（不依赖 Django/数据库）
├── frontend/                React + Vite（Leaflet 地图、个体复测表、分量报告）
├── data/fixtures/           虚构林木数据（JSON，可直接导入）
├── scripts/load_fixtures.py
└── tests/                   验收测试（unittest，直接 python3 -m unittest 运行）
```

## 快速开始

```bash
# 1) 计算核心与验收测试（无需数据库，NumPy 即可）
python3 -m unittest discover -s tests -v

# 2) 后端（需要 PostgreSQL + PostGIS）
createdb forest
psql forest -c "CREATE EXTENSION postgis;"
cd backend
python manage.py migrate
python manage.py loaddata ../data/fixtures/equations.json
python ../scripts/load_fixtures.py --fixture ../data/fixtures/surveys.json
python manage.py runserver

# 3) 前端
cd frontend && npm install && npm run dev
```

## 领域规则（硬性约束，均有测试覆盖）

### 1. 单位必须显式记录，禁止隐式假设

- 胸径（DBH）字段同时保存 `dbh_value` 与 `dbh_unit`（`mm` / `cm` / `m` / `in`）；
  树高保存 `height_value` 与 `height_unit`（`m` / `dm` / `ft`）。
- 计算核心内部统一为 **cm（胸径）/ m（树高）/ kg（生物量）**，转换在边界完成。
- 记录级单位冲突（如同一次调查同一棵树前后两份记录分别写 cm 与 mm）触发
  `UnitConflictError`；数值超出该单位的合理区间触发 `UnitPlausibilityError`，
  API 返回 422 并列入「待核实」而不是静默换算。
- 验收用例 `tests/test_units.py` 包含「测量单位错误」核对（12.5 m 胸径、
  2500 cm 胸径、字段写 cm 实际值为 0.25 的疑似 m 录入等）。

### 2. 异速生长方程必须版本化、适用树种显式记录

见 `backend/core/allometry.py`：

- 每条方程记录：方程 ID、版本、函数形式（字符串）、参数、生物量分量
  （树干/地上等）、**适用树种列表**、适用 DBH 区间、适用区域、残差 CV、
  数据来源文献、发布日期。
- 方程按 `EquationRelease`（方程集版本）冻结；一次分析运行
  （`AnalysisRun`）记录所用 release ID。
- **已确认的调查版本/已冻结的分析结果，不允许被新方程静默改变**：
  - 用旧 release 重算只会复现旧结果（release 内容不可变）；
  - 新方程 = 新 release + 新的 `AnalysisRun`，旧 run 原样保留；
  - 对已确认（approved）run 用新 release 重算必须显式传
    `allow_recreate`，否则抛 `FrozenReleaseError`（验收测试覆盖）。
- 树种不在某方程的适用树种清单中 → `SpeciesNotCoveredError`，不借用近似树种。

### 3. 编号相同但位置矛盾 → 先核实，不能直接认成同株

复测匹配规则（`backend/core/remeasure.py`）：

1. 优先使用外业复测交叉表（`tag_t1 -> tag_t2` 的显式改号映射）；
2. 否则用相同树木编号匹配，并检查两点平面距离：
   - `distance <= xy_tolerance_m`（默认 1.0 m，考虑测绘误差）→ 接受为同株；
   - 超过容差 → 输出 `UNRESOLVED_LOCATION_CONFLICT`，**既不计生长也不计进界/死亡**，
     进入人工核实队列（`IdentityReview` 表）；
3. 第一次调查有、第二次无匹配：若 t2 记录状态为 `dead` → 死亡；
   否则若第二次调查未覆盖该位置 → `UNRESOLVED_MISSING`（缺测，不等于死亡）。
4. 第二次调查的新编号：若有交叉表或伐桩/枯倒位置证据可对上死亡木则归并；
   达到起测胸径且无 t1 前身 → 进界。

React 界面以连线展示 t1→t2 个体，位置矛盾对显示为红色虚线并要求核实结论。

### 4. 真实零生长、缺测、死亡严格区分

单株层面只有三种互斥状态：`alive` / `dead` / `unknown`；再与两次调查的
有无测量组合（见 `components.py` 文档表）：

| t1 胸径 | t2 胸径 | 判定 |
|---|---|---|
| 有，alive | 有，alive，增量 ≈ 0（在测量误差 epsilon 内） | **真实零生长**（survivor，Δ=0，保留） |
| 有，alive | 有，alive，Δ<0 且超误差 | `NegativeGrowthError`（待核实，不计入） |
| 有，alive | 无测量、身份可确认 | **缺测**（excluded，不计零、不填补） |
| 有，alive | 无、状态 dead / 伐桩 | **死亡** |
| 无 | 有，alive，≥ 起测径阶 | **进界** |

缺测采用完整木分析（complete-case），不做插补；缺失影响写入不确定性假设。

### 5. 总体估计按抽样设计加权，绝不「全部树木平均 × 面积」

`backend/core/weighting.py`：

- 样地先扩成每公顷值：`y_ha = y_tree / area_ha`（不等面积样地自然正确处理）；
- 分层估计：`Ŷ_stratum = (1/n_h) Σ w_hi · y_ha,i`（w 为单木包含概率倒数
  在样地内的归一化权重，等概率时为 1）；
- 总体：`Ŷ = Σ A_h · Ŷ_h`（A_h = 层总面积，公顷）；
- 方差：层内样地方差 / n_h，按 A_h² 汇总，输出 SE 与 t 分位 95% CI；
- 同时提供 `naive_pooled_estimate()`（把所有树简单平均乘总面积），
  **仅供测试与对照**，报告中会显著标注为错误方法；
- 验收测试 `tests/test_weighting.py` 用两片面积不等的样地证明加权与朴素法结果不同。

### 6. 每个分量输出来源与不确定性假设

分析结果 JSON 对生长 / 死亡 / 进界三个分量分别给出：

- `source`：来自哪些样地、哪些株数、用的哪条方程/哪个 release、是实测还是推算；
- `uncertainty`：抽样误差（SE、CI、自由度）、测量误差假设（胸径 ±0.3 cm、
  树高 ±0.5 m）、方程残差 CV（一阶 delta 近似传播）、缺测处理假设
  （完整木、最坏情形上下限）。

## 验收测试

```bash
python3 -m unittest discover -s tests -v
```

| 测试文件 | 验收点 |
|---|---|
| `test_remeasure.py` | 复测改号（交叉表优先）、编号相同位置矛盾不自动合并 |
| `test_weighting.py` | 样地面积不等、加权法 ≠ 简单平均乘面积 |
| `test_units.py` | 测量单位错误被拦截（含 API 422 路径） |
| `test_release_freeze.py` | 已确认调查版不被新方程静默改变 |
| `test_components.py` | 真实零生长 / 缺测 / 死亡 / 进界区分 |

虚构数据见 `data/fixtures/`：2 个分层、4 个面积不等样地，包含马尾松
（*Pinus massoniana*）与杉木（*Cunninghamia lanceolata*），内含全部上述情形。
