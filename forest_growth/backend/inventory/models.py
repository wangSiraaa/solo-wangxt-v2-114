"""PostGIS 数据模型：样地边界、调查版、树木编号、测量高度、复测交叉表、
改号/位置核实队列、异速方程版本与分析运行。

设计要点
--------
* 单位与数值分列存储（dbh_value + dbh_unit），数据库 CHECK 约束限定合法单位；
* 样地与树木均有 PostGIS 空间字段（边界 Polygon、点位 Point，含 SRID）；
* Survey（调查版）一旦 approved 即锁定；AnalysisRun 绑定具体方程 release，
  已确认 run 不能被新方程静默改写（保护逻辑见 api/services.py）。
"""

from django.contrib.gis.db import models as gis
from django.db import models


class Stratum(models.Model):
    """抽样总体分层。"""

    code = models.CharField("层代码", max_length=16, unique=True)
    name = models.CharField("层名称", max_length=100)
    area_ha = models.FloatField("层总面积(公顷)")

    class Meta:
        verbose_name = "分层"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.code} {self.name}"


class Plot(models.Model):
    """固定样地：面积可能不等；边界用 PostGIS Polygon 保存。"""

    plot_id = models.CharField("样地编号", max_length=32, unique=True)
    stratum = models.ForeignKey(Stratum, on_delete=models.PROTECT,
                                related_name="plots", verbose_name="所属层")
    area_ha = models.FloatField("样地面积(公顷)")
    boundary = gis.PolygonField("样地边界", srid=4326)
    centroid = gis.PointField("样地中心点", srid=4326, null=True, blank=True)
    established_on = models.DateField("建立日期", null=True, blank=True)

    class Meta:
        verbose_name = "固定样地"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.plot_id


class Survey(models.Model):
    """一次调查版本（t1 / t2 …）。approved 后冻结，不允许静默改动。"""

    survey_no = models.CharField("调查期次", max_length=16, unique=True)
    survey_date = models.DateField("调查日期")
    status = models.CharField(
        "状态", max_length=16,
        choices=[("draft", "草稿"), ("approved", "已确认"), ("locked", "已锁定归档")],
        default="draft")
    approved_by = models.CharField("确认人", max_length=64, blank=True)
    remark = models.TextField("备注", blank=True)

    class Meta:
        verbose_name = "调查版本"
        verbose_name_plural = verbose_name
        ordering = ("survey_date",)

    def __str__(self):
        return f"{self.survey_no} ({self.survey_date})"


class PlotSurvey(models.Model):
    """某样地在某次调查中的边界实测与备注（边界可能有复测修正）。"""

    plot = models.ForeignKey(Plot, on_delete=models.CASCADE, related_name="visits")
    survey = models.ForeignKey(Survey, on_delete=models.PROTECT, related_name="visits")
    boundary_observed = gis.PolygonField(srid=4326, null=True, blank=True)
    crew = models.CharField("调查小组", max_length=128, blank=True)
    remark = models.TextField(blank=True)

    class Meta:
        unique_together = ("plot", "survey")


class TreeRecord(models.Model):
    """一株树在某次调查中的单条记录：编号、位置、胸径、树高、存活状态。"""

    DBH_UNITS = [("mm", "毫米"), ("cm", "厘米"), ("m", "米"), ("in", "英寸")]
    HEIGHT_UNITS = [("mm", "毫米"), ("cm", "厘米"), ("dm", "分米"),
                    ("m", "米"), ("ft", "英尺")]
    STATUS = [("alive", "存活"), ("dead", "死亡(伐桩/枯立)"), ("unknown", "状态未知")]

    plot = models.ForeignKey(Plot, on_delete=models.CASCADE, related_name="trees")
    survey = models.ForeignKey(Survey, on_delete=models.PROTECT, related_name="trees")
    tag = models.CharField("树木编号", max_length=32)
    species_code = models.CharField("树种代码", max_length=16)
    status = models.CharField("存活状态", max_length=8, choices=STATUS)
    geom = gis.PointField("树木位置(地理坐标)", srid=4326)
    # 样地局部坐标（米），复测位置容差检查用；缺测绘图时可为空
    plot_x_m = models.FloatField("样地内坐标X(m)", null=True, blank=True)
    plot_y_m = models.FloatField("样地内坐标Y(m)", null=True, blank=True)

    # 数值与单位分列；缺测时数值为 NULL，但单位保留（记录「没测」而非 0）
    dbh_value = models.FloatField("胸径数值", null=True, blank=True)
    dbh_unit = models.CharField("胸径单位", max_length=2, choices=DBH_UNITS,
                                default="cm")
    height_value = models.FloatField("树高数值", null=True, blank=True)
    height_unit = models.CharField("树高单位", max_length=2, choices=HEIGHT_UNITS,
                                   default="m")
    measured_on = models.DateField(null=True, blank=True)
    remark = models.CharField("备注", max_length=255, blank=True)

    class Meta:
        verbose_name = "树木调查记录"
        verbose_name_plural = verbose_name
        # 同一次调查、同一样地内编号唯一（重号在入库前必须核实）
        unique_together = ("plot", "survey", "tag")

    def __str__(self):
        return f"{self.plot.plot_id}/{self.tag}@{self.survey.survey_no}"


