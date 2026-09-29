# 部署与运维说明（PostgreSQL + PostGIS + DRF + React）

## 1. 数据库准备

```bash
sudo -u postgres createdb forest
sudo -u postgres createuser forest -P        # 密码与 settings.py 一致
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE forest TO forest;"
psql -d forest -U forest -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

系统依赖（Debian/Ubuntu）：

```bash
apt-get install gdal-bin libgdal-dev libgeos-dev libproj-dev postgis
```

## 2. 后端

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd backend
python manage.py makemigrations --check --dry-run   # 应与手写 0001 一致，无输出
python manage.py migrate
python manage.py createsuperuser
# 方程版本（冻结载荷）
python ../scripts/load_fixtures.py --fixture ../data/fixtures/equations.json
# 虚构样地/调查/树木（单位错误的记录会被拒绝，而不是静默换算）
python ../scripts/load_fixtures.py --fixture ../data/fixtures/surveys.json
python manage.py runserver 0.0.0.0:8000
```

## 3. 前端

```bash
cd frontend
npm install
npm run dev        # 开发，/api 代理到 :8000
npm run build      # 生产静态文件在 dist/
```

## 4. 典型工作流（与业务规则对应）

1. 两期调查记录经 `POST /api/trees/` 入库：`dbh_value` 与 `dbh_unit`
   成对出现，单位错误返回 **422 unit_plausibility**，记录退回外业核实。
2. 复测改号：由复测组填写 `POST /api/crosswalks/`（tag_t1 → tag_t2）。
3. `GET /api/remeasure-preview/?plot=..&survey_t1=..&survey_t2=..`
   预览个体匹配；同号位置矛盾不会被自动合并。
4. `POST /api/analysis-runs/approve/` 确认调查版；
   `POST /api/analysis-runs/execute/` 执行分层加权分析，
   位置矛盾/缺测自动进入 `/api/reviews/` 核实队列。
5. 已确认分析运行如要换方程：必须 `allow_recreate: true`，
   系统新建 run 并以 `supersedes` 指向旧 run；直接换 release 返回
   **409 frozen_release**，旧结果永不静默改变。

## 5. 不依赖数据库的离线核对

计算核心与验收测试只需要 NumPy：

```bash
python3 -m unittest discover -s tests -v
```
