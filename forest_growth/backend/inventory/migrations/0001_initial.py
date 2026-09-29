"""PostGIS 初始迁移（手写；部署后可用 makemigrations --check 核对一致）。"""

import django.db.models.deletion
from django.db import migrations, models

import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Stratum",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                          serialize=False)),
                ("code", models.CharField(max_length=16, unique=True,
                                          verbose_name="层代码")),
                ("name", models.CharField(max_length=100, verbose_name="层名称")),
                ("area_ha", models.FloatField(verbose_name="层总面积(公顷)")),
            ],
            options={"verbose_name": "分层",
                     "verbose_name_plural": "分层"},
        ),
        migrations.CreateModel(
            name="Plot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                          serialize=False)),
                ("plot_id", models.CharField(max_length=32, unique=True,
                                             verbose_name="样地编号")),
                ("area_ha", models.FloatField(verbose_name="样地面积(公顷)")),
                ("boundary", django.contrib.gis.db.models.fields.PolygonField(
                    srid=4326, verbose_name="样地边界")),
                ("centroid", django.contrib.gis.db.models.fields.PointField(
                    blank=True, null=True, srid=4326,
                    verbose_name="样地中心点")),
                ("established_on", models.DateField(blank=True, null=True,
                                                    verbose_name="建立日期")),
                ("stratum", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="plots", to="inventory.stratum",
                    verbose_name="所属层")),
            ],
            options={"verbose_name": "固定样地",
                     "verbose_name_plural": "固定样地"},
        ),
        migrations.CreateModel(
            name="Survey",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                          serialize=False)),
                ("survey_no", models.CharField(max_length=16, unique=True,
                                               verbose_name="调查期次")),
                ("survey_date", models.DateField(verbose_name="调查日期")),
                ("status", models.CharField(
                    choices=[("draft", "草稿"), ("approved", "已确认"),
                             ("locked", "已锁定归档")],
                    default="draft", max_length=16, verbose_name="状态")),
                ("approved_by", models.CharField(blank=True, max_length=64,
                                                 verbose_name="确认人")),
                ("remark", models.TextField(blank=True, verbose_name="备注")),
            ],
            options={"verbose_name": "调查版本",
                     "verbose_name_plural": "调查版本",
                     "ordering": ("survey_date",)},
        ),
        migrations.CreateModel(
            name="EquationReleaseModel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                          serialize=False)),
                ("release_id", models.CharField(max_length=64, unique=True)),
                ("published_on", models.DateField()),
                ("description", models.TextField()),
                ("payload", models.JSONField(verbose_name="冻结的方程清单(完整元数据)")),
                ("is_active", models.BooleanField(default=False,
                                                  verbose_name="当前推荐版本")),
            ],
            options={"verbose_name": "异速方程版本",
                     "verbose_name_plural": "异速方程版本"},
        ),
        migrations.CreateModel(
            name="PlotSurvey",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                          serialize=False)),
                ("boundary_observed",
                 django.contrib.gis.db.models.fields.PolygonField(
                     blank=True, null=True, srid=4326)),
                ("crew", models.CharField(blank=True, max_length=128,
                                          verbose_name="调查小组")),
                ("remark", models.TextField(blank=True)),
                ("plot", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="visits", to="inventory.plot")),
                ("survey", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="visits", to="inventory.survey")),
            ],
            options={"unique_together": {("plot", "survey")}},
        ),
        migrations.CreateModel(
            name="TreeRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                          serialize=False)),
                ("tag", models.CharField(max_length=32, verbose_name="树木编号")),
                ("species_code", models.CharField(max_length=16,
                                                  verbose_name="树种代码")),
                ("status", models.CharField(
                    choices=[("alive", "存活"),
                             ("dead", "死亡(伐桩/枯立)"),
                             ("unknown", "状态未知")],
                    max_length=8, verbose_name="存活状态")),
                ("geom", django.contrib.gis.db.models.fields.PointField(
                    srid=4326, verbose_name="树木位置(地理坐标)")),
                ("plot_x_m", models.FloatField(
                    blank=True, null=True, verbose_name="样地内坐标X(m)")),
                ("plot_y_m", models.FloatField(
                    blank=True, null=True, verbose_name="样地内坐标Y(m)")),
                ("dbh_value", models.FloatField(blank=True, null=True,
                                                verbose_name="胸径数值")),
                ("dbh_unit", models.CharField(
                    choices=[("mm", "毫米"), ("cm", "厘米"),
                             ("m", "米"), ("in", "英寸")],
                    default="cm", max_length=2, verbose_name="胸径单位")),
                ("height_value", models.FloatField(blank=True, null=True,
                                                   verbose_name="树高数值")),
                ("height_unit", models.CharField(
                    choices=[("mm", "毫米"), ("cm", "厘米"), ("dm", "分米"),
                             ("m", "米"), ("ft", "英尺")],
                    default="m", max_length=2, verbose_name="树高单位")),
                ("measured_on", models.DateField(blank=True, null=True)),
                ("remark", models.CharField(blank=True, max_length=255,
                                            verbose_name="备注")),
                ("plot", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="trees", to="inventory.plot")),
                ("survey", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="trees", to="inventory.survey")),
            ],
            options={"verbose_name": "树木调查记录",
                     "verbose_name_plural": "树木调查记录",
                     "unique_together": {("plot", "survey", "tag")}},
        ),
        migrations.CreateModel(
            name="TagCrosswalk",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                          serialize=False)),
                ("tag_t1", models.CharField(max_length=32,
                                            verbose_name="t1 编号")),
                ("tag_t2", models.CharField(max_length=32,
                                            verbose_name="t2 编号")),
                ("confirmed_by", models.CharField(max_length=64,
                                                  verbose_name="核实人")),
                ("note", models.CharField(blank=True, max_length=255,
                                          verbose_name="核实说明")),
                ("plot", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="crosswalks", to="inventory.plot")),
                ("survey_t1", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="crosswalks_as_t1", to="inventory.survey")),
                ("survey_t2", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="crosswalks_as_t2", to="inventory.survey")),
            ],
            options={"unique_together": {
                ("plot", "survey_t1", "survey_t2", "tag_t1")}},
        ),
        migrations.CreateModel(
            name="IdentityReview",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                          serialize=False)),
                ("tag_t1", models.CharField(blank=True, max_length=32)),
                ("tag_t2", models.CharField(blank=True, max_length=32)),
                ("distance_m", models.FloatField(blank=True, null=True,
                                                 verbose_name="位置偏差(m)")),
                ("kind", models.CharField(
                    choices=[("location_conflict", "同号位置矛盾"),
                             ("missing_unresolved", "缺测/死亡待核"),
                             ("renumber_unverified", "改号未核实")],
                    max_length=24)),
                ("status", models.CharField(
                    choices=[("open", "待核实"),
                             ("same_tree", "确认同株"),
                             ("different_tree", "确认不同株(重号)"),
                             ("dead_confirmed", "确认死亡"),
                             ("alive_found", "找到存活木"),
                             ("rejected", "记录作废")],
                    default="open", max_length=20)),
                ("raised_by", models.CharField(blank=True, max_length=64,
                                               verbose_name="提出人")),
                ("resolution_note", models.TextField(verbose_name="核实结论")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("plot", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="reviews", to="inventory.plot")),
                ("survey_t1", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="reviews_as_t1", to="inventory.survey")),
                ("survey_t2", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="reviews_as_t2", to="inventory.survey")),
            ],
            options={"verbose_name": "身份核实",
                     "verbose_name_plural": "身份核实"},
        ),
        migrations.CreateModel(
            name="AnalysisRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                          serialize=False)),
                ("status", models.CharField(
                    choices=[("draft", "草稿"), ("approved", "已确认"),
                             ("superseded", "已被替代")],
                    default="draft", max_length=16)),
                ("result_payload", models.JSONField(
                    default=dict, verbose_name="结果(分量/来源/不确定性)")),
                ("params", models.JSONField(
                    default=dict, verbose_name="计算参数(容差/径阶/单位等)")),
                ("created_by", models.CharField(blank=True, max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("equation_release", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to="inventory.equationreleasemodel")),
                ("supersedes", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="superseded_by",
                    to="inventory.analysisrun")),
                ("survey_t1", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="runs_as_t1", to="inventory.survey")),
                ("survey_t2", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="runs_as_t2", to="inventory.survey")),
            ],
            options={"verbose_name": "分析运行",
                     "verbose_name_plural": "分析运行",
                     "ordering": ("-created_at",)},
        ),
    ]