class TagCrosswalk(models.Model):
    """外业确认的复测改号映射（同株树两次调查编号不同）。"""

    plot = models.ForeignKey(Plot, on_delete=models.CASCADE,
                             related_name="crosswalks")
    survey_t1 = models.ForeignKey(Survey, on_delete=models.PROTECT,
                                  related_name="crosswalks_as_t1")
    survey_t2 = models.ForeignKey(Survey, on_delete=models.PROTECT,
                                  related_name="crosswalks_as_t2")
    tag_t1 = models.CharField("t1 编号", max_length=32)
    tag_t2 = models.CharField("t2 编号", max_length=32)
    confirmed_by = models.CharField("核实人", max_length=64)
    note = models.CharField("核实说明", max_length=255, blank=True)

    class Meta:
        unique_together = ("plot", "survey_t1", "survey_t2", "tag_t1")


class IdentityReview(models.Model):
    """编号相同但位置矛盾、或身份无法确认时的人工核实队列。"""

    KIND = [
        ("location_conflict", "同号位置矛盾"),
        ("missing_unresolved", "缺测/死亡待核"),
        ("renumber_unverified", "改号未核实"),
    ]
    RESOLUTION = [
        ("open", "待核实"),
        ("same_tree", "确认同株"),
        ("different_tree", "确认不同株(重号)"),
        ("dead_confirmed", "确认死亡"),
        ("alive_found", "找到存活木"),
        ("rejected", "记录作废"),
    ]

    plot = models.ForeignKey(Plot, on_delete=models.CASCADE, related_name="reviews")
    survey_t1 = models.ForeignKey(Survey, on_delete=models.PROTECT,
                                  related_name="reviews_as_t1")
    survey_t2 = models.ForeignKey(Survey, on_delete=models.PROTECT,
                                  related_name="reviews_as_t2")
    tag_t1 = models.CharField(max_length=32, blank=True)
    tag_t2 = models.CharField(max_length=32, blank=True)
    distance_m = models.FloatField("位置偏差(m)", null=True, blank=True)
    kind = models.CharField(max_length=24, choices=KIND)
    status = models.CharField(max_length=20, choices=RESOLUTION, default="open")
    raised_by = models.CharField("提出人", max_length=64, blank=True)
    resolution_note = models.TextField("核实结论", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "身份核实"
        verbose_name_plural = verbose_name


class EquationReleaseModel(models.Model):
    """方程集发布版本（数据库镜像；内容以 payload JSON 冻结，不可改）。"""

    release_id = models.CharField(max_length=64, unique=True)
    published_on = models.DateField()
    description = models.TextField()
    payload = models.JSONField("冻结的方程清单(完整元数据)")
    is_active = models.BooleanField("当前推荐版本", default=False)

    class Meta:
        verbose_name = "异速方程版本"
        verbose_name_plural = verbose_name


class AnalysisRun(models.Model):
    """一次完整的样地/总体分析运行：输入版本与方程版本都被记录，可复现。"""

    survey_t1 = models.ForeignKey(Survey, on_delete=models.PROTECT,
                                  related_name="runs_as_t1")
    survey_t2 = models.ForeignKey(Survey, on_delete=models.PROTECT,
                                  related_name="runs_as_t2")
    equation_release = models.ForeignKey(EquationReleaseModel,
                                         on_delete=models.PROTECT)
    status = models.CharField(
        max_length=16,
        choices=[("draft", "草稿"), ("approved", "已确认"), ("superseded", "已被替代")],
        default="draft")
    result_payload = models.JSONField("结果(分量/来源/不确定性)", default=dict)
    params = models.JSONField("计算参数(容差/径阶/单位等)", default=dict)
    created_by = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    supersedes = models.ForeignKey("self", null=True, blank=True,
                                   on_delete=models.PROTECT,
                                   related_name="superseded_by")

    class Meta:
        verbose_name = "分析运行"
        verbose_name_plural = verbose_name
        ordering = ("-created_at",)
