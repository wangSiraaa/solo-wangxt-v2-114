"""DRF 视图：调查数据 CRUD、复测匹配预览、分析运行（含方程冻结保护）。"""

from django.conf import settings
from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.allometry import FrozenReleaseError, SpeciesNotCoveredError
from core.components import PlotInputs
from core.remeasure import TreeObs, TreeStatus, match_trees
from core.units import UnitConflictError, UnitPlausibilityError
from inventory.models import (
    AnalysisRun, EquationReleaseModel, IdentityReview, Plot, Stratum, Survey,
    TagCrosswalk, TreeRecord,
)

from .serializers import (
    AnalysisRunSerializer, EquationReleaseSerializer, IdentityReviewSerializer,
    PlotSerializer, StratumSerializer, SurveySerializer, TagCrosswalkSerializer,
    TreeRecordSerializer,
)
from .services import get_release, run_analysis, tree_obs_from_record

F = settings.FOREST


def _exception_response(exc, code, http_status):
    return Response({"detail": str(exc), "code": code}, status=http_status)


class StratumViewSet(viewsets.ModelViewSet):
    queryset = Stratum.objects.all()
    serializer_class = StratumSerializer


class PlotViewSet(viewsets.ModelViewSet):
    queryset = Plot.objects.select_related("stratum").all()
    serializer_class = PlotSerializer


class SurveyViewSet(viewsets.ModelViewSet):
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        """确认调查版：确认后锁定，写入新数据需走修正流程。"""
        survey = self.get_object()
        if survey.status == "approved":
            return Response({"detail": "该调查版本已确认，不可重复确认"},
                            status=status.HTTP_409_CONFLICT)
        survey.status = "approved"
        survey.approved_by = request.data.get("approved_by", "")
        survey.save(update_fields=["status", "approved_by"])
        return Response(SurveySerializer(survey).data)


class TreeRecordViewSet(viewsets.ModelViewSet):
    queryset = TreeRecord.objects.select_related("plot", "survey").all()
    serializer_class = TreeRecordSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("plot"):
            qs = qs.filter(plot_id=params["plot"])
        if params.get("survey"):
            qs = qs.filter(survey_id=params["survey"])
        return qs


class TagCrosswalkViewSet(viewsets.ModelViewSet):
    queryset = TagCrosswalk.objects.all()
    serializer_class = TagCrosswalkSerializer


class IdentityReviewViewSet(viewsets.ModelViewSet):
    queryset = IdentityReview.objects.all()
    serializer_class = IdentityReviewSerializer

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        from django.utils import timezone
        review = self.get_object()
        review.status = request.data.get("status", review.status)
        review.resolution_note = request.data.get("resolution_note", "")
        review.resolved_at = timezone.now()
        review.save(update_fields=["status", "resolution_note", "resolved_at"])
        return Response(IdentityReviewSerializer(review).data)


