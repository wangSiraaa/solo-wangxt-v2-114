"""DRF 序列化器：单位显式字段、GeoJSON 几何、单位错误 -> 422。"""

from rest_framework import serializers

from inventory.models import (
    AnalysisRun, EquationReleaseModel, IdentityReview, Plot, PlotSurvey,
    Stratum, Survey, TagCrosswalk, TreeRecord,
)

from .validation import (
    UnitConflictError, UnitPlausibilityError, validate_record_units,
)


class StratumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stratum
        fields = ("id", "code", "name", "area_ha")


class PlotSerializer(serializers.ModelSerializer):
    # 边界/中心点用 GeoJSON 交换（{"type":"Polygon", ...}）
    boundary = serializers.JSONField()
    centroid = serializers.JSONField(required=False, allow_null=True)
    stratum_code = serializers.CharField(source="stratum.code", read_only=True)

    class Meta:
        model = Plot
        fields = ("id", "plot_id", "stratum", "stratum_code", "area_ha",
                  "boundary", "centroid", "established_on")


class SurveySerializer(serializers.ModelSerializer):
    class Meta:
        model = Survey
        fields = ("id", "survey_no", "survey_date", "status",
                  "approved_by", "remark")
        read_only_fields = ("status", "approved_by")


class TreeRecordSerializer(serializers.ModelSerializer):
    """树木记录：dbh/height 的值与单位必须成对出现。"""

    class Meta:
        model = TreeRecord
        fields = ("id", "plot", "survey", "tag", "species_code", "status",
                  "geom", "plot_x_m", "plot_y_m",
                  "dbh_value", "dbh_unit",
                  "height_value", "height_unit", "measured_on", "remark")

    def validate(self, attrs):
        tag = attrs.get("tag", getattr(self.instance, "tag", "?"))
        # 部分更新(PATCH)时未提供的字段沿用实例值；None 表示显式缺测，允许
        def pick(field, default):
            if field in attrs:
                return attrs[field]
            return getattr(self.instance, field, default)
        try:
            validate_record_units(
                tag=tag,
                dbh_value=pick("dbh_value", None),
                dbh_unit=pick("dbh_unit", "cm"),
                height_value=pick("height_value", None),
                height_unit=pick("height_unit", "m"),
            )
        except UnitPlausibilityError as exc:
            # 单位错误不是 400 格式问题，而是 422 语义不可处理：列入待核实
            raise serializers.ValidationError({
                "detail": str(exc),
                "code": "unit_plausibility",
            }) from exc
        except UnitConflictError as exc:
            raise serializers.ValidationError({
                "detail": str(exc),
                "code": "unit_conflict",
            }) from exc
        return attrs


class TagCrosswalkSerializer(serializers.ModelSerializer):
    class Meta:
        model = TagCrosswalk
        fields = ("id", "plot", "survey_t1", "survey_t2",
                  "tag_t1", "tag_t2", "confirmed_by", "note")


class IdentityReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdentityReview
        fields = ("id", "plot", "survey_t1", "survey_t2", "tag_t1", "tag_t2",
                  "distance_m", "kind", "status", "raised_by",
                  "resolution_note", "created_at", "resolved_at")
        read_only_fields = ("created_at", "resolved_at")


class EquationReleaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquationReleaseModel
        fields = ("id", "release_id", "published_on", "description",
                  "payload", "is_active")

    def validate_payload(self, payload):
        # 复用核心的发布校验：形式不支持/ID 重复会直接拒绝
        from .services import build_release_from_payload
        build_release_from_payload(payload)
        return payload


class AnalysisRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisRun
        fields = ("id", "survey_t1", "survey_t2", "equation_release", "status",
                  "result_payload", "params", "created_by", "created_at",
                  "supersedes")
        read_only_fields = ("status", "result_payload", "created_at")