class EquationReleaseViewSet(viewsets.ModelViewSet):
    """方程版本只增不改；删除/覆盖已发布版本被禁止。"""

    queryset = EquationReleaseModel.objects.all()
    serializer_class = EquationReleaseSerializer

    def destroy(self, request, *args, **kwargs):
        return Response({"detail": "方程 release 一经发布即冻结，禁止删除"},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        return Response({"detail": "方程 release 不可修改，请发布新版本"},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)


class AnalysisRunViewSet(viewsets.ModelViewSet):
    queryset = AnalysisRun.objects.select_related(
        "survey_t1", "survey_t2", "equation_release").all()
    serializer_class = AnalysisRunSerializer

    @action(detail=False, methods=["post"])
    def execute(self, request):
        """按 (survey_t1, survey_t2, release) 执行分层分析。

        已确认 run 换方程必须显式 ``allow_recreate=true``，
        且系统会新建 run（旧 run 保留），绝不静默覆盖。
        """
        try:
            return self._execute(request)
        except FrozenReleaseError as exc:
            return _exception_response(exc, "frozen_release",
                                       status.HTTP_409_CONFLICT)
        except (UnitPlausibilityError, UnitConflictError) as exc:
            return _exception_response(exc, "unit_error",
                                       status.HTTP_422_UNPROCESSABLE_ENTITY)
        except SpeciesNotCoveredError as exc:
            return _exception_response(exc, "species_not_covered",
                                       status.HTTP_422_UNPROCESSABLE_ENTITY)

    def _execute(self, request):
        s1 = Survey.objects.get(pk=request.data["survey_t1"])
        s2 = Survey.objects.get(pk=request.data["survey_t2"])
        release_model = EquationReleaseModel.objects.get(
            pk=request.data["equation_release"])
        allow_recreate = bool(request.data.get("allow_recreate", False))

        plots = list(Plot.objects.select_related("stratum"))
        plot_inputs, areas = [], {}
        for plot in plots:
            t1_recs = list(TreeRecord.objects.filter(plot=plot, survey=s1))
            t2_recs = list(TreeRecord.objects.filter(plot=plot, survey=s2))
            crosswalk = dict(
                TagCrosswalk.objects.filter(
                    plot=plot, survey_t1=s1, survey_t2=s2
                ).values_list("tag_t1", "tag_t2"))
            plot_inputs.append(PlotInputs(
                plot_id=plot.plot_id, area_ha=plot.area_ha,
                stratum_id=plot.stratum.code,
                t1=[tree_obs_from_record(r) for r in t1_recs],
                t2=[tree_obs_from_record(r) for r in t2_recs],
                crosswalk=crosswalk,
                ingrowth_threshold_cm=F["INGROWTH_THRESHOLD_CM"],
                xy_tolerance_m=F["XY_TOLERANCE_M"],
                zero_growth_epsilon_cm=F["ZERO_GROWTH_EPSILON_CM"],
            ))
            areas[plot.stratum.code] = plot.stratum.area_ha

        run = AnalysisRun(survey_t1=s1, survey_t2=s2,
                          equation_release=release_model,
                          params=dict(F),
                          created_by=request.data.get("created_by", ""))
        payload = run_analysis(
            run=run, release_model=release_model,
            plot_inputs_by_id={p.plot_id: p for p in plot_inputs},
            stratum_areas_ha=areas, allow_recreate=allow_recreate,
        )
        run.result_payload = payload
        with transaction.atomic():
            run.save()
            self._raise_identity_reviews(run, plot_inputs, payload)
        return Response(AnalysisRunSerializer(run).data,
                        status=status.HTTP_201_CREATED)

    def _raise_identity_reviews(self, run, plot_inputs, payload):
        """位置矛盾/缺测挂起项写入人工核实队列。"""
        by_plot = {p["plot_id"]: p for p in payload["plots"]}
        for inp in plot_inputs:
            p = by_plot[inp.plot_id]
            plot = Plot.objects.get(plot_id=inp.plot_id)
            for pair in p["pairs"]:
                if pair["status"] == "unresolved_location_conflict":
                    kind = "location_conflict"
                elif pair["status"] == "unresolved_missing":
                    kind = "missing_unresolved"
                else:
                    continue
                IdentityReview.objects.get_or_create(
                    plot=plot, survey_t1=run.survey_t1, survey_t2=run.survey_t2,
                    tag_t1=pair["tag_t1"] or "", tag_t2=pair["tag_t2"] or "",
                    defaults={"kind": kind,
                              "distance_m": pair["distance_m"],
                              "raised_by": run.created_by,
                              "resolution_note": pair["note"]},
                )

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        run = self.get_object()
        if run.status == "approved":
            return Response({"detail": "分析运行已确认"},
                            status=status.HTTP_409_CONFLICT)
        run.status = "approved"
        run.save(update_fields=["status"])
        return Response(AnalysisRunSerializer(run).data)


class RemeasurePreviewView(viewsets.ViewSet):
    """不落库，仅预览某样地两期复测匹配结果（供前端连线与核实）。"""

    def list(self, request):
        plot = Plot.objects.get(plot_id=request.query_params["plot"])
        s1 = Survey.objects.get(pk=request.query_params["survey_t1"])
        s2 = Survey.objects.get(pk=request.query_params["survey_t2"])
        t1 = [tree_obs_from_record(r)
              for r in TreeRecord.objects.filter(plot=plot, survey=s1)]
        t2 = [tree_obs_from_record(r)
              for r in TreeRecord.objects.filter(plot=plot, survey=s2)]
        crosswalk = dict(TagCrosswalk.objects.filter(
            plot=plot, survey_t1=s1, survey_t2=s2
        ).values_list("tag_t1", "tag_t2"))
        pairs = match_trees(
            t1=t1, t2=t2, crosswalk=crosswalk,
            xy_tolerance_m=float(request.query_params.get(
                "xy_tolerance_m", F["XY_TOLERANCE_M"])),
            ingrowth_threshold_cm=float(request.query_params.get(
                "ingrowth_threshold_cm", F["INGROWTH_THRESHOLD_CM"])),
        )
        return Response([
            {"status": p.status.value,
             "tag_t1": p.t1.tag if p.t1 else None,
             "tag_t2": p.t2.tag if p.t2 else None,
             "distance_m": p.distance_m,
             "matched_via": p.matched_via, "note": p.note}
            for p in pairs
        ])
